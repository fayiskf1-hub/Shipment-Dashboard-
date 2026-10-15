#!/usr/bin/env node
// Render a dashboard in headless Chromium and catch what static checks can't:
// JS errors, failed requests, horizontal overflow at phone width, empty charts.
// Saves desktop-light, desktop-dark and mobile screenshots for a visual review.
//
// Usage:
//   node render_check.mjs dashboard.html [--out shots/] [--lib URL=local/file.js ...]
//
// --lib lets you serve a CDN script from a local file when the sandbox has no
// internet, e.g. --lib https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js=./chart.umd.js
// (get the file with: npm pack chart.js@4.4.1 && tar xzf chart.js-4.4.1.tgz -> package/dist/chart.umd.js)

import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';

async function loadPlaywright() {
  try { return await import('playwright'); } catch {}
  try {
    const root = execSync('npm root -g', { encoding: 'utf8' }).trim();
    return createRequire(path.join(root, 'noop.js'))('playwright');
  } catch {
    console.error('playwright not found. Install with: npm i -g playwright (browsers: npx playwright install chromium)');
    process.exit(2);
  }
}

const args = process.argv.slice(2);
const file = args.find(a => !a.startsWith('--') && !args[args.indexOf(a) - 1]?.startsWith('--'));
if (!file) { console.error('usage: node render_check.mjs dashboard.html [--out dir] [--lib URL=file]'); process.exit(2); }
const outDir = args.includes('--out') ? args[args.indexOf('--out') + 1] : path.join(path.dirname(file), 'shots');
const libs = Object.fromEntries(args.flatMap((a, i) => a === '--lib' ? [args[i + 1].split(/=(.+)/).slice(0, 2)] : []));
fs.mkdirSync(outDir, { recursive: true });

const { chromium } = await loadPlaywright();
const exe = process.env.PW_EXEC; // optional explicit Chromium path
const browser = await chromium.launch(exe ? { executablePath: exe } : {});
const url = pathToFileURL(path.resolve(file)).href;
const problems = [];

async function run(name, viewport, colorScheme) {
  const page = await browser.newPage({ viewport, colorScheme });
  const errs = [];
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  page.on('console', m => m.type() === 'error' && errs.push('console: ' + m.text()));
  page.on('requestfailed', r => errs.push('request failed: ' + r.url()));
  await page.route('**/*', route => {
    const u = route.request().url();
    if (libs[u]) return route.fulfill({ path: libs[u], contentType: 'application/javascript' });
    return route.continue();
  });
  await page.goto(url, { waitUntil: 'load' });
  await page.waitForTimeout(400);
  const m = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    canvases: [...document.querySelectorAll('canvas')].map(c => ({ id: c.id, w: c.width, h: c.height, empty: !!c.closest('.is-empty') })),
    chartLib: typeof window.Chart !== 'undefined' || typeof window.echarts !== 'undefined' || typeof window.Plotly !== 'undefined' || typeof window.d3 !== 'undefined',
    textLen: document.body.innerText.length,
  }));
  if (m.overflow > 1) errs.push(`horizontal overflow of ${m.overflow}px at ${viewport.width}px wide`);
  if (m.canvases.length && !m.chartLib) errs.push('canvases present but no chart library loaded');
  m.canvases.filter(c => !c.empty && (c.w < 50 || c.h < 50)).forEach(c => errs.push(`chart #${c.id} rendered tiny (${c.w}x${c.h})`));
  const shot = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: shot, fullPage: true });
  console.log(`${errs.length ? 'FAIL' : 'ok  '} ${name.padEnd(14)} ${viewport.width}x${viewport.height} ${colorScheme}  -> ${shot}`);
  errs.forEach(e => console.log('       ' + e));
  problems.push(...errs);
  await page.close();
}

await run('desktop-light', { width: 1440, height: 900 }, 'light');
await run('desktop-dark', { width: 1440, height: 900 }, 'dark');
await run('mobile-light', { width: 390, height: 844 }, 'light');
await browser.close();
console.log(problems.length ? `\n${problems.length} problem(s)` : '\nall render checks passed');
process.exit(problems.length ? 1 : 0);
