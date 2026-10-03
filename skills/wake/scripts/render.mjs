// Frame renderer (Playwright + headless Chromium). Page contract: window.CFG / window.render(t) / window.READY
// Usage:
//   node render.mjs <srcDir> stills 0.5 1.2 4.9      → <srcDir>/stills/t_<t>.png
//   node render.mjs <srcDir> frames [workers=4]      -> <srcDir>/frames/f_00000.jpg ... (FMT=png for PNG)
// Page errors, failed images and failed fonts go to <srcDir>/render.log and exit code 2 (qa.py reads it too).
// Browser lookup: env CHROME -> Playwright chromium-headless-shell / chromium -> installed Chrome.
import { chromium } from 'playwright-core';
import fs from 'fs';
import path from 'path';
import os from 'os';

function pwCacheDir() {
  if (process.env.PLAYWRIGHT_BROWSERS_PATH && process.env.PLAYWRIGHT_BROWSERS_PATH !== '0') return process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (process.platform === 'darwin') return path.join(os.homedir(), 'Library/Caches/ms-playwright');
  if (process.platform === 'win32') return path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData/Local'), 'ms-playwright');
  return path.join(process.env.XDG_CACHE_HOME || path.join(os.homedir(), '.cache'), 'ms-playwright');
}

export function findChromium() {
  if (process.env.CHROME) return process.env.CHROME;
  const base = pwCacheDir(), cands = [];
  const rels = [
    'chrome-headless-shell-mac-arm64/chrome-headless-shell', 'chrome-headless-shell-mac-x64/chrome-headless-shell',
    'chrome-headless-shell-linux64/chrome-headless-shell', 'chrome-headless-shell-win64/chrome-headless-shell.exe',
    'chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium',
    'chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',
    'chrome-linux/chrome', 'chrome-linux64/chrome', 'chrome-win/chrome.exe', 'chrome-win64/chrome.exe',
  ];
  if (fs.existsSync(base)) for (const d of fs.readdirSync(base)) for (const rel of rels) {
    const p = path.join(base, d, rel);
    if (fs.existsSync(p)) cands.push({ p, n: parseInt(d.split('-').pop()) || 0, shell: d.includes('headless_shell') });
  }
  cands.sort((a, b) => (b.shell - a.shell) || (b.n - a.n));
  if (cands.length) return cands[0].p;
  const sys = {
    darwin: ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium'],
    linux: ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser'],
    win32: [path.join(process.env['PROGRAMFILES'] || 'C:/Program Files', 'Google/Chrome/Application/chrome.exe'),
            path.join(process.env['PROGRAMFILES(X86)'] || 'C:/Program Files (x86)', 'Google/Chrome/Application/chrome.exe')],
  }[process.platform] || [];
  for (const p of sys) if (fs.existsSync(p)) return p;
  return null;
}

const isMain = import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('render.mjs');
if (isMain) {
  const srcDir = path.resolve(process.argv[2] || '.');
  const mode = process.argv[3];
  const URL = 'file://' + path.join(srcDir, 'index.html').split(path.sep).join('/').replace(/^([A-Za-z]):/, '/$1:');
  const EXE = findChromium();
  if (!EXE) { console.error('no browser found: run node <skill>/scripts/doctor.mjs --fix, or set CHROME=<browser path>'); process.exit(1); }
  const ARGS = ['--font-render-hinting=none', '--force-color-profile=srgb', '--allow-file-access-from-files', '--enable-gpu', '--ignore-gpu-blocklist'];
  if (process.platform === 'darwin') ARGS.push('--use-angle=metal');
  const FMT = process.env.FMT || 'jpg';
  const errors = new Set();

  async function openPage(browser) {
    const page = await browser.newPage({ viewport: { width: 800, height: 800 }, deviceScaleFactor: 1 });
    page.on('console', m => {
      if (m.type() !== 'error') return;
      const url = m.location()?.url || '';
      if (/favicon/.test(url)) return;
      errors.add(`[console] ${m.text()}${url ? ' @ ' + path.basename(url) : ''}`);
    });
    page.on('pageerror', e => errors.add(`[pageerror] ${e.message}`));
    page.on('requestfailed', r => { if (!/favicon/.test(r.url())) errors.add(`[load failed] ${path.basename(r.url())} ${r.failure()?.errorText || ''}`); });
    await page.goto(URL);
    const cfg = await page.evaluate(() => window.CFG);
    if (!cfg) throw new Error('page has no window.CFG (config.js not loaded?)');
    await page.setViewportSize({ width: cfg.outW, height: cfg.outH });
    await page.reload();
    await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
    const badFonts = await page.evaluate(() => [...document.fonts].filter(f => f.status === 'error').map(f => f.family));
    for (const f of badFonts) errors.add(`[font] ${f} failed to load (falls back to a system font)`);
    return { page, cfg };
  }

  function finish() {
    const log = path.join(srcDir, 'render.log');
    fs.writeFileSync(log, [...errors].join('\n') + (errors.size ? '\n' : ''));
    if (errors.size) { console.error(`render reported ${errors.size} error(s) (see ${log}):\n  ` + [...errors].slice(0, 8).join('\n  ')); process.exit(2); }
  }

  if (mode === 'stills') {
    const browser = await chromium.launch({ executablePath: EXE, args: ARGS });
    fs.mkdirSync(path.join(srcDir, 'stills'), { recursive: true });
    const { page } = await openPage(browser);
    for (const ts of process.argv.slice(4)) {
      await page.evaluate(t => window.render(t), parseFloat(ts));
      await page.screenshot({ path: path.join(srcDir, 'stills', `t_${ts}.png`) });
    }
    await browser.close();
    console.log('stills →', path.join(srcDir, 'stills'));
    finish();
  } else if (mode === 'frames') {
    const Wk = parseInt(process.argv[4] || String(Math.min(4, Math.max(1, os.cpus().length - 1))));
    const fdir = path.join(srcDir, 'frames');
    fs.rmSync(fdir, { recursive: true, force: true }); fs.mkdirSync(fdir, { recursive: true });
    const b0 = await chromium.launch({ executablePath: EXE, args: ARGS });
    const { cfg } = await openPage(b0); await b0.close();
    const TOTAL = Math.round(cfg.fps * cfg.dur);
    const per = Math.ceil(TOTAL / Wk), t0 = Date.now();
    await Promise.all([...Array(Wk)].map(async (_, w) => {
      const a = w * per, b = Math.min(TOTAL, a + per);
      if (a >= b) return;
      const br = await chromium.launch({ executablePath: EXE, args: ARGS });
      const { page } = await openPage(br);
      for (let f = a; f < b; f++) {
        await page.evaluate(t => window.render(t), f / cfg.fps);
        const buf = await page.screenshot(FMT === 'png' ? { type: 'png' } : { type: 'jpeg', quality: 95 });
        fs.writeFileSync(path.join(fdir, `f_${String(f).padStart(5, '0')}.${FMT}`), buf);
      }
      await br.close();
    }));
    console.log(`done ${TOTAL} frames (${cfg.outW}x${cfg.outH} @${cfg.fps}fps) in ${((Date.now() - t0) / 1000).toFixed(0)}s → ${fdir}`);
    finish();
  } else {
    console.log('usage: node render.mjs <srcDir> stills <t...> | frames [workers]');
    process.exit(1);
  }
}
