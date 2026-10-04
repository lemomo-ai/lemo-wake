// lemo-wake 工具库 —— 全部"随机访问"：给定 t 就能算出那一帧，不依赖上一帧的状态。
// （渲染时多个浏览器并行、乱序取帧；任何 t+=dt 式的累积状态都会穿帮。需要物理就用解析解，或每帧从 0 重算。）
// 设计坐标 = 原图像素（CFG.srcW × CFG.srcH）；用户选了别的输出尺寸时 = 输出像素（CFG.img 是原图尺寸）。#cam 里的一切都用这套坐标。
(function (G) {
const L = {};
// ---------------- 数学 / 缓动 ----------------
L.clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
L.lerp = (a, b, t) => a + (b - a) * t;
L.prog = (t, a, b) => L.clamp((t - a) / (b - a));           // t 在 [a,b] 内的 0..1 进度
L.mix = (a, b, t) => a.map((v, i) => L.lerp(v, b[i], t));
const P = Math.pow;
L.E = {
  linear: x => x,
  inQuad: x => x * x, outQuad: x => 1 - (1 - x) * (1 - x),
  inCubic: x => x * x * x, outCubic: x => 1 - P(1 - x, 3), inOutCubic: x => x < .5 ? 4 * x * x * x : 1 - P(-2 * x + 2, 3) / 2,
  outQuart: x => 1 - P(1 - x, 4), inOutQuart: x => x < .5 ? 8 * x ** 4 : 1 - P(-2 * x + 2, 4) / 2,
  inExpo: x => x <= 0 ? 0 : P(2, 10 * x - 10), outExpo: x => x >= 1 ? 1 : 1 - P(2, -10 * x),
  inOutExpo: x => x <= 0 ? 0 : x >= 1 ? 1 : x < .5 ? P(2, 20 * x - 10) / 2 : (2 - P(2, -20 * x + 10)) / 2,
  inOutSine: x => -(Math.cos(Math.PI * x) - 1) / 2,
  outBack: (x, s = 1.70158) => 1 + (s + 1) * P(x - 1, 3) + s * P(x - 1, 2),
  inBack: (x, s = 1.70158) => (s + 1) * x * x * x - s * x * x,
  outElastic: x => x <= 0 ? 0 : x >= 1 ? 1 : P(2, -10 * x) * Math.sin((x * 10 - .75) * (2 * Math.PI) / 3) + 1,
};
// 分段关键帧：kf(t, [[0, 0], [0.4, 120, 'outExpo'], [1.2, 80, 'inOutCubic']]) —— 每段的 ease 写在段终点
L.kf = (t, keys) => {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    const [t1, v1, e] = keys[i], [t0, v0] = keys[i - 1];
    if (t <= t1) { const f = (L.E[e] || L.E.inOutCubic)(L.prog(t, t0, t1)); return Array.isArray(v0) ? L.mix(v0, v1, f) : L.lerp(v0, v1, f); }
  }
  return keys[keys.length - 1][1];
};
// 阻尼弹簧（解析解）：从 t0 开始，从 from 弹到 to
L.spring = (t, t0, from, to, freq = 6, damp = 5) => {
  if (t < t0) return from; const x = t - t0;
  return to + (from - to) * Math.exp(-damp * x) * Math.cos(freq * 2 * Math.PI * x);
};
// 无缝循环：用"整数圈数"的周期函数，t=0 与 t=dur 完全一致（循环结构必用）
L.cyc = (t, n = 1, phase = 0) => Math.sin(2 * Math.PI * (n * t / CFG.dur + phase));
L.loopNoise = (t, seed = 0, r = 1) => { const a = 2 * Math.PI * t / CFG.dur; return L.noise(seed + Math.cos(a) * r) * .6 + L.noise(seed + 50 + Math.sin(a) * r) * .6; }; // 圆周采样噪声，首尾闭合
// 冲击抖动：t0 起衰减的正弦，返回 [-1,1]
L.shake = (t, t0, dur = .35, freq = 32) => t < t0 || t > t0 + dur ? 0 : Math.exp(-(t - t0) * 9) * Math.sin((t - t0) * freq * 2 * Math.PI / 4.5);
// 种子随机 & 1D 值噪声（平滑、可复现）
L.rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
L.hash = n => { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); };
L.noise = x => { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return L.lerp(L.hash(i), L.hash(i + 1), u) * 2 - 1; };
L.fbm = (x, o = 3) => { let v = 0, a = .5, f = 1; for (let i = 0; i < o; i++) { v += a * L.noise(x * f + i * 17.3); a *= .5; f *= 2; } return v; };

// ---------------- 资源 ----------------
L.loadImg = src => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.onerror = () => { console.error('img fail ' + src); r(null); }; i.src = src; });
// fonts: ['400 100px Anton', ['900 100px "Noto Serif JP"', '紙']]
L.loadFonts = async list => { for (const f of list) Array.isArray(f) ? await document.fonts.load(f[0], f[1]) : await document.fonts.load(f); await document.fonts.ready; };
L.el = (tag, cls, parent, style = {}, html = '') => { const e = document.createElement(tag); if (cls) e.className = cls; Object.assign(e.style, style); if (html) e.innerHTML = html; if (parent) parent.appendChild(e); return e; };
L.canvas = (w, h, K = 3) => { const c = document.createElement('canvas'); c.width = Math.round(w * K); c.height = Math.round(h * K); const x = c.getContext('2d'); x.scale(K, K); c.K = K; return [c, x]; };
// 从原图裁一块做成 canvas（作为素材时用；注意：整体不要靠"裁原图平移"糊弄，见 SKILL.md）
L.crop = (img, x, y, w, h, K = 2) => { const [c, g] = L.canvas(w, h, K); g.drawImage(img, x, y, w, h, 0, 0, w, h); return c; };

// ---------------- 质感 ----------------
// 印刷油墨质感：细小脱墨点 + 极淡浓度起伏。amt 控制强度，0.5~1 足够；过量会像星空。
L.inkify = (ctx, w, h, seed = 1, amt = 1, K = 3) => {
  const R = L.rng(seed); ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalCompositeOperation = 'destination-out';
  for (let i = 0; i < w * h / 5000 * amt; i++) { const x = R() * w, y = R() * h, r = (0.3 + R() * R() * 1.4) * K * .5; ctx.globalAlpha = .2 + R() * .6; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); }
  for (let i = 0; i < w * h / 60000 * amt; i++) { const x = R() * w, y = R() * h, r = (20 + R() * 70) * K * .5; const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, `rgba(0,0,0,${.02 + R() * .05})`); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.globalAlpha = 1; ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r); }
  ctx.restore();
};
// 把一个字形精确塞进 box（设计坐标），返回高分辨率 canvas。量好原图里字母的边界再塞，别目测。
L.glyph = (ch, font, box, color, { K = 3, pad = 0, ink = 0, seed = 1 } = {}) => {
  const [c, x] = L.canvas(box.w + pad * 2, box.h + pad * 2, K); x.font = font; const m = x.measureText(ch);
  const gw = m.actualBoundingBoxLeft + m.actualBoundingBoxRight, gh = m.actualBoundingBoxAscent + m.actualBoundingBoxDescent;
  x.save(); x.translate(pad, pad); x.scale(box.w / gw, box.h / gh); x.fillStyle = color; x.fillText(ch, m.actualBoundingBoxLeft, m.actualBoundingBoxAscent); x.restore();
  if (ink) L.inkify(x, c.width, c.height, seed, ink, K); return c;
};
// 静态胶片颗粒（multiply 叠加）。静态比逐帧闪烁更高级，GIF 也更小。
L.grain = (cv, seed = 42, lo = 200) => { const g = cv.getContext('2d'), id = g.createImageData(cv.width, cv.height), R = L.rng(seed); for (let i = 0; i < id.data.length; i += 4) { const v = lo + R() * (255 - lo); id.data[i] = v; id.data[i + 1] = v - 3; id.data[i + 2] = v - 8; id.data[i + 3] = 255; } g.putImageData(id, 0, 0); };

// ---------------- 纹理映射 ----------------
// 精确三角形贴图：src 三点(纹理像素) → dst 三点(设计坐标)。曲线带状物一定要用这个，平行四边形切片在弯道会错位出条纹。
L.drawTri = (g, img, s0, s1, s2, d0, d1, d2, K = 3) => {
  const cx = (d0[0] + d1[0] + d2[0]) / 3, cy = (d0[1] + d1[1] + d2[1]) / 3, ex = p => { const dx = p[0] - cx, dy = p[1] - cy, l = Math.hypot(dx, dy) || 1; return [p[0] + dx / l * .35, p[1] + dy / l * .35]; };
  const e0 = ex(d0), e1 = ex(d1), e2 = ex(d2);
  g.save(); g.setTransform(K, 0, 0, K, 0, 0); g.beginPath(); g.moveTo(...e0); g.lineTo(...e1); g.lineTo(...e2); g.closePath(); g.clip();
  const [x0, y0] = s0, [x1, y1] = s1, [x2, y2] = s2, den = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0);
  if (Math.abs(den) < 1e-9) { g.restore(); return; }
  const a = ((d1[0] - d0[0]) * (y2 - y0) - (d2[0] - d0[0]) * (y1 - y0)) / den, c = ((d2[0] - d0[0]) * (x1 - x0) - (d1[0] - d0[0]) * (x2 - x0)) / den;
  const b = ((d1[1] - d0[1]) * (y2 - y0) - (d2[1] - d0[1]) * (y1 - y0)) / den, d = ((d2[1] - d0[1]) * (x1 - x0) - (d1[1] - d0[1]) * (x2 - x0)) / den;
  g.transform(a, b, c, d, d0[0] - a * x0 - c * y0, d0[1] - b * x0 - d * y0);
  const mnx = Math.max(0, Math.min(x0, x1, x2) - 2), mxx = Math.min(img.width, Math.max(x0, x1, x2) + 2);
  const mny = Math.max(0, Math.min(y0, y1, y2) - 2), mxy = Math.min(img.height, Math.max(y0, y1, y2) + 2);
  g.drawImage(img, mnx, mny, mxx - mnx, mxy - mny, mnx, mny, mxx - mnx, mxy - mny); g.restore();
};
// 曲线点工具
L.catmull = (pts, n = 20) => { const out = []; for (let i = 0; i < pts.length - 1; i++) { const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)]; for (let k = 0; k < n; k++) { const t = k / n, t2 = t * t, t3 = t2 * t; out.push([0, 1].map(j => .5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3))); } } out.push(pts[pts.length - 1]); return out; };
L.resample = (pts, step) => { const out = [pts[0]]; let acc = 0; for (let i = 1; i < pts.length; i++) { let [ax, ay] = out[out.length - 1]; const [bx, by] = pts[i]; let d = Math.hypot(bx - ax, by - ay); while (acc + d >= step) { const f = (step - acc) / d; ax += (bx - ax) * f; ay += (by - ay) * f; out.push([ax, ay]); d = Math.hypot(bx - ax, by - ay); acc = 0; } acc += d; } return out; };
// 带状物（纸带/胶片/丝带/横幅）：沿中心线贴一条纹理，可扭转、可从起点"抽出"。
//   opt: { pts:控制点, W:带宽, tex:纹理canvas(宽=长度*R, 高=W*R), R:纹理分辨率, len:当前露出长度,
//          wave:(s)=>横向偏移, twist:(s)=>扭转角, shadow:ctx|null, backColor, K }
//   纹理坐标 u = len - s（像从起点吐出来：内容跟着纸走）。想要"静止纸带逐渐显露"就传 uFixed:true（u = s）。
L.strip = (g, o) => {
  const K = o.K || 3, R = o.R || 4, W = o.W, step = o.step || 4;
  if (!o._base) { o._base = L.resample(L.catmull(o.pts, 24), step); }
  const B = o._base, n = Math.min(B.length - 1, Math.floor(o.len / step)); if (n < 1) return;
  const P = []; for (let i = 0; i <= n; i++) { const [px, py] = B[i], [qx, qy] = B[Math.min(B.length - 1, i + 1)], [ox, oy] = B[Math.max(0, i - 1)]; let tx = qx - ox, ty = qy - oy; const l = Math.hypot(tx, ty) || 1; tx /= l; ty /= l; const s = i * step, w = o.wave ? o.wave(s) : 0; P.push([px - ty * w, py + tx * w, s]); }
  const N = P.map((p, i) => { const a = P[Math.max(0, i - 1)], b = P[Math.min(P.length - 1, i + 1)]; let tx = b[0] - a[0], ty = b[1] - a[1]; const l = Math.hypot(tx, ty) || 1; return [-ty / l, tx / l]; });
  const ph = s => o.twist ? o.twist(s) : 0, U = s => o.uFixed ? s : o.len - s;
  for (let i = 0; i < P.length - 1; i++) {
    const c0 = Math.cos(ph(P[i][2])), c1 = Math.cos(ph(P[i + 1][2])), c = (c0 + c1) / 2;
    const A = [P[i][0] + N[i][0] * W / 2 * c0, P[i][1] + N[i][1] * W / 2 * c0], Bq = [P[i + 1][0] + N[i + 1][0] * W / 2 * c1, P[i + 1][1] + N[i + 1][1] * W / 2 * c1];
    const Cq = [P[i + 1][0] - N[i + 1][0] * W / 2 * c1, P[i + 1][1] - N[i + 1][1] * W / 2 * c1], D = [P[i][0] - N[i][0] * W / 2 * c0, P[i][1] - N[i][1] * W / 2 * c0];
    const quad = (ctx, dx = 0, dy = 0) => { ctx.beginPath(); ctx.moveTo(A[0] + dx, A[1] + dy); ctx.lineTo(Bq[0] + dx, Bq[1] + dy); ctx.lineTo(Cq[0] + dx, Cq[1] + dy); ctx.lineTo(D[0] + dx, D[1] + dy); ctx.closePath(); };
    const fade = L.clamp(P[i][2] / 14);
    if (o.shadow) { const s = o.shadow; s.setTransform(K, 0, 0, K, 0, 0); s.globalAlpha = fade; s.fillStyle = o.shadowColor || '#2a1d10'; quad(s, 7, 10); s.fill(); s.globalAlpha = 1; }
    g.globalAlpha = fade; const u0 = U(P[i][2]), u1 = U(P[i + 1][2]);
    if (c > .02 && Math.min(u0, u1) >= 0) {
      const tA = [u0 * R, 0], tB = [u1 * R, 0], tC = [u1 * R, W * R], tD = [u0 * R, W * R];
      L.drawTri(g, o.tex, tA, tB, tC, A, Bq, Cq, K); L.drawTri(g, o.tex, tA, tC, tD, A, Cq, D, K);
      g.setTransform(K, 0, 0, K, 0, 0); g.fillStyle = `rgba(40,30,20,${(1 - c) * .5})`; quad(g); g.fill();
    } else { g.setTransform(K, 0, 0, K, 0, 0); g.fillStyle = o.backColor || '#d9d0be'; quad(g); g.fill(); g.fillStyle = `rgba(40,30,20,${L.clamp(.1 + (1 + c) * .25)})`; g.fill(); }
  }
  g.globalAlpha = 1;
};
// 把图切成网格碎片（拼合/爆散/翻牌用）。返回 [{c:canvas, x,y,w,h, i,j, r:随机数}]
L.tiles = (img, x0, y0, w, h, cols, rows, seed = 3, K = 2) => { const R = L.rng(seed), out = []; for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) { const tw = w / cols, th = h / rows, x = x0 + i * tw, y = y0 + j * th; out.push({ c: L.crop(img, x, y, tw, th, K), x, y, w: tw, h: th, i, j, r: R() }); } return out; };

// 图片粒子化：按 step 网格采样像素 → [{x,y(原位,设计坐标), r,g,b,a, rnd}]。之后每帧自己算位置（散开/聚合/风吹）再画方点或圆点。
//   例：const P=L.pixelate(img,{x:0,y:0,w:400,h:400},4); 画：g.fillStyle=`rgb(${p.r},${p.g},${p.b})`; g.fillRect(x,y,s,s)
L.pixelate = (img, rect, step = 4, alphaMin = 20) => { const c = document.createElement('canvas'); c.width = Math.ceil(rect.w / step); c.height = Math.ceil(rect.h / step); const g = c.getContext('2d'); g.drawImage(img, rect.x, rect.y, rect.w, rect.h, 0, 0, c.width, c.height); const d = g.getImageData(0, 0, c.width, c.height).data, out = []; for (let j = 0; j < c.height; j++) for (let i = 0; i < c.width; i++) { const k = (j * c.width + i) * 4; if (d[k + 3] < alphaMin) continue; out.push({ x: rect.x + i * step, y: rect.y + j * step, r: d[k], g: d[k + 1], b: d[k + 2], a: d[k + 3] / 255, rnd: L.hash(i * 31.7 + j * 7.13) }); } out.step = step; return out; };
// 噪声溶解：在 ctx 上画 img（dst 矩形，设计坐标），只保留噪声值 < level 的区域（level 0→1 = 从无到全显；反过来就是溶解消失）。
//   edge>0 时在溶解边界画一圈 edgeColor（燃烧/显影亮边）。scale 控制噪声颗粒大小。res 是遮罩分辨率（设计单位/格）。
L.dissolve = (ctx, img, dst, level, { scale = 60, seed = 1, edge = 0.04, edgeColor = '#ffb347', res = 3, K = 3 } = {}) => {
  if (level <= 0) return; const cw = Math.ceil(dst.w / res), ch = Math.ceil(dst.h / res);
  const m = document.createElement('canvas'); m.width = cw; m.height = ch; const mg = m.getContext('2d'), id = mg.createImageData(cw, ch);
  const e = document.createElement('canvas'); e.width = cw; e.height = ch; const eg = e.getContext('2d'), ed = eg.createImageData(cw, ch);
  const [er, egc, eb] = [1, 3, 5].map(i => parseInt(edgeColor.slice(i, i + 2), 16));
  for (let j = 0; j < ch; j++) for (let i = 0; i < cw; i++) {
    const x = i * res / scale, y = j * res / scale, n = (L.noise(x + seed * 13.1 + L.noise(y * .7 + seed) * 2) * .5 + L.noise(y * 1.3 + seed * 7.7 + L.noise(x * .9) * 2) * .5) * .5 + .5;
    const k = (j * cw + i) * 4, v = level >= 1 ? 255 : (n < level ? 255 : 0); id.data[k + 3] = v;
    if (edge > 0 && level < 1 && n < level && n > level - edge) { ed.data[k] = er; ed.data[k + 1] = egc; ed.data[k + 2] = eb; ed.data[k + 3] = 255; }
  }
  mg.putImageData(id, 0, 0); eg.putImageData(ed, 0, 0);
  const tmp = document.createElement('canvas'); tmp.width = Math.ceil(dst.w * K); tmp.height = Math.ceil(dst.h * K); const tg = tmp.getContext('2d');
  tg.drawImage(img, 0, 0, tmp.width, tmp.height); tg.globalCompositeOperation = 'destination-in'; tg.imageSmoothingEnabled = true; tg.drawImage(m, 0, 0, tmp.width, tmp.height);
  tg.globalCompositeOperation = 'source-over'; tg.drawImage(e, 0, 0, tmp.width, tmp.height);
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.drawImage(tmp, dst.x * K, dst.y * K); ctx.restore();
};

// ---------------- 文字动画 ----------------
// 把元素文字拆成逐字 span（\n → <br>）。返回 span 数组。
L.splitChars = el => { const s = el.textContent; el.innerHTML = [...s].map(c => c === '\n' ? '<br>' : `<span class="ch" style="display:inline-block">${c === ' ' ? '&nbsp;' : c}</span>`).join(''); return [...el.querySelectorAll('.ch')]; };
// 模式：type(打字+高亮光标) rise(从下方遮罩升起) drop(从上落下带回弹) blur(失焦到清晰) scramble(乱码解码) roll(数字滚动)
L.textAnim = (chs, t, t0, mode = 'rise', o = {}) => {
  const st = o.stagger ?? (mode === 'type' ? .022 : .035), d = o.dur ?? .5, hl = o.hl || '#d8452a';
  chs.forEach((c, i) => {
    const a = t0 + i * st, p = L.prog(t, a, a + d);
    if (mode === 'type') { const on = t >= a, cur = on && t < a + .05; c.style.opacity = on ? 1 : 0; c.style.background = cur ? hl : ''; c.style.color = cur ? (o.hlText || '#fff') : ''; }
    else if (mode === 'rise') { const e = L.E.outExpo(p); c.style.opacity = L.clamp(e * 3); c.style.transform = `translateY(${(1 - e) * .9}em)`; }
    else if (mode === 'drop') { const e = L.E.outBack(p, 1.4); c.style.opacity = L.clamp(p * 6); c.style.transform = `translateY(${(1 - e) * -.9}em)`; }
    else if (mode === 'blur') { const e = L.E.outCubic(p); c.style.opacity = e; c.style.filter = e < 1 ? `blur(${(1 - e) * 8}px)` : 'none'; c.style.transform = `scale(${L.lerp(1.4, 1, e)})`; }
    else if (mode === 'scramble') { if (!c.dataset.o) c.dataset.o = c.textContent; const pool = o.pool || 'ABCDEFGHJKLMNPQRSTUVWXYZ0123456789#*/'; c.style.opacity = t >= a ? 1 : 0; c.textContent = p >= 1 || c.dataset.o.trim() === '' ? c.dataset.o : pool[Math.floor(L.hash(i * 7 + Math.floor(t * 24)) * pool.length)]; }
  });
};
// 数字滚动：把 span 里的数字做成竖排滚轴。先 L.rollPrep(chs) 一次，之后每帧 L.rollAnim(chs, t, t0)
L.rollPrep = chs => chs.forEach(c => { const d = c.textContent; if (!/\d/.test(d)) return; c.style.position = 'relative'; c.style.overflow = 'hidden'; c.style.verticalAlign = 'top'; c.style.height = '1.25em'; const col = []; for (let k = 0; k < 10; k++) col.push((+d + k + 1) % 10); col.push(d); c.innerHTML = `<span style="visibility:hidden">${d}</span><span class="col" style="position:absolute;left:0;top:0;display:flex;flex-direction:column;line-height:1.25em">${col.map(v => `<span>${v}</span>`).join('')}</span>`; });
L.rollAnim = (chs, t, t0, st = .018) => chs.forEach((c, i) => { const a = t0 + i * st, p = L.prog(t, a, a + .5 + (i % 3) * .08); c.style.opacity = L.clamp(L.prog(t, a, a + .08)); const col = c.querySelector('.col'); if (col) col.style.transform = `translateY(${-L.E.outCubic(p) * 12.5}em)`; });

// ---------------- 粒子（解析式，可随机访问） ----------------
// 每个粒子由种子决定出生时间/初速/寿命；位置是 t 的闭式函数（抛体 + 阻尼 + 噪声漂移）。
// emit: { n, seed, t0, spread:[s0,s1](出生时间窗), x, y, (r)=>({vx,vy}) , g:重力, drag, life:[a,b], size:[a,b] }
L.particles = (t, em) => {
  const R = L.rng(em.seed || 7), out = [];
  for (let i = 0; i < em.n; i++) {
    const born = em.t0 + L.lerp(em.spread?.[0] ?? 0, em.spread?.[1] ?? 0, R()), life = L.lerp(...(em.life || [.6, 1.4]), R());
    const v = em.vel ? em.vel(R, i) : { vx: (R() - .5) * 400, vy: (R() - .5) * 400 }, size = L.lerp(...(em.size || [1, 4]), R()), seed = R() * 100;
    const a = t - born; if (a < 0 || a > life) continue;
    const k = em.drag ?? 2, f = (1 - Math.exp(-k * a)) / k;
    const x = (em.x ?? 0) + v.vx * f + L.noise(seed + a * 2) * (em.jitter ?? 0), y = (em.y ?? 0) + v.vy * f + .5 * (em.g ?? 0) * a * a;
    out.push({ x, y, size, age: a / life, seed, i });
  }
  return out;
};

// ---------------- 镜头 ----------------
// keys: [[t, z, cx, cy, rot?], ...]  z=1 时整张原图正好铺满画面；cx/cy 为设计坐标里的注视点。
// 关键帧之间用 Catmull-Rom 平滑（不会每个关键帧都"停一下"）。
// opts:
//   clampEdges (default true): never show anything outside the source (or outside the extended area, see extend).
//   minZ: lowest zoom. Default 1 when clampEdges is on - the spline can undershoot below a z=1 plateau between
//         keys > 1 and would expose dark edges; default .9 when clampEdges is off. Pass minZ < 1 explicitly for a
//         deliberate pull-back past the source; below z=1 the edge clamp is then skipped.
//   extend {top,right,bottom,left} (px, design coordinates, default 0): the camera may also look at that much
//         canvas OUTSIDE the source - only if you paint it yourself (e.g. sky painted in code above the image).
//         See references/recipes.md "Extending the canvas beyond the source".
L.Camera = class {
  constructor(keys, { clampEdges = true, minZ, extend = {} } = {}) {
    this.k = keys; this.clampEdges = clampEdges; this.minZ = minZ ?? (clampEdges ? 1 : .9);
    this.ext = { top: extend.top || 0, right: extend.right || 0, bottom: extend.bottom || 0, left: extend.left || 0 };
  }
  at(t) {
    const k = this.k; let i = 0; while (i < k.length - 2 && t > k[i + 1][0]) i++;
    const p0 = k[Math.max(0, i - 1)], p1 = k[i], p2 = k[i + 1] || p1, p3 = k[Math.min(k.length - 1, i + 2)];
    const span = (p2[0] - p1[0]) || 1, u = L.clamp((t - p1[0]) / span);
    const cr = j => { const a = p0[j] ?? 0, b = p1[j] ?? 0, c = p2[j] ?? 0, d = p3[j] ?? 0; const m1 = (c - a) / ((p2[0] - p0[0]) || 1) * span, m2 = (d - b) / ((p3[0] - p1[0]) || 1) * span; const u2 = u * u, u3 = u2 * u; return (2 * u3 - 3 * u2 + 1) * b + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * c + (u3 - u2) * m2; };
    let z = Math.max(this.minZ, cr(1)), cx = cr(2), cy = cr(3), rot = cr(4);
    if (this.clampEdges && z >= 1) {
      const e = this.ext, hw = CFG.srcW / 2 / z, hh = CFG.srcH / 2 / z;
      cx = L.clamp(cx, hw - e.left, CFG.srcW + e.right - hw); cy = L.clamp(cy, hh - e.top, CFG.srcH + e.bottom - hh);
    }
    return { z, cx, cy, rot };
  }
  // 应用到 #cam；extra 可叠加抖动 {dx,dy,drot}
  apply(el, t, extra = {}) {
    const { z, cx, cy, rot } = this.at(t), S = CFG.outW / CFG.srcW * z;
    el.style.transform = `translate(${CFG.outW / 2}px,${CFG.outH / 2}px) rotate(${(rot || 0) + (extra.drot || 0)}deg) scale(${S}) translate(${-(cx + (extra.dx || 0))}px,${-(cy + (extra.dy || 0))}px)`;
    return { z, cx, cy, rot, S };
  }
};
// 视差：depth 0 = 与镜头平面一致；>0 更远（移动更少）；<0 更近（移动更多，适合前景遮挡物）
L.parallax = (el, cam, depth, base = { x: 0, y: 0 }) => { const f = depth; el.style.transform = `translate(${(cam.cx - CFG.srcW / 2) * f + base.x}px,${(cam.cy - CFG.srcH / 2) * f + base.y}px)`; };

G.L = L;
})(window);
