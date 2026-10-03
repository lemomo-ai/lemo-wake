#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["numpy", "opencv-python-headless"]
# ///
"""复位转场：在片尾把画面用一种"符合画风"的方式送回首帧，让 GIF/WebP 无缝循环。

GIF 会无限循环。片子如果从空白/冷色开始、以完整原图结束，每轮循环都会"啪"地硬切一下。
复位转场把最后一段从 末帧(A) 过渡回 首帧(B)，下一轮从首帧接着播，看不出接缝。
它是帧级后期：对任何片子都能用，不需要改 index.html。

用法：
  reset.py --list [--json]                     # 全部种类：中文名、分组、适合的画风、默认时长
  reset.py <frames目录> --kind <种类> [--dur 秒] [--fps 30] [--mode append|overlay] [--pre-hold 0.3]
           [--dir lr|rl|tb|bt | --angle 度] [--origin x,y(0..1)] [--color #hex] [--seed 1] [--out 目录]

  --dur           转场时长；不写就用该种类的默认时长（--list 里有）。
  --mode append   （默认）在片尾追加转场帧：总时长 = 原时长 + pre-hold + dur。
                  规划新片时把渲染时长设成 目标时长 - 复位时长，再追加复位。
  --mode overlay  转场覆盖在最后 dur 秒上，总时长不变（片尾本来就有静止段时用）。
  --pre-hold      追加转场前先定格多少秒（片尾还在动、来不及看清完整画面时用）。
  --seed          同一种转场换个种子，形状就不一样（边界、笔触、碎片…），避免每支片都一模一样。
  输出：默认写到 <frames目录>_loop/，原帧不动。

种类按画风选，--list 看全表。同一种类用不同的 --origin / --dir / --color / --seed 也能做出不同的样子。
"""
import argparse, glob, json, os, shutil, sys
import cv2
import numpy as np


# ---------------- 工具 ----------------
def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 + 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


def ease(name, p):
    if name == "in": return p ** 3
    if name == "out": return 1 - (1 - p) ** 3
    if name == "linear": return p
    if name == "sine": return -(np.cos(np.pi * p) - 1) / 2
    return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2  # inOutCubic


def hexrgb(h, default):
    h = (h or default).lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)[::-1] / 255  # BGR


def fbm(h, w, seed, base=6, octaves=4):
    """平滑噪声场 0..1（低分辨率随机网格三次插值，多倍频叠加）。"""
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = max(2, int(base * 2 ** o * h / max(h, w)) + 2), max(2, int(base * 2 ** o * w / max(h, w)) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        acc += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC); tot += amp; amp *= .5
    acc /= tot
    return (acc - acc.min()) / (acc.max() - acc.min() + 1e-9)


def grid(h, w):
    """以画面高为单位的坐标（x 0..w/h，y 0..1）。"""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x / h, y / h


def axis_u(h, w, a):
    """沿方向 a（弧度，0=从左到右）的归一化坐标 0..1。"""
    x, y = grid(h, w)
    u = x * np.cos(a) + y * np.sin(a)
    return (u - u.min()) / (u.max() - u.min())


def radial(h, w, origin):
    x, y = grid(h, w)
    d = np.hypot(x - origin[0] * w / h, y - origin[1])
    return d / d.max()


def dir_angle(args, default=0.0):
    if args.angle is not None: return np.deg2rad(args.angle)
    if args.dir: return {"lr": 0, "rl": np.pi, "tb": np.pi / 2, "bt": -np.pi / 2}[args.dir]
    return default


def has_dir(args):
    return args.angle is not None or args.dir is not None


def equalize(T):
    """按像素排名重排到达时间：形状不变，但每帧推进的面积均匀，不会挤在中间几帧。"""
    sm = cv2.resize(T, (256, max(2, int(256 * T.shape[0] / T.shape[1]))), interpolation=cv2.INTER_AREA)
    qs = np.quantile(sm, np.linspace(0, 1, 257))
    return np.interp(T, qs, np.linspace(0, 1, 257)).astype(np.float32)


def norm01(T):
    return ((T - T.min()) / (T.max() - T.min() + 1e-9)).astype(np.float32)


def mix(a, b, m):
    m = np.asarray(m, np.float32)
    return a + (b - a) * (m[..., None] if m.ndim == 2 else m)


def blur(img, s):
    return cv2.GaussianBlur(img, (0, 0), max(.1, s))


def gray(img):
    return (img @ np.array([.114, .587, .299], np.float32))[..., None]


def remap(img, mx, my, border=cv2.BORDER_REFLECT):
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=border, borderValue=0)


def screen(base, light):
    return 1 - (1 - base) * (1 - np.clip(light, 0, 1))


def pix(h, w):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x, y


def drops_field(h, w, a, n, warp, spread=(.12, .3)):
    """几处起点各自往外扩的到达时间场（起点 = --origin + 随机几处），边界被噪声扭曲。"""
    rng = np.random.default_rng(a.seed); x, y = grid(h, w)
    wx = (fbm(h, w, a.seed + 1, base=3) - .5) * warp; wy = (fbm(h, w, a.seed + 2, base=3) - .5) * warp
    pts = [(a.origin[0] * w / h, a.origin[1], 0)] + [(rng.uniform(.1, .9) * w / h, rng.uniform(.15, .85), rng.uniform(*spread)) for _ in range(n - 1)]
    return np.min([np.hypot(x + wx - dx, y + wy - dy) + dl for dx, dy, dl in pts], axis=0)


def scribble_path(W, th, rows, amp, period, seed):
    """来回涂的路径（坐标以画面高为单位，x 0..W）：沿方向 th 分几行，每行之字形往返前进。"""
    d = np.array([np.cos(th), np.sin(th)]); n = np.array([-d[1], d[0]]); rng = np.random.default_rng(seed)
    cs = np.array([(0, 0), (W, 0), (0, 1), (W, 1)])
    a0, a1 = (cs @ d).min(), (cs @ d).max(); c0, c1 = (cs @ n).min(), (cs @ n).max()
    pts = []
    for i in range(rows):
        ci = c0 + (i + .5) * (c1 - c0) / rows
        al = np.arange(a0 - period, a1 + period * 2, period / 2)
        if i % 2: al = al[::-1]
        pts += [d * v + n * (ci + (amp if k % 2 else -amp) * rng.uniform(.8, 1.15)) for k, v in enumerate(al)]
    return np.array(pts), (c1 - c0) / rows


def path_arrival(h, w, pts, r, res=320, empty=1.0):
    """沿路径画圆（pts 以画面高为单位），像素的到达时间 = 路径第一次经过它的弧长比例 0..1。"""
    sw = res; sh = max(2, int(res * h / w)); k = sh  # 低分辨率下 1 个高度单位 = sh 像素
    P = pts * k; seg = np.hypot(*np.diff(P, axis=0).T); s = np.r_[0, np.cumsum(seg)]; s /= s[-1]
    T = np.full((sh, sw), empty, np.float32); R = max(1, int(round(r * k)))
    dense = [(P[i] * (1 - t) + P[i + 1] * t, s[i] * (1 - t) + s[i + 1] * t)
             for i in range(len(P) - 1) for t in np.arange(max(1, int(seg[i]))) / max(1, int(seg[i]))]
    for (px, py), si in reversed(dense):  # 倒着画：先到的覆盖后到的
        cv2.circle(T, (int(round(px)), int(round(py))), R, float(si), -1, lineType=cv2.LINE_AA)
    return cv2.resize(T, (w, h), interpolation=cv2.INTER_LINEAR)


def paste_affine(out, tex, al, M):
    """把一块贴图（tex + alpha）按仿射矩阵 M（贴图坐标 → 画面坐标）合成到 out 上，只算它覆盖的那一块。"""
    H, W_ = out.shape[:2]; th_, tw = al.shape
    c = np.array([[0, 0, 1], [tw, 0, 1], [0, th_, 1], [tw, th_, 1]], np.float32) @ M.T
    x0, y0 = max(0, int(c[:, 0].min()) - 1), max(0, int(c[:, 1].min()) - 1)
    x1, y1 = min(W_, int(c[:, 0].max()) + 2), min(H, int(c[:, 1].max()) + 2)
    if x1 <= x0 or y1 <= y0: return
    M2 = M.copy(); M2[0, 2] -= x0; M2[1, 2] -= y0
    t = cv2.warpAffine(tex, M2, (x1 - x0, y1 - y0)); m = cv2.warpAffine(al, M2, (x1 - x0, y1 - y0))
    out[y0:y1, x0:x1] = mix(out[y0:y1, x0:x1], t, m)


# ---------------- 注册表 ----------------
# 每种转场：make(A, B, args) → step(A, B, p)，p 从 0（全是末帧 A）走到 1（全是首帧 B）。
# make 里做一次性的准备（到达时间场、碎片形状…），step 每帧调用；overlay 模式下 A 每帧不同。
KINDS = {}
GROUPS = ["自然", "手作", "光与胶片", "数字", "动势"]


def kind(name, zh, group, suits, desc, dur=.6, film=False):
    def reg(make):
        KINDS[name] = dict(zh=zh, group=group, suits=suits, desc=desc, dur=dur, film=film, make=make)
        return make
    return reg


# ---------------- 场类：按"到达时间场 T"逐步显露 B，前沿带装饰 ----------------
def comp_field(A, B, T, q, deco):
    soft, band = deco["soft"], deco["band"]
    # 前沿从"装饰带完全在画外"走到"装饰带完全离开"：q=0 时整幅是 A，q=1 时整幅是 B
    lvl = -deco["ahead"] - soft + q * (1 + deco["ahead"] + deco["behind"] + 2 * soft)
    m = 1 - smooth(lvl - soft, lvl + soft, T)  # B 的权重
    out = mix(A, B, m)
    if band > 0:
        dist = (T - lvl) / band
        alpha = np.exp(-(dist * 1.2) ** 2) * deco["strength"]
        c = deco["color"]; a3 = alpha[..., None]
        if deco["blend"] == "multiply": out = out * (1 - a3 * (1 - c))
        elif deco["blend"] == "screen": out = 1 - (1 - out) * (1 - a3 * c)
        else: out = out * (1 - a3) + c * a3
    return out


def field_step(T, deco, a, eq=True):
    T = norm01(T)
    if eq: T = equalize(T)
    if a.soft is not None: deco["soft"] = a.soft
    if a.band is not None: deco["band"] = a.band
    return lambda A, B, p: comp_field(A, B, T, ease(a.ease or "sine", p), deco)


# ================= 自然 =================
@kind("mist", "云雾", "自然", "山水、风景、雾、梦幻、水墨", "一团云雾涌过来盖住画面，雾散开时底下已是首帧", dur=.9)
def k_mist(A, B, a):
    h, w = A.shape[:2]
    T = axis_u(h, w, dir_angle(a)) if has_dir(a) else radial(h, w, a.origin)
    T = equalize(norm01(T * .65 + fbm(h, w, a.seed, base=2.5, octaves=3) * .35))
    pad = int(.25 * max(h, w))
    tex = fbm(h + pad, w + pad, a.seed + 5, base=4, octaves=5)  # 云的明暗纹理，随时间漂移
    col = hexrgb(a.color, "#eeeeea")
    sig = max(2., min(h, w) / 50)

    def step(A, B, p):
        q = ease(a.ease or "sine", p)
        d = (-.5 + q * 2.0) - T  # >0：雾的前沿已经越过这里
        thick = smooth(-.45, -.05, d) * (1 - smooth(.1, .45, d))  # 前沿到来前渐浓，越过后渐散
        o = int(p * pad * .8)
        tx = tex[pad // 2: pad // 2 + h, o: o + w]
        fog = np.clip(thick * (.55 + .75 * smooth(.2, .75, tx)), 0, 1) * .97
        base = mix(A, B, smooth(-.18, .18, d))  # 换图发生在雾最浓的时候
        base = mix(base, blur(base, sig), np.clip(fog * 1.5, 0, 1))
        return mix(base, col * (.93 + .07 * tx[..., None]), fog)
    return step


@kind("ink", "墨晕", "自然", "水墨、水彩、书法", "墨从几处洇开、漫过画面，墨色退去时底下已是首帧", dur=1.0)
def k_ink(A, B, a):
    h, w = A.shape[:2]; rng = np.random.default_rng(a.seed)
    x, y = grid(h, w)
    wx = (fbm(h, w, a.seed + 1, base=3) - .5) * .4; wy = (fbm(h, w, a.seed + 2, base=3) - .5) * .4  # 边界不规则
    drops = [(a.origin[0] * w / h, a.origin[1], 0)] + [(rng.uniform(.1, .9) * w / h, rng.uniform(.15, .85), rng.uniform(.12, .3)) for _ in range(2)]
    T = np.min([np.hypot(x + wx - dx, y + wy - dy) + dl for dx, dy, dl in drops], axis=0)
    T = equalize(norm01(T + (fbm(h, w, a.seed + 3, base=40, octaves=2) - .5) * .03))  # 纸纤维让边缘毛一点
    tex = fbm(h, w, a.seed + 4, base=7, octaves=5)
    tex = smooth(.15, .85, tex) * .6 + smooth(.45, .55, fbm(h, w, a.seed + 6, base=14, octaves=3)) * .4  # 墨的浓淡：云团 + 丝缕
    col = hexrgb(a.color, "#1c1b19")
    seep, back = .2, .16

    def step(A, B, p):
        q = ease(a.ease or "sine", p)
        d = T - (-seep + q * (1 + seep + back * 1.6))  # >0：墨还没到这里
        out = mix(A, B, smooth(.03, -.03, d))
        dens = np.where(d > 0, np.clip(1 - d / seep, 0, 1) ** 1.5, np.exp(-(d / back) ** 2))  # 前方洇开、身后退去
        dens = np.clip(dens * (.45 + .75 * tex), 0, 1) * .88
        return out * (1 - dens[..., None] * (1 - col))
    return step


@kind("watercolor", "水彩晕染", "自然", "水彩、插画、绘本、花卉", "首帧像水彩颜料从几处洇开，边缘积着一圈颜料，湿的地方慢慢干透", dur=1.0)
def k_watercolor(A, B, a):
    h, w = A.shape[:2]
    T = drops_field(h, w, a, 4, .5)
    T = equalize(norm01(T + (fbm(h, w, a.seed + 3, base=36, octaves=3) - .5) * .05))  # 花边一样的水渍边
    gran = fbm(h, w, a.seed + 7, base=90, octaves=2)  # 颜料颗粒
    Bb = blur(B, max(1.5, min(h, w) / 90))

    def step(A, B, p):
        q = ease(a.ease or "sine", p)
        d = T - (-.02 + q * 1.24)  # >0：水还没到
        m = 1 - smooth(-.012, .012, d)
        wet = smooth(-.22, 0, d)  # 刚洇到的地方湿、糊、颗粒明显；越往后越干
        Bw = mix(B, Bb, wet * .8) * (1 - (wet * .22 * (gran - .5))[..., None])
        pig = np.exp(-((d + .012) / .01) ** 2) * .55  # 边缘积颜料：用首帧自己的颜色叠深
        Bw = Bw * (1 - pig[..., None] * (1 - Bw))
        sheen = np.exp(-(d / .03) ** 2) * (d > 0) * .12  # 水先浸湿前方一点点
        return mix(A * (1 - sheen[..., None]), Bw, m)
    return step


@kind("ripple", "涟漪", "自然", "水面、湖、雨、倒影、清新风", "一圈涟漪从一点荡开，波纹过处变成首帧，水波随之平息", dur=1.0)
def k_ripple(A, B, a):
    h, w = A.shape[:2]
    x, y = grid(h, w); X, Y = pix(h, w)
    dx, dy = x - a.origin[0] * w / h, y - a.origin[1]; r = np.hypot(dx, dy) + 1e-6; ux, uy = dx / r, dy / r
    lam, amp, decay = .075, .014, .32

    def step(A, B, p):
        q = ease(a.ease or "sine", p)
        s_ = (-lam + q * (r.max() + lam * 4)) - r  # >0：波已经过来了
        env = np.where(s_ > 0, np.exp(-s_ / decay), 0) * smooth(0, lam * .5, s_) * (1 - smooth(.72, 1, p))
        ph = 2 * np.pi * s_ / lam
        disp = amp * h * np.sin(ph) * env
        Ad, Bd = remap(A, X + ux * disp, Y + uy * disp), remap(B, X + ux * disp, Y + uy * disp)
        out = mix(Ad, Bd, smooth(lam * .2, lam * .9, s_))
        hl = np.cos(ph) * env  # 波峰受光、波谷发暗
        out = screen(out, (np.clip(hl, 0, 1) * .35)[..., None])
        return out * (1 - (np.clip(-hl, 0, 1) * .18)[..., None])
    return step


@kind("steam", "热气", "自然", "美食、咖啡、温泉、冬天、厨房", "一股热气从底下升起漫过画面，空气跟着扭动，热气散开时已是首帧", dur=1.0)
def k_steam(A, B, a):
    h, w = A.shape[:2]; X, Y = pix(h, w)
    T = equalize(norm01((1 - Y / h) * .7 + fbm(h, w, a.seed, base=3, octaves=3) * .3))
    th = int(h * 1.7)
    tex = fbm(th, w, a.seed + 5, base=4, octaves=5)
    curl = fbm(th, w, a.seed + 6, base=2, octaves=2) * 2 * np.pi  # 丝缕往两边卷的相位
    col = hexrgb(a.color, "#f6f6f3"); sig = max(2., min(h, w) / 60)

    def step(A, B, p):
        q = ease(a.ease or "sine", p)
        d = (-.5 + q * 2.0) - T
        thick = smooth(-.42, -.05, d) * (1 - smooth(.1, .45, d))
        o = int((1 - p) * (th - h))  # 纹理往上走
        sway = np.sin(Y / h * 7 + p * 5 + curl[o: o + h]) * .05 * w * (1.3 - Y / h)  # 越往上卷得越开
        tx = remap(tex[o: o + h], X + sway, Y)
        vap = np.clip(thick * (.5 + .9 * smooth(.3, .8, tx)), 0, 1) * .94
        base = mix(A, B, smooth(-.18, .18, d))
        sh = np.sin(Y / h * 26 + p * 14 + np.sin(X / w * 9) * 2) * .006 * w * smooth(0, .5, thick)  # 热空气扭动
        base = remap(base, X + sh, Y)
        base = mix(base, blur(base, sig), np.clip(vap * 1.4, 0, 1))
        return mix(base, col * (.94 + .06 * tx[..., None]), vap)
    return step


@kind("defog", "雾窗擦开", "自然", "雨天、冬天、窗边、夜景、咖啡馆", "画面像玻璃起了一层水雾，一只手几下抹开雾气，抹过的地方是首帧", dur=1.2)
def k_defog(A, B, a):
    h, w = A.shape[:2]; S = min(h, w); rng = np.random.default_rng(a.seed)
    haze = hexrgb(a.color, "#dde3e6"); sig = S / 45
    pts, sp = scribble_path(w / h, np.deg2rad(a.angle if a.angle is not None else -4), 3, .1, .55, a.seed)
    T = path_arrival(h, w, pts, sp * .62)
    dm = np.zeros((h, w), np.float32)  # 凝在玻璃上的小水珠
    for _ in range(int(w * h / 900)):
        cv2.circle(dm, (int(rng.uniform(0, w)), int(rng.uniform(0, h))), int(max(1, rng.uniform(.6, 2.2) * S / 360)), float(rng.uniform(.4, 1)), -1, cv2.LINE_AA)

    def step(A, B, p):
        fogp = smooth(0, .32, p)
        src = mix(A, B, smooth(.22, .36, p))  # 换图藏在雾最浓的时候
        F = mix(mix(src, blur(src, sig), fogp), haze * np.ones_like(A), fogp * .5)
        F = screen(F, (dm * fogp * .22)[..., None])
        lvl = -.03 + smooth(.34, 1, p) * 1.08  # 雾起来之后才开始抹
        d = T - lvl
        m = 1 - smooth(-.012, .012, d)
        film = np.exp(-((d + .02) / .018) ** 2) * .5 * (lvl > 0)  # 抹过的边上还挂着一层水膜
        Bw = mix(B, blur(B, sig * .3), film)
        return mix(F, screen(Bw, (film * .12)[..., None]), m)
    return step


# ================= 手作 =================
@kind("brush", "笔刷", "手作", "手绘、拼贴、书法、毛笔字海报", "几道斜向大笔刷来回刷过，边缘带飞白（--strokes 道数）", dur=.7)
def k_brush(A, B, a):
    h, w = A.shape[:2]
    T = brush_field(h, w, a)
    col = hexrgb(a.color, "#2a2622")
    return field_step(T, dict(soft=.006, band=.025, ahead=.03, behind=0, color=col, blend="multiply", strength=.35 if a.color else 0), a, eq=False)


def brush_field(h, w, args):
    """几道斜向大笔刷依次刷过（每道从一端刷到另一端），刷过的地方露出首帧；笔刷两侧与笔尖带飞白。"""
    th = np.deg2rad(args.angle if args.angle is not None else -18)
    d = np.array([np.cos(th), np.sin(th)], np.float32); nrm = np.array([-d[1], d[0]], np.float32)
    x, y = grid(h, w)
    along = x * d[0] + y * d[1]; across = x * nrm[0] + y * nrm[1]
    a0, a1 = along.min(), along.max(); c0, c1 = across.min(), across.max()
    n = args.strokes; r = (c1 - c0) / n * .8  # 半宽：最窄处也和相邻笔刷重叠，不留缝
    rng = np.random.default_rng(args.seed)
    T = np.full((h, w), 2.0, np.float32)
    for i in range(n):
        ci = c0 + (i + .5) * (c1 - c0) / n + (rng.random() - .5) * r * .2
        q = across - ci
        fw = rng.random() * 100
        bristle = fbm_1d(q / r * 9 + fw, args.seed + i)          # 跨笔刷方向的鬃毛条纹
        edge = r * (.82 + .3 * (bristle - .5))                    # 笔刷边缘随鬃毛参差
        prog = (along - a0) / (a1 - a0)
        if i % 2: prog = 1 - prog                                 # 来回刷
        tip = (bristle - .5) * .16                                # 笔尖参差（鬃毛长短不一）
        dry = np.clip((np.abs(q) / edge - .55) * 2.2, 0, 1) * np.clip((bristle - .45) * 3, 0, 1)  # 靠边的飞白：晚一点才被填上
        inside = np.abs(q) < edge
        Ti = (i + np.clip(prog + tip + dry * .5, 0, 1.4)) / n
        T = np.where(inside & (Ti < T), Ti, T)
    T[T > 1.5] = 1.0  # 没被刷到的缝隙最后补上
    return T


def fbm_1d(u, seed):
    rng = np.random.default_rng(seed + 77); g = rng.random(4096).astype(np.float32)
    acc = np.zeros_like(u); amp, tot = 1., 0.
    for o in range(3):
        v = (u * 2 ** o) % 4000; i = np.floor(v).astype(np.int32); f = v - i; f = f * f * (3 - 2 * f)
        acc += amp * (g[i] * (1 - f) + g[i + 1] * f); tot += amp; amp *= .5
    return acc / tot


@kind("erase", "橡皮擦", "手作", "儿童画、铅笔稿、手账", "橡皮来回擦掉末帧，擦过的地方露出首帧", dur=.8)
def k_erase(A, B, a):
    h, w = A.shape[:2]
    return field_step(erase_field(h, w, a), dict(soft=.01, band=.02, ahead=.02, behind=0, color=hexrgb(a.color, "#f4f1ea"), blend="normal", strength=.6), a, eq=False)


def erase_field(h, w, args):
    """橡皮来回擦：之字形路径，像素的到达时间 = 路径第一次擦到它的弧长比例。"""
    sw = 240; sh = max(2, int(sw * h / w)); r = sh / 7.0
    rows = int(np.ceil(sh / (r * 1.5))) + 1
    pts = []
    for i in range(rows):
        yy = i * sh / (rows - 1)
        xs = np.linspace(-r, sw + r, 60)
        if i % 2: xs = xs[::-1]
        pts += [(x, yy + np.sin(x / 9 + i + args.seed) * r * .25) for x in xs]
    pts = np.array(pts, np.float32); s = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]; s /= s[-1]
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32); T = np.full((sh, sw), 1.0, np.float32)
    for (px, py), si in zip(pts, s):
        m = (xx - px) ** 2 + (yy - py) ** 2 < r * r
        T[m] = np.minimum(T[m], si)
    return cv2.resize(T, (w, h), interpolation=cv2.INTER_LINEAR)


@kind("paper", "抽纸", "手作", "印刷、海报、版式、拼贴", "整张纸被一把抽走，露出底下的首帧", dur=.6)
def k_paper(A, B, a):
    h, w = A.shape[:2]; ang = dir_angle(a, default=-np.pi / 3.2)  # 默认往右上抽走
    ones = np.ones((h, w), np.float32)

    def step(A, B, p):
        e = p ** 2.4  # 先慢后快：像被手抽走
        dx, dy = np.cos(ang) * e * w * 1.35, np.sin(ang) * e * h * 1.35
        rot = 9 * e * (1 if np.cos(ang) >= 0 else -1)
        sc = 1 + .04 * np.sin(np.pi * min(1, p * 1.6))  # 抬起时略微放大
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, sc); M[0, 2] += dx; M[1, 2] += dy
        Aw = cv2.warpAffine(A, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
        mw = cv2.warpAffine(ones, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
        lift = min(1, p * 3)
        Ms = M.copy(); Ms[0, 2] += 14 * lift * w / 640; Ms[1, 2] += 22 * lift * w / 640
        sh = blur(cv2.warpAffine(ones, Ms, (w, h), borderValue=0), (6 + 18 * lift) * w / 640) * .45 * lift
        base = B * (1 - sh[..., None])
        return mix(base, np.clip(Aw * (1 + .05 * lift), 0, 1), mw)  # 抬起受光
    return step


@kind("pagecurl", "翻页", "手作", "绘本、杂志、日记、手账、书页", "末帧从一角掀起整页翻走，翻起的背面透出一点画，底下是首帧", dur=.9)
def k_pagecurl(A, B, a):
    h, w = A.shape[:2]; X, Y = pix(h, w)
    ang = dir_angle(a, default=np.arctan2(-1, -1.5))  # 默认从右下角往左上翻
    tx, ty = np.cos(ang), np.sin(ang)
    proj = X * tx + Y * ty; u = proj - proj.min(); umax = float(u.max())
    r = .085 * min(h, w)
    paper = hexrgb(a.color, "#f3efe6"); ones = np.ones((h, w), np.float32)

    def layer(img, s):  # 纸上 s 处的那一点，现在显示在 u 处：沿翻页方向取样
        k = s - u
        mx, my = X + k * tx, Y + k * ty
        return remap(img, mx, my, cv2.BORDER_CONSTANT), remap(ones, mx, my, cv2.BORDER_CONSTANT) * np.clip(s + .5, 0, 1)

    def step(A, B, p):
        f = ease(a.ease or "sine", p) * (umax + r * 1.1)  # 折线位置
        out = B * (1 - (np.where(u < f - r, np.exp(-(f - r - u) / (.7 * r)), 0) * .42 * smooth(0, r, f))[..., None])  # 卷起的纸投在首帧上的影子
        flat = smooth(f - .5, f + .5, u)
        uend = 2 * f - np.pi * r
        shA = np.where(u > uend, np.exp(-(u - uend) / (.45 * r)), 0) * .3 * smooth(np.pi * r, np.pi * r * 1.5, f)  # 翻过来的纸压在末帧上的影子
        out = mix(out, A * (1 - shA[..., None]), flat)
        cyl = (u >= f - r - 1) & (u <= f + .5)
        th = np.arcsin(np.clip((f - u) / r, 0, 1))
        edge = np.clip(u - (f - r) + .5, 0, 1) * cyl
        img, al = layer(A, f - r * th)  # 卷筒下半：正面，越往里越暗
        out = mix(out, img * (.5 + .5 * np.cos(th))[..., None], al * edge)
        img, al = layer(A, f - r * (np.pi - th))  # 卷筒上半：背面
        out = mix(out, mix(paper * ones[..., None], img, .2) * (.72 + .28 * np.sin(th))[..., None], al * edge)
        img, al = layer(A, 2 * f - u - np.pi * r)  # 翻过来平压着的部分：背面
        return mix(out, mix(paper * ones[..., None], img, .2) * .97, al * flat)
    return step


@kind("tear", "撕纸", "手作", "拼贴、海报、剪报、手账", "末帧从中间被撕成两半往两边扯开，毛边露出白纸芯，底下是首帧", dur=.85)
def k_tear(A, B, a):
    h, w = A.shape[:2]; S = min(h, w); X, Y = pix(h, w)
    phi = np.deg2rad(a.angle if a.angle is not None else 6)  # 撕口偏离竖直的角度
    nx, ny = np.cos(phi), np.sin(phi)  # 法线：指向右半张
    ox, oy = a.origin[0] * w, a.origin[1] * h
    along = -(X - ox) * ny + (Y - oy) * nx
    seed = a.seed
    jag = (fbm_1d(along / S * 2.2 + seed * 3.1, seed) - .5) * .2 * S + (fbm_1d(along / S * 34 + seed, seed + 5) - .5) * .022 * S
    sd = (X - ox) * nx + (Y - oy) * ny - jag
    fl = fbm_1d(along / S * 14 + 7, seed + 9)
    bwl, bwr = S * (.006 + .016 * fl), S * (.002 + .006 * (1 - fl))  # 两边毛边宽窄不一
    paper = hexrgb(a.color, "#f7f4ec")
    fray = fbm(h, w, seed + 4, base=80, octaves=1)
    alL, alR = smooth(.6, -.6, sd), smooth(-.6, .6, sd)
    texL = mix(A, paper * np.ones_like(A), smooth(-bwl * (.6 + .8 * fray) - .6, -bwl * (.6 + .8 * fray) + .6, sd))
    texR = mix(A, paper * np.ones_like(A), smooth(bwr * (.6 + .8 * fray) + .6, bwr * (.6 + .8 * fray) - .6, sd))
    py = h + .05 * h  # 两半绕撕口底端转开：先从上面裂开，再整个扯走
    piv = (ox + (py - oy) * np.tan(-phi) * 0 + 0, py)

    def mat(sign, p):
        e1 = smooth(0, .45, p); e2 = max(0., (p - .35) / .65) ** 2
        M = cv2.getRotationMatrix2D(piv, sign * (6 * e1 + 12 * e2), 1 + .02 * e1)
        M[0, 2] += -sign * e2 * w * .85; M[1, 2] += e2 * h * .12
        return M

    def step(A, B, p):
        out = B.copy(); lift = smooth(0, .3, p)
        for sign, tex, al in ((-1, texR, alR), (1, texL, alL)):  # 右半张在下，左半张在上
            M = mat(sign, p)
            Ms = M.copy(); Ms[0, 2] += .012 * S * lift; Ms[1, 2] += .022 * S * lift
            shd = blur(cv2.warpAffine(al, Ms, (w, h)), .02 * S + .03 * S * lift) * .45 * lift
            out = out * (1 - shd[..., None])
            out = mix(out, cv2.warpAffine(tex, M, (w, h)), cv2.warpAffine(al, M, (w, h)))
        return out
    return step


@kind("halftone", "网点", "手作", "印刷、波普、漫画、复古海报", "末帧化成印刷网点，网点缩没、再长出首帧的网点，最后还原成首帧", dur=1.0)
def k_halftone(A, B, a):
    h, w = A.shape[:2]; X, Y = pix(h, w)
    c = max(5., min(h, w) / 46)
    th = np.deg2rad(45); ct, st = np.cos(th), np.sin(th)
    ru, rv = X * ct + Y * st, -X * st + Y * ct
    cu, cv_ = (np.floor(ru / c) + .5) * c, (np.floor(rv / c) + .5) * c
    dist = np.hypot(ru - cu, rv - cv_)
    cx, cy = cu * ct - cv_ * st, cu * st + cv_ * ct
    paper = hexrgb(a.color, "#f6f1e6")

    def cells(img):  # 每格取一个颜色；网点面积 = 需要的墨量，网点颜色让一格的平均色还原原色
        col = remap(blur(img, c * .45), cx, cy)
        k = np.clip(1 - col.min(axis=2), .04, 1)
        ink = np.clip(1 - (1 - col) / k[..., None], 0, 1)
        return ink, c * np.sqrt(k / np.pi) * 1.05
    inkA, radA = cells(A); inkB, radB = cells(B)
    u = axis_u(h, w, dir_angle(a, default=np.deg2rad(30)))

    def dots(ink, rad, k):
        return mix(paper * np.ones_like(ink), ink, smooth(rad * k + .7, rad * k - .7, dist))

    def step(A, B, p):
        e = np.clip(p * 1.8 - u * .8, 0, 1)
        HA = dots(inkA, radA, np.clip(1 - (e - .25) / .25, 0, 1))
        HB = dots(inkB, radB, np.clip((e - .5) / .25, 0, 1))
        return np.where((e < .5)[..., None], mix(A, HA, smooth(0, .25, e)), mix(HB, B, smooth(.75, 1, e)))
    return step


@kind("crayon", "蜡笔涂抹", "手作", "儿童画、蜡笔画、手账、童趣插画", "像小孩拿蜡笔来回涂：先是一道道带缝的笔触，再交叉涂满，笔触带着纸纹颗粒", dur=1.2)
def k_crayon(A, B, a):
    h, w = A.shape[:2]; S = min(h, w); W = w / h
    th = np.deg2rad(a.angle if a.angle is not None else -28)
    r1, r2 = .032, .058  # 两遍的笔触半径（以画面高为单位）
    _, sp = scribble_path(W, th, 5, 0, 1, a.seed)
    p1, _ = scribble_path(W, th, 5, sp * .56, r1 * 8, a.seed)  # 第一遍：线和线之间留缝
    _, sp2 = scribble_path(W, th + 1.25, 4, 0, 1, a.seed)
    p2, _ = scribble_path(W, th + 1.25, 4, sp2 * .6, r2 * 3.2, a.seed + 1)  # 第二遍：换个角度交叉涂满
    T1, T2 = path_arrival(h, w, p1, r1, empty=9), path_arrival(h, w, p2, r2, empty=9)
    T = np.minimum(np.where(T1 < 1.01, T1 * .55, 9), np.where(T2 < 1.01, .5 + T2 * .45, 9))
    T[T > 1.01] = 1.0
    n = np.random.default_rng(a.seed + 3).random((h, w)).astype(np.float32)  # 蜡笔在纸纹上的颗粒：顺着笔触方向拉长
    L = max(3, int(S / 60)) | 1; ker = np.zeros((L, L), np.float32)
    cv2.line(ker, (int(L / 2 - np.cos(th) * L / 2), int(L / 2 - np.sin(th) * L / 2)), (int(L / 2 + np.cos(th) * L / 2), int(L / 2 + np.sin(th) * L / 2)), 1, 1)
    tooth = equalize(norm01(cv2.filter2D(blur(n, .7), -1, ker / ker.sum())))

    def step(A, B, p):
        lvl = -.02 + ease(a.ease or "linear", p) * 1.04
        cov = np.clip((lvl - T) / .05, 0, 1) * (.8 + .5 * smooth(.7, 1, p))  # 笔触里留一点纸纹，最后几帧补满
        return mix(A, B, smooth(tooth - .1, tooth + .1, cov))
    return step


# ================= 光与胶片 =================
@kind("sweep", "光扫", "光与胶片", "摄影、产品、风景（--color 给深色时变成云影扫过）", "一道柔光带扫过画面，光带过后已是首帧", dur=.7)
def k_sweep(A, B, a):
    h, w = A.shape[:2]
    T = axis_u(h, w, dir_angle(a, default=np.deg2rad(20))) + (fbm(h, w, a.seed, base=2, octaves=2) - .5) * .05
    col = hexrgb(a.color, "#fff2da")
    dark = float(col.mean()) < .5
    band = .22 if dark else .15
    deco = dict(soft=.07, band=band, ahead=band * 1.8, behind=band * 1.8, color=col,
                blend="multiply" if dark else "screen", strength=.5 if dark else .92)
    return field_step(T, deco, a)


@kind("develop", "显影", "光与胶片", "老照片、胶片、摄影", "画面褪成一张相纸，首帧像照片显影一样从暗部先浮出来", dur=1.0)
def k_develop(A, B, a):
    h, w = A.shape[:2]
    paper = hexrgb(a.color, "#f0e4cc")
    var = (fbm(h, w, a.seed, base=2, octaves=2) - .5) * .2  # 药水不匀：有的地方先显
    dens = lambda img: -np.log(np.clip(img, 1 / 255, 1))
    Db = dens(B)

    def step(A, B, p):
        v = p + var * np.sin(np.pi * p)  # 首尾两端不受不匀影响
        fa = 1 - smooth(0, .55, v); fb = smooth(.4, .92, v)
        img = np.exp(-(dens(A) * fa[..., None] + Db * fb[..., None]))  # 在密度空间里淡出/显影：暗部最先出现、最后消失
        k = smooth(0, .3, p) * (1 - smooth(.7, 1, p))  # 中段褪色偏暖
        img = mix(img, gray(img), k * .85)
        return img * (1 + (paper - 1) * k)
    return step


@kind("iris", "圆窗", "光与胶片", "复古、胶片、漫画、默片", "画面收进一个圆窗里缩没，窗外已是首帧", dur=.6)
def k_iris(A, B, a):
    h, w = A.shape[:2]
    T = 1 - radial(h, w, a.origin)  # 外圈先到 → 圆窗收拢到 origin
    return field_step(T, dict(soft=.004, band=.015, ahead=.02, behind=0, color=hexrgb(a.color, "#111111"), blend="normal", strength=1), a)


@kind("flash", "闪白", "光与胶片", "通用兜底；冲击感强的片子（--color 换闪色）", "闪一下白（或指定颜色）切回首帧", dur=.4)
def k_flash(A, B, a):
    c = hexrgb(a.color, "#ffffff")

    def step(A, B, p):
        if p < .35: return mix(A, c * np.ones_like(A), smooth(0, 1, p / .35))
        return mix(c * np.ones_like(A), B, smooth(0, 1, (p - .35) / .65))
    return step


@kind("leak", "漏光", "光与胶片", "胶片、生活照、旅行、复古、人像", "胶片漏光的暖光从边上漫进来、把画面烧亮，光退去时已是首帧", dur=.9)
def k_leak(A, B, a):
    h, w = A.shape[:2]; rng = np.random.default_rng(a.seed)
    x, y = grid(h, w); W = w / h
    ang = dir_angle(a, default=rng.choice([0, np.pi, np.deg2rad(200), np.deg2rad(-20)]))
    vx, vy = np.cos(ang), np.sin(ang)
    outers = [hexrgb(None, c) for c in ("#ff4a1c", "#ff8a1e", "#ff2f4f")]; core = hexrgb(a.color, "#ffe3a6")
    blobs = []
    for i in range(3):
        cx0 = W / 2 - vx * (W * .75 + rng.uniform(0, .3)); cy0 = .5 - vy * .8 + rng.uniform(-.35, .35)
        blobs.append((cx0, cy0, rng.uniform(.95, 1.4) * (W + 1) * .5, rng.uniform(.45, .8), outers[i]))

    def step(A, B, p):
        I = np.sin(np.pi * p) ** 1.2
        L = np.zeros_like(A)
        for cx0, cy0, sp, rad, oc in blobs:
            cx, cy = cx0 + vx * sp * p * 1.6, cy0 + vy * sp * p * 1.6
            g = np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / rad ** 2)
            L += g[..., None] * mix(oc * np.ones_like(A), core * np.ones_like(A), g ** 8)  # 外圈是橙红，只有芯是亮黄
        base = mix(A, B, smooth(.4, .6, p))
        base = np.clip(base * (1 + .35 * I), 0, 1)
        wash = smooth(.25, .5, p) * (1 - smooth(.5, .75, p)) * .5  # 最亮那几帧整幅泛暖，换图藏在里面
        base = mix(base, mix(core, outers[1], .55) * np.ones_like(A), wash)
        return screen(base, L * I * .85)
    return step


@kind("burn", "胶片烧灼", "光与胶片", "胶片、复古、电影感、暗调", "末帧像卡在放映机里的胶片被烧穿，焦边带着火光往外扩，洞里是首帧", dur=.9)
def k_burn(A, B, a):
    h, w = A.shape[:2]
    T = drops_field(h, w, a, 2, .28, spread=(.15, .3))
    T = equalize(norm01(T + (fbm(h, w, a.seed + 3, base=22, octaves=3) - .5) * .06))
    brown, yel, ora = hexrgb(None, "#6b3a12"), hexrgb(None, "#ffe28a"), hexrgb(None, "#ff6a10")
    S = min(h, w)

    def step(A, B, p):
        q = ease(a.ease or "sine", p)
        d = T - (-.1 + q * 1.24)  # >0：还没烧到
        out = mix(A, B, smooth(-.004, -.014, d))
        scorch = (np.clip(1 - d / .1, 0, 1) * (d > 0)) ** 2 * .8  # 焦黄
        out = out * (1 - scorch[..., None] * (1 - brown))
        out = out * (1 - (np.exp(-((d - .004) / .006) ** 2) * .9)[..., None])  # 焦黑的一圈
        glow = np.exp(-((d + .007) / .007) ** 2) * (.85 + .15 * np.sin(p * 61))  # 火线，微微闪
        out = screen(out, glow[..., None] * yel)
        out = screen(out, blur(glow, S / 40)[..., None] * ora * 1.4)
        over = np.where(d < 0, np.exp(d / .07), 0) * (1 - smooth(.75, 1, p)) * .6  # 刚烧开的地方过曝
        return out + (1 - out) * over[..., None]
    return step


@kind("rewind", "倒带", "光与胶片", "生活记录、Vlog、复古、有情节的片子", "整支片像录像带一样快速倒放回第一帧，带跟踪噪声、扫描线和 ◀◀", dur=1.0, film=True)
def k_rewind(A, B, a):
    h, w = A.shape[:2]; X, Y = pix(h, w); fs = a.frame_paths; N = len(fs)
    def load(i):
        im = a.rd(fs[i])
        return im if im.shape[:2] == (h, w) else cv2.resize(im, (w, h))

    def step(A, B, p):
        img = load(int(round((1 - ease("inout", p)) * (N - 1))))
        I = np.sin(np.pi * p) ** .5
        rng = np.random.default_rng(a.seed * 7919 + int(p * 997))
        yb = ((p * 2.3 + .2) % 1.25 - .1) * h; bh = .09 * h  # 跟踪噪声带，从下往上滚
        band = np.exp(-((Y - yb) / bh) ** 2)
        jit = (fbm_1d(Y / h * 40 + p * 90, a.seed) - .5) * .012 * w + band * (fbm_1d(Y / h * 160 + p * 300, a.seed + 1) - .5) * .09 * w
        img = remap(img, X + jit * I, Y)
        c = int(.004 * w * I) + 1
        img[..., 2] = np.roll(img[..., 2], c, axis=1); img[..., 0] = np.roll(img[..., 0], -c, axis=1)  # 色差
        img = mix(img, gray(img) * np.ones_like(img), .25 * I)
        img = screen(img, (band * (rng.random((h, w)) > .82) * .7 * I).astype(np.float32)[..., None])  # 雪花
        img[::2] *= 1 - .14 * I
        if I > .25:  # 左上角 ◀◀
            u = S0 = min(h, w) * .045; x0, y0 = int(.05 * w), int(.06 * h)
            for k in range(2):
                tri = np.array([[x0 + k * u, y0 + u / 2], [x0 + (k + 1) * u, y0], [x0 + (k + 1) * u, y0 + u]], np.int32)
                cv2.fillPoly(img, [tri + 2], (0, 0, 0)); cv2.fillPoly(img, [tri], (1, 1, 1))
        return img
    return step


# ================= 数字 =================
@kind("dissolve", "像素溶解", "数字", "像素、赛博、UI、游戏", "方块像素按方向溶解，溶解边带一圈亮色", dur=.6)
def k_dissolve(A, B, a):
    h, w = A.shape[:2]
    cs = max(4, int(min(h, w) / 45)); gh, gw = h // cs + 1, w // cs + 1
    g = np.random.default_rng(a.seed).random((gh, gw)).astype(np.float32)
    g = g * .55 + axis_u(gh, gw, dir_angle(a)) * .45
    T = cv2.resize(g, (gw * cs, gh * cs), interpolation=cv2.INTER_NEAREST)[:h, :w]
    return field_step(T, dict(soft=.0, band=.03, ahead=.03, behind=0, color=hexrgb(a.color, "#7cf3ff"), blend="screen", strength=.9), a, eq=False)


@kind("glitch", "故障", "数字", "赛博、潮流、电音、科技、UI", "信号故障：画面错行、RGB 分离、色块乱跳，在抖动里切回首帧", dur=.6)
def k_glitch(A, B, a):
    h, w = A.shape[:2]
    pal = [hexrgb(None, c) for c in ("#00f0ff", "#ff2bd6", "#f4f4f4")]

    def step(A, B, p):
        rng = np.random.default_rng(a.seed * 7919 + int(p * 997))
        I = np.sin(np.pi * p) ** .6
        useB = rng.random() < smooth(.3, .7, p)
        img = (B if useB else A).copy(); other = A if useB else B
        for _ in range(int(3 + 10 * I)):  # 错行
            y0 = int(rng.integers(0, h)); hh = int(rng.integers(2, max(3, h // 9)) * I) + 1
            src = other if rng.random() < .3 else img
            img[y0:y0 + hh] = np.roll(src[y0:y0 + hh], int(rng.normal(0, .07 * w * I)), axis=1)
        c = int(.014 * w * I * (.5 + rng.random())) + 1  # RGB 分离
        img[..., 2] = np.roll(img[..., 2], c, axis=1); img[..., 0] = np.roll(img[..., 0], -c, axis=1)
        for _ in range(int(5 * I)):  # 色块 / 局部马赛克
            bw, bh = int(rng.integers(w // 30, w // 6)), int(rng.integers(h // 40, h // 9))
            x0, y0 = int(rng.integers(0, w - bw)), int(rng.integers(0, h - bh))
            blk = img[y0:y0 + bh, x0:x0 + bw]
            if rng.random() < .5: img[y0:y0 + bh, x0:x0 + bw] = blk * .2 + pal[rng.integers(3)] * .8
            else: img[y0:y0 + bh, x0:x0 + bw] = cv2.resize(cv2.resize(blk, (max(1, bw // 8), max(1, bh // 4)), interpolation=cv2.INTER_AREA), (bw, bh), interpolation=cv2.INTER_NEAREST)
        img[::2] *= 1 - .12 * I
        return mix(img, B, smooth(.82, 1, p))
    return step


@kind("mosaic", "马赛克", "数字", "像素、游戏、UI、科技、波普", "末帧的像素块越变越大，最大时换成首帧，再一格格清晰回来", dur=.7)
def k_mosaic(A, B, a):
    h, w = A.shape[:2]; big = max(8., min(h, w) / 7)

    def px(img, bs):
        if bs < 1.05: return img
        return cv2.resize(cv2.resize(img, (max(1, round(w / bs)), max(1, round(h / bs))), interpolation=cv2.INTER_AREA), (w, h), interpolation=cv2.INTER_NEAREST)

    def step(A, B, p):
        bs = big ** smooth(0, 1, 1 - abs(2 * p - 1))
        k = smooth(.44, .56, p)
        return px(A, bs) if k <= 0 else px(B, bs) if k >= 1 else mix(px(A, bs), px(B, bs), k)
    return step


@kind("crt", "电视关机", "数字", "复古、电视、游戏、Y2K、怀旧", "末帧像老电视关机一样压成一道亮线、缩成光点，再开机亮出首帧", dur=.8)
def k_crt(A, B, a):
    h, w = A.shape[:2]; S = min(h, w); X, Y = pix(h, w)
    vig = 1 - .35 * ((X / w - .5) ** 2 + (Y / h - .5) ** 2) * 2

    def step(A, B, p):
        img, e = (A, p / .5) if p < .5 else (B, (1 - p) / .5)  # e：0 = 正常画面，1 = 完全关掉；开机是关机倒过来
        sy = max(2.5 / h, 1 - smooth(0, .55, e) ** 1.6)
        sx = 1 if e < .55 else max(2 / w, 1 - smooth(.55, .88, e) ** 1.4)
        g = smooth(.25, .6, e) * 2.2
        im = np.clip(img * (1 + g) + g * .25, 0, 1)
        M = np.float32([[sx, 0, w / 2 * (1 - sx)], [0, sy, h / 2 * (1 - sy)]])
        out = cv2.warpAffine(im, M, (w, h), flags=cv2.INTER_AREA if sy < .5 else cv2.INTER_LINEAR, borderValue=0)
        out = out * (1 - smooth(.88, 1, e))
        out = screen(out, blur(out, S / 30) * .8 * smooth(.3, .7, e))
        out[::2] *= 1 - .1 * (1 - e * .5)
        return out * mix(np.ones_like(vig), vig, .6 + .4 * smooth(0, .3, e))[..., None]
    return step


# ================= 动势 =================
@kind("squash", "压扁", "动势", "黏土、3D、Q 版", "整张画被压扁到地面消失，露出首帧", dur=.5)
def k_squash(A, B, a):
    h, w = A.shape[:2]; ones = np.ones((h, w), np.float32)

    def step(A, B, p):
        if p < .3: q = p / .3; sy, sx = 1 + .06 * np.sin(np.pi * q), 1 - .03 * np.sin(np.pi * q)
        else: q = (p - .3) / .7; sy, sx = (1 - q) ** 2.2, 1 + .18 * np.sin(np.pi * min(1, q * 1.2))
        sy = max(sy, .001)
        M = np.float32([[sx, 0, w / 2 * (1 - sx)], [0, sy, h * (1 - sy)]])
        Aw = cv2.warpAffine(A, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
        return mix(B, Aw, cv2.warpAffine(ones, M, (w, h), borderValue=0))
    return step


@kind("shatter", "碎片", "动势", "冲击感、运动、玻璃、科技、潮流海报", "末帧从一点裂开，碎成玻璃片一片片掉下去，露出首帧", dur=1.1)
def k_shatter(A, B, a):
    h, w = A.shape[:2]; S = min(h, w); rng = np.random.default_rng(a.seed); X, Y = pix(h, w)
    ix, iy = a.origin[0] * w, a.origin[1] * h
    pts = [(ix + rng.normal(0, .1 * S), iy + rng.normal(0, .1 * S)) for _ in range(12)] + [(rng.uniform(0, w), rng.uniform(0, h)) for _ in range(26)]
    best = np.full((h, w), np.inf, np.float32); lab = np.zeros((h, w), np.int32)
    for i, (px_, py_) in enumerate(pts):
        d = (X - px_) ** 2 + (Y - py_) ** 2; sel = d < best; best[sel] = d[sel]; lab[sel] = i
    edge = np.zeros((h, w), np.float32)
    edge[:, 1:] += lab[:, 1:] != lab[:, :-1]; edge[1:, :] += lab[1:, :] != lab[:-1, :]
    edge = np.clip(blur(np.clip(edge, 0, 1), .6) * 2.5, 0, 1)  # 裂纹
    rimp = np.hypot(X - ix, Y - iy); rimp /= rimp.max()
    shards = []
    for i in range(len(pts)):
        ys, xs = np.nonzero(lab == i)
        if len(xs) == 0: continue
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        al = (lab[y0:y1, x0:x1] == i).astype(np.float32)
        cx, cy = xs.mean(), ys.mean()
        t0 = .14 + .42 * np.hypot(cx - ix, cy - iy) / np.hypot(w, h) + rng.uniform(0, .1)
        shards.append(dict(box=(x0, y0, x1, y1), al=al, c=(cx - x0, cy - y0), t0=t0, rot=rng.choice([-1, 1]) * rng.uniform(15, 55),
                           drift=(cx - ix) / S * .25 * w, fall=h - y0 + np.hypot(x1 - x0, y1 - y0) * .6 + .04 * h, glint=rng.uniform(0, 6)))

    def step(A, B, p):
        R = smooth(0, .16, p) * 1.05  # 裂纹从撞击点往外爬
        cr = edge * smooth(R, R - .06, rimp)
        Ac = screen(A * (1 - cr[..., None] * .55), (cr * .7)[..., None])
        stat = np.zeros((h, w), np.float32); out = B.copy(); moving = []
        for sd in shards:
            tt = np.clip((p - sd["t0"]) / (1 - sd["t0"]), 0, 1)
            x0, y0, x1, y1 = sd["box"]
            if tt <= 0: stat[y0:y1, x0:x1] += sd["al"]
            else: moving.append((tt, sd))
        out = mix(out, Ac, np.clip(stat, 0, 1))
        for tt, sd in sorted(moving, key=lambda m: -m[0]):  # 掉得远的在下面
            x0, y0, x1, y1 = sd["box"]
            tex = Ac[y0:y1, x0:x1] * (1 + .12 * np.sin(sd["glint"] + tt * 9))  # 转动时反一下光
            M = cv2.getRotationMatrix2D(sd["c"], sd["rot"] * tt, 1 + .12 * tt)
            M[0, 2] += x0 + sd["drift"] * tt; M[1, 2] += y0 + sd["fall"] * tt ** 2
            paste_affine(out, np.clip(tex, 0, 1), sd["al"], M)
        return out
    return step


@kind("zoom", "推拉穿越", "动势", "运动、旅行、城市、潮流、快节奏", "镜头猛推进末帧（带径向模糊），穿过去时已是首帧，再从近处拉回原位", dur=.6)
def k_zoom(A, B, a):
    h, w = A.shape[:2]; cx, cy = a.origin[0] * w, a.origin[1] * h; zmax = 3.4

    def zoomed(img, z, blur_):
        n = 1 if blur_ < .01 else 7; acc = 0
        for i in range(n):
            s_ = z * (1 + blur_ * i / max(1, n - 1))
            acc = acc + cv2.warpAffine(img, np.float32([[s_, 0, cx * (1 - s_)], [0, s_, cy * (1 - s_)]]), (w, h), borderMode=cv2.BORDER_REFLECT)
        return acc / n

    def side(img, e):  # e：0 = 原位，1 = 推到最近
        return zoomed(img, zmax ** (e ** 2.2), .3 * e ** 1.5)

    def step(A, B, p):
        k = smooth(.44, .56, p)
        fa = side(A, min(1, p / .5)) if k < 1 else 0
        fb = side(B, min(1, (1 - p) / .5)) if k > 0 else 0
        out = fa if k <= 0 else fb if k >= 1 else mix(fa, fb, k)
        return screen(out, np.full_like(A, np.exp(-((p - .5) / .07) ** 2) * .3))  # 穿过去那一下微微发亮
    return step


# ---------------- 主流程 ----------------
def table():
    rows = []
    for g in GROUPS:
        for k, m in KINDS.items():
            if m["group"] == g:
                rows.append(f"  {k:<11}{m['zh']:<6}{g:<6}{m['dur']:.1f}s  {m['desc']}（{m['suits']}）")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser(description="复位转场：把片尾送回首帧", epilog="种类：\n" + table(),
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frames", nargs="?"); ap.add_argument("--kind", choices=list(KINDS))
    ap.add_argument("--list", action="store_true", help="列出全部种类"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--dur", type=float, help="转场时长（秒），默认用种类自己的"); ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--mode", choices=["append", "overlay"], default="append"); ap.add_argument("--pre-hold", type=float, default=0)
    ap.add_argument("--dir", default=None, choices=["lr", "rl", "tb", "bt"]); ap.add_argument("--angle", type=float)
    ap.add_argument("--origin", default=".5,.5"); ap.add_argument("--color")
    ap.add_argument("--ease", default=None, help="sine(默认)/inout/in/out/linear：场类转场的推进节奏"); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--strokes", type=int, default=4, help="brush：笔刷道数")
    ap.add_argument("--soft", type=float, help="场类：覆盖默认的前沿柔和度（0..0.2）"); ap.add_argument("--band", type=float, help="场类：覆盖默认的装饰带宽度")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.list:
        if a.json: print(json.dumps({"groups": GROUPS, "kinds": {k: {f: v for f, v in m.items() if f != "make"} for k, m in KINDS.items()}}, ensure_ascii=False, indent=1))
        else: print(table())
        return
    if not a.frames or not a.kind: ap.error("需要 <frames目录> 和 --kind（--list 看种类）")
    a.origin = tuple(float(v) for v in a.origin.split(","))
    meta = KINDS[a.kind]; dur = a.dur if a.dur is not None else meta["dur"]
    fs = sorted(glob.glob(os.path.join(a.frames, "f_*.*")))
    if len(fs) < 2: sys.exit(f"没有帧：{a.frames}")
    ext = os.path.splitext(fs[0])[1]
    out = a.out or a.frames.rstrip("/") + "_loop"
    if os.path.abspath(out) == os.path.abspath(a.frames): sys.exit("--out 不能和输入目录相同")
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    M = max(2, round(dur * a.fps)); H = round(a.pre_hold * a.fps) if a.mode == "append" else 0
    keep = fs if a.mode == "append" else fs[:-M]
    for i, f in enumerate(keep): shutil.copyfile(f, os.path.join(out, f"f_{i:05d}{ext}"))
    rd = lambda f: cv2.imread(f, cv2.IMREAD_COLOR).astype(np.float32) / 255
    a.rd, a.frame_paths = rd, fs
    B = rd(fs[0]); n = len(keep)
    for k in range(H): shutil.copyfile(fs[-1], os.path.join(out, f"f_{n + k:05d}{ext}"))
    n += H
    step = None
    for k in range(M):
        A = rd(fs[-1] if a.mode == "append" else fs[len(fs) - M + k])
        if step is None: step = meta["make"](A, B, a)
        fr = step(A, B, (k + 1) / (M + 1))
        cv2.imwrite(os.path.join(out, f"f_{n + k:05d}{ext}"), (np.clip(fr, 0, 1) * 255 + .5).astype(np.uint8),
                    [cv2.IMWRITE_JPEG_QUALITY, 95] if ext == ".jpg" else [])
    total = n + M
    print(f"{a.kind}: {len(fs)} 帧 → {total} 帧（{total / a.fps:.2f}s，转场 {M} 帧 {dur:.2f}s，定格 {H} 帧）→ {out}")


main()
