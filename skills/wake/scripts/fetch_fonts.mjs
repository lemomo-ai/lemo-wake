// Download Google Fonts locally (rendering needs no network and every frame uses the same font)
// Usage: node fetch_fonts.mjs <srcDir> "family=Anton" "family=Archivo:wght@500;700;900" "family=Noto+Serif+JP:wght@700;900&text=紙上都市"
// - CJK fonts: always add &text= (only the characters used, tens of KB; otherwise dozens of slices, several MB)
// - cyrillic/greek/vietnamese slices are dropped automatically
// Output: <srcDir>/fonts/*.woff2 + <srcDir>/fonts.css (appended; can be called repeatedly)
import fs from 'fs';
import path from 'path';
const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36';
const [srcDir, ...fams] = process.argv.slice(2);
if (!srcDir || !fams.length) { console.log('usage: node fetch_fonts.mjs <srcDir> "family=..." ...'); process.exit(1); }
const fdir = path.join(srcDir, 'fonts'); fs.mkdirSync(fdir, { recursive: true });
const cssPath = path.join(srcDir, 'fonts.css');
let out = fs.existsSync(cssPath) ? fs.readFileSync(cssPath, 'utf8') : '';
let n = fs.readdirSync(fdir).length;
for (let f of fams) {
  f = f.replace(/&text=([^&]+)/, (_, t) => '&text=' + encodeURIComponent(decodeURIComponent(t)));
  const res = await fetch(`https://fonts.googleapis.com/css2?${f}&display=block`, { headers: { 'User-Agent': UA } });
  if (!res.ok) { console.error('failed', f, res.status); continue; }
  let css = await res.text();
  const blocks = css.split('}').filter(b => b.includes('@font-face')).filter(b => !/\/\* (cyrillic|greek|vietnamese)/.test(b));
  css = blocks.map(b => b + '}').join('\n');
  for (const u of [...new Set(css.match(/https:\/\/[^)]+/g) || [])]) {
    const name = `f${n++}.woff2`;
    fs.writeFileSync(path.join(fdir, name), Buffer.from(await (await fetch(u)).arrayBuffer()));
    css = css.split(u).join('fonts/' + name);
  }
  out += `/* ${f} */\n` + css + '\n';
  console.log('ok', f);
}
fs.writeFileSync(cssPath, out);
