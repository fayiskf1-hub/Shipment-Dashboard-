#!/usr/bin/env python3
"""Static QA for a single-file HTML dashboard. Fast, no browser, no network.

Usage:  python check_dashboard.py dashboard.html
Exit code 1 if any ERROR is found; WARNs are advice.

For the rendered checks (console errors, overflow at phone width, screenshots in
light + dark) run scripts/render_check.mjs as well.
"""
import re
import sys
from pathlib import Path

ALLOWED_CDN = ("cdnjs.cloudflare.com", "cdn.jsdelivr.net/npm/", "unpkg.com", "cdn.tailwindcss.com", "code.jquery.com")
VERSION_RE = re.compile(r"(@|/)\d+\.\d+\.\d+")


def main(path):
    html = Path(path).read_text(encoding="utf-8")
    errors, warns, ok = [], [], []

    def check(cond, msg, level="error"):
        if cond:
            ok.append(msg)
        else:
            (errors if level == "error" else warns).append(msg)

    check(html.lstrip().lower().startswith("<!doctype html"), "starts with <!doctype html>")
    check(re.search(r"<meta[^>]+charset", html, re.I), "declares a charset")
    check(re.search(r'<meta[^>]+name=["\']viewport', html, re.I), "has a viewport meta (mobile)")
    check(re.search(r"<html[^>]+lang=", html, re.I), "<html> has a lang attribute", "warn")
    t = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    check(t and 0 < len(t.group(1).split()) <= 6, "has a short <title> (1–6 words)")

    # External scripts / styles: allowed hosts, exact pinned versions
    for src in re.findall(r'<script[^>]+src=["\']([^"\']+)', html, re.I):
        if not src.startswith("http"):
            continue
        check(any(h in src for h in ALLOWED_CDN), f"script host allowed: {src}")
        check(VERSION_RE.search(src) and "latest" not in src, f"script version pinned: {src}")
    for href in re.findall(r'<link[^>]+href=["\'](https?://[^"\']+)', html, re.I):
        check("fonts.googleapis.com" in href or "fonts.gstatic.com" in href, f"only Google Fonts stylesheets: {href}", "warn")

    # Theming
    check(":root" in html and "--" in html, "colours defined as CSS custom properties")
    check("prefers-color-scheme: dark" in html or "prefers-color-scheme:dark" in html, "has a dark-mode block")
    check('[data-theme="dark"]' in html or "[data-theme=dark]" in html, "manual dark override ([data-theme=\"dark\"])", "warn")
    check(re.search(r"body\s*\{[^}]*background", html), "body has an explicit background")
    hexes_outside_root = re.findall(r"#[0-9a-fA-F]{6}\b", re.sub(r":root[^{]*\{[^}]*\}", "", re.sub(r"@media[^{]*\{\s*:root[^{]*\{[^}]*\}\s*\}", "", html)))
    check(len(hexes_outside_root) <= 6, f"few hard-coded hex colours outside tokens ({len(hexes_outside_root)} found)", "warn")

    # Layout / responsiveness
    check("@media" in html, "has responsive @media rules")
    check(re.search(r"overflow-x\s*:\s*auto", html), "wide tables sit in an overflow-x:auto wrapper", "warn")
    check("tabular-nums" in html, "numbers use tabular-nums", "warn")

    # Data & JS hygiene
    check(not re.search(r"fetch\(\s*['\"]https?://", html), "no runtime fetch to external URLs (self-contained)", "warn")
    check("localStorage" not in html or "try" in html, "localStorage access guarded by try/catch")
    check(not re.search(r"Math\.random\(", html), "no Math.random (demo data should be seeded / reproducible)", "warn")
    check("Intl.NumberFormat" in html or "toLocaleString" in html, "numbers formatted with Intl / toLocaleString", "warn")
    check(re.search(r"aria-label|role=\"img\"", html), "charts/controls carry aria labels", "warn")
    check(not re.search(r"\b(TODO|FIXME|lorem ipsum)\b", html, re.I), "no TODO / lorem ipsum left in", "warn")

    size_kb = len(html.encode()) / 1024
    check(size_kb < 5000, f"file size {size_kb:,.0f} KB (< 5 MB)", "warn")

    for m in ok:
        if m:
            print(f"  ok    {m}")
    for m in warns:
        print(f"  WARN  {m}")
    for m in errors:
        print(f"  ERROR {m}")
    print(f"\n{len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
