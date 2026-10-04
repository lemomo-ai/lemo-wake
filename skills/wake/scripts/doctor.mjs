// Environment check - run it the first time. Says what is missing and how to install it; --fix installs
// what it can (npm deps + headless browser, ~190 MB).
// Usage: node doctor.mjs [--fix]
// Installs only what this skill uses: scripts/node_modules and Playwright's chromium-headless-shell
// (--no-remove: your other browsers are left alone). ffmpeg / uv are system tools: only the install command is shown.
import { execSync, spawnSync } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SKILL = path.dirname(HERE);
const FIX = process.argv.includes('--fix');
const rows = []; let bad = 0;
const ok = (k, v) => rows.push(['ok  ', k, v]);
const no = (k, v) => { rows.push(['MISS', k, v]); bad++; };
const has = cmd => spawnSync(process.platform === 'win32' ? 'where' : 'which', [cmd], { stdio: 'ignore' }).status === 0;
const ver = cmd => { try { return execSync(cmd, { stdio: ['ignore', 'pipe', 'ignore'] }).toString().split('\n')[0].trim(); } catch { return ''; } };
const hint = {
  darwin: { ffmpeg: 'brew install ffmpeg', uv: 'brew install uv' },
  linux: { ffmpeg: 'sudo apt install ffmpeg', uv: 'curl -LsSf https://astral.sh/uv/install.sh | sh' },
  win32: { ffmpeg: 'winget install Gyan.FFmpeg', uv: 'winget install astral-sh.uv' },
}[process.platform] || { ffmpeg: 'install ffmpeg', uv: 'install uv (https://docs.astral.sh/uv/)' };

// Node
const nodeMajor = parseInt(process.versions.node);
nodeMajor >= 18 ? ok('Node', process.versions.node) : no('Node', `${process.versions.node}, need >= 18`);

// npm deps
const pw = path.join(HERE, 'node_modules', 'playwright-core');
if (!fs.existsSync(pw) && FIX) { console.log('installing npm dependencies...'); execSync('npm install --silent', { cwd: HERE, stdio: 'inherit' }); }
fs.existsSync(pw) ? ok('playwright-core', JSON.parse(fs.readFileSync(path.join(pw, 'package.json'))).version) : no('playwright-core', `not installed -> (cd "${HERE}" && npm install), or node doctor.mjs --fix`);

// browser
let exe = null;
if (fs.existsSync(pw)) {
  const { findChromium } = await import('./render.mjs');
  exe = findChromium();
  if (!exe && FIX) {
    console.log('installing chromium-headless-shell (~190 MB)...');
    execSync(`node "${path.join(pw, 'cli.js')}" install --only-shell --no-remove chromium`, { stdio: 'inherit' });
    exe = findChromium();
  }
}
exe ? ok('browser', exe) : no('browser', 'not found -> node doctor.mjs --fix, or set CHROME=<path to Chrome/Chromium>');
// found is not enough: start it once (agent sandboxes can block the browser from starting)
if (exe) {
  try {
    const { chromium } = await import('playwright-core');
    const b = await chromium.launch({ executablePath: exe, timeout: 30000 }); await b.close();
    ok('browser start', 'ok');
  } catch (e) {
    const line = String(e.message || e).split('\n').find(l => /Permission denied|denied|EPERM/i.test(l)) || String(e.message || e).split('\n')[0];
    no('browser start', `failed: ${line.slice(0, 160)} -> in an agent sandbox, run render.mjs with permission to run outside the sandbox`);
  }
}

// system tools
for (const k of ['ffmpeg', 'ffprobe', 'uv']) {
  if (has(k)) ok(k, ver(`${k} ${k === 'uv' ? '--version' : '-version'}`).slice(0, 60));
  else no(k, `not found -> ${hint[k === 'ffprobe' ? 'ffmpeg' : k]}`);
}

// local models (optional, downloaded on first use after a one-time consent) - same lookup as _models.py
function modelsDir() {
  const env = (process.env.LEMO_WAKE_MODELS || '').trim();
  // ignore placeholders and another plugin's data folder (a shell may carry another plugin's CLAUDE_PLUGIN_DATA)
  const ep = env.split(/[\\/]+/), di = ep.findIndex((p, i) => p === 'plugins' && ep[i + 1] === 'data');
  const foreign = di >= 0 && ep[di + 2] !== undefined && !ep[di + 2].toLowerCase().includes('lemo-wake');
  const badEnv = foreign || env.includes('${') || env.includes('CLAUDE_PLUGIN_DATA') || ['/models', '\\models', 'models'].includes(env.replace(/[\\/]+$/, ''));
  if (env && !badEnv) return env.replace(/^~(?=$|[\\/])/, os.homedir());
  const parts = fs.realpathSync(SKILL).split(path.sep);
  for (let i = 0; i < parts.length - 3; i++) if (parts[i] === 'plugins' && parts[i + 1] === 'cache') {
    const clean = s => s.replace(/[^A-Za-z0-9_-]/g, '-');
    return path.join(parts.slice(0, i + 1).join(path.sep) || path.sep, 'data', `${clean(parts[i + 3])}-${clean(parts[i + 2])}`, 'models');
  }
  return path.join(SKILL, 'models');
}
const mdir = modelsDir();
const legacy = path.join(os.homedir(), '.cache', 'lemo-wake', 'models');
const onnx = d => fs.existsSync(d) ? fs.readdirSync(d).filter(f => f.endsWith('.onnx')) : [];
const got = new Set([...onnx(mdir), ...onnx(legacy)]);
let consent = got.size >= 6 ? 'not needed (models already installed)' : 'not asked yet (asked only when a missing model must be downloaded)';
try { consent = JSON.parse(fs.readFileSync(path.join(mdir, 'consent.json'))).download ? 'yes' : 'declined'; } catch {}
rows.push(['info', 'local models', `${got.size}/6 files present; download consent: ${consent}; folder: ${mdir}` + (onnx(legacy).length ? ` (also reusing ${legacy})` : '')]);

for (const [i, k, v] of rows) console.log(`${i} ${k.padEnd(16)} ${v}`);
console.log(bad ? `\n${bad} item(s) missing - install them as shown above, then start.` : '\nReady.');
process.exit(bad ? 1 : 0);
