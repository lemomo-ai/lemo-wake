#!/usr/bin/env python3
"""Rebuild films.json (data for index.html, the GitHub Pages gallery), thumbs/<id>.jpg (small originals for the
before/after cards; needs Pillow) and README.md from films/*/meta.json. Run from the branch root."""
import json
from pathlib import Path

CATS = [("people", "People & portraits", "人像合影"), ("art", "Paintings & drawings", "绘画作品"),
        ("social", "Social posts & chats", "社交分享"), ("poster", "Posters & ads", "海报广告"),
        ("brand", "Logos & brands", "品牌标志"), ("data", "Charts & reports", "数据图表"),
        ("sticker", "Stickers & greetings", "表情问候"), ("life", "Everyday photos", "生活随拍")]
COLS = 3


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def cell(fid, m):
    d = f"films/{fid}"
    film = next(f"{d}/{n}" for n in ("film.webp", "film.gif") if Path(d, n).exists())
    who = esc(m["author"])
    if m.get("author_url"):
        who = f'<a href="{esc(m["author_url"])}">{who}</a>'
    extra = []
    if Path(d, "source.jpg").exists():
        extra.append(f'<a href="{d}/source.jpg">original</a>')
    if Path(d, "notes.md").exists():
        extra.append(f'<a href="{d}/notes.md">notes</a>')
    extra = (" · " + " · ".join(extra)) if extra else ""
    return (f'<td align="center" valign="top" width="33%"><a href="{film}"><img src="{d}/preview.webp" width="260" '
            f'alt="{esc(m["title"])}"></a><br><b>{esc(m["title"])}</b>'
            + (f'<br><sub>{esc(m["title_en"])}</sub>' if m.get("title_en") and m["title_en"] != m["title"] else "")
            + f'<br><sub>by {who}{extra}</sub></td>')


def make_thumbs(items):
    """thumbs/<id>.jpg: the original at long side 480, for the before/after cards (source.jpg is up to 2 MB)."""
    try:
        from PIL import Image
    except ImportError:
        print("! Pillow missing - thumbs/ not updated")
        return
    Path("thumbs").mkdir(exist_ok=True)
    keep = set()
    for i in items:
        src, out = Path("films") / i["id"] / "source.jpg", Path("thumbs") / f'{i["id"]}.jpg'
        if not src.exists():
            continue
        keep.add(out.name)
        i["thumb"] = f"thumbs/{out.name}"
        with Image.open(src) as im0:
            i["sw"], i["sh"] = im0.size
        if out.exists():          # films are only ever added, so an existing thumb is current
            continue
        im = Image.open(src).convert("RGB")
        im.thumbnail((480, 480), Image.LANCZOS)
        im.save(out, "JPEG", quality=80, optimize=True, progressive=True)
    for f in Path("thumbs").glob("*.jpg"):
        if f.name not in keep:
            f.unlink()


def write_llms(items):
    """llms.txt: a plain summary of the project and gallery for AI assistants and search."""
    names = {k: f"{en} · {zh}" for k, en, zh in CATS}
    lines = ["# lemo-wake", "",
             "> Wake your image. 把你的照片叫醒。 lemo-wake is a Claude Code plugin that turns one still image into a ~5 second "
             "seamlessly looping animation (MP4, GIF, WebP, WeChat sticker GIF) by reading the picture, taking it "
             "apart and re-choreographing it in code. No image generation, no API keys; it runs locally. "
             "把一张图做成约 5 秒、无缝循环的动图的 Claude Code 插件。", "",
             "- Official repository: https://github.com/lemomo-ai/lemo-wake",
             "- Official gallery: https://lemomo-ai.github.io/lemo-wake/",
             "- Install: `/plugin marketplace add lemomo-ai/lemo-wake` then `/plugin install lemo-wake@lemo-wake`",
             "- Commands: `/lemo-wake:wake <image>` makes a film; `/lemo-wake:upload` shares one to the gallery",
             "- License: code CC BY-NC 4.0; gallery films CC BY-NC 4.0 by their authors; no commercial use", "",
             f"## Gallery ({len(items)} films)", ""]
    for i in items:
        t = i["title"] + (f" / {i['title_en']}" if i.get("title_en") and i["title_en"] != i["title"] else "")
        lines.append(f"- [{t}](https://lemomo-ai.github.io/lemo-wake/#{i['id']}): {names.get(i['category'], i['category'])}, by {i['author']}")
    Path("llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    films = {}
    for p in sorted(Path("films").glob("*/meta.json")):
        m = json.loads(p.read_text(encoding="utf-8"))
        films[p.parent.name] = m
    out = ["# lemo-wake gallery", "",
           "Films made with [lemo-wake](https://github.com/lemomo-ai/lemo-wake): one still image in, a ~5 second "
           "seamless loop out. **Browse it as a page: https://lemomo-ai.github.io/lemo-wake/** (or click a film below).", "",
           "用 lemo-wake 做的动图：一张静态图进去，一支约 5 秒、无缝循环的动图出来。网页版：https://lemomo-ai.github.io/lemo-wake/", "",
           f"**{len(films)} films.** Share yours with `/lemo-wake:upload` - see [CONTRIBUTING.md](CONTRIBUTING.md). "
           "Films are licensed by their authors under [CC BY-NC 4.0](LICENSE).", "",
           "Official repository · 官方仓库: https://github.com/lemomo-ai/lemo-wake · "
           "Official gallery · 官方作品墙: https://lemomo-ai.github.io/lemo-wake/", ""]
    toc = []
    for key, en, zh in CATS:
        ids = sorted((i for i, m in films.items() if m["category"] == key),
                     key=lambda i: (films[i].get("order", 9999), films[i].get("created", ""), i))
        if not ids:
            continue
        toc.append(f"[{en}](#{key})")
        out += [f'<h2 id="{key}">{en} · {zh} <sub>({len(ids)})</sub></h2>', "", "<table>"]
        for r in range(0, len(ids), COLS):
            out.append("<tr>" + "".join(cell(i, films[i]) for i in ids[r:r + COLS]) + "</tr>")
        out += ["</table>", ""]
    out.insert(10, " · ".join(toc) + "\n")
    Path("README.md").write_text("\n".join(out), encoding="utf-8")

    order = {k: n for n, (k, _, _) in enumerate(CATS)}
    items = []
    for fid, m in films.items():
        d = Path("films") / fid
        items.append({
            "id": fid, "title": m["title"], "title_en": m.get("title_en", ""), "category": m["category"], "author": m["author"],
            "author_url": m.get("author_url", ""), "width": m.get("width"), "height": m.get("height"),
            "seconds": m.get("seconds"), "created": m.get("created", ""), "sample": bool(m.get("sample")),
            "film": next(n for n in ("film.webp", "film.gif") if (d / n).exists()),
            "source": (d / "source.jpg").exists(), "notes": (d / "notes.md").exists(),
            "bytes": next((d / n).stat().st_size for n in ("film.webp", "film.gif") if (d / n).exists()),
        })
    # community films first (newest first), then the samples in category order
    community = sorted((i for i in items if not i["sample"]), key=lambda i: (i["created"], i["id"]), reverse=True)
    samples = sorted((i for i in items if i["sample"]), key=lambda i: (order.get(i["category"], 99), i["id"]))
    items = community + samples
    make_thumbs(items)
    data = {"categories": [{"key": k, "en": en, "zh": zh} for k, en, zh in CATS], "films": items}
    Path("films.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    write_llms(items)
    print(f"README.md + films.json + llms.txt: {len(films)} films")


if __name__ == "__main__":
    main()
