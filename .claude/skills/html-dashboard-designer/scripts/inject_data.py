#!/usr/bin/env python3
"""Load a CSV / XLSX / JSON file, clean it, and embed it in a dashboard HTML file.

The dashboard must contain the markers  /*DATA_START*/ ... /*DATA_END*/  around
its data literal (the bundled template does). Everything between them is replaced
with a compact JSON array of row objects.

Usage
  python inject_data.py data.xlsx dashboard.html                 # in-place
  python inject_data.py data.csv template.html -o out.html       # write a copy
  python inject_data.py data.csv --profile                       # just describe the data
  python inject_data.py data.xlsx --sheet "Shipments" --rename "Ship Date=ship_date,ETA=eta" -o out.html template.html

Cleaning applied
  * column names -> snake_case (unless --keep-names), then --rename applied
  * dates / datetimes -> 'YYYY-MM-DD' strings (what the template's date helpers expect)
  * numeric-looking strings ("1,234.50", "12%") -> numbers
  * blanks / NaN -> null
  * '</' escaped so the JSON can never close the <script> tag early
"""
import argparse
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

START, END = "/*DATA_START*/", "/*DATA_END*/"
NUM_RE = re.compile(r"^\s*[-+]?[\d,]*\.?\d+(?:[eE][-+]?\d+)?\s*%?\s*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?$")
DMY_RE = re.compile(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$")


def snake(name: str) -> str:
    s = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip()).strip("_")
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower() or "col"


def clean_value(v, dayfirst: bool):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, (dt.datetime, dt.date)):
        return v.strftime("%Y-%m-%d")
    if hasattr(v, "to_pydatetime"):  # pandas Timestamp
        try:
            return v.to_pydatetime().strftime("%Y-%m-%d")
        except ValueError:
            return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return int(v) if float(v).is_integer() and abs(v) < 2**53 else float(v)
    s = str(v).strip()
    if s == "" or s.lower() in {"nan", "nat", "null", "none", "n/a", "#n/a", "-"}:
        return None
    if DATE_RE.match(s):
        return s[:10]
    m = DMY_RE.match(s)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        d, mo = (a, b) if dayfirst else (b, a)
        try:
            return dt.date(y, mo, d).isoformat()
        except ValueError:
            return s
    if NUM_RE.match(s) and not re.match(r"^0\d", s.replace(",", "")):  # keep IDs like 00123 as text
        n = float(s.replace(",", "").replace("%", ""))
        if s.endswith("%"):
            n /= 100
        return int(n) if n.is_integer() and "." not in s else n
    return s


def load(path: Path, sheet):
    ext = path.suffix.lower()
    if ext == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):  # {"rows": [...]} or {"data": [...]}
            data = next((v for v in data.values() if isinstance(v, list)), [])
        return data
    if ext in {".xlsx", ".xlsm", ".xls"}:
        import pandas as pd
        df = pd.read_excel(path, sheet_name=sheet or 0)
        return df.to_dict(orient="records")
    import csv
    raw = path.read_bytes()
    text = None
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|") if text.strip() else csv.excel
    return list(csv.DictReader(text.splitlines(), dialect=dialect))


def profile(rows):
    cols = list(rows[0].keys()) if rows else []
    print(f"{len(rows)} rows x {len(cols)} columns\n")
    print(f"{'column':28} {'type':8} {'nulls':>6} {'distinct':>8}  sample / range")
    for c in cols:
        vals = [r.get(c) for r in rows]
        nn = [v for v in vals if v is not None]
        types = {type(v).__name__ for v in nn}
        t = "date" if nn and all(isinstance(v, str) and DATE_RE.match(v) for v in nn) else "/".join(sorted(types)) or "empty"
        distinct = len({json.dumps(v) for v in nn})
        if t == "date" or t in {"int", "float", "float/int"}:
            rng = f"{min(nn)} .. {max(nn)}" if nn else ""
        else:
            rng = ", ".join(map(str, list(dict.fromkeys(nn))[:4]))
        print(f"{c[:28]:28} {t[:8]:8} {len(vals) - len(nn):6} {distinct:8}  {rng[:60]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data")
    ap.add_argument("html", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("--sheet")
    ap.add_argument("--rename", default="", help="'Old=new,Other=other' applied after snake_casing")
    ap.add_argument("--keep-names", action="store_true")
    ap.add_argument("--dayfirst", action="store_true", default=True, help="treat 03/04/2026 as 3 April (default)")
    ap.add_argument("--monthfirst", dest="dayfirst", action="store_false")
    ap.add_argument("--profile", action="store_true", help="print a column profile")
    ap.add_argument("--json-out", help="also write the cleaned rows to this .json file")
    args = ap.parse_args()

    rows = load(Path(args.data), args.sheet)
    renames = dict(p.split("=", 1) for p in args.rename.split(",") if "=" in p)
    renames.update({snake(k): v for k, v in list(renames.items())})
    cleaned = []
    for r in rows:
        out = {}
        for k, v in r.items():
            if k is None or str(k).startswith("Unnamed:"):
                continue
            key = str(k) if args.keep_names else snake(k)
            key = renames.get(str(k), renames.get(key, key))
            out[key] = clean_value(v, args.dayfirst)
        if any(v is not None for v in out.values()):
            cleaned.append(out)

    if args.profile or not args.html:
        profile(cleaned)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(cleaned, ensure_ascii=False), encoding="utf-8")
    if not args.html:
        return

    html_path = Path(args.html)
    html = html_path.read_text(encoding="utf-8")
    i, j = html.find(START), html.find(END)
    if i < 0 or j < i:
        sys.exit(f"error: markers {START} ... {END} not found in {html_path}")
    payload = json.dumps(cleaned, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html[: i + len(START)] + payload + html[j:]
    out = Path(args.out) if args.out else html_path
    out.write_text(html, encoding="utf-8")
    kb = len(payload.encode()) / 1024
    print(f"\nembedded {len(cleaned)} rows ({kb:,.0f} KB) -> {out}")
    if kb > 5000:
        print("warning: payload > 5 MB — pre-aggregate or drop unused columns; the page will be slow to open.")


if __name__ == "__main__":
    main()
