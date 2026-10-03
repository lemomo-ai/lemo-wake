// lemo-wake 特效积木（FX）—— 让画面里某样东西动起来、变起来的可复用方式。
// 一支片 = 1 个主动作 + 1–2 个配角积木 + 1 个复位转场。积木多半当配角，也可以当主动作。
//
// 用法（src/index.html 里在 lib.js 之后引入 fx.js）：
//   const g = FX.layer();                                    // 一张铺满原图的透明画布（设计坐标），放进 #cam
//   const rain = FX.make('rain', { seed: 3, angle: 12, area: [0, 0, 1, .8] });
//   await rain.ready;                                        // build() 里等它准备好（有的要先采样原图）
//   function render(t) { g.clearRect(0, 0, CFG.srcW, CFG.srcH); rain.draw(g, t); }
//
// 约定：
//   - 区域 area = [x0, y0, x1, y1]，点 = [x, y]，都是相对原图的 0..1 比例，不写像素。
//   - draw(g, t) 是纯函数，只依赖 t。周期运动一律"每轮整数圈"：t = 0 和 t = CFG.dur 画面完全一样，可以直接无缝循环。
//   - 换 seed，粒子分布、纹理、相位全换；FX.pick(name, seed) 在推荐范围里随机取一组参数，避免每支片长得一样。
//   - 能从原图取的就从原图取：光尘落在亮处，萤火在暗处，星闪长在高光点上，光斑用图里的灯色（palette: 'auto'）。
//   - FX.meta[name]：中文名、分组、效果、适合、从图里什么长出来（anchor）、参数（默认值 d、推荐范围 min..max、说明）。
const FX = { meta: {}, defs: {}, groups: ['粒子', '空气和水'] };
(() => {
  const TAU = Math.PI * 2, fr = x => x - Math.floor(x), cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const sstep = (a, b, x) => { const t = cl((x - a) / (b - a)); return t * t * (3 - 2 * t); };
  const rngf = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const P = (d, min = null, max = null, note = '', int = false) => ({ d, min, max, note, int });
  const AREA = P([0, 0, 1, 1], null, null, '区域 [x0,y0,x1,y1]（0..1）');

  FX.def = (name, meta, make) => { FX.meta[name] = meta; FX.defs[name] = make; };
  FX.defaults = name => Object.fromEntries(Object.entries(FX.meta[name].params).map(([k, p]) => [k, p.d]));
  // 在推荐范围里随机取一组数值参数（区域、颜色这类跟图有关的不动）
  FX.pick = (name, seed = 1) => {
    const R = rngf(seed * 7 + 3), o = {};
    for (const [k, p] of Object.entries(FX.meta[name].params)) if (typeof p.d === 'number' && p.min != null) { const v = p.min + (p.max - p.min) * R(); o[k] = p.int ? Math.round(v) : +v.toFixed(3); }
    return o;
  };
  FX.make = (name, opt = {}) => {
    if (!FX.defs[name]) throw new Error('没有这个积木：' + name + '（有：' + Object.keys(FX.defs).join(' ') + '）');
    const o = { seed: 1, ...FX.defaults(name), ...opt }, W = CFG.srcW, H = CFG.srcH;
    const e = { W, H, D: CFG.dur, u: Math.min(W, H) / 1000, img: o.img || window.SRC, R: rngf(o.seed * 9973 + 17) };
    const fx = FX.defs[name](o, e); fx.name = name; fx.ready = Promise.resolve(fx.ready); return fx;
  };
  // 一张设计坐标的透明画布，放进 parent（默认 #cam）
  FX.layer = (parent = document.querySelector('#cam'), K = 1) => {
    const c = document.createElement('canvas'); c.width = Math.round(CFG.srcW * K); c.height = Math.round(CFG.srcH * K);
    Object.assign(c.style, { position: 'absolute', left: 0, top: 0, width: CFG.srcW + 'px', height: CFG.srcH + 'px' });
    parent.appendChild(c); const g = c.getContext('2d'); g.scale(K, K); return g;
  };

  // ---------------- 工具 ----------------
  const cache = new Map();
  const U = FX.util = {
    rect: (a, e) => { const [x0, y0, x1, y1] = a || [0, 0, 1, 1]; return { x: x0 * e.W, y: y0 * e.H, w: (x1 - x0) * e.W, h: (y1 - y0) * e.H, a: a || [0, 0, 1, 1] }; },
    canvas: (w, h) => { const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w)); c.height = Math.max(1, Math.round(h)); return [c, c.getContext('2d')]; },
    // 径向渐变小图（发光点、雪花、烟团…）。stops: [[位置, 透明度], …]
    sprite: (color, stops, size = 128) => {
      const k = color + JSON.stringify(stops) + size; if (cache.has(k)) return cache.get(k);
      const [c, g] = U.canvas(size, size), gr = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2), [r, gg, b] = U.rgb(color);
      for (const [p, a] of stops) gr.addColorStop(p, `rgba(${r},${gg},${b},${a})`);
      g.fillStyle = gr; g.fillRect(0, 0, size, size); cache.set(k, c); return c;
    },
    rgb: c => { if (Array.isArray(c)) return c; const h = c.replace('#', ''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); },
    hex: ([r, g, b]) => '#' + [r, g, b].map(v => Math.round(cl(v, 0, 255)).toString(16).padStart(2, '0')).join(''),
    // 原图缩小后的亮度表（采样位置、找高光、取色都用它）
    lum: (img, side = 240) => {
      const k = 'lum' + img.src + side; if (cache.has(k)) return cache.get(k);
      const s = side / Math.max(img.width, img.height), w = Math.max(2, Math.round(img.width * s)), h = Math.max(2, Math.round(img.height * s));
      const [c, g] = U.canvas(w, h); g.drawImage(img, 0, 0, w, h); const d = g.getImageData(0, 0, w, h).data, L = new Float32Array(w * h);
      for (let i = 0; i < w * h; i++) L[i] = (d[i * 4] * .299 + d[i * 4 + 1] * .587 + d[i * 4 + 2] * .114) / 255;
      const r = { w, h, L, d, sx: img.width / w, sy: img.height / h }; cache.set(k, r); return r;
    },
    // 在区域里按权重撒点：weight(亮度) 越大越容易落点。返回设计坐标 [[x,y,亮度], …]
    weighted: (e, n, A, weight, R) => {
      if (!e.img) return Array.from({ length: n }, () => [A.x + R() * A.w, A.y + R() * A.h, .5]);
      const T = U.lum(e.img), out = []; let tries = 0;
      while (out.length < n && tries++ < n * 400) {
        const x = A.x + R() * A.w, y = A.y + R() * A.h, l = T.L[Math.min(T.h - 1, Math.floor(y / T.sy)) * T.w + Math.min(T.w - 1, Math.floor(x / T.sx))];
        if (R() < weight(l)) out.push([x, y, l]);
      }
      while (out.length < n) out.push([A.x + R() * A.w, A.y + R() * A.h, .5]);
      return out;
    },
    // 图里最亮的几个高光点（局部极大值，彼此隔开 minDist·短边）
    highlights: (e, n, A, minDist = .06) => {
      const T = U.lum(e.img), c = [];
      for (let j = 2; j < T.h - 2; j++) for (let i = 2; i < T.w - 2; i++) {
        const x = (i + .5) * T.sx, y = (j + .5) * T.sy; if (x < A.x || x > A.x + A.w || y < A.y || y > A.y + A.h) continue;
        const v = T.L[j * T.w + i]; let mx = true;
        for (let dj = -2; dj <= 2 && mx; dj++) for (let di = -2; di <= 2; di++) if ((di || dj) && T.L[(j + dj) * T.w + i + di] > v) { mx = false; break; }
        if (mx) c.push([x, y, v]);
      }
      c.sort((a, b) => b[2] - a[2]); const out = [], md = minDist * Math.min(e.W, e.H);
      for (const p of c) { if (out.every(q => Math.hypot(q[0] - p[0], q[1] - p[1]) > md)) out.push(p); if (out.length >= n) break; }
      return out;
    },
    // 从图里取几种颜色（偏亮、偏鲜艳的），给光斑、彩纸用
    palette: (e, n = 6, A = null, minL = .45) => {
      const T = U.lum(e.img), b = new Map();
      for (let j = 0; j < T.h; j++) for (let i = 0; i < T.w; i++) {
        const x = (i + .5) * T.sx, y = (j + .5) * T.sy; if (A && (x < A.x || x > A.x + A.w || y < A.y || y > A.y + A.h)) continue;
        const k = (j * T.w + i) * 4, r = T.d[k], g = T.d[k + 1], bl = T.d[k + 2], mx = Math.max(r, g, bl), mn = Math.min(r, g, bl);
        if (mx / 255 < minL) continue; const sat = (mx - mn) / (mx || 1), hue = Math.round(U.hue(r, g, bl) / 30) % 12;
        const s = b.get(hue) || { n: 0, r: 0, g: 0, b: 0, w: 0 }, wgt = .2 + sat; s.n++; s.w += wgt; s.r += r * wgt; s.g += g * wgt; s.b += bl * wgt; b.set(hue, s);
      }
      const out = [...b.values()].sort((a, c) => c.w - a.w).slice(0, n).map(s => U.hex([s.r / s.w, s.g / s.w, s.b / s.w].map(v => v + (255 - v) * .25)));
      return out.length ? out : ['#ffffff'];
    },
    hue: (r, g, b) => { const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn || 1; const h = mx === r ? (g - b) / d : mx === g ? 2 + (b - r) / d : 4 + (r - g) / d; return (h * 60 + 360) % 360; },
    // 横竖都能无缝平铺的值噪声（0..1），雾和云用
    tileNoise: (w, h, seed, cells = 5, oct = 4) => {
      const R = rngf(seed), out = new Float32Array(w * h); let amp = 1, tot = 0;
      for (let o = 0; o < oct; o++) {
        const cx = cells << o, cy = Math.max(1, Math.round(cells * h / w)) << o, g = Float32Array.from({ length: cx * cy }, R);
        for (let j = 0; j < h; j++) {
          const fy = j / h * cy, y0 = Math.floor(fy), ty = fy - y0, sy = ty * ty * (3 - 2 * ty);
          for (let i = 0; i < w; i++) {
            const fx = i / w * cx, x0 = Math.floor(fx), tx = fx - x0, sx = tx * tx * (3 - 2 * tx), x1 = (x0 + 1) % cx, yy0 = y0 % cy, yy1 = (y0 + 1) % cy;
            const a = g[yy0 * cx + x0] * (1 - sx) + g[yy0 * cx + x1] * sx, b = g[yy1 * cx + x0] * (1 - sx) + g[yy1 * cx + x1] * sx;
            out[j * w + i] += amp * (a * (1 - sy) + b * sy);
          }
        }
        tot += amp; amp *= .5;
      }
      for (let i = 0; i < out.length; i++) out[i] /= tot;
      return out;
    },
    // 软边遮罩：区域边上（贴着原图边缘的那几条边除外）渐隐
    softMask: (A, featherPx) => {
      const [c, g] = U.canvas(A.w, A.h), [x0, y0, x1, y1] = A.a, f = featherPx, big = f * 4;
      g.filter = `blur(${f / 2}px)`; g.fillStyle = '#fff';
      const l = x0 <= 0 ? -big : f, t = y0 <= 0 ? -big : f, r = x1 >= 1 ? A.w + big : A.w - f, b = y1 >= 1 ? A.h + big : A.h - f;
      g.fillRect(l, t, r - l, b - t); return c;
    },
    // 把一张区域大小的离屏画布按软边遮罩贴回去
    blit: (g, off, A, mask, alpha = 1, op = 'source-over') => {
      const og = off.getContext('2d'); og.globalCompositeOperation = 'destination-in'; og.drawImage(mask, 0, 0); og.globalCompositeOperation = 'source-over';
      g.save(); g.globalAlpha = alpha; g.globalCompositeOperation = op; g.drawImage(off, A.x, A.y, A.w, A.h); g.restore();
    },
  };
  const clip = (g, A) => { g.save(); g.beginPath(); g.rect(A.x, A.y, A.w, A.h); g.clip(); };

  // ======================= 粒子 =======================
  FX.def('rain', {
    zh: '雨', group: '粒子', desc: '雨丝分远近几层斜着落下，近处粗长、远处细短', suits: '雨夜、街景、窗边、伞、电影感',
    anchor: '图里本来在下雨、地面有积水、有人打伞，或者夜景想更潮湿',
    params: { density: P(.6, .25, 1, '密度'), angle: P(10, -22, 22, '倾斜角（度，正数往右下）'), speed: P(8, 5, 13, '每轮落下的趟数（整数，越大越快）', true), length: P(1, .6, 1.8, '雨丝长度'), width: P(1, .7, 1.5, '粗细'), opacity: P(.5, .3, .75, '透明度'), layers: P(3, 2, 3, '远近层数', true), color: P('#dfe7ef', null, null, '颜色'), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, a = o.angle * Math.PI / 180, ta = Math.tan(a), sa = Math.sin(a), ca = Math.cos(a);
    const n = Math.round(o.density * 900 * (A.w * A.h) / (e.W * e.H)), lay = Array.from({ length: o.layers }, () => []);
    for (let i = 0; i < n; i++) {
      const z = Math.floor(R() * o.layers), d = (z + 1) / o.layers, L = (14 + 46 * d) * e.u * o.length, trav = ta * (A.h + 2 * L);
      lay[z].push({ x: A.x - Math.max(0, trav) + R() * (A.w + Math.abs(trav)), L, ph: R(), k: Math.max(2, o.speed - (o.layers - 1 - z) * 2) });
    }
    return {
      draw(g, t) {
        clip(g, A); g.lineCap = 'round'; g.strokeStyle = o.color;
        lay.forEach((ds, z) => {
          const d = (z + 1) / o.layers; g.lineWidth = (.7 + 1.6 * d) * e.u * o.width;
          for (const [part, al] of [[1, .4], [.45, 1]]) {  // 尾巴淡、头部实
            g.globalAlpha = o.opacity * (.3 + .7 * d) * al; g.beginPath();
            for (const p of ds) { const y = A.y - p.L + fr(p.k * t / e.D + p.ph) * (A.h + 2 * p.L), x = p.x + ta * (y - A.y); g.moveTo(x, y); g.lineTo(x - sa * p.L * part, y - ca * p.L * part); }
            g.stroke();
          }
        });
        g.restore();
      },
    };
  });

  FX.def('snow', {
    zh: '雪', group: '粒子', desc: '雪花分远近飘落、左右轻摆，近处大而虚、远处小而实', suits: '冬天、雪景、节日、夜景、温馨',
    anchor: '图里有雪、冷色调、冬天的衣着或节日元素',
    params: { density: P(.5, .2, 1, '密度'), size: P(1, .6, 1.8, '雪花大小'), speed: P(2, 1, 3, '每轮落下的趟数', true), sway: P(1, .3, 2, '左右摆幅'), opacity: P(.9, .6, 1, '透明度'), layers: P(3, 2, 3, '远近层数', true), color: P('#ffffff', null, null, '颜色'), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, n = Math.round(o.density * 520 * (A.w * A.h) / (e.W * e.H)), fl = [];
    for (let i = 0; i < n; i++) {
      const d = (Math.floor(R() * o.layers) + 1) / o.layers, r = (2.2 + 8 * d ** 1.6) * e.u * o.size * 1.5, amp = o.sway * (6 + 20 * d) * e.u * 1.5;
      fl.push({ d, r, amp, x: A.x - amp + R() * (A.w + 2 * amp), ph: R(), k: Math.max(1, Math.round(o.speed * (.6 + .6 * d))), m: 1 + Math.floor(R() * 2), ps: R() });
    }
    fl.sort((a, b) => a.d - b.d);
    const soft = U.sprite(o.color, [[0, 1], [.35, .8], [1, 0]]), hard = U.sprite(o.color, [[0, 1], [.6, .95], [1, 0]]);
    return {
      draw(g, t) {
        clip(g, A);
        for (const f of fl) {
          const y = A.y - f.r + fr(f.k * t / e.D + f.ph) * (A.h + 2 * f.r), x = f.x + f.amp * Math.sin(TAU * (f.m * t / e.D + f.ps));
          g.globalAlpha = o.opacity * (.45 + .55 * f.d); g.drawImage(f.d > .8 ? soft : hard, x - f.r, y - f.r, 2 * f.r, 2 * f.r);
        }
        g.restore();
      },
    };
  });

  FX.def('dust', {
    zh: '光尘', group: '粒子', desc: '光里的浮尘慢慢飘、忽明忽暗，自动只出现在亮处', suits: '窗边光束、逆光、室内、图书馆、老房子',
    anchor: '图里有光束、窗户透进来的光、逆光（浮尘按原图亮度撒点）',
    params: { count: P(150, 60, 320, '颗数', true), size: P(1, .6, 1.6, '大小'), drift: P(1, .5, 1.8, '飘动幅度'), twinkle: P(1, .3, 1.5, '明暗闪烁'), opacity: P(.85, .5, 1, '透明度'), follow: P('light', null, null, "'light' 只在亮处 / 'all' 到处都有"), color: P('#fff2d2', null, null, '颜色'), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, sp = U.sprite(o.color, [[0, 1], [.22, .85], [.5, .2], [1, 0]]);
    const pts = U.weighted(e, o.count, A, o.follow === 'light' ? l => sstep(.35, .7, l) * (1 - .7 * sstep(.85, 1, l)) : () => 1, R).map(([x, y, l]) => ({
      x, y, l, a: R(), b: R(), c: R(), m1: 1 + Math.floor(R() * 2), m2: 1 + Math.floor(R() * 2), mt: 1 + Math.floor(R() * 3), amp: o.drift * (10 + 30 * R()) * e.u, r: (1.6 + 4.5 * R() ** 2) * e.u * o.size * 1.5,
    }));
    return {
      draw(g, t) {
        const s = t / e.D; g.save(); g.globalCompositeOperation = 'lighter';
        for (const p of pts) {
          const x = p.x + p.amp * (.7 * Math.sin(TAU * (p.m1 * s + p.a)) + .3 * Math.sin(TAU * (p.m2 * s + p.b))), y = p.y + p.amp * .8 * (.6 * Math.cos(TAU * (p.m1 * s + p.c)) + .4 * Math.sin(TAU * (p.m2 * s + p.a)));
          const tw = .5 + .5 * Math.sin(TAU * (p.mt * s + p.c));
          g.globalAlpha = cl(o.opacity * (1 - o.twinkle * .75 + o.twinkle * .75 * tw * tw)); g.drawImage(sp, x - p.r * 3, y - p.r * 3, p.r * 6, p.r * 6);
        }
        g.restore();
      },
    };
  });

  FX.def('bokeh', {
    zh: '光斑', group: '粒子', desc: '虚化的圆形光斑缓慢漂移、呼吸，颜色取自图里的灯光', suits: '夜景、夜市、灯串、节日、人像背景',
    anchor: '图里有虚化的灯、霓虹、串灯；光斑颜色默认从原图亮处取（palette: auto）',
    params: { count: P(24, 8, 50, '个数', true), size: P(1, .6, 1.8, '大小'), drift: P(1, .3, 2, '漂移幅度'), breathe: P(1, 0, 1.5, '明暗呼吸'), opacity: P(.45, .25, .7, '透明度'), shape: P('circle', null, null, "'circle' 圆 / 'hex' 六边形（光圈叶片）"), palette: P('auto', null, null, "'auto' 从原图取色，或给颜色数组"), follow: P('light', null, null, "'light' 多落在亮处 / 'all'"), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, cols = o.palette === 'auto' ? (e.img ? U.palette(e, 5, A, .72) : ['#ffd27a', '#ff8fb1', '#8fd3ff']) : o.palette;
    const spr = cols.map(c => {
      const [cv, g] = U.canvas(128, 128), [r, gg, b] = U.rgb(c), gr = g.createRadialGradient(64, 64, 0, 64, 64, 62);
      gr.addColorStop(0, `rgba(${r},${gg},${b},.5)`); gr.addColorStop(.82, `rgba(${r},${gg},${b},.62)`); gr.addColorStop(.94, `rgba(${r},${gg},${b},.9)`); gr.addColorStop(1, `rgba(${r},${gg},${b},0)`);
      g.fillStyle = gr; g.beginPath();
      if (o.shape === 'hex') for (let k = 0; k < 6; k++) g.lineTo(64 + 62 * Math.cos(k * TAU / 6 + .3), 64 + 62 * Math.sin(k * TAU / 6 + .3)); else g.arc(64, 64, 63, 0, TAU);
      g.fill(); return cv;
    });
    const pts = U.weighted(e, o.count, A, o.follow === 'light' ? l => sstep(.55, .9, l) : () => 1, R).map(([x, y]) => ({
      x, y, s: spr[Math.floor(R() * spr.length)], r: (14 + 46 * R() ** 1.6) * e.u * o.size * 1.5, a: R(), b: R(), m: 1 + Math.floor(R() * 2), amp: o.drift * (8 + 22 * R()) * e.u,
    })).sort((p, q) => q.r - p.r);
    return {
      draw(g, t) {
        const s = t / e.D; g.save(); g.globalCompositeOperation = 'screen';
        for (const p of pts) {
          const x = p.x + p.amp * Math.sin(TAU * (s + p.a)), y = p.y + p.amp * .6 * Math.cos(TAU * (s + p.b));
          g.globalAlpha = cl(o.opacity * (1 - .45 * o.breathe * (.5 + .5 * Math.sin(TAU * (p.m * s + p.b))))); g.drawImage(p.s, x - p.r, y - p.r, 2 * p.r, 2 * p.r);
        }
        g.restore();
      },
    };
  });

  const PETAL_COLS = { petal: ['#f9cfd9', '#f5b8c8', '#fde6ec', '#f0a9bd'], leaf: ['#d9822b', '#c7612a', '#e3a33b', '#9c4a1f'], ginkgo: ['#f2c94c', '#e8b730', '#f5d76e'] };
  FX.def('petals', {
    zh: '花瓣', group: '粒子', desc: '花瓣（或落叶、银杏）边转边翻着飘落，随风斜飞', suits: '樱花、春天、婚礼、古风、秋天（leaf / ginkgo）',
    anchor: '图里有花树、花枝、秋叶，或古风人物需要一点风',
    params: { count: P(36, 12, 90, '片数', true), size: P(1, .6, 1.6, '大小'), speed: P(1, 1, 3, '每轮落下的趟数', true), sway: P(1, .4, 1.8, '左右摆幅'), spin: P(1, .5, 2, '翻转快慢'), wind: P(.35, -1, 1, '横向风（负数往左）'), opacity: P(.95, .75, 1, '透明度'), shape: P('petal', null, null, "'petal' 花瓣 / 'leaf' 叶子 / 'ginkgo' 银杏"), colors: P('auto', null, null, "'auto' 按形状给默认色，或给颜色数组"), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, cols = o.colors === 'auto' ? PETAL_COLS[o.shape] || PETAL_COLS.petal : o.colors, ps = [];
    for (let i = 0; i < o.count; i++) {
      const d = .35 + .65 * R(), s = (6 + 12 * d) * e.u * o.size * 1.6, amp = o.sway * (15 + 35 * d) * e.u, drift = o.wind * A.h * .6;
      ps.push({ d, s, amp, x: A.x - amp - Math.max(0, drift) + R() * (A.w + 2 * amp + Math.abs(drift)), drift, ph: R(), k: o.speed + (d > .8 ? 1 : 0), m: 1 + Math.floor(R() * 2), nr: Math.max(1, Math.round((1 + R()) * o.spin)), nf: Math.max(1, Math.round((1 + 2 * R()) * o.spin)), a: R(), b: R(), c: cols[Math.floor(R() * cols.length)] });
    }
    ps.sort((a, b) => a.d - b.d);
    const shape = (g, s) => {
      g.beginPath();
      if (o.shape === 'leaf') { g.moveTo(0, -s); g.quadraticCurveTo(s * .7, -s * .2, 0, s); g.quadraticCurveTo(-s * .7, -s * .2, 0, -s); }
      else if (o.shape === 'ginkgo') { g.moveTo(0, s * .9); g.lineTo(-s * .12, s * .1); g.quadraticCurveTo(-s * 1.1, -s * .2, -s * .8, -s * .8); g.quadraticCurveTo(0, -s * 1.15, s * .8, -s * .8); g.quadraticCurveTo(s * 1.1, -s * .2, s * .12, s * .1); g.closePath(); }
      else { g.moveTo(0, -s * .72); g.bezierCurveTo(-s * .12, -s * 1.02, -s * .78, -s * .9, -s * .62, -s * .1); g.bezierCurveTo(-s * .5, s * .5, -s * .1, s * .9, 0, s); g.bezierCurveTo(s * .1, s * .9, s * .5, s * .5, s * .62, -s * .1); g.bezierCurveTo(s * .78, -s * .9, s * .12, -s * 1.02, 0, -s * .72); }
    };
    return {
      draw(g, t) {
        const s = t / e.D; clip(g, A);
        for (const p of ps) {
          const q = fr(p.k * s + p.ph), y = A.y - 2 * p.s + q * (A.h + 4 * p.s), x = p.x + p.drift * q + p.amp * Math.sin(TAU * (p.m * s + p.a));
          const flip = Math.cos(TAU * (p.nf * s + p.b));
          g.save(); g.translate(x, y); g.rotate(TAU * (p.nr * s + p.a)); g.scale(Math.max(.12, Math.abs(flip)), 1);
          g.globalAlpha = o.opacity * (.55 + .45 * p.d); shape(g, p.s); g.fillStyle = p.c; g.fill();
          if (flip < 0) { g.fillStyle = 'rgba(60,20,30,.12)'; g.fill(); }  // 翻到背面略暗
          if (o.shape === 'leaf') { g.strokeStyle = 'rgba(80,30,10,.35)'; g.lineWidth = p.s * .06; g.beginPath(); g.moveTo(0, -p.s * .9); g.lineTo(0, p.s * .95); g.stroke(); }
          g.restore();
        }
        g.restore();
      },
    };
  });

  FX.def('fireflies', {
    zh: '萤火', group: '粒子', desc: '萤火虫在暗处慢慢游走、一闪一闪', suits: '夏夜、森林、绘本、童话、湖边',
    anchor: '夜景、草丛、树林；默认落在原图暗的地方',
    params: { count: P(28, 10, 60, '只数', true), size: P(1, .6, 1.6, '大小'), wander: P(1, .4, 2, '游走范围'), pulse: P(2, 1, 4, '每轮闪几次', true), color: P('#e4ff8a', null, null, '颜色'), opacity: P(1, .7, 1, '透明度'), follow: P('dark', null, null, "'dark' 多在暗处 / 'all'"), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, glow = U.sprite(o.color, [[0, .9], [.12, .55], [.4, .12], [1, 0]]), core = U.sprite('#fffbe0', [[0, 1], [.5, .6], [1, 0]], 32);
    const pts = U.weighted(e, o.count, A, o.follow === 'dark' ? l => (1 - l) ** 2 : () => 1, R).map(([x, y]) => ({ x, y, a: R(), b: R(), c: R(), m1: 1 + Math.floor(R() * 2), m2: 1 + Math.floor(R() * 2), amp: o.wander * (20 + 40 * R()) * e.u, r: (3.2 + 3 * R()) * e.u * o.size * 1.4 }));
    return {
      draw(g, t) {
        const s = t / e.D; g.save(); g.globalCompositeOperation = 'lighter';
        for (const p of pts) {
          const x = p.x + p.amp * Math.sin(TAU * (p.m1 * s + p.a)), y = p.y + p.amp * .6 * Math.sin(TAU * (p.m2 * s + p.b));
          const b = .12 + .88 * (.5 + .5 * Math.sin(TAU * (o.pulse * s + p.c))) ** 2;
          g.globalAlpha = o.opacity * b; g.drawImage(glow, x - p.r * 8, y - p.r * 8, p.r * 16, p.r * 16); g.drawImage(core, x - p.r, y - p.r, 2 * p.r, 2 * p.r);
        }
        g.restore();
      },
    };
  });

  FX.def('embers', {
    zh: '火星', group: '粒子', desc: '火星从火源升起，边飞边扭、由黄变红、渐渐熄灭', suits: '篝火、蜡烛、烟花、铁匠、金箔、暖光',
    anchor: '图里有火、灯、蜡烛、炉子；from 给火源所在的区域',
    params: { count: P(60, 20, 140, '颗数', true), from: P([[0, .92, 1, 1]], null, null, '发射区 [[x0,y0,x1,y1], …]'), rise: P(.5, .25, .9, '飞多高（占画面高）'), speed: P(2, 1, 4, '每轮飞的趟数', true), wiggle: P(1, .3, 2, '左右扭动'), size: P(1, .6, 1.6, '大小'), opacity: P(1, .7, 1, '透明度'), colors: P(['#ffe08a', '#ff9a2e', '#ff4d1a'], null, null, '从新到旧的颜色') },
  }, (o, e) => {
    const R = e.R, src = o.from.map(a => U.rect(a, e)), tot = src.reduce((s, A) => s + A.w * A.h + 1, 0);
    const spr = o.colors.map(c => U.sprite(c, [[0, 1], [.15, .8], [.45, .15], [1, 0]], 64)), ps = [];
    for (let i = 0; i < o.count; i++) {
      let r = R() * tot, A = src[0]; for (const S of src) { if ((r -= S.w * S.h + 1) <= 0) { A = S; break; } }
      ps.push({ x: A.x + R() * A.w, y: A.y + R() * A.h, ph: R(), k: o.speed + (R() < .4 ? 1 : 0), f: 1 + R() * 2, a: R(), rise: o.rise * (.55 + .45 * R()) * e.H, dr: (R() - .5) * .12 * e.W * o.wiggle, r: (2.4 + 3.6 * R()) * e.u * o.size * 1.6 });
    }
    return {
      draw(g, t) {
        g.save(); g.globalCompositeOperation = 'lighter';
        const pos = (p, q) => [p.x + p.dr * q + Math.sin(TAU * (q * p.f + p.a)) * o.wiggle * 14 * e.u * q, p.y - q * p.rise];
        g.lineCap = 'round';
        for (const p of ps) {
          const q = fr(p.k * t / e.D + p.ph), [x, y] = pos(p, q), [px, py] = pos(p, Math.max(0, q - .035 / p.k)), ci = Math.min(o.colors.length - 1, Math.floor(q * o.colors.length));
          const al = Math.sin(Math.PI * q) ** .7 * (.75 + .25 * Math.sin(TAU * (q * 9 + p.a))), r = p.r * (1 - .5 * q);
          g.globalAlpha = cl(o.opacity * al); g.drawImage(spr[ci], x - r * 4, y - r * 4, r * 8, r * 8);
          g.globalAlpha = cl(o.opacity * al * .8); g.strokeStyle = o.colors[ci]; g.lineWidth = r * .9; g.beginPath(); g.moveTo(px, py); g.lineTo(x, y); g.stroke();  // 拖尾
        }
        g.restore();
      },
    };
  });

  FX.def('bubbles', {
    zh: '气泡', group: '粒子', desc: '气泡晃着往上冒，带亮边和高光点（soap 是飘着的彩色肥皂泡）', suits: '饮料、水下、鱼缸、清凉、吹泡泡',
    anchor: '杯子、水、水族箱、泡泡；area 给气泡能冒的范围（比如杯子里）',
    params: { count: P(40, 15, 100, '个数', true), size: P(1, .6, 1.8, '大小'), speed: P(2, 1, 4, '每轮升起的趟数', true), wobble: P(1, .3, 2, '左右晃'), kind: P('water', null, null, "'water' 水里的气泡 / 'soap' 肥皂泡"), opacity: P(.85, .6, 1, '透明度'), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, soap = o.kind === 'soap';
    const [sp, g0] = U.canvas(128, 128);
    if (soap) {
      const cg = g0.createConicGradient(0, 64, 64);['#ff9ad5', '#ffe58a', '#9dffb0', '#8fd8ff', '#c9a2ff', '#ff9ad5'].forEach((c, i) => cg.addColorStop(i / 5, c));
      g0.globalAlpha = .55; g0.strokeStyle = cg; g0.lineWidth = 7; g0.beginPath(); g0.arc(64, 64, 58, 0, TAU); g0.stroke();
      const rg = g0.createRadialGradient(64, 64, 40, 64, 64, 62); rg.addColorStop(0, 'rgba(255,255,255,0)'); rg.addColorStop(1, 'rgba(255,255,255,.35)'); g0.globalAlpha = 1; g0.fillStyle = rg; g0.fill();
    } else {
      const rg = g0.createRadialGradient(64, 64, 0, 64, 64, 62); rg.addColorStop(0, 'rgba(255,255,255,.04)'); rg.addColorStop(.72, 'rgba(255,255,255,.08)'); rg.addColorStop(.84, 'rgba(255,255,255,.75)'); rg.addColorStop(.92, 'rgba(30,70,80,.55)'); rg.addColorStop(.98, 'rgba(30,70,80,.3)'); rg.addColorStop(1, 'rgba(30,70,80,0)');
      g0.fillStyle = rg; g0.beginPath(); g0.arc(64, 64, 62, 0, TAU); g0.fill();
    }
    g0.globalAlpha = .95; g0.fillStyle = '#fff'; g0.beginPath(); g0.ellipse(44, 40, 13, 8, -.7, 0, TAU); g0.fill();
    const ps = Array.from({ length: o.count }, () => {
      const r = (soap ? 14 + 30 * R() : 4 + 14 * R() ** 2) * e.u * o.size * 1.4;
      return { r, x: A.x + R() * A.w, ph: R(), k: soap ? 1 : o.speed + (r < 6 * e.u ? 1 : 0), a: R(), m: 1 + Math.floor(R() * 3), amp: o.wobble * (soap ? 40 : 3 + r * .6) * e.u };
    });
    return {
      draw(g, t) {
        clip(g, A);
        for (const p of ps) {
          const q = fr(p.k * t / e.D + p.ph), y = A.y + A.h + p.r - q * (A.h + 2 * p.r), x = p.x + p.amp * Math.sin(TAU * (p.m * t / e.D + p.a) + q * 6);
          g.globalAlpha = o.opacity * sstep(0, .1, q) * (1 - sstep(.85, 1, q)); g.drawImage(sp, x - p.r, y - p.r, 2 * p.r, 2 * p.r);
        }
        g.restore();
      },
    };
  });

  FX.def('confetti', {
    zh: '彩纸', group: '粒子', desc: '彩纸片和彩带翻着跟头飘落', suits: '生日、庆祝、开业、新年、促销',
    anchor: '派对、蛋糕、气球、庆祝文字；palette: auto 用图里的颜色',
    params: { count: P(70, 25, 160, '片数', true), size: P(1, .6, 1.6, '大小'), speed: P(2, 1, 3, '每轮落下的趟数', true), sway: P(1, .4, 1.8, '左右摆幅'), spin: P(1, .5, 2, '翻转快慢'), opacity: P(1, .8, 1, '透明度'), palette: P('auto', null, null, "'auto' 用图里的颜色，或给颜色数组"), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, base = ['#ff5c7a', '#ffd23f', '#3ec1d3', '#7b5cff', '#4cd97b', '#ff8c42'];
    let cols = o.palette === 'auto' ? (e.img ? U.palette(e, 6, null, .5) : base) : o.palette; if (cols.length < 3) cols = base;
    const ps = Array.from({ length: o.count }, () => {
      const d = .4 + .6 * R(), s = (7 + 9 * d) * e.u * o.size * 1.6, amp = o.sway * (12 + 30 * d) * e.u;
      return { d, s, amp, x: A.x - amp + R() * (A.w + 2 * amp), ph: R(), k: o.speed + (d > .85 ? 1 : 0), m: 1 + Math.floor(R() * 2), nr: Math.max(1, Math.round((1 + R()) * o.spin)), nf: Math.max(1, Math.round((2 + 3 * R()) * o.spin)), a: R(), b: R(), c: cols[Math.floor(R() * cols.length)], kind: R() < .6 ? 0 : R() < .7 ? 1 : 2 };
    }).sort((a, b) => a.d - b.d);
    return {
      draw(g, t) {
        const s = t / e.D; clip(g, A);
        for (const p of ps) {
          const y = A.y - 2 * p.s + fr(p.k * s + p.ph) * (A.h + 4 * p.s), x = p.x + p.amp * Math.sin(TAU * (p.m * s + p.a)), fl = Math.cos(TAU * (p.nf * s + p.b));
          g.save(); g.translate(x, y); g.rotate(TAU * (p.nr * s + p.a)); g.scale(1, Math.max(.1, Math.abs(fl))); g.globalAlpha = o.opacity; g.fillStyle = p.c;
          if (p.kind === 0) g.fillRect(-p.s * .8, -p.s * .45, p.s * 1.6, p.s * .9); else if (p.kind === 1) g.fillRect(-p.s * 1.3, -p.s * .2, p.s * 2.6, p.s * .4); else { g.beginPath(); g.arc(0, 0, p.s * .55, 0, TAU); g.fill(); }
          if (fl < 0) { g.fillStyle = 'rgba(0,0,0,.18)'; g.fillRect(-p.s * 1.3, -p.s * .6, p.s * 2.6, p.s * 1.2); }
          g.restore();
        }
        g.restore();
      },
    };
  });

  FX.def('sparkle', {
    zh: '星闪', group: '粒子', desc: '图里最亮的高光点上轮流闪出十字星芒', suits: '珠宝、手表、金属、水面、眼睛、玻璃、节日',
    anchor: '自动找原图的高光点（points: auto），也可以手动给点',
    params: { count: P(7, 3, 16, '颗数', true), size: P(1, .6, 1.8, '大小'), cycles: P(1, 1, 2, '每轮每颗闪几次', true), points: P('auto', null, null, "'auto' 自动找高光，或给 [[x,y], …]"), color: P('#ffffff', null, null, '颜色'), opacity: P(1, .7, 1, '透明度'), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, pts = o.points === 'auto' ? (e.img ? U.highlights(e, o.count, A) : []) : o.points.map(([x, y]) => [x * e.W, y * e.H]);
    const glow = U.sprite(o.color, [[0, .9], [.2, .35], [1, 0]], 64), win = .3;
    const gl = pts.map(([x, y], i) => ({ x, y, tc: i / Math.max(1, pts.length) + R() * .12, L: (45 + 55 * R()) * e.u * o.size * 1.6, rot: R() * .6 }));
    const star = (g, L, w) => { g.beginPath(); g.moveTo(0, -L); g.lineTo(w, 0); g.lineTo(0, L); g.lineTo(-w, 0); g.closePath(); g.fill(); };
    return {
      draw(g, t) {
        g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = o.color;
        for (const p of gl) {
          const q = fr(o.cycles * t / e.D - p.tc); if (q > win) continue;
          const k = Math.sin(Math.PI * q / win) ** 1.5, L = p.L * k;
          g.save(); g.translate(p.x, p.y); g.globalAlpha = o.opacity * k; g.drawImage(glow, -L * .45, -L * .45, L * .9, L * .9);
          g.rotate(p.rot + q * 1.5); star(g, L, L * .06); g.rotate(Math.PI / 2); star(g, L * .8, L * .05); g.rotate(Math.PI / 4); star(g, L * .35, L * .04); g.rotate(Math.PI / 2); star(g, L * .35, L * .04);
          g.restore();
        }
        g.restore();
      },
    };
  });

  // ======================= 空气和水 =======================
  FX.def('fog', {
    zh: '雾流', group: '空气和水', desc: '几层薄雾以不同速度横着飘过一个区域，上下边软', suits: '山水、湖面、清晨、森林、水墨、梦幻',
    anchor: '山腰、湖面、林间、远景交界处；area 给雾带所在的区域',
    params: { area: P([0, .35, 1, .75], null, null, '雾带区域'), density: P(.7, .4, .95, '浓度'), speed: P(1, 1, 2, '每轮飘过的圈数', true), scale: P(1, .6, 1.6, '雾团大小'), layers: P(2, 1, 3, '层数', true), dir: P(1, null, null, '1 往右飘 / -1 往左'), color: P('#ffffff', null, null, '颜色'), feather: P(.35, .15, .5, '边缘柔和度') },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, tw = 256, th = 128, [r, gg, b] = U.rgb(o.color), sc = .5;  // 离屏半分辨率：雾本来就软
    const tiles = Array.from({ length: o.layers }, (_, l) => {
      const n = U.tileNoise(tw, th, o.seed * 31 + l * 7, 4, 4), [c, g] = U.canvas(tw, th), id = g.createImageData(tw, th);
      for (let i = 0; i < n.length; i++) { id.data[i * 4] = r; id.data[i * 4 + 1] = gg; id.data[i * 4 + 2] = b; id.data[i * 4 + 3] = 255 * sstep(.32, .75, n[i]); }
      g.putImageData(id, 0, 0); return { c, ph: R(), k: o.speed + l, w: A.w * (1.1 + .5 * l) * o.scale * sc, h: A.h * (1 + .2 * l) * sc };
    });
    const [off, og] = U.canvas(A.w * sc, A.h * sc), mask = U.softMask({ ...U.rect(o.area, e), w: A.w * sc, h: A.h * sc }, Math.min(A.w, A.h) * sc * o.feather);
    return {
      draw(g, t) {
        og.clearRect(0, 0, off.width, off.height);
        for (const L of tiles) {
          og.globalAlpha = o.density / Math.sqrt(o.layers); const x0 = -fr(o.dir * L.k * t / e.D + L.ph) * L.w, y0 = (off.height - L.h) / 2;
          for (let x = x0; x < off.width; x += L.w) og.drawImage(L.c, x, y0, L.w + 1, L.h);
        }
        og.globalAlpha = 1; U.blit(g, off, A, mask);
      },
    };
  });

  FX.def('steam', {
    zh: '蒸汽', group: '空气和水', desc: '热气一团团从热的东西上升起，边升边散、轻轻打卷', suits: '热饮、拉面、火锅、温泉、冬天的早餐',
    anchor: '碗口、杯口、锅、温泉水面；from 给冒气的区域',
    params: { from: P([[.4, .55, .6, .6]], null, null, '冒气的区域 [[x0,y0,x1,y1], …]'), height: P(.45, .25, .8, '升多高（占画面高）'), count: P(70, 30, 140, '烟团数', true), speed: P(1, 1, 2, '每轮升起的趟数', true), spread: P(1, .5, 1.8, '散开程度'), curl: P(1, .4, 2, '打卷'), size: P(1, .6, 1.6, '烟团大小'), opacity: P(.16, .08, .3, '浓淡'), color: P('#ffffff', null, null, '颜色') },
  }, (o, e) => {
    const R = e.R, src = o.from.map(a => U.rect(a, e)), sp = U.sprite(o.color, [[0, .9], [.45, .45], [1, 0]]);
    const ps = Array.from({ length: o.count }, (_, i) => {
      const A = src[i % src.length];
      return { x: A.x + R() * A.w, y: A.y + R() * A.h, ph: R(), f: .5 + R(), a: R(), b: R(), dx: (R() - .5) * o.spread * .25 * e.H };
    });
    return {
      draw(g, t) {
        const s = t / e.D; g.save(); g.globalCompositeOperation = 'screen';
        for (const p of ps) {
          const q = fr(o.speed * s + p.ph), y = p.y - q * o.height * e.H, x = p.x + p.dx * q + Math.sin(TAU * (q * p.f + p.a)) * o.curl * 40 * e.u * q + Math.sin(TAU * (s + p.b)) * 10 * e.u * q;
          const r = (25 + 110 * q) * e.u * o.size * Math.sqrt(o.spread);
          g.globalAlpha = cl(o.opacity * Math.sin(Math.PI * q) ** 1.3 * (1 - .4 * q)); g.drawImage(sp, x - r, y - r, 2 * r, 2 * r);
        }
        g.restore();
      },
    };
  });

  FX.def('smoke', {
    zh: '烟缕', group: '空气和水', desc: '一缕或几缕细烟从一点升起，越往上越宽越淡，波浪一样往上爬', suits: '炊烟、香、蜡烛熄灭、烟囱、茶馆、禅意',
    anchor: '烟囱、香炉、蜡烛、烟斗、篝火；from 给起点（可以几个）',
    params: { from: P([[.5, .6]], null, null, '起点 [[x,y], …]'), height: P(.5, .25, .8, '升多高（占画面高）'), strands: P(2, 1, 4, '每个起点几缕', true), sway: P(1, .4, 2, '摆动幅度'), width: P(1, .6, 1.8, '烟的宽度'), lean: P(.15, -.5, .5, '整体往一边飘（正数往右）'), speed: P(1, 1, 2, '波纹上爬的速度', true), opacity: P(.5, .25, .7, '浓淡'), color: P('auto', null, null, "'auto' 亮底用灰烟、暗底用白烟，或给颜色") },
  }, (o, e) => {
    const R = e.R, N = 70, T = e.img ? U.lum(e.img) : null;
    let bg = .3;  // 烟要升过的那一竖条的平均亮度
    if (T) { let sm = 0, k = 0; for (const [fx, fy] of o.from) for (let q = 0; q <= 1; q += .05) { const y = Math.max(0, fy - q * o.height), x = cl(fx + o.lean * q * o.height * .8 * e.H / e.W, 0, .999); sm += T.L[Math.min(T.h - 1, Math.floor(y * T.h)) * T.w + Math.floor(x * T.w)]; k++; } bg = sm / k; }
    const light = bg > .55, sp = U.sprite(o.color === 'auto' ? (light ? '#6f6b66' : '#ece9e2') : o.color, [[0, .8], [.5, .35], [1, 0]], 64), op = light ? 'source-over' : 'screen', k0 = light ? .7 : 1;
    const strands = o.from.flatMap(([fx, fy]) => Array.from({ length: o.strands }, () => ({ x: fx * e.W, y: fy * e.H, h: o.height * e.H * (.75 + .25 * R()), w: [1, .5, .25].map(a => a * (.7 + .6 * R())), f: [1.1 + R() * .4, 2.2 + R() * .6, 3.6 + R()], k: [1, 2, 1], ps: [R(), R(), R()].map(v => v * TAU) })));
    return {
      draw(g, t) {
        const s = t / e.D; g.save(); g.globalCompositeOperation = op;
        for (const S of strands) for (let i = 0; i < N; i++) {
          const q = i / (N - 1), y = S.y - q * S.h;
          let x = S.x + o.lean * q * S.h * .8; for (let j = 0; j < 3; j++) x += S.w[j] * q ** 1.3 * Math.sin(TAU * (S.f[j] * q - S.k[j] * o.speed * s) + S.ps[j]) * o.sway * e.H * .05;
          const r = (9 + 80 * q ** 1.2) * e.u * o.width; g.globalAlpha = cl(k0 * o.opacity * (1 - q) ** 1.4 * sstep(0, .04, q) * .5);
          g.drawImage(sp, x - r, y - r, 2 * r, 2 * r);
        }
        g.restore();
      },
    };
  });

  FX.def('clouds', {
    zh: '云移', group: '空气和水', desc: '一层噪声云在天空区域里横着飘，云顶亮、云底带一点灰', suits: '蓝天、风景、旅行、田野、童话',
    anchor: '天空；area 只框天空，别盖到主体',
    params: { area: P([0, 0, 1, .35], null, null, '天空区域'), cover: P(.45, .3, .7, '云量'), scale: P(1, .6, 1.6, '云团大小'), speed: P(1, 1, 2, '每轮飘过的趟数', true), dir: P(1, null, null, '1 往右 / -1 往左'), opacity: P(.85, .5, 1, '透明度'), shadow: P('#9aa6b6', null, null, '云底颜色'), feather: P(.3, .1, .5, '边缘柔和度') },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, tw = 384, th = 192, sh = U.rgb(o.shadow), sc = .5;
    const layers = [0, 1].map(l => {
      const n = U.tileNoise(tw, th, o.seed * 13 + l * 5, 5, 5), [c, g] = U.canvas(tw, th), id = g.createImageData(tw, th), lo = 1 - o.cover - .08 * l;
      for (let j = 0; j < th; j++) for (let i = 0; i < tw; i++) {
        const v = n[j * tw + i], a = sstep(lo - .08, lo + .14, v), lit = cl(.78 + 7 * (n[((j + 3) % th) * tw + i] - n[((j - 3 + th) % th) * tw + i]), .55, 1), k = (j * tw + i) * 4;
        for (let ch = 0; ch < 3; ch++) id.data[k + ch] = sh[ch] + (255 - sh[ch]) * lit;
        id.data[k + 3] = 255 * a * (l ? .55 : 1);
      }
      g.putImageData(id, 0, 0); return { c, k: o.speed + l, ph: R(), w: A.w * (1.2 - .3 * l) * o.scale * sc, h: A.h * 1.25 * sc };
    }).reverse();
    const [off, og] = U.canvas(A.w * sc, A.h * sc), mask = U.softMask({ ...A, w: A.w * sc, h: A.h * sc }, Math.min(A.w, A.h) * sc * o.feather);
    return {
      draw(g, t) {
        og.clearRect(0, 0, off.width, off.height);
        for (const L of layers) { const x0 = -fr(o.dir * L.k * t / e.D + L.ph) * L.w; for (let x = x0; x < off.width; x += L.w) og.drawImage(L.c, x, (off.height - L.h) / 2, L.w + 1, L.h); }
        U.blit(g, off, A, mask, o.opacity);
      },
    };
  });

  FX.def('water', {
    zh: '水波光', group: '空气和水', desc: '水面区域按行轻轻错动出波纹，越近波越大，亮处闪着碎波光', suits: '湖面、海面、河、积水倒影、泳池、霓虹倒影',
    anchor: '原图里的水面、倒影；area 只框水面',
    params: { area: P([0, .75, 1, 1], null, null, '水面区域'), amp: P(1, .4, 2, '波动幅度'), wave: P(1, .6, 1.6, '波长'), speed: P(2, 1, 4, '每轮波纹走几个周期', true), persp: P(1, 0, 1.5, '越靠下波越大（透视）'), glints: P(1, 0, 2, '碎波光数量'), feather: P(.15, .05, .3, '上边缘柔和度') },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, hs = Math.max(1, Math.round(1.6 * e.u)), rows = Math.ceil(A.h / hs), ph = new Float32Array(rows + 1);
    for (let i = 1; i <= rows; i++) { const q = i / rows; ph[i] = ph[i - 1] + hs / ((12 + 30 * q) * e.u * o.wave); }
    const [off, og] = U.canvas(A.w, A.h), mask = U.softMask(A, A.h * o.feather), gs = U.sprite('#ffffff', [[0, 1], [.4, .5], [1, 0]], 32);
    const gl = e.img && o.glints > 0 ? U.highlights(e, Math.round(40 * o.glints), A, .015).map(([x, y]) => ({ x, y, m: 2 + Math.floor(R() * 3), a: R(), L: (6 + 14 * R()) * e.u })) : [];
    return {
      draw(g, t) {
        const s = t / e.D; og.clearRect(0, 0, A.w, A.h);
        for (let i = 0; i < rows; i++) {
          const q = i / rows, amp = o.amp * e.u * 5 * (.25 + .75 * q ** o.persp), y = i * hs;
          const dx = amp * (Math.sin(TAU * (ph[i] - o.speed * s)) + .4 * Math.sin(TAU * (ph[i] * 1.7 + 2 * o.speed * s) + .3));
          og.drawImage(e.img, A.x, A.y + y, A.w, hs, dx, y, A.w, hs);
        }
        U.blit(g, off, A, mask);
        g.save(); g.globalCompositeOperation = 'lighter';
        for (const p of gl) { const b = (.5 + .5 * Math.sin(TAU * (p.m * s + p.a))) ** 4; if (b < .02) continue; g.globalAlpha = b * .9; g.drawImage(gs, p.x - p.L, p.y - p.L * .25, p.L * 2, p.L * .5); }
        g.restore();
      },
    };
  });

  FX.def('caustics', {
    zh: '焦散', group: '空气和水', desc: '水下或水边那种流动的网状光纹', suits: '水下、泳池、海边、玻璃、清凉夏天',
    anchor: '水下画面、泳池底、被水反光照到的墙面；area 框光纹落的地方',
    params: { area: AREA, scale: P(1, .6, 1.8, '纹理密度'), speed: P(1, 1, 2, '流动快慢', true), intensity: P(.45, .2, .8, '亮度'), color: P('#eafcff', null, null, '光的颜色'), feather: P(.15, 0, .3, '边缘柔和度') },
  }, (o, e) => {
    const A = U.rect(o.area, e), cw = 200, ch = Math.max(2, Math.round(cw * A.h / A.w)), [lo, lg] = U.canvas(cw, ch), id = lg.createImageData(cw, ch), [r, gg, b] = U.rgb(o.color);
    const [off, og] = U.canvas(A.w, A.h), mask = U.softMask(A, Math.min(A.w, A.h) * o.feather), ks = [1, -1, 2, -1, 1].map(k => k * o.speed), sc = 1.6 * o.scale / Math.min(A.w, A.h);
    return {
      draw(g, t) {
        const s = t / e.D;
        for (let j = 0; j < ch; j++) for (let i = 0; i < cw; i++) {
          const px = ((i / cw * A.w * sc * TAU) % TAU) - 250, py = ((j / ch * A.h * sc * TAU) % TAU) - 250; let ix = px, iy = py, c = 1;
          for (let n = 0; n < 5; n++) { const tn = TAU * ks[n] * s + n * 1.7; const nx = px + Math.cos(tn - ix) + Math.sin(tn + iy), ny = py + Math.sin(tn - iy) + Math.cos(tn + ix); ix = nx; iy = ny; c += 1 / Math.hypot(px / (Math.sin(ix + tn) / .005), py / (Math.cos(iy + tn) / .005)); }
          c = 1.17 - Math.pow(c / 5, 1.4); const v = cl(Math.pow(Math.abs(c), 8)), k = (j * cw + i) * 4;
          id.data[k] = r; id.data[k + 1] = gg; id.data[k + 2] = b; id.data[k + 3] = 255 * v;
        }
        lg.putImageData(id, 0, 0); og.clearRect(0, 0, A.w, A.h); og.imageSmoothingQuality = 'high'; og.drawImage(lo, 0, 0, A.w, A.h);
        U.blit(g, off, A, mask, o.intensity, 'lighter');
      },
    };
  });

  FX.def('haze', {
    zh: '热浪', group: '空气和水', desc: '热空气让一块区域的画面细细地扭动，波纹往上走', suits: '沙漠、柏油路、火锅、篝火上方、夏天正午',
    anchor: '热源上方、远处地平线；area 框扭动的区域',
    params: { area: P([0, .5, 1, .85], null, null, '扭动区域'), amp: P(1, .4, 2, '扭动幅度'), freq: P(1, .6, 1.6, '波纹密度'), speed: P(3, 2, 5, '每轮上爬的周期数', true), feather: P(.25, .1, .4, '边缘柔和度') },
  }, (o, e) => {
    const A = U.rect(o.area, e), hs = Math.max(1, Math.round(1.2 * e.u)), rows = Math.ceil(A.h / hs), lam = 22 * e.u / o.freq;
    const [off, og] = U.canvas(A.w, A.h), mask = U.softMask(A, Math.min(A.w, A.h) * o.feather);
    return {
      draw(g, t) {
        const s = t / e.D; og.clearRect(0, 0, A.w, A.h);
        for (let i = 0; i < rows; i++) {
          const y = i * hs, dx = o.amp * e.u * 1.8 * (Math.sin(TAU * (y / lam + o.speed * s)) + .5 * Math.sin(TAU * (y / (lam * .43) + (o.speed + 1) * s) + 1.3));
          og.drawImage(e.img, A.x, A.y + y, A.w, hs, dx, y, A.w, hs);
        }
        U.blit(g, off, A, mask);
      },
    };
  });

  FX.def('ripples', {
    zh: '雨打水面', group: '空气和水', desc: '水面上此起彼伏地荡开一圈圈椭圆涟漪', suits: '池塘、湖面、雨天、积水、锦鲤、禅意',
    anchor: '原图里的水面；area 只框水面，squash 按俯视角度调扁',
    params: { area: P([0, .6, 1, 1], null, null, '水面区域'), count: P(10, 4, 24, '同时的涟漪数', true), size: P(1, .6, 1.6, '大小'), squash: P(.4, .2, .8, '扁度（视角越低越扁）'), speed: P(1, 1, 3, '每轮每处荡几次', true), rings: P(2, 1, 3, '每次几圈', true), persp: P(1, 0, 1.5, '越靠下越大'), color: P('#ffffff', null, null, '亮环颜色'), shadow: P('#2a3a3a', null, null, '暗环颜色'), opacity: P(.6, .35, .85, '透明度') },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R;
    const rp = Array.from({ length: o.count }, () => { const y = A.y + R() * A.h, k = 1 - o.persp * .5 + o.persp * .5 * ((y - A.y) / A.h) * 2; return { x: A.x + R() * A.w, y, ph: R(), Rm: (40 + 50 * R()) * e.u * o.size * 1.4 * Math.max(.3, k) }; });
    return {
      draw(g, t) {
        clip(g, A);
        for (const p of rp) {
          const q0 = fr(o.speed * t / e.D + p.ph);
          for (let j = 0; j < o.rings; j++) {
            const q = q0 - j * .12; if (q <= 0) continue;
            const rr = q * p.Rm, al = o.opacity * (1 - q) ** 1.6 * sstep(0, .05, q);
            g.lineWidth = Math.max(.8, (1.6 - q) * 2.4 * e.u);
            g.globalAlpha = al * .7; g.strokeStyle = o.shadow; g.beginPath(); g.ellipse(p.x, p.y + 1.6 * e.u, rr * .94, rr * .94 * o.squash, 0, 0, TAU); g.stroke();  // 暗环：亮底上靠它看得见
            g.globalAlpha = al; g.strokeStyle = o.color; g.beginPath(); g.ellipse(p.x, p.y, rr, rr * o.squash, 0, 0, TAU); g.stroke();
          }
          if (q0 < .06) { g.globalAlpha = o.opacity * (1 - q0 / .06); g.fillStyle = o.color; g.beginPath(); g.arc(p.x, p.y, 2.2 * e.u, 0, TAU); g.fill(); }
        }
        g.restore();
      },
    };
  });
  // ---------------- 网格变形（摇摆、飘动、呼吸用） ----------------
  // 精确三角形贴图：src 三点 → dst 三点。只取 src 三角形的包围盒来画，快。
  U.tri = (g, img, s0, s1, s2, d0, d1, d2) => {
    const [x0, y0] = s0, [x1, y1] = s1, [x2, y2] = s2, den = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0); if (!den) return;
    const a = ((d1[0] - d0[0]) * (y2 - y0) - (d2[0] - d0[0]) * (y1 - y0)) / den, c = ((d2[0] - d0[0]) * (x1 - x0) - (d1[0] - d0[0]) * (x2 - x0)) / den;
    const b = ((d1[1] - d0[1]) * (y2 - y0) - (d2[1] - d0[1]) * (y1 - y0)) / den, d = ((d2[1] - d0[1]) * (x1 - x0) - (d1[1] - d0[1]) * (x2 - x0)) / den;
    const cx = (d0[0] + d1[0] + d2[0]) / 3, cy = (d0[1] + d1[1] + d2[1]) / 3, ex = p => { const dx = p[0] - cx, dy = p[1] - cy, l = Math.hypot(dx, dy) || 1; return [p[0] + dx / l * .6, p[1] + dy / l * .6]; };
    const e0 = ex(d0), e1 = ex(d1), e2 = ex(d2);
    g.save(); g.beginPath(); g.moveTo(e0[0], e0[1]); g.lineTo(e1[0], e1[1]); g.lineTo(e2[0], e2[1]); g.closePath(); g.clip();
    g.transform(a, b, c, d, d0[0] - a * x0 - c * y0, d0[1] - b * x0 - d * y0);
    const mx = Math.max(0, Math.min(x0, x1, x2) - 2), my = Math.max(0, Math.min(y0, y1, y2) - 2), Mx = Math.min(img.width, Math.max(x0, x1, x2) + 2), My = Math.min(img.height, Math.max(y0, y1, y2) + 2);
    if (Mx > mx && My > my) g.drawImage(img, mx, my, Mx - mx, My - my, mx, my, Mx - mx, My - my);
    g.restore();
  };
  // 把区域 A 的原图按位移场 disp(x, y) → [dx, dy] 画出来。位移在区域边上应当归零，这样不会露缝、不会重影。
  U.meshWarp = (g, img, A, cols, rows, disp) => {
    const V = [];
    for (let j = 0; j <= rows; j++) for (let i = 0; i <= cols; i++) { const x = A.x + A.w * i / cols, y = A.y + A.h * j / rows, [dx, dy] = disp(x, y); V.push([[x, y], [x + dx, y + dy]]); }
    const at = (i, j) => V[j * (cols + 1) + i];
    for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
      const a = at(i, j), b = at(i + 1, j), c = at(i, j + 1), d = at(i + 1, j + 1);
      U.tri(g, img, a[0], b[0], d[0], a[1], b[1], d[1]); U.tri(g, img, a[0], d[0], c[0], a[1], d[1], c[1]);
    }
  };
  // 区域边缘权重：贴着原图边的那几条边不归零（那边本来就没有"外面"）
  const edgeW = (A, x, y, f = .15) => { const [x0, y0, x1, y1] = A.a, u = (x - A.x) / A.w, v = (y - A.y) / A.h; return (x0 <= 0 ? 1 : sstep(0, f, u)) * (x1 >= 1 ? 1 : sstep(0, f, 1 - u)) * (y0 <= 0 ? 1 : sstep(0, f, v)) * (y1 >= 1 ? 1 : sstep(0, f, 1 - v)); };
  const loadImg = src => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.onerror = () => { console.error('FX 读图失败 ' + src); r(null); }; i.src = src; });
  const colorAt = (e, x, y) => { const T = U.lum(e.img), i = Math.min(T.w - 1, Math.max(0, Math.floor(x / T.sx))), j = Math.min(T.h - 1, Math.max(0, Math.floor(y / T.sy))), k = (j * T.w + i) * 4; return [T.d[k], T.d[k + 1], T.d[k + 2]]; };
  const lowres = (e, A, cw) => { const ch = Math.max(2, Math.round(cw * A.h / A.w)), [c, g] = U.canvas(cw, ch); return { c, g, cw, ch, id: g.createImageData(cw, ch) }; };

  // ======================= 光 =======================
  FX.groups.push('光', '局部动作', '镜头');
  FX.def('godrays', {
    zh: '光束', group: '光', desc: '从光源（窗、太阳、树缝）射出一束束光，慢慢摇曳、忽明忽暗', suits: '窗边、森林、教堂、舞台、逆光人像、清晨',
    anchor: '光源位置；from 给光源点（可以在画外），dir / spread 给照射方向和张角',
    params: { from: P([.8, .05], null, null, '光源点 [x,y]'), dir: P(120, null, null, '照射方向（度，0 向右，90 向下）'), spread: P(60, 20, 120, '张角（度）'), length: P(1, .5, 1.5, '光束长度'), rays: P(1, .5, 2, '光束疏密'), speed: P(1, 1, 2, '摇曳快慢', true), intensity: P(.5, .25, .8, '亮度'), color: P('#fff1cc', null, null, '光的颜色'), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), L = lowres(e, A, 220), [r, gg, b] = U.rgb(o.color), sx = o.from[0] * e.W, sy = o.from[1] * e.H, dir = o.dir * Math.PI / 180, half = o.spread * Math.PI / 360, M = Math.min(e.W, e.H), R = e.R;
    const f = [17, 29, 47].map(v => Math.round(v * o.rays)), ph = [R(), R(), R()].map(v => v * TAU);
    return {
      draw(g, t) {
        const s = t / e.D, d = L.id.data;
        for (let j = 0; j < L.ch; j++) for (let i = 0; i < L.cw; i++) {
          const x = A.x + (i + .5) / L.cw * A.w, y = A.y + (j + .5) / L.ch * A.h, dx = x - sx, dy = y - sy, rr = Math.hypot(dx, dy) / M;
          let da = Math.atan2(dy, dx) - dir; da = Math.atan2(Math.sin(da), Math.cos(da));
          const cone = sstep(half, half * .5, Math.abs(da)); if (cone <= 0) { d[(j * L.cw + i) * 4 + 3] = 0; continue; }
          const th = da / (half * 2);
          const v = .5 + .25 * Math.sin(th * f[0] + TAU * o.speed * s + ph[0]) + .15 * Math.sin(th * f[1] - TAU * o.speed * s + ph[1]) + .1 * Math.sin(th * f[2] + TAU * 2 * o.speed * s + ph[2]);
          const k = (j * L.cw + i) * 4, val = cone * sstep(.42, .85, v) * Math.exp(-rr / (.9 * o.length)) * sstep(0, .06, rr);
          d[k] = r; d[k + 1] = gg; d[k + 2] = b; d[k + 3] = 255 * cl(val * o.intensity * 1.6);
        }
        L.g.putImageData(L.id, 0, 0);
        g.save(); g.globalCompositeOperation = 'screen'; g.imageSmoothingQuality = 'high'; g.drawImage(L.c, A.x, A.y, A.w, A.h); g.restore();
      },
    };
  });

  FX.def('glow', {
    zh: '光晕呼吸', group: '光', desc: '灯、窗、火这些亮处罩上一圈光晕，慢慢一呼一吸', suits: '灯笼、吊灯、蜡烛、霓虹、窗灯、夜景',
    anchor: '自动找原图里的灯（亮处，颜色取灯本身）；也可手动给点',
    params: { points: P('auto', null, null, "'auto' 或 [[x,y], …]"), count: P(6, 1, 16, '光晕个数', true), size: P(1, .5, 2, '大小'), breathe: P(.5, .2, .9, '呼吸幅度'), speed: P(1, 1, 3, '每轮呼吸几次', true), intensity: P(.6, .3, 1, '亮度'), color: P('auto', null, null, "'auto' 用灯本身的颜色，或给颜色"), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, pts = o.points === 'auto' ? U.highlights(e, o.count, A, .1).filter(p => p[2] > .6) : o.points.map(([x, y]) => [x * e.W, y * e.H, 1]);
    const gl = pts.map(([x, y, l]) => {
      const c = o.color === 'auto' ? U.hex(colorAt(e, x, y).map(v => v + (255 - v) * .3)) : o.color;
      return { x, y, s: U.sprite(c, [[0, .85], [.15, .5], [.45, .14], [1, 0]]), r: (70 + 110 * R()) * e.u * o.size * (.6 + .4 * l), ph: R() };
    });
    return {
      draw(g, t) {
        const s = t / e.D; g.save(); g.globalCompositeOperation = 'screen';
        for (const p of gl) { const v = .5 + .5 * Math.sin(TAU * (o.speed * s + p.ph)), r = p.r * (1 + .1 * v); g.globalAlpha = o.intensity * (1 - o.breathe + o.breathe * v); g.drawImage(p.s, p.x - r, p.y - r, 2 * r, 2 * r); }
        g.restore();
      },
    };
  });

  // 不规则但周期的跳动信号（几种整数频率叠加），0..1
  const jitter = (s, a, ks = [7, 13, 23, 31]) => cl(.62 + .16 * Math.sin(TAU * (ks[0] * s) + a) + .1 * Math.sin(TAU * (ks[1] * s) + a * 2.3) + .08 * Math.sin(TAU * (ks[2] * s) + a * 4.1) + .05 * Math.sin(TAU * (ks[3] * s) + a * 7.7));
  FX.def('flicker', {
    zh: '烛火闪', group: '光', desc: '火光不规则地跳：火苗的光晕忽大忽小，整个画面的暖光跟着明暗（neon 模式是霓虹接触不良的闪）', suits: '蜡烛、篝火、壁炉、油灯、霓虹招牌',
    anchor: '火苗、灯管的位置：points 手动给，或在 area 里自动找最亮的点',
    params: { points: P('auto', null, null, "'auto' 或 [[x,y], …]"), count: P(5, 1, 12, '火苗数', true), mode: P('candle', null, null, "'candle' 烛火 / 'neon' 霓虹"), size: P(1, .5, 2, '光晕大小'), intensity: P(.75, .4, 1, '亮度'), ambient: P(.3, 0, .6, '整个画面跟着明暗的幅度'), color: P('#ffb45a', null, null, '火光颜色'), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, pts = o.points === 'auto' ? U.highlights(e, o.count, A, .02) : o.points.map(([x, y]) => [x * e.W, y * e.H, 1]);
    const sp = U.sprite(o.color, [[0, .9], [.12, .55], [.4, .15], [1, 0]]), fl = pts.map(([x, y]) => ({ x, y, a: R() * TAU, r: (40 + 30 * R()) * e.u * o.size }));
    const win = [R() * .5, .5 + R() * .45];
    const sig = (s, a) => o.mode === 'neon' ? (win.some(w => fr(s - w) < .07) ? (Math.sin(TAU * s * 90 + a) > -.2 ? 1 : .12) : 1) : jitter(s, a);
    return {
      draw(g, t) {
        const s = t / e.D; let avg = 0; g.save(); g.globalCompositeOperation = 'lighter';
        for (const p of fl) { const v = sig(s, p.a); avg += v; const r = p.r * (.85 + .3 * v); g.globalAlpha = o.intensity * v; g.drawImage(sp, p.x - r, p.y - r, 2 * r, 2 * r); }
        avg = fl.length ? avg / fl.length : 1;
        const k = o.ambient * (avg - (o.mode === 'neon' ? .9 : .62)) * 2;
        if (k > 0) { g.globalCompositeOperation = 'screen'; g.globalAlpha = cl(k * .5); g.fillStyle = o.color; g.fillRect(0, 0, e.W, e.H); }
        else if (k < 0) { g.globalCompositeOperation = 'multiply'; g.globalAlpha = cl(-k * .8); g.fillStyle = '#3a3028'; g.fillRect(0, 0, e.W, e.H); }
        g.restore();
      },
    };
  });

  FX.def('sheen', {
    zh: '高光扫', group: '光', desc: '一道斜向高光从表面扫过，只亮在本来就亮的面上（金属、玻璃、包装、烫金字）', suits: '产品、手表、珠宝、包装、汽车、金属字、Logo',
    anchor: 'area 框商品或亮面；maskBy: light 让高光只落在亮面上',
    params: { area: AREA, angle: P(25, -60, 60, '光带倾斜（度）'), width: P(1, .5, 2, '光带宽度'), times: P(1, 1, 2, '每轮扫几次', true), at: P(.3, 0, .7, '开始扫的时刻（占一轮）'), dur: P(.35, .2, .6, '扫过用时（占一轮）'), intensity: P(.85, .4, 1, '亮度'), maskBy: P('light', null, null, "'light' 只亮在亮面 / 'none'"), color: P('#ffffff', null, null, '颜色') },
  }, (o, e) => {
    const A = U.rect(o.area, e), sc = .5, [off, og] = U.canvas(A.w * sc, A.h * sc), [mk, mg] = U.canvas(A.w * sc, A.h * sc);
    if (o.maskBy === 'light' && e.img) {
      mg.drawImage(e.img, A.x, A.y, A.w, A.h, 0, 0, mk.width, mk.height); const id = mg.getImageData(0, 0, mk.width, mk.height), d = id.data;
      for (let i = 0; i < d.length; i += 4) { const l = (d[i] * .299 + d[i + 1] * .587 + d[i + 2] * .114) / 255; d[i] = d[i + 1] = d[i + 2] = 255; d[i + 3] = 255 * sstep(.3, .8, l); }
      mg.putImageData(id, 0, 0);
    } else { mg.fillStyle = '#fff'; mg.fillRect(0, 0, mk.width, mk.height); }
    const ang = o.angle * Math.PI / 180, W2 = off.width, H2 = off.height, diag = Math.hypot(W2, H2), bw = diag * .09 * o.width, [r, gg, b] = U.rgb(o.color);
    return {
      draw(g, t) {
        const q = fr(o.times * t / e.D - o.at) / o.dur; if (q <= 0 || q >= 1) return;
        const pos = -diag / 2 - bw * 2 + (q * q * (3 - 2 * q)) * (diag + bw * 4);
        og.clearRect(0, 0, W2, H2); og.save(); og.translate(W2 / 2, H2 / 2); og.rotate(ang);
        const gr = og.createLinearGradient(pos - bw, 0, pos + bw, 0); gr.addColorStop(0, `rgba(${r},${gg},${b},0)`); gr.addColorStop(.45, `rgba(${r},${gg},${b},.9)`); gr.addColorStop(.5, `rgba(${r},${gg},${b},1)`); gr.addColorStop(.55, `rgba(${r},${gg},${b},.9)`); gr.addColorStop(1, `rgba(${r},${gg},${b},0)`);
        og.fillStyle = gr; og.fillRect(-diag, -diag, diag * 2, diag * 2);
        const g2 = og.createLinearGradient(pos - bw * 2.2, 0, pos - bw * 1.6, 0); g2.addColorStop(0, `rgba(${r},${gg},${b},0)`); g2.addColorStop(.5, `rgba(${r},${gg},${b},.5)`); g2.addColorStop(1, `rgba(${r},${gg},${b},0)`);
        og.fillStyle = g2; og.fillRect(-diag, -diag, diag * 2, diag * 2); og.restore();
        og.globalCompositeOperation = 'destination-in'; og.drawImage(mk, 0, 0); og.globalCompositeOperation = 'source-over';
        g.save(); g.globalCompositeOperation = 'screen'; g.globalAlpha = o.intensity * Math.sin(Math.PI * q) ** .3; g.drawImage(off, A.x, A.y, A.w, A.h); g.restore();
      },
    };
  });

  FX.def('shadows', {
    zh: '树影', group: '光', desc: '窗外树叶的影子落在墙上、桌上，随风轻轻摇', suits: '窗边、室内、午后、咖啡馆、卧室、人像',
    anchor: '受光的墙面、桌面、地面；area 框那块面',
    params: { area: AREA, density: P(.5, .3, .7, '叶影多少'), scale: P(1, .6, 1.6, '叶子大小'), sway: P(1, .4, 2, '摇动幅度'), speed: P(1, 1, 3, '每轮摇几次', true), softness: P(1, .5, 2, '影子虚实'), strength: P(.4, .15, .6, '影子深浅'), angle: P(-20, -60, 60, '影子斜度（度）'), color: P('#2a2540', null, null, '影子颜色'), feather: P(.2, .05, .4, '边缘柔和度') },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, sc = .5, TS = 512, [tx, tg] = U.canvas(TS, TS), n = U.tileNoise(64, 64, o.seed * 3 + 1, 3, 3);
    tg.fillStyle = o.color;
    for (let i = 0; i < 900 * o.density; i++) {  // 叶子成团：按噪声决定这里有没有叶
      const x = R() * TS, y = R() * TS; if (n[Math.floor(y / TS * 64) * 64 + Math.floor(x / TS * 64)] < .45 + (1 - o.density) * .2) continue;
      const s = (7 + 10 * R()) * o.scale; tg.save(); tg.translate(x, y); tg.rotate(R() * TAU); tg.beginPath(); tg.ellipse(0, 0, s, s * .45, 0, 0, TAU); tg.fill(); tg.restore();
    }
    const [sx, sg] = U.canvas(TS, TS); sg.filter = `blur(${2.5 * o.softness}px)`; sg.drawImage(tx, 0, 0);
    const [off, og] = U.canvas(A.w * sc, A.h * sc), mask = U.softMask({ ...A, w: A.w * sc, h: A.h * sc }, Math.min(A.w, A.h) * sc * o.feather), ph = R(), ang = o.angle * Math.PI / 180;
    return {
      draw(g, t) {
        const s = t / e.D, W2 = off.width, H2 = off.height, sz = Math.max(W2, H2) * 1.5; og.clearRect(0, 0, W2, H2);
        [[1, .6], [-.7, .45]].forEach(([k, al], l) => {
          const sw = Math.sin(TAU * (o.speed * s + ph + l * .3)) + .35 * Math.sin(TAU * (2 * o.speed * s + ph * 2 + l));
          og.save(); og.globalAlpha = al; og.translate(W2 / 2 + sw * k * o.sway * 12 * e.u * sc, H2 / 2 + sw * .4 * o.sway * 6 * e.u * sc); og.rotate(ang + sw * .02 * o.sway * k);
          og.drawImage(sx, -sz / 2 + l * 97, -sz / 2 + l * 53, sz, sz); og.restore();
        });
        U.blit(g, off, A, mask, o.strength * 1.6, 'multiply');
      },
    };
  });

  const catmull = (pts, n = 16) => { const out = []; for (let i = 0; i < pts.length - 1; i++) { const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)]; for (let k = 0; k < n; k++) { const t = k / n, t2 = t * t, t3 = t2 * t; out.push([0, 1].map(j => .5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3))); } } out.push(pts[pts.length - 1]); return out; };
  FX.def('pulse', {
    zh: '光脉冲', group: '光', desc: '光点沿着线（光纤、霓虹管、电路、车道）一串串跑过去，带拖尾', suits: '科技、光纤、电路、城市车流、霓虹、数据',
    anchor: '图里线条的走向；paths 给一条或几条折线（0..1 坐标），会自动画成平滑曲线',
    params: { paths: P([[[0, .5], [1, .5]]], null, null, '路径 [[[x,y], …], …]'), count: P(14, 4, 40, '同时跑的光点数', true), spread: P(.03, 0, .1, '光点偏离路径的范围（占短边）'), speed: P(2, 1, 4, '每轮跑几趟', true), tail: P(1, .4, 2, '拖尾长度'), size: P(1, .6, 1.6, '大小'), colors: P(['#9be7ff', '#ffd27a'], null, null, '颜色'), intensity: P(1, .6, 1, '亮度') },
  }, (o, e) => {
    const R = e.R, M = Math.min(e.W, e.H), spr = o.colors.map(c => U.sprite(c, [[0, 1], [.15, .8], [.45, .15], [1, 0]], 64));
    const P_ = o.paths.map(p => { const c = catmull(p.map(([x, y]) => [x * e.W, y * e.H]), 24), L = [0]; for (let i = 1; i < c.length; i++) L.push(L[i - 1] + Math.hypot(c[i][0] - c[i - 1][0], c[i][1] - c[i - 1][1])); return { c, L, len: L[L.length - 1] }; });
    const at = (p, u, off) => { const s = u * p.len; let i = 1; while (i < p.L.length - 1 && p.L[i] < s) i++; const f = (s - p.L[i - 1]) / ((p.L[i] - p.L[i - 1]) || 1), a = p.c[i - 1], b = p.c[i], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1; return [a[0] + dx * f - dy / l * off, a[1] + dy * f + dx / l * off]; };
    const ps = Array.from({ length: o.count }, (_, i) => ({ p: P_[i % P_.length], off: (R() - .5) * 2 * o.spread * M, ph: R(), k: o.speed + (R() < .3 ? 1 : 0), s: spr[Math.floor(R() * spr.length)], r: (5 + 5 * R()) * e.u * o.size }));
    return {
      draw(g, t) {
        g.save(); g.globalCompositeOperation = 'lighter';
        for (const q of ps) {
          const u = fr(q.k * t / e.D + q.ph), tl = .07 * o.tail;
          for (let k = 8; k >= 0; k--) {
            const uu = u - tl * k / 8; if (uu < 0) continue; const [x, y] = at(q.p, uu, q.off), f = 1 - k / 9, r = q.r * (k ? .7 * f : 1.6);
            g.globalAlpha = o.intensity * (k ? .55 * f * f : 1) * sstep(0, .04, u) * sstep(1, .96, u); g.drawImage(q.s, x - r * 3, y - r * 3, r * 6, r * 6);
          }
        }
        g.restore();
      },
    };
  });

  FX.def('grade', {
    zh: '天光变化', group: '光', desc: '整幅或天空区域的色调慢慢变过去再变回来：暖↔冷、亮↔暗，像天色在走', suits: '城市、风景、天空、黄昏、蓝调时刻、夜景入夜',
    anchor: '天空或整个场景；area 只框天空时就只变天；lights 让变暗时灯更亮',
    params: { area: AREA, to: P('#1d3c78', null, null, '变到的颜色（冷蓝 = 入夜，暖橙 = 黄昏）'), amount: P(.4, .15, .65, '变化幅度'), blend: P('soft-light', null, null, "'soft-light' / 'color' / 'multiply' / 'screen'"), cycles: P(1, 1, 2, '每轮来回几次', true), lights: P(.5, 0, 1, '变暗时亮处（灯）跟着更亮'), feather: P(.3, .1, .5, '边缘柔和度') },
  }, (o, e) => {
    const A = U.rect(o.area, e), sc = .5, [off, og] = U.canvas(A.w * sc, A.h * sc), mask = U.softMask({ ...A, w: A.w * sc, h: A.h * sc }, Math.min(A.w, A.h) * sc * o.feather);
    let bright = null;
    if (o.lights > 0 && e.img) {
      const [c, g2] = U.canvas(A.w * sc, A.h * sc); g2.drawImage(e.img, A.x, A.y, A.w, A.h, 0, 0, c.width, c.height); const id = g2.getImageData(0, 0, c.width, c.height), d = id.data;
      for (let i = 0; i < d.length; i += 4) d[i + 3] = 255 * sstep(.65, .95, (d[i] * .299 + d[i + 1] * .587 + d[i + 2] * .114) / 255);
      g2.putImageData(id, 0, 0); bright = c;
    }
    return {
      draw(g, t) {
        const k = .5 - .5 * Math.cos(TAU * o.cycles * t / e.D); if (k < .002) return;
        og.globalCompositeOperation = 'source-over'; og.fillStyle = o.to; og.fillRect(0, 0, off.width, off.height);
        U.blit(g, off, A, mask, k * o.amount, o.blend);
        if (bright) { g.save(); g.globalCompositeOperation = 'screen'; g.globalAlpha = k * o.lights * .6; g.drawImage(bright, A.x, A.y, A.w, A.h); g.restore(); }
      },
    };
  });

  FX.def('twinkle', {
    zh: '灯火闪烁', group: '光', desc: '图里许多小灯（窗灯、路灯、星星）各自忽明忽暗', suits: '城市夜景、星空、灯串、圣诞、远景灯火',
    anchor: '自动找原图里的小亮点（颜色取自灯本身）',
    params: { count: P(60, 20, 150, '灯数', true), size: P(1, .6, 1.6, '大小'), speed: P(2, 1, 4, '每轮闪几次', true), depth: P(.75, .4, 1, '闪烁深浅'), minDist: P(.015, .008, .04, '灯和灯最少隔多远（占短边）'), area: AREA },
  }, (o, e) => {
    const A = U.rect(o.area, e), R = e.R, dark = U.sprite('#000000', [[0, .9], [.5, .5], [1, 0]], 32);
    const ls = U.highlights(e, o.count, A, o.minDist).map(([x, y, l]) => ({ x, y, s: U.sprite(U.hex(colorAt(e, x, y).map(v => v + (255 - v) * .35)), [[0, 1], [.2, .6], [.5, .15], [1, 0]], 64), r: (6 + 8 * R()) * e.u * o.size * (.5 + .5 * l), ph: R(), k: o.speed + Math.floor(R() * 2), blink: R() < .3 }));
    return {
      draw(g, t) {
        const s = t / e.D; g.save();
        for (const p of ls) {
          let v = .5 + .5 * Math.sin(TAU * (p.k * s + p.ph)); if (p.blink) v = v > .3 ? 1 : 0;
          if (v < .5) { g.globalCompositeOperation = 'multiply'; g.globalAlpha = (.5 - v) * 2 * o.depth * .8; g.drawImage(dark, p.x - p.r * .9, p.y - p.r * .9, p.r * 1.8, p.r * 1.8); }
          else { g.globalCompositeOperation = 'lighter'; g.globalAlpha = (v - .5) * 2 * o.depth; g.drawImage(p.s, p.x - p.r * 2.5, p.y - p.r * 2.5, p.r * 5, p.r * 5); }
        }
        g.restore();
      },
    };
  });

  // ======================= 局部动作 =======================
  FX.def('sway', {
    zh: '摇摆', group: '局部动作', desc: '区域里的东西像草、花、树枝、吊灯一样左右摆，根部不动、越往梢摆得越大', suits: '草、花、树、芦苇、麦穗、吊灯、挂饰',
    anchor: 'area 框住要摆的东西（上沿略高过梢）；root 选 bottom（长在地上）或 top（挂着）',
    params: { area: P([0, .6, 1, 1], null, null, '摆动区域'), root: P('bottom', null, null, "'bottom' 根在下 / 'top' 挂在上"), amp: P(1, .4, 2, '摆幅'), speed: P(1, 1, 3, '每轮摆几次', true), wave: P(.6, 0, 1.5, '左右错开的程度（0 = 整片一起摆）'), grid: P(20, 12, 32, '网格细度', true) },
  }, (o, e) => {
    const A = U.rect(o.area, e), ph = e.R() * TAU;
    return {
      draw(g, t) {
        const s = t / e.D;
        U.meshWarp(g, e.img, A, o.grid, o.grid, (x, y) => {
          const v = (y - A.y) / A.h, h = o.root === 'top' ? v : 1 - v, xr = (x - A.x) / A.w, w = h ** 1.5 * sstep(1, .82, h) * edgeW(A, x, y, .12);
          return [o.amp * e.u * 30 * w * (Math.sin(TAU * o.speed * s - o.wave * xr * Math.PI * 2 + ph) + .25 * Math.sin(TAU * 2 * o.speed * s - o.wave * xr * 9 + ph * 2)), 0];
        });
      },
    };
  });

  FX.def('wave', {
    zh: '飘动', group: '局部动作', desc: '旗子、飘带、衣角、长发像被风吹着起伏，波从固定端往外传', suits: '旗、飘带、丝巾、裙摆、长发、风筝尾巴、窗帘',
    anchor: 'area 框住飘的东西（留一点余量）；fixed 是固定的那一端',
    params: { area: AREA, fixed: P('left', null, null, "固定端：'left' / 'right' / 'top' / 'bottom'"), amp: P(1, .4, 2, '起伏幅度'), wavelength: P(1, .5, 2, '波长'), speed: P(2, 1, 4, '每轮传几个波', true), grid: P(20, 12, 32, '网格细度', true) },
  }, (o, e) => {
    const A = U.rect(o.area, e), horiz = o.fixed === 'left' || o.fixed === 'right', len = horiz ? A.w : A.h, lam = len * .45 * o.wavelength;
    return {
      draw(g, t) {
        const s = t / e.D;
        U.meshWarp(g, e.img, A, o.grid, o.grid, (x, y) => {
          const u = (x - A.x) / A.w, v = (y - A.y) / A.h, d = { left: u, right: 1 - u, top: v, bottom: 1 - v }[o.fixed], w = d ** 1.2 * edgeW(A, x, y, .12);
          const off = o.amp * e.u * 22 * w * Math.sin(TAU * (d * len / lam - o.speed * s));
          return horiz ? [0, off] : [off, 0];
        });
      },
    };
  });

  FX.def('breathe', {
    zh: '呼吸', group: '局部动作', desc: '一块区域轻轻胀缩，像睡着的猫在呼吸、气球被风鼓动', suits: '睡着的动物和人、气球、面包、心形、发光物',
    anchor: 'area 框住要呼吸的身体或物件；center 是胀缩中心（默认区域中心偏下）',
    params: { area: AREA, amount: P(.025, .01, .05, '胀缩幅度'), speed: P(2, 1, 4, '每轮呼吸几次', true), center: P(null, null, null, '胀缩中心 [x,y]，不给就用区域中心'), axis: P('both', null, null, "'both' / 'y'（只上下鼓）"), grid: P(16, 10, 24, '网格细度', true) },
  }, (o, e) => {
    const A = U.rect(o.area, e), cx = o.center ? o.center[0] * e.W : A.x + A.w / 2, cy = o.center ? o.center[1] * e.H : A.y + A.h * .55;
    return {
      draw(g, t) {
        const k = o.amount * (.5 - .5 * Math.cos(TAU * o.speed * t / e.D));
        U.meshWarp(g, e.img, A, o.grid, o.grid, (x, y) => {
          const u = (x - A.x) / A.w * 2 - 1, v = (y - A.y) / A.h * 2 - 1, w = sstep(1, .35, Math.hypot(u, v));
          return [o.axis === 'y' ? 0 : (x - cx) * k * w, (y - cy) * k * w];
        });
      },
    };
  });

  FX.def('blink', {
    zh: '眨眼', group: '局部动作', desc: '角色眨一下眼：眼皮从上往下合上再睁开', suits: '插画角色、动物、玩偶、头像、吉祥物',
    anchor: '眼睛的位置和大小：eyes = [[x, y, r], …]，r 是眼睛半径（占画面宽）',
    params: { eyes: P([[.45, .4, .02], [.55, .4, .02]], null, null, '眼睛 [[x,y,r], …]'), times: P(1, 1, 3, '每轮眨几次', true), at: P(.55, 0, .95, '第一次眨眼的时刻（占一轮）'), dur: P(.18, .1, .3, '一次眨眼多久（秒）'), double: P(false, null, null, '连眨两下'), lid: P('auto', null, null, "'auto' 取眼睛上方的颜色，或给颜色"), line: P('#2b1d14', null, null, '眼睑线颜色') },
  }, (o, e) => {
    const eyes = o.eyes.map(([x, y, r]) => {
      const X = x * e.W, Y = y * e.H, rr = r * e.W, c = o.lid === 'auto' ? [-.4, 0, .4].map(dx => colorAt(e, X + dx * rr, Y - rr * 1.7)).reduce((a, b) => a.map((v, i) => v + b[i] / 3), [0, 0, 0]) : U.rgb(o.lid);
      return { X, Y, rr, c: U.hex(c), d: U.hex(c.map(v => v * .8)) };
    });
    const starts = []; for (let j = 0; j < o.times; j++) { const t0 = (o.at + j / o.times) % 1 * e.D; starts.push(t0); if (o.double) starts.push(t0 + o.dur * 1.25); }
    return {
      draw(g, t) {
        let c = 0; for (const t0 of starts) { const q = (t - t0) / o.dur; if (q > 0 && q < 1) c = Math.max(c, Math.sin(Math.PI * q) ** .7); }
        if (c < .02) return;
        for (const E of eyes) {
          const ry = E.rr * 1.15, top = E.Y - ry, bot = E.Y + ry, meet = E.Y + ry * .18, up = top + (meet - top) * c, lo = bot - (bot - meet) * c, w = E.rr * 1.35, bend = E.rr * .35;
          g.save(); g.beginPath(); g.ellipse(E.X, E.Y, E.rr * 1.2, ry, 0, 0, TAU); g.clip();
          const gr = g.createLinearGradient(0, top, 0, up); gr.addColorStop(0, E.c); gr.addColorStop(1, E.d); g.fillStyle = gr;  // 上眼皮：往眼缝方向略暗
          g.beginPath(); g.moveTo(E.X - w, top - E.rr); g.lineTo(E.X + w, top - E.rr); g.lineTo(E.X + w, up - bend * c); g.quadraticCurveTo(E.X, up + bend * c, E.X - w, up - bend * c); g.closePath(); g.fill();
          g.fillStyle = E.c; g.beginPath(); g.moveTo(E.X - w, bot + E.rr); g.lineTo(E.X + w, bot + E.rr); g.lineTo(E.X + w, lo - bend * c); g.quadraticCurveTo(E.X, lo + bend * c, E.X - w, lo - bend * c); g.closePath(); g.fill();  // 下眼皮
          g.restore();
          g.save(); g.globalAlpha = sstep(.05, .4, c); g.strokeStyle = o.line; g.lineWidth = E.rr * .17; g.lineCap = 'round';  // 眼缝线（合上时画在眼睛中间偏下）
          g.beginPath(); g.moveTo(E.X - E.rr * 1.12, up - bend * c * .8); g.quadraticCurveTo(E.X, up + bend * c * 1.1, E.X + E.rr * 1.12, up - bend * c * .8); g.stroke(); g.restore();
        }
      },
    };
  });

  FX.def('spin', {
    zh: '旋转', group: '局部动作', desc: '圆形的东西原地转：太阳、轮子、齿轮、唱片、风车、钟面', suits: '太阳、轮子、齿轮、唱片、风车、圆形 Logo、表盘',
    anchor: 'items 给圆心和半径（r 占画面宽）；齿轮用 symmetry = 齿数，每轮转整数格就能无缝循环；背景不均匀时给 mask / plate',
    params: { items: P([{ c: [.5, .5], r: .1 }], null, null, "[{c:[x,y], r, dir:1, turns, symmetry}, …]"), turns: P(1, 1, 3, '每轮转几圈（有 symmetry 时是转几格）', true), symmetry: P(1, null, null, '旋转对称数（齿轮 = 齿数，风车 = 叶片数）'), mask: P(null, null, null, "null 整个圆一起转 / 'auto' 只转和背景颜色不同的部分（背景要比较均匀，比如纸、墙、天空）/ 蒙版图路径"), plate: P(null, null, null, '可选：补好洞的底图路径（mask: auto 时自动用背景色补）'), feather: P(.05, 0, .15, '圆边柔和度') },
  }, (o, e) => {
    const its = o.items.map(it => ({ x: it.c[0] * e.W, y: it.c[1] * e.H, r: it.r * e.W, dir: it.dir ?? 1, turns: it.turns ?? o.turns, sym: it.symmetry ?? o.symmetry }));
    let mask = null, plate = null;
    const ready = Promise.all([o.mask && o.mask !== 'auto' ? loadImg(o.mask).then(i => mask = i) : 0, o.plate ? loadImg(o.plate).then(i => plate = i) : 0]);
    if (o.mask === 'auto') for (const it of its) {  // 背景色 = 圆周外一圈的平均色；转的只是和背景差得多的像素
      const ring = Array.from({ length: 48 }, (_, k) => colorAt(e, it.x + Math.cos(k / 48 * TAU) * it.r * 1.04, it.y + Math.sin(k / 48 * TAU) * it.r * 1.04)), bg = [0, 1, 2].map(ch => ring.map(c => c[ch]).sort((a, b) => a - b)[24]);
      const S = Math.ceil(it.r * 2), [c, cg] = U.canvas(S, S); cg.drawImage(e.img, it.x - it.r, it.y - it.r, S, S, 0, 0, S, S);
      const id = cg.getImageData(0, 0, S, S), d = id.data;
      for (let k = 0; k < d.length; k += 4) { const dist = Math.hypot(d[k] - bg[0], d[k + 1] - bg[1], d[k + 2] - bg[2]) / 255; d[k] = d[k + 1] = d[k + 2] = 255; d[k + 3] = 255 * sstep(.1, .22, dist); }
      cg.putImageData(id, 0, 0); const [m2, mg2] = U.canvas(S, S); mg2.filter = 'blur(1px)'; mg2.drawImage(c, 0, 0); it.km = m2; it.bg = U.hex(bg);
    }
    return {
      ready,
      draw(g, t) {
        const s = t / e.D;
        for (const it of its) {
          const S = Math.ceil(it.r * 2), [c, cg] = U.canvas(S, S), a = it.dir * TAU * it.turns / it.sym * s;
          cg.save(); cg.translate(S / 2, S / 2); cg.rotate(a); cg.drawImage(e.img, it.x - it.r, it.y - it.r, S, S, -S / 2, -S / 2, S, S); cg.restore();
          cg.globalCompositeOperation = 'destination-in';
          if (it.km) { cg.save(); cg.translate(S / 2, S / 2); cg.rotate(a); cg.drawImage(it.km, -S / 2, -S / 2); cg.restore(); cg.globalCompositeOperation = 'destination-in'; }
          if (mask) { cg.save(); cg.translate(S / 2, S / 2); cg.rotate(a); cg.drawImage(mask, (it.x - it.r) * mask.width / e.W, (it.y - it.r) * mask.height / e.H, S * mask.width / e.W, S * mask.height / e.H, -S / 2, -S / 2, S, S); cg.restore(); }
          else { const gr = cg.createRadialGradient(S / 2, S / 2, it.r * (1 - o.feather), S / 2, S / 2, it.r); gr.addColorStop(0, '#fff'); gr.addColorStop(1, 'rgba(255,255,255,0)'); cg.fillStyle = gr; cg.fillRect(0, 0, S, S); }
          if (plate) { g.save(); g.beginPath(); g.arc(it.x, it.y, it.r, 0, TAU); g.clip(); g.drawImage(plate, it.x - it.r, it.y - it.r, S, S, it.x - it.r, it.y - it.r, S, S); g.restore(); }
          else if (it.km) { const gr = g.createRadialGradient(it.x, it.y, it.r * (1 - o.feather), it.x, it.y, it.r); gr.addColorStop(0, it.bg); gr.addColorStop(1, it.bg + '00'); g.fillStyle = gr; g.beginPath(); g.arc(it.x, it.y, it.r, 0, TAU); g.fill(); }  // 用背景色盖住原来的图案
          g.drawImage(c, it.x - it.r, it.y - it.r);
        }
      },
    };
  });

  // ======================= 镜头 =======================
  // 镜头积木不画东西，而是给 #cam 设变换：cam.apply(el, t)；at(t) 返回 {z, cx, cy, rot}（或 shake 的 {dx, dy, drot}），可以和 L.Camera 叠用。
  const camApply = (el, { z, cx, cy, rot = 0 }, ex = {}) => {
    const S = CFG.outW / CFG.srcW * z;
    el.style.transform = `translate(${CFG.outW / 2}px,${CFG.outH / 2}px) rotate(${rot + (ex.drot || 0)}deg) scale(${S}) translate(${-(cx + (ex.dx || 0))}px,${-(cy + (ex.dy || 0))}px)`;
  };
  FX.def('parallax', {
    zh: '景深视差', group: '镜头', desc: '按景深把画面切成很多层，镜头轻轻绕圈或平移时近处动得多、远处动得少，出现立体感', suits: '风景、人像、街景、室内、任何前后层次分明的照片',
    anchor: '需要景深图：scripts/depth.py 生成（近 = 白）；这个积木自己画整张图，放在最底层',
    params: { depth: P('assets/depth.png', null, null, '景深图路径'), layers: P(14, 8, 20, '分层数', true), amp: P(.8, .4, 1.6, '位移幅度'), path: P('orbit', null, null, "'orbit' 绕小圈 / 'sway' 左右 / 'push' 前后推"), cycles: P(1, 1, 2, '每轮绕几圈', true), focus: P(.4, 0, 1, '不动的那一层（0 远 1 近）'), zoom: P(1.05, 1, 1.12, '放大一点，避免露边') },
  }, (o, e) => {
    let Ls = [];
    const ready = loadImg(o.depth).then(dimg => {
      if (!dimg) return;
      const sc = Math.min(1, 900 / Math.max(e.W, e.H)), w = Math.round(e.W * sc), h = Math.round(e.H * sc), [dc, dg] = U.canvas(w, h);
      dg.drawImage(dimg, 0, 0, w, h); const D = dg.getImageData(0, 0, w, h).data;
      for (let i = 0; i < o.layers; i++) {
        const lo = i / o.layers, hi = (i + 1) / o.layers, [mc, mg] = U.canvas(w, h), id = mg.createImageData(w, h);
        for (let k = 0; k < w * h; k++) { const d = D[k * 4] / 255; id.data[k * 4 + 3] = 255 * (i === 0 ? 1 : sstep(lo - .015, lo + .008, d)) * (i === o.layers - 1 ? 1 : sstep(hi + .015, hi - .008, d)); }  // 相邻层边缘各多盖一点，不留缝
        mg.putImageData(id, 0, 0);
        const [lc, lg] = U.canvas(e.W, e.H); lg.drawImage(e.img, 0, 0); lg.globalCompositeOperation = 'destination-in'; lg.filter = 'blur(1.5px)'; lg.drawImage(mc, 0, 0, e.W, e.H);
        Ls.push({ c: lc, d: (lo + hi) / 2 });
      }
    });
    return {
      ready,
      draw(g, t) {
        const s = t / e.D, a = TAU * o.cycles * s, M = Math.min(e.W, e.H) * .02 * o.amp;
        const [vx, vy, vz] = o.path === 'sway' ? [Math.sin(a), 0, 0] : o.path === 'push' ? [0, 0, .5 - .5 * Math.cos(a)] : [Math.cos(a) - 1, Math.sin(a) * .6, 0];
        const draw1 = (img, d) => { const k = d - o.focus, z = o.zoom * (1 + vz * k * .06 * o.amp); g.drawImage(img, e.W / 2 - e.W * z / 2 + vx * k * M * 2, e.H / 2 - e.H * z / 2 + vy * k * M * 2, e.W * z, e.H * z); };
        draw1(e.img, 0); for (const L of Ls) draw1(L.c, L.d);
      },
    };
  });

  FX.def('drift', {
    zh: '推拉摇', group: '镜头', desc: '镜头慢慢推近再拉回、绕小圈漂移、或左右轻摇，首尾回到原位', suits: '几乎所有静态画面：风景、海报、产品、名画',
    anchor: 'focus 给想推向的点（比如主体的脸）；用 cam.apply(document.querySelector("#cam"), t) 代替 L.Camera',
    params: { mode: P('push', null, null, "'push' 推近拉回 / 'orbit' 绕圈漂移 / 'pan' 左右摇"), focus: P([.5, .5], null, null, '推向的点'), amount: P(1, .4, 2, '幅度'), cycles: P(1, 1, 2, '每轮来回几次', true), rotate: P(0, -2, 2, '顺带转的角度（度）') },
  }, (o, e) => {
    const at = t => {
      const a = TAU * o.cycles * t / e.D, k = .5 - .5 * Math.cos(a); let z = 1, cx = e.W / 2, cy = e.H / 2;
      if (o.mode === 'push') { z = 1 + .1 * o.amount * k; cx += (o.focus[0] * e.W - cx) * k * .8; cy += (o.focus[1] * e.H - cy) * k * .8; }
      else if (o.mode === 'orbit') { cx += Math.sin(a) * .025 * e.W * o.amount; cy += (Math.cos(a) - 1) * .02 * e.H * o.amount; }
      else { cx += Math.sin(a) * .035 * e.W * o.amount; }
      z = Math.max(z, 1 + 2 * Math.max(Math.abs(cx - e.W / 2) / e.W, Math.abs(cy - e.H / 2) / e.H) + .004);
      return { z, cx, cy, rot: o.rotate * k };
    };
    return { at, apply: (el, t, ex) => camApply(el, at(t), ex), draw() {} };
  });

  FX.def('shake', {
    zh: '手持晃动', group: '镜头', desc: '像手拿着拍一样的轻微晃动；hits 给时刻还能震一下', suits: '自拍、街拍、纪实、运动、音乐节、冲击',
    anchor: '通常叠在别的镜头上：L.Camera.apply(el, t, shake.at(t))；单独用就 shake.apply(el, t)',
    params: { amount: P(1, .3, 2, '幅度'), speed: P(3, 1, 6, '晃动快慢', true), rotate: P(.4, 0, 1.2, '旋转幅度（度）'), hits: P([], null, null, '撞击时刻（秒）列表') },
  }, (o, e) => {
    const R = e.R, ph = Array.from({ length: 6 }, () => R() * TAU), k = o.speed;
    const at = t => {
      const s = t / e.D, A = o.amount * e.u * 7;
      let dx = A * (.6 * Math.sin(TAU * k * s + ph[0]) + .3 * Math.sin(TAU * (2 * k + 1) * s + ph[1]) + .15 * Math.sin(TAU * (4 * k + 3) * s + ph[2]));
      let dy = A * (.6 * Math.sin(TAU * (k + 1) * s + ph[3]) + .3 * Math.sin(TAU * (2 * k + 3) * s + ph[4]) + .15 * Math.sin(TAU * (5 * k + 1) * s + ph[5]));
      let drot = o.rotate * (.7 * Math.sin(TAU * k * s + ph[4]) + .3 * Math.sin(TAU * (3 * k + 2) * s + ph[2]));
      for (const h of o.hits) { const a = t - h; if (a >= 0 && a < .5) { const d = Math.exp(-a * 9) * Math.sin(a * 60); dx += d * A * 4; dy += d * A * 3; drot += d * o.rotate * 3; } }
      return { dx, dy, drot };
    };
    const z = 1 + 2 * o.amount * e.u * 9 / Math.min(e.W, e.H) + .01;
    return { at, apply: (el, t) => camApply(el, { z, cx: e.W / 2, cy: e.H / 2, rot: 0 }, at(t)), draw() {} };
  });
  // ======================= 生长揭示 =======================
  // 揭示类有两种模式：'in' 从 t0 开始出现一次、之后保持（片子靠复位转场接回去）；
  // 'pulse' 完整图 → 倒着退掉 → 再长出来 → 完整图，首尾一样，不用复位转场。t0 / dur 都是占一轮的比例。
  FX.groups.push('生长揭示', '质感');
  const MODE = P('pulse', null, null, "'pulse' 完整 → 退掉 → 长回来（首尾一样）/ 'in' 只出现一次");
  const stages = (o, s, n) => {
    const out = new Array(n).fill(1);
    if (o.mode === 'pulse') {
      const a = o.t0, b = 1 - .03, seg = (b - a) / (2 * n);
      for (let k = 0; k < n; k++) { const d0 = a + (n - 1 - k) * seg, u0 = a + (n + k) * seg; out[k] = s < d0 ? 1 : s < d0 + seg ? 1 - (s - d0) / seg : s < u0 ? 0 : s < u0 + seg ? (s - u0) / seg : 1; }
    } else { const seg = o.dur / n; for (let k = 0; k < n; k++) out[k] = cl((s - o.t0 - k * seg * .85) / seg); }
    return out.map(v => v * v * (3 - 2 * v));
  };
  // 工作分辨率的像素层：src 是区域内原图的像素，每帧往 out 里写、再贴回去
  const pixLayer = (e, A, side = 720) => {
    const k = Math.min(1, side / Math.max(A.w, A.h)), w = Math.max(2, Math.round(A.w * k)), h = Math.max(2, Math.round(A.h * k)), [c, g] = U.canvas(w, h);
    g.drawImage(e.img, A.x, A.y, A.w, A.h, 0, 0, w, h); const src = g.getImageData(0, 0, w, h).data.slice(), id = g.createImageData(w, h);
    const L = new Float32Array(w * h); for (let i = 0; i < w * h; i++) L[i] = (src[i * 4] * .299 + src[i * 4 + 1] * .587 + src[i * 4 + 2] * .114) / 255;
    return { w, h, c, g, src, id, L, put(gg) { g.putImageData(id, 0, 0); gg.save(); gg.imageSmoothingQuality = 'high'; gg.drawImage(c, A.x, A.y, A.w, A.h); gg.restore(); } };
  };
  const vnoise = (w, h, seed, cells, oct = 3) => U.tileNoise(w, h, seed, cells, oct);
  const boxBlur = (a, w, h, r) => {  // 简单的两遍盒式模糊（Float32Array）
    const t = new Float32Array(a.length), o = new Float32Array(a.length);
    for (let j = 0; j < h; j++) { let s = 0; for (let i = -r; i <= r; i++) s += a[j * w + Math.min(w - 1, Math.max(0, i))]; for (let i = 0; i < w; i++) { t[j * w + i] = s / (2 * r + 1); s += a[j * w + Math.min(w - 1, i + r + 1)] - a[j * w + Math.max(0, i - r)]; } }
    for (let i = 0; i < w; i++) { let s = 0; for (let j = -r; j <= r; j++) s += t[Math.min(h - 1, Math.max(0, j)) * w + i]; for (let j = 0; j < h; j++) { o[j * w + i] = s / (2 * r + 1); s += t[Math.min(h - 1, j + r + 1) * w + i] - t[Math.max(0, j - r) * w + i]; } }
    return o;
  };
  const orderField = (P_, o, seed) => {  // 揭示顺序：按方向扫 / 从中心往外 / 东一块西一块，叠一点噪声
    const { w, h } = P_, n = vnoise(w, h, seed, 4, 4), T = new Float32Array(w * h), a = (o.dir ?? 20) * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a);
    let mn = 1e9, mx = -1e9;
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
      const x = i / h, y = j / h, k = j * w + i;
      const base = o.order === 'radial' ? Math.hypot(i / w - .5, (j / h - .5) * h / w) : o.order === 'random' ? 0 : x * ca + y * sa;
      T[k] = base * (o.order === 'random' ? 0 : 1) + n[k] * (o.order === 'random' ? 1 : .35); mn = Math.min(mn, T[k]); mx = Math.max(mx, T[k]);
    }
    for (let k = 0; k < T.length; k++) T[k] = (T[k] - mn) / (mx - mn || 1);
    return T;
  };

  FX.def('draw', {
    zh: '线稿描出', group: '生长揭示', desc: '先像钢笔一样把画里的线条一笔笔描出来，再一片片上色，变回原图', suits: '插画、速写、建筑、绘本、儿童画、版画、Logo',
    anchor: '自动从原图提取线条（比周围暗的细节）；area 可以只描一块',
    params: { area: AREA, mode: MODE, t0: P(.08, 0, .3, '开始时刻（占一轮）'), dur: P(.6, .3, .8, "'in' 模式下描线 + 上色总共占一轮的比例"), order: P('sweep', null, null, "'sweep' 按方向扫 / 'radial' 从中心往外 / 'random' 东一笔西一笔"), dir: P(20, -180, 180, 'sweep 的方向（度）'), lines: P(1, .5, 2, '线条多少（提取阈值）'), paper: P('#f6f1e7', null, null, '纸的颜色'), ink: P('#2a2622', null, null, '线的颜色') },
  }, (o, e) => {
    const A = U.rect(o.area, e), X = pixLayer(e, A), { w, h, L } = X, bl = boxBlur(L, w, h, Math.max(2, Math.round(w / 160))), ln = new Float32Array(w * h);
    for (let k = 0; k < w * h; k++) ln[k] = sstep(.02 / o.lines, .1 / o.lines, bl[k] - L[k]) + sstep(.35, .12, L[k]) * .6;  // 比周围暗的细节 + 本来就很暗的地方
    const T1 = orderField(X, o, o.seed * 5 + 1), T2 = orderField(X, { ...o, order: 'random' }, o.seed * 5 + 2), pp = U.rgb(o.paper), ik = U.rgb(o.ink), d = X.id.data, src = X.src;
    return {
      draw(g, t) {
        const [ql, qc] = stages(o, t / e.D, 2);
        for (let k = 0; k < w * h; k++) {
          const a = cl(ln[k]) * sstep(T1[k] - .02, T1[k] + .02, ql * 1.04 - .02), c = sstep(T2[k] - .05, T2[k] + .05, qc * 1.1 - .05), i = k * 4;
          for (let ch = 0; ch < 3; ch++) { const v = pp[ch] + (ik[ch] - pp[ch]) * a; d[i + ch] = v + (src[i + ch] - v) * c; }
          d[i + 3] = 255;
        }
        X.put(g);
      },
    };
  });

  FX.def('paint', {
    zh: '笔刷上色', group: '生长揭示', desc: '画面被一道道大笔刷刷出来，笔触边缘带飞白', suits: '油画、水彩、名画、海报、插画、手作',
    anchor: '整幅或 area；可以接在"线稿描出"后面',
    params: { area: AREA, mode: MODE, t0: P(.08, 0, .3, '开始时刻（占一轮）'), dur: P(.6, .3, .8, "'in' 模式下刷完占一轮的比例"), strokes: P(7, 4, 12, '笔刷道数', true), angle: P(-20, -60, 60, '笔刷方向（度）'), paper: P('#f3eee4', null, null, '底色') },
  }, (o, e) => {
    const A = U.rect(o.area, e), X = pixLayer(e, A), { w, h } = X, R = rngf(o.seed * 31 + 7), th = o.angle * Math.PI / 180, dx = Math.cos(th), dy = Math.sin(th), nx = -dy, ny = dx;
    const cs = [[0, 0], [w / h, 0], [0, 1], [w / h, 1]], al = cs.map(([x, y]) => x * dx + y * dy), ac = cs.map(([x, y]) => x * nx + y * ny), a0 = Math.min(...al), a1 = Math.max(...al), c0 = Math.min(...ac), c1 = Math.max(...ac);
    const n = o.strokes, r = (c1 - c0) / n * .8, T = new Float32Array(w * h).fill(2), g1 = Float32Array.from({ length: 4096 }, R);
    const n1 = u => { let v = 0, amp = 1, tot = 0; for (let k = 0; k < 3; k++) { const x = ((u * 2 ** k) % 4000 + 4000) % 4000, i = Math.floor(x), f = x - i, s = f * f * (3 - 2 * f); v += amp * (g1[i] * (1 - s) + g1[i + 1] * s); tot += amp; amp *= .5; } return v / tot; };
    for (let si = 0; si < n; si++) {
      const ci = c0 + (si + .5) * (c1 - c0) / n + (R() - .5) * r * .2, fw = R() * 100;
      for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
        const x = i / h, y = j / h, q = x * nx + y * ny - ci, br = n1(q / r * 9 + fw), edge = r * (.82 + .3 * (br - .5)); if (Math.abs(q) >= edge) continue;
        let pr = (x * dx + y * dy - a0) / (a1 - a0); if (si % 2) pr = 1 - pr;
        const dry = cl((Math.abs(q) / edge - .55) * 2.2) * cl((br - .45) * 3), Ti = (si + Math.min(1.4, Math.max(0, pr + (br - .5) * .16 + dry * .5))) / n, k = j * w + i;
        if (Ti < T[k]) T[k] = Ti;
      }
    }
    for (let k = 0; k < T.length; k++) if (T[k] > 1.5) T[k] = 1;
    const pp = U.rgb(o.paper), d = X.id.data, src = X.src;
    return {
      draw(g, t) {
        const [q] = stages(o, t / e.D, 1), lv = q * 1.02 - .01;
        for (let k = 0; k < w * h; k++) { const m = sstep(T[k] - .004, T[k] + .004, lv), i = k * 4; for (let ch = 0; ch < 3; ch++) d[i + ch] = pp[ch] + (src[i + ch] - pp[ch]) * m; d[i + 3] = 255; }
        X.put(g);
      },
    };
  });

  FX.def('inkbloom', {
    zh: '墨迹晕开', group: '生长揭示', desc: '画面从几处墨点开始晕开显现，边缘积着一圈深色水痕', suits: '水墨、水彩、书法、国风海报',
    anchor: '默认从原图最暗的几处（墨最重的地方）开始晕；也可以给 seeds',
    params: { area: AREA, mode: MODE, t0: P(.06, 0, .3, '开始时刻（占一轮）'), dur: P(.6, .3, .8, "'in' 模式下晕满占一轮的比例"), seeds: P('auto', null, null, "'auto' 从最暗处起，或 [[x,y], …]"), count: P(3, 1, 6, '起点数', true), edge: P(.5, 0, 1, '水痕深浅'), paper: P('#f4efe3', null, null, '纸色') },
  }, (o, e) => {
    const A = U.rect(o.area, e), X = pixLayer(e, A), { w, h, L } = X, R = rngf(o.seed * 17 + 3);
    let sd = o.seeds === 'auto' ? null : o.seeds.map(([x, y]) => [(x * e.W - A.x) / A.w * w, (y * e.H - A.y) / A.h * h]);
    if (!sd) { const bl = boxBlur(L, w, h, Math.round(w / 40)), c = []; for (let k = 0; k < w * h; k += 7) c.push([k % w, Math.floor(k / w), bl[k]]); c.sort((a, b) => a[2] - b[2]); sd = []; for (const p of c) { if (sd.every(q => Math.hypot(q[0] - p[0], q[1] - p[1]) > w * .25)) sd.push(p); if (sd.length >= o.count) break; } }
    const nx_ = vnoise(w, h, o.seed * 3 + 1, 3, 3), ny_ = vnoise(w, h, o.seed * 3 + 2, 3, 3), fine = vnoise(w, h, o.seed * 3 + 5, 24, 2), T = new Float32Array(w * h), dl = sd.map((_, i) => i ? R() * .15 : 0);
    let mn = 1e9, mx = -1e9;
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) { const k = j * w + i, x = i + (nx_[k] - .5) * w * .3, y = j + (ny_[k] - .5) * w * .3; let m = 1e9; sd.forEach(([sx, sy], q) => { m = Math.min(m, Math.hypot(x - sx, y - sy) / w + dl[q]); }); T[k] = m + (fine[k] - .5) * .03; mn = Math.min(mn, T[k]); mx = Math.max(mx, T[k]); }
    for (let k = 0; k < T.length; k++) T[k] = (T[k] - mn) / (mx - mn);
    const pp = U.rgb(o.paper), d = X.id.data, src = X.src;
    return {
      draw(g, t) {
        const [q] = stages(o, t / e.D, 1), lv = q * 1.08 - .04;
        for (let k = 0; k < w * h; k++) {
          const m = sstep(T[k] - .012, T[k] + .012, lv), rim = Math.exp(-((((lv - T[k]) - .012) / .012) ** 2)) * o.edge * (q < .999 ? 1 : 0), i = k * 4;
          for (let ch = 0; ch < 3; ch++) { const v = pp[ch] + (src[i + ch] - pp[ch]) * m; d[i + ch] = v * (1 - rim * .55 * (1 - src[i + ch] / 255 * .6)); }
          d[i + 3] = 255;
        }
        X.put(g);
      },
    };
  });

  FX.def('grow', {
    zh: '藤蔓生长', group: '生长揭示', desc: '藤蔓从起点一路长出来、分叉、冒出叶子（和小花）', suits: '边框装饰、春天、花店、婚礼、童话、儿童画',
    anchor: 'from 给起点和生长方向（比如从画面下角往上爬）；颜色可以取图里的绿',
    params: { from: P([[0, 1, -60]], null, null, '起点 [[x, y, 方向角（度）], …]'), length: P(.55, .3, .9, '主藤长度（占画面高）'), branches: P(4, 1, 8, '分叉数', true), curl: P(1, .4, 2, '弯曲程度'), width: P(1, .6, 1.8, '粗细'), mode: MODE, t0: P(.05, 0, .3, '开始时刻（占一轮）'), dur: P(.65, .3, .8, "'in' 模式下长完占一轮的比例"), stem: P('#4f7a3a', null, null, '藤的颜色'), leaf: P('#7fb35a', null, null, '叶子颜色'), flower: P(null, null, null, '花的颜色（null = 不开花）') },
  }, (o, e) => {
    const R = rngf(o.seed * 13 + 5), U0 = e.H, vines = [];
    const make = (x, y, ang, len, w0, t0, depth) => {
      const pts = [[x, y]], step = U0 * .008, n = Math.max(4, Math.round(len / step)), ph = R() * TAU; let a = ang;
      for (let i = 1; i <= n; i++) { a += Math.sin(i * .12 + ph) * .05 * o.curl + (R() - .5) * .06; x += Math.cos(a) * step; y += Math.sin(a) * step; pts.push([x, y]); }
      const v = { pts, w0, t0, span: .55 * len / (o.length * U0), leaves: [], flower: depth > 0 && o.flower && R() < .7 }; vines.push(v);
      for (let i = 4; i < n; i += Math.round(4 + R() * 4)) v.leaves.push({ i, side: (i % 2 ? 1 : -1), s: (8 + 8 * R()) * e.u * o.width * 1.6, rot: R() * .6 });
      return v;
    };
    for (const [fx, fy, fa] of o.from) {
      const main = make(fx * e.W, fy * e.H, fa * Math.PI / 180, o.length * U0, 5 * e.u * o.width, 0, 0);
      for (let b = 0; b < o.branches; b++) {
        const at = .25 + .6 * R(), i = Math.floor(at * (main.pts.length - 1)), [px, py] = main.pts[i], [qx, qy] = main.pts[Math.min(main.pts.length - 1, i + 1)];
        make(px, py, Math.atan2(qy - py, qx - px) + (b % 2 ? 1 : -1) * (.5 + R() * .6), o.length * U0 * (.25 + .25 * R()), 3 * e.u * o.width, main.t0 + at * main.span, 1);
      }
    }
    const ease = x => { const s = 1.70158; x = cl(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2; };
    const leaf = (g, s) => { g.beginPath(); g.moveTo(0, 0); g.quadraticCurveTo(s * .55, -s * .45, s, 0); g.quadraticCurveTo(s * .55, s * .45, 0, 0); g.fill(); };
    return {
      draw(g, t) {
        const [q] = stages(o, t / e.D, 1); if (q <= 0) return;
        g.save(); g.lineCap = 'round'; g.lineJoin = 'round';
        for (const v of vines) {
          const p = cl((q - v.t0) / v.span), n = Math.floor(p * (v.pts.length - 1)); if (n < 1) continue;
          g.strokeStyle = o.stem;
          for (let i = 1; i <= n; i++) { g.lineWidth = Math.max(.6, v.w0 * (1 - i / v.pts.length * .75)); g.beginPath(); g.moveTo(...v.pts[i - 1]); g.lineTo(...v.pts[i]); g.stroke(); }
          g.fillStyle = o.leaf;
          for (const L of v.leaves) {
            if (L.i > n) continue; const k = ease((n - L.i) / 10), [x, y] = v.pts[L.i], [x2, y2] = v.pts[Math.min(v.pts.length - 1, L.i + 1)], a = Math.atan2(y2 - y, x2 - x) + L.side * (1 + L.rot);
            g.save(); g.translate(x, y); g.rotate(a); leaf(g, L.s * k); g.restore();
          }
          if (v.flower && p >= 1) { const [x, y] = v.pts[v.pts.length - 1], k = ease((q - v.t0 - v.span) / .05), r = 6 * e.u * o.width * 1.6 * k; g.fillStyle = o.flower; for (let pi = 0; pi < 5; pi++) { g.beginPath(); g.arc(x + Math.cos(pi * TAU / 5) * r, y + Math.sin(pi * TAU / 5) * r, r * .7, 0, TAU); g.fill(); } g.fillStyle = '#ffe28a'; g.beginPath(); g.arc(x, y, r * .55, 0, TAU); g.fill(); }
        }
        g.restore();
      },
    };
  });

  const ringColor = (e, A) => { const c = []; for (let k = 0; k < 40; k++) { const f = k / 40, side = k % 4; c.push(colorAt(e, side < 2 ? A.x + f * A.w : (side === 2 ? A.x - 2 : A.x + A.w + 2), side === 0 ? A.y - 2 : side === 1 ? A.y + A.h + 2 : A.y + f * A.h)); } return U.hex([0, 1, 2].map(ch => c.map(v => v[ch]).sort((a, b) => a - b)[20])); };
  FX.def('write', {
    zh: '逐行写出', group: '生长揭示', desc: '图里的文字一行行从左到右（或从上到下）"写"出来，前面带发光笔尖或光标', suits: '标题、书法、手写字、海报文字、字幕、聊天截图',
    anchor: 'lines 给每行文字的框（按书写顺序）；文字底下的背景要比较均匀（用框边的颜色先盖住）',
    params: { lines: P([[.1, .4, .9, .5]], null, null, '每行的框 [[x0,y0,x1,y1], …]'), dir: P('right', null, null, "'right' 横排 / 'down' 竖排"), mode: MODE, t0: P(.08, 0, .3, '开始时刻（占一轮）'), dur: P(.6, .3, .8, "'in' 模式下写完占一轮的比例"), tip: P('glow', null, null, "'glow' 发光笔尖 / 'caret' 光标 / 'none'"), color: P('#ffffff', null, null, '笔尖颜色'), plate: P('auto', null, null, "'auto' 用框边颜色盖住，或给颜色") },
  }, (o, e) => {
    const Ls = o.lines.map(a => { const A = U.rect(a, e); A.c = o.plate === 'auto' ? ringColor(e, A) : o.plate; return A; }), tot = Ls.reduce((s, A) => s + (o.dir === 'down' ? A.h : A.w), 0);
    const glow = U.sprite(o.color, [[0, 1], [.2, .6], [1, 0]], 64);
    return {
      draw(g, t) {
        const [q] = stages(o, t / e.D, 1); let done = q * tot;
        for (const A of Ls) {
          const len = o.dir === 'down' ? A.h : A.w, p = cl(done / len); done -= len;
          if (p >= 1) continue;
          const f = 6 * e.u, cut = p * len;
          g.save(); g.fillStyle = A.c;
          if (o.dir === 'down') { const gr = g.createLinearGradient(0, A.y + cut - f, 0, A.y + cut + f); gr.addColorStop(0, A.c + '00'); gr.addColorStop(1, A.c); g.fillStyle = gr; g.fillRect(A.x - 2, A.y + cut - f, A.w + 4, A.h - cut + f + 2); }
          else { const gr = g.createLinearGradient(A.x + cut - f, 0, A.x + cut + f, 0); gr.addColorStop(0, A.c + '00'); gr.addColorStop(1, A.c); g.fillStyle = gr; g.fillRect(A.x + cut - f, A.y - 2, A.w - cut + f + 2, A.h + 4); }
          g.restore();
          if (p > 0 && o.tip !== 'none') {
            const x = o.dir === 'down' ? A.x + A.w / 2 : A.x + cut, y = o.dir === 'down' ? A.y + cut : A.y + A.h / 2, r = Math.min(A.w, A.h) * .35;
            g.save(); if (o.tip === 'caret') { g.fillStyle = o.color; g.globalAlpha = (t * 2.2 % 1) < .55 ? 1 : 0; g.fillRect(x, A.y + A.h * .1, Math.max(2, 3 * e.u), A.h * .8); } else { g.globalCompositeOperation = 'lighter'; g.drawImage(glow, x - r, y - r, 2 * r, 2 * r); } g.restore();
          }
        }
      },
    };
  });

  FX.def('pop', {
    zh: '逐个弹出', group: '生长揭示', desc: '图里的元素（气泡、贴纸、图标、卡片）一个个弹出来，带一点回弹', suits: '聊天截图、UI、信息图、贴纸、列表、海报元素',
    anchor: 'items 给每个元素的框（按出现顺序）；背景要比较均匀（用框边颜色先盖住）',
    params: { items: P([], null, null, '元素框 [[x0,y0,x1,y1], …]'), t0: P(.05, 0, .3, '第一个出现的时刻（占一轮）'), every: P(.4, .15, .8, '间隔（秒）'), dur: P(.35, .2, .6, '弹出用时（秒）'), from: P('auto', null, null, "'auto' 左边的从左下角、右边的从右下角弹 / 'center' / 'bottom'"), overshoot: P(1.6, 1, 2.5, '回弹程度'), out: P(.9, null, null, '这个时刻（占一轮）开始倒着收回，让首尾一样；null = 不收'), plate: P('auto', null, null, "'auto' 用框边颜色盖住，或给颜色") },
  }, (o, e) => {
    const its = o.items.map((a, i) => { const A = U.rect(a, e); const cx = A.x + A.w / 2; return { A, c: o.plate === 'auto' ? ringColor(e, A) : o.plate, i, ox: o.from === 'center' ? cx : o.from === 'bottom' ? cx : cx < e.W / 2 ? A.x : A.x + A.w, oy: o.from === 'center' ? A.y + A.h / 2 : A.y + A.h }; });
    const n = its.length, back = x => { const s = o.overshoot; x = cl(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2; };
    return {
      draw(g, t) {
        for (const it of its) {
          let k = back((t - (o.t0 * e.D + it.i * o.every)) / o.dur);
          if (o.out != null) { const ts = o.out * e.D + (n - 1 - it.i) * Math.min(o.every, (e.D * (1 - o.out) - o.dur) / Math.max(1, n)) * .9; if (t > ts) k = Math.min(k, 1 - cl((t - ts) / (o.dur * .6)) ** 2); }
          if (k >= .999) continue;
          const { A } = it; g.save(); g.fillStyle = it.c; g.fillRect(A.x - 2, A.y - 2, A.w + 4, A.h + 4);
          if (k > .001) { g.globalAlpha = cl(k * 3); g.translate(it.ox, it.oy); g.scale(k, k); g.translate(-it.ox, -it.oy); g.drawImage(e.img, A.x, A.y, A.w, A.h, A.x, A.y, A.w, A.h); }
          g.restore();
        }
      },
    };
  });

  // ======================= 质感 =======================
  FX.def('grain', {
    zh: '胶片颗粒', group: '质感', desc: '每帧都在变的胶片颗粒，老照片和电影感常用', suits: '老照片、胶片、电影感、夜景、复古',
    anchor: '整幅；黑白照片用 mono',
    params: { amount: P(.2, .08, .4, '颗粒强度'), size: P(1.2, .7, 2, '颗粒大小'), mono: P(true, null, null, '黑白颗粒'), frames: P(8, 4, 16, '几张颗粒轮流', true), blend: P('overlay', null, null, "'overlay' / 'soft-light' / 'multiply'") },
  }, (o, e) => {
    const R = rngf(o.seed * 41 + 9), w = Math.round(e.W / 2 / o.size), h = Math.round(e.H / 2 / o.size);
    const fs = Array.from({ length: o.frames }, () => { const [c, g] = U.canvas(w, h), id = g.createImageData(w, h), d = id.data; for (let i = 0; i < d.length; i += 4) { const v = 128 + (R() + R() + R() - 1.5) * 90; d[i] = v; d[i + 1] = o.mono ? v : 128 + (R() - .5) * 200; d[i + 2] = o.mono ? v : 128 + (R() - .5) * 200; d[i + 3] = 255; } g.putImageData(id, 0, 0); return c; });
    return { draw(g, t) { const i = Math.floor(t * CFG.fps + .001) % o.frames; g.save(); g.globalCompositeOperation = o.blend; g.globalAlpha = o.amount; g.drawImage(fs[i], 0, 0, e.W, e.H); g.restore(); } };
  });

  FX.def('scratches', {
    zh: '划痕灰尘', group: '质感', desc: '老胶片的竖划痕、灰尘点和毛发一闪一闪', suits: '老照片、默片、复古海报、胶片、档案感',
    anchor: '整幅',
    params: { amount: P(1, .4, 2, '整体强度'), lines: P(2, 0, 5, '同时的划痕数', true), dust: P(14, 0, 40, '每帧灰尘点数', true), hair: P(.3, 0, 1, '出现毛发的概率'), light: P(.6, 0, 1, '亮色（而不是暗色）的比例') },
  }, (o, e) => {
    const fps = CFG.fps, N = Math.round(e.D * fps), R0 = rngf(o.seed * 7 + 1), sc = [];
    for (let i = 0; i < o.lines * 3; i++) sc.push({ x: R0() * e.W, a: Math.floor(R0() * N), len: 6 + Math.floor(R0() * 14), lt: R0() < o.light, w: (.6 + R0() * 1.2) * e.u, dr: (R0() - .5) * 4 * e.u });
    return {
      draw(g, t) {
        const f = Math.floor(t * fps + .001), R = rngf(f * 131 + o.seed); g.save(); g.lineCap = 'round';
        for (const s of sc) { const k = ((f - s.a) % N + N) % N; if (k >= s.len) continue; g.globalAlpha = .35 * o.amount * (R() * .5 + .5); g.strokeStyle = s.lt ? '#f4efe4' : '#1c1915'; g.lineWidth = s.w * o.amount; const x = s.x + s.dr * k + (R() - .5) * 2 * e.u; g.beginPath(); g.moveTo(x, 0); g.lineTo(x + (R() - .5) * 6 * e.u, e.H); g.stroke(); }
        for (let i = 0; i < o.dust; i++) { g.globalAlpha = (.3 + .5 * R()) * Math.min(1, o.amount); g.fillStyle = R() < o.light ? '#f6f2ea' : '#16130f'; g.beginPath(); g.ellipse(R() * e.W, R() * e.H, (.6 + 2.5 * R() ** 3) * e.u * 1.5, (.6 + 2 * R() ** 3) * e.u * 1.5, R() * 3, 0, TAU); g.fill(); }
        if (R() < o.hair * .3) { g.globalAlpha = .45 * o.amount; g.strokeStyle = R() < o.light ? '#f0ebe0' : '#1a1612'; g.lineWidth = .9 * e.u; const x = R() * e.W, y = R() * e.H, s = (30 + 60 * R()) * e.u; g.beginPath(); g.moveTo(x, y); g.bezierCurveTo(x + s * (R() - .5), y + s * (R() - .5), x + s * (R() - .5), y + s * (R() - .5), x + s * (R() - .5), y + s * (R() - .5)); g.stroke(); }
        g.restore();
      },
    };
  });

  FX.def('vignette', {
    zh: '暗角', group: '质感', desc: '四角压暗，可以慢慢呼吸，把视线收到中间', suits: '人像、老照片、电影感、夜景、产品',
    anchor: 'center 放在主体上',
    params: { amount: P(.55, .25, .8, '压暗程度'), size: P(.62, .4, .9, '中间亮区大小'), breathe: P(.15, 0, .4, '呼吸幅度'), speed: P(1, 1, 2, '每轮呼吸几次', true), center: P([.5, .5], null, null, '中心'), color: P('#000000', null, null, '暗角颜色') },
  }, (o, e) => {
    const [r, gg, b] = U.rgb(o.color), cx = o.center[0] * e.W, cy = o.center[1] * e.H, D = Math.hypot(Math.max(cx, e.W - cx), Math.max(cy, e.H - cy));
    return {
      draw(g, t) {
        const k = 1 + o.breathe * (.5 - .5 * Math.cos(TAU * o.speed * t / e.D)), gr = g.createRadialGradient(cx, cy, D * o.size * .45 / k, cx, cy, D * 1.02);
        gr.addColorStop(0, `rgba(${r},${gg},${b},0)`); gr.addColorStop(.55, `rgba(${r},${gg},${b},${o.amount * .35 * k})`); gr.addColorStop(1, `rgba(${r},${gg},${b},${Math.min(1, o.amount * k)})`);
        g.save(); g.fillStyle = gr; g.fillRect(0, 0, e.W, e.H); g.restore();
      },
    };
  });

  FX.def('chroma', {
    zh: '色散', group: '质感', desc: '红绿蓝三色轻微错开（越靠边越明显），可以随节奏一跳一跳', suits: '赛博、潮流、音乐、科技、故障风、霓虹、黑白图形',
    anchor: '整幅；这个积木自己画整张图，放在最底层',
    params: { amount: P(1, .3, 2, '错开距离'), pulse: P(.6, 0, 1, '跳动幅度'), speed: P(4, 1, 8, '每轮跳几下', true), radial: P(true, null, null, 'true 越靠边越明显 / false 整体左右错开') },
  }, (o, e) => {
    const [base, bg] = U.canvas(e.W, e.H); bg.drawImage(e.img, 0, 0); const src = bg.getImageData(0, 0, e.W, e.H).data;
    const ch = [0, 1, 2].map(c => { const [cv, cg] = U.canvas(e.W, e.H), id = cg.createImageData(e.W, e.H), d = id.data; for (let i = 0; i < d.length; i += 4) { d[i + c] = src[i + c]; d[i + 3] = 255; } cg.putImageData(id, 0, 0); return cv; });
    return {
      draw(g, t) {
        const s = t / e.D, beat = Math.max(0, Math.sin(TAU * o.speed * s)) ** 6, a = o.amount * (1 - o.pulse + o.pulse * (.3 + .7 * beat)) * e.u * 6;
        g.save(); g.fillStyle = '#000'; g.fillRect(0, 0, e.W, e.H); g.globalCompositeOperation = 'lighter';
        [-1, 0, 1].forEach((k, c) => {
          if (o.radial) { const z = 1 + k * a / Math.min(e.W, e.H) * 2; g.drawImage(ch[c], e.W / 2 * (1 - z), e.H / 2 * (1 - z), e.W * z, e.H * z); }
          else g.drawImage(ch[c], k * a, 0);
        });
        g.restore();
      },
    };
  });

  FX.def('texture', {
    zh: '纸纹', group: '质感', desc: '给画面叠一层纸、画布、亚麻或牛皮纸的纹理，可以让一道柔光在纸面上慢慢扫过', suits: '插画、水彩、海报、手作、复古；电子图想要手作感',
    anchor: '整幅',
    params: { kind: P('paper', null, null, "'paper' 纸 / 'canvas' 画布 / 'linen' 亚麻 / 'kraft' 牛皮纸"), amount: P(.3, .12, .55, '纹理强度'), scale: P(1, .6, 1.8, '纹理粗细'), light: P(.1, 0, .3, '纸面上慢慢移动的柔光') },
  }, (o, e) => {
    const R = rngf(o.seed * 19 + 3), w = Math.round(e.W / 1.5), h = Math.round(e.H / 1.5), [c, cg] = U.canvas(w, h), id = cg.createImageData(w, h), d = id.data;
    const n1 = vnoise(256, 256, o.seed + 1, Math.round(24 / o.scale), 3), n2 = vnoise(256, 256, o.seed + 2, 4, 3);
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
      const k = (j * w + i) * 4, a = n1[(j % 256) * 256 + (i % 256)], b = n2[(Math.floor(j / 3) % 256) * 256 + (Math.floor(i / 3) % 256)], r = R();
      let v = 128;
      if (o.kind === 'canvas' || o.kind === 'linen') { const p = o.kind === 'canvas' ? 3 : 2; const wx = Math.sin(i / (p * o.scale) * Math.PI), wy = Math.sin(j / (p * o.scale) * Math.PI); v += (wx * wx - wy * wy) * 22 + (r - .5) * 26 + (a - .5) * 30; }
      else v += (a - .5) * 50 + (b - .5) * 40 + (r - .5) * 30 + (R() < .004 ? -60 : 0);
      d[k] = d[k + 1] = d[k + 2] = cl(v, 0, 255); if (o.kind === 'kraft') { d[k] = cl(v + 10, 0, 255); d[k + 2] = cl(v - 20, 0, 255); } d[k + 3] = 255;
    }
    cg.putImageData(id, 0, 0);
    const lg = U.sprite('#fff6e0', [[0, .9], [.5, .35], [1, 0]]);
    return {
      draw(g, t) {
        g.save(); g.globalCompositeOperation = 'overlay'; g.globalAlpha = o.amount; g.drawImage(c, 0, 0, e.W, e.H);
        if (o.light > 0) { const a = TAU * t / e.D, r = Math.max(e.W, e.H) * .7; g.globalCompositeOperation = 'soft-light'; g.globalAlpha = o.light; g.drawImage(lg, e.W / 2 + Math.cos(a) * e.W * .3 - r, e.H / 2 + Math.sin(a) * e.H * .25 - r, 2 * r, 2 * r); }
        g.restore();
      },
    };
  });
  // ======================= 画内复位 =======================
  // 片子正文播完后，再用 tail 秒、用画面里的东西把状态送回第一帧（比帧级的 reset.py 更像片子本身的一部分）。
  // 总时长 CFG.dur = 正文时长 + tail。render(t) 里这样接：
  //   const T = R.time(t);        // 用 T 驱动正文（正文时间轴是 0..CFG.dur - tail）
  //   …正文按 T 画…
  //   R.apply?.(view, t);         // 推进切回：给 #view 加缩放
  //   g.clearRect(…); R.draw(g, t); // 最上层的遮挡物 / 光（g 是不随镜头动的一层，放在 #view 里、#cam 外面）
  FX.groups.push('画内复位');
  const io = x => { x = cl(x); return x < .5 ? 4 * x * x * x : 1 - (-2 * x + 2) ** 3 / 2; };
  const TAIL = P(1, .6, 1.6, '复位用的秒数（加在正文后面）');
  const resetBase = (o, e) => { const Dc = e.D - o.tail, mid = Dc + o.tail * (o.cut ?? .5); return { Dc, mid, a: t => cl((t - Dc) / o.tail), time: t => t < mid ? Math.min(t, Dc) : 0 }; };

  FX.def('backplay', {
    zh: '倒放归位', group: '画内复位', desc: '正文播完后整段快速倒放回第一帧（先慢后快再慢），像时间倒流', suits: '从空白搭起来的片子、生长、拼合、绘制过程、有剧情的片子',
    anchor: '正文本身；适合首帧和末帧差很多、但过程好看的片子',
    params: { tail: TAIL, curve: P('inout', null, null, "'inout' 先慢后快再慢 / 'in' 越倒越快") },
  }, (o, e) => {
    const Dc = e.D - o.tail;
    return { time: t => t <= Dc ? t : Dc * (1 - (o.curve === 'in' ? cl((t - Dc) / o.tail) ** 2 : io((t - Dc) / o.tail))), draw() {} };
  });

  FX.def('passby', {
    zh: '前景掠过', group: '画内复位', desc: '一个很近的前景（柱子、树叶、云、人影）从镜头前横着掠过，挡住画面的一瞬间换回第一帧', suits: '街景、室内、风景、海报、任何片子（最通用的画内复位）',
    anchor: 'shape 选和画面搭的前景；颜色默认取原图最暗处（柱子、树叶）或白（云）',
    params: { tail: TAIL, shape: P('pillar', null, null, "'pillar' 柱子 / 'leaves' 树叶 / 'cloud' 云雾 / 'figure' 人影"), dir: P(1, null, null, '1 从左往右 / -1 从右往左'), color: P('auto', null, null, "'auto' 或颜色"), cut: P(.5, .4, .6, '挡满的时刻（占 tail 的比例）') },
  }, (o, e) => {
    const B = resetBase(o, e), R = rngf(o.seed * 23 + 1), W = e.W, H = e.H;
    let col = o.color;
    if (col === 'auto') { if (o.shape === 'cloud') col = '#f4f3ef'; else if (e.img) { const T = U.lum(e.img); let mi = 0; for (let i = 1; i < T.L.length; i++) if (T.L[i] < T.L[mi]) mi = i; col = U.hex([T.d[mi * 4], T.d[mi * 4 + 1], T.d[mi * 4 + 2]].map(v => v * .7)); } else col = '#1b1915'; }
    const BW = W * 1.25, pad = W * .45, [c, g] = U.canvas((BW + pad * 2) / 2, H / 2), k = .5;  // 半分辨率，前景本来就是虚的
    g.scale(k, k); g.fillStyle = col; g.filter = `blur(${(o.shape === 'cloud' ? 40 : 14) * e.u}px)`;
    if (o.shape === 'leaves' || o.shape === 'cloud') {
      g.fillRect(pad + BW * .1, -H * .1, BW * .8, H * 1.2);
      for (let i = 0; i < 160; i++) { const side = R() < .5 ? 0 : 1, x = pad + (side ? BW * (.82 + R() * .3) : BW * (.18 - R() * .3)), y = R() * H, s = (o.shape === 'cloud' ? 160 : 70) * e.u * (.5 + R()); g.save(); g.translate(x, y); g.rotate(R() * TAU); g.beginPath(); g.ellipse(0, 0, s, s * (o.shape === 'cloud' ? .7 : .38), 0, 0, TAU); g.fill(); g.restore(); }
    } else if (o.shape === 'figure') {
      g.fillRect(pad + BW * .12, -H * .1, BW * .76, H * 1.2); g.beginPath(); g.ellipse(pad + BW * .5, H * .02, BW * .32, H * .3, 0, 0, TAU); g.fill();
    } else {
      g.fillRect(pad, -H * .1, BW, H * 1.2); g.filter = 'none'; g.globalAlpha = .12; g.fillStyle = '#fff'; g.fillRect(pad + BW * .08, 0, BW * .03, H);  // 柱子边上一点反光
    }
    return {
      time: B.time,
      draw(gg, t) {
        const a = B.a(t); if (a <= 0 || a >= 1) return;
        const span = W + BW + pad * 2, x = -BW - pad * 2 + a * span, X = o.dir > 0 ? x : W - x - (BW + pad * 2);
        gg.drawImage(c, X, 0, BW + pad * 2, H);
      },
    };
  });

  FX.def('pushcut', {
    zh: '推进切回', group: '画内复位', desc: '镜头猛推进画面里一小块颜色均匀的地方（暗处、天空、纸面），推满的一瞬间换回第一帧，再拉出来', suits: '有大片均匀颜色的画面；首帧是空白纸面/纯色的片子尤其合适',
    anchor: 'focus 给一个"首帧和末帧在那里都差不多颜色"的点（比如天空、纸面、暗部）',
    params: { tail: TAIL, focus: P([.5, .5], null, null, '推向的点'), zoom: P(9, 5, 14, '推到多大'), blur: P(1, 0, 2, '推拉时的模糊') },
  }, (o, e) => {
    const B = resetBase(o, e);
    const z = t => { const a = B.a(t); if (a <= 0 || a >= 1) return 1; const q = a < .5 ? io(a * 2) : 1 - io(a * 2 - 1), qq = a < .5 ? (a * 2) ** 2.2 : (1 - (a * 2 - 1)) ** 2.2; return 1 + (o.zoom - 1) * (.15 * q + .85 * qq); };
    return {
      time: B.time, draw() {},
      at: t => ({ z: z(t), cx: o.focus[0] * e.W, cy: o.focus[1] * e.H }),
      apply(el, t) {
        const zz = z(t), fx = o.focus[0] * CFG.outW, fy = o.focus[1] * CFG.outH;
        el.style.transformOrigin = `${fx}px ${fy}px`; el.style.transform = zz > 1.0001 ? `scale(${zz})` : '';
        const v = Math.abs(z(t + 1 / 60) - zz) / o.zoom * 60; el.style.filter = o.blur > 0 && v > .05 ? `blur(${Math.min(12, v * 3 * o.blur)}px)` : '';
      },
    };
  });

  FX.def('lightcut', {
    zh: '光收回', group: '画内复位', desc: '画面暗下去、只剩光源一圈光（或从光源亮成一片），最暗 / 最亮那一下换回第一帧，再从光源亮回来', suits: '有灯、窗、太阳、火的画面；夜景；首帧是空白纸面的片子用 bright',
    anchor: 'from 给光源位置（默认自动找原图最亮的地方）',
    params: { tail: TAIL, mode: P('dark', null, null, "'dark' 暗下去只剩光源 / 'bright' 从光源亮成一片"), from: P('auto', null, null, "'auto' 或 [x,y]"), color: P('auto', null, null, "dark 时是暗场颜色（默认近黑），bright 时是亮场颜色（默认暖白）"), glow: P('#ffd59a', null, null, '光源的光晕颜色') },
  }, (o, e) => {
    const B = resetBase(o, e), [lx, ly] = o.from === 'auto' ? (e.img ? U.highlights(e, 1, U.rect(null, e), .2)[0] || [e.W / 2, e.H / 2] : [e.W / 2, e.H / 2]) : [o.from[0] * e.W, o.from[1] * e.H];
    const col = o.color === 'auto' ? (o.mode === 'bright' ? '#fbf3e4' : '#0d0b09') : o.color, [r, gg, b] = U.rgb(col), gl = U.sprite(o.glow, [[0, .95], [.2, .55], [.55, .12], [1, 0]]);
    const Dmax = Math.hypot(Math.max(lx, e.W - lx), Math.max(ly, e.H - ly));
    return {
      time: B.time,
      draw(g, t) {
        const a = B.a(t); if (a <= 0 || a >= 1) return;
        const k = a < .5 ? io(a * 2) : 1 - io(a * 2 - 1);  // 0 → 1（全暗/全亮）→ 0
        g.save();
        if (o.mode === 'bright') {
          const gr = g.createRadialGradient(lx, ly, 0, lx, ly, Dmax * (.05 + 1.2 * k)); gr.addColorStop(0, `rgba(${r},${gg},${b},${k})`); gr.addColorStop(.6, `rgba(${r},${gg},${b},${k * k})`); gr.addColorStop(1, `rgba(${r},${gg},${b},${k ** 4})`);
          g.fillStyle = gr; g.fillRect(0, 0, e.W, e.H); g.globalCompositeOperation = 'lighter'; g.globalAlpha = Math.sin(Math.PI * a) * .8; const s = Dmax * .5; g.drawImage(gl, lx - s, ly - s, 2 * s, 2 * s);
        } else {
          const rad = Dmax * (1.15 - 1.12 * k), gr = g.createRadialGradient(lx, ly, rad * .15, lx, ly, rad);
          gr.addColorStop(0, `rgba(${r},${gg},${b},0)`); gr.addColorStop(1, `rgba(${r},${gg},${b},${Math.min(1, k * 1.6)})`);
          g.fillStyle = gr; g.fillRect(0, 0, e.W, e.H);
          if (k > .9) { g.fillStyle = `rgba(${r},${gg},${b},${(k - .9) * 10})`; g.fillRect(0, 0, e.W, e.H); }  // 最暗那几帧整幅压黑，换图藏在里面
          g.globalCompositeOperation = 'lighter'; g.globalAlpha = Math.sin(Math.PI * a) * .9; const s = Math.min(e.W, e.H) * (.12 + .1 * k); g.drawImage(gl, lx - s, ly - s, 2 * s, 2 * s);
        }
        g.restore();
      },
    };
  });
})();
if (typeof module === 'object' && module.exports) module.exports = FX;
