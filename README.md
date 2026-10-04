<div align="center">

# lemo-wake

**把你的照片叫醒**<br>
**Wake your image.**

一张图进去，一段约 5 秒、无缝循环的动图出来。<br>
One picture in, a seamless loop of about five seconds out.

<img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/assets/readme/cover.webp" width="100%" alt="lemo-wake: one picture in, a seamless loop out">

[**▶ 去作品墙看看 See the gallery**](https://lemomo-ai.github.io/lemo-wake/)

**English** | [中文](README.zh-CN.md)

![version](https://img.shields.io/badge/version-1.0.0-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-d97757)

</div>

> **中文用户请看这里：[完整中文说明 README.zh-CN.md](README.zh-CN.md)**<br>
> English readers: keep reading below.

## What it does 它做什么

Give Claude Code one picture and say "make it move". You get a loop of about 5 seconds whose end joins its start seamlessly. Photos, portraits, posters, illustrations, logos, charts, stickers, Xiaohongshu covers and chat screenshots all work.

It is not a filter. Claude first reads the image, takes it apart into text, shapes, objects, people and light, rebuilds the pieces in code and choreographs a short film for this one picture. It then renders the frames in a headless browser, joins the end back to the start and encodes the result.

- **No image generation.** Everything comes from your picture, from code and from small local models.
- **No API keys.** No cloud services. Everything runs on your machine.
- **Same size.** Every film keeps your image's exact pixel size and aspect ratio.

**中文简介**

把一张图交给 Claude Code，说一句“让它动起来”，就能拿到一段约 5 秒、首尾无缝相接的动图。照片、人像、海报、插画、Logo、图表、表情包、小红书封面、聊天截图都可以。

这不是套滤镜。Claude 会先读懂画面，把文字、图形、物体、人物和光拆开，用代码重建，再为这张图编排一段专属的动作。最后在无头浏览器里逐帧渲染，把结尾接回开头，编码出片。

- **不生图**：素材只来自你的图、代码和本地小模型。
- **不用 API key**：不连云服务，全部在你的电脑上完成。
- **同尺寸**：成片和原图的像素尺寸、比例完全一致。

## Install

As a Claude Code plugin (recommended):

```
/plugin marketplace add lemomo-ai/lemo-wake
/plugin install lemo-wake@lemo-wake
```

As a plain skill (without the upload command):

```bash
git clone --depth 1 https://github.com/lemomo-ai/lemo-wake
cp -R lemo-wake/skills/wake ~/.claude/skills/lemo-wake
```

You can also put it in a project's `.claude/skills/lemo-wake`.

## Use

Give Claude an image and say "make it move". No command needed. Or use the commands:

| Command | What it does |
|---|---|
| `/lemo-wake:wake <image>` | Make a film from an image |
| `/lemo-wake:upload` | Share a film to the gallery |

With a plain skill install, the command is `/lemo-wake <image>`.

## What you get

Every film comes as four files, all made from the same frames:

| File | Size | For |
|---|---|---|
| `<name>.mp4` | Original size, no audio | Posts on WeChat Moments, Xiaohongshu, Douyin, Instagram, X |
| `<name>.gif` | At most 5 MB, under 1080 wide | Chats on WeChat, QQ, Weibo |
| `<name>.webp` | Original size, about 8 MB | Web pages, GitHub, galleries |
| `<name>-sticker.gif` | Long side 240 px, at most 500 KB | A WeChat custom sticker |

Why four: most chat apps and phone galleries don't play animated WebP, social platforms want MP4 for posts, and GIF works everywhere but is heavy. If a platform has another limit, such as "GIF under 2 MB", tell Claude.

Photos with a long side over 2560 px are scaled to 2560 first to keep rendering fast. Ask for full resolution if you need it.

## First run

On first use Claude runs `node scripts/doctor.mjs` in the skill folder (`skills/wake/`). With `--fix` it installs what is missing.

| Needs | Size | How |
|---|---|---|
| Node.js 18 or later | | Install it yourself |
| ffmpeg and ffprobe | | `brew install ffmpeg`, `sudo apt install ffmpeg` or `winget install Gyan.FFmpeg` |
| uv (runs the Python scripts) | | `brew install uv`, or see https://docs.astral.sh/uv/ |
| Headless Chromium and `playwright-core` | About 190 MB | `node scripts/doctor.mjs --fix`, or use an installed Chrome with `CHROME=<path>` |
| Python packages (Pillow, NumPy, OpenCV, onnxruntime) | About 150 MB | Downloaded automatically on first use |

Tested on macOS. Linux and Windows should work. If a step fails, Claude works out what is missing.

## Local models (optional)

Some images benefit from small models that run locally on the CPU. **A model is downloaded only when a film needs it**, after you say yes once. Many films use none.

| Model | What it does | Size | Source | License |
|---|---|---|---|---|
| Depth Anything V2 Small | Depth map for 3D parallax | 99 MB | [onnx-community/depth-anything-v2-small](https://huggingface.co/onnx-community/depth-anything-v2-small) | Apache-2.0 |
| BiRefNet-lite | Cuts out the main subject | 224 MB | [onnx-community/BiRefNet_lite-ONNX](https://huggingface.co/onnx-community/BiRefNet_lite-ONNX) | MIT |
| MODNet | Portrait matting with fine hair | 26 MB | [Xenova/modnet](https://huggingface.co/Xenova/modnet) | Apache-2.0 |
| MobileSAM (2 files) | Picks one element by point or box | 44 MB | [Acly/MobileSAM](https://huggingface.co/Acly/MobileSAM) | MIT |
| LaMa | Fills the hole behind a moved object | 208 MB | [Carve/LaMa-ONNX](https://huggingface.co/Carve/LaMa-ONNX) | Apache-2.0 |

About 600 MB in all. Every file is checked by sha256.

**Asked once.** The first time a film needs a model, Claude tells you which one, what it is for, how big it is, where it comes from and where it will be stored, and asks once. Your answer is saved. If you say no, Claude finds a compromise in code and still finishes the film.

**Where they are stored.** With a plugin install, in `~/.claude/plugins/data/<plugin-id>/models/`, kept across updates and removed on uninstall. With a plain skill install, in `models/` in the skill folder. Set `LEMO_WAKE_MODELS=<folder>` to use another folder.

**Commands.** Run them in `skills/wake/`, or just ask Claude:

```bash
scripts/models.py                     # status
scripts/models.py fetch all --yes     # download everything now
scripts/models.py consent yes|no      # change your answer
```

## Mainland China

Hugging Face is often unreachable from mainland China. Use the mirror. Files are still checked against the same sha256:

```bash
HF_ENDPOINT=https://hf-mirror.com scripts/models.py fetch all --yes
```

To use the mirror for every download, add it to `~/.claude/settings.json`:

```json
{ "env": { "HF_ENDPOINT": "https://hf-mirror.com" } }
```

If a download fails, Claude also tries a mirror on its own. For other slow downloads:

- Python packages: `UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple`
- npm: `npm config set registry https://registry.npmmirror.com`
- Headless browser: an installed Google Chrome works too, with `CHROME=<path>`
- Models by hand: download them from the links above, rename them to `depth_anything_v2_small.onnx`, `birefnet_lite.onnx`, `modnet.onnx`, `mobile_sam_image_encoder.onnx`, `sam_mask_decoder_multi.onnx` and `lama_fp32.onnx`, and put them in the models folder

## Community

The gallery is not only for our samples. You are welcome to add your own films. Community films sit on the same wall as the samples, with an orange "Community" badge in the corner of the card and the author's name. The gallery also has a "Community" filter that shows only shared films.

**How to share**

1. Make a film you like with the plugin and run `/lemo-wake:upload`. This command is only available with a plugin install.
2. Claude checks the film (animated WebP or GIF, at most 8 MB) and makes a small preview. It asks for a title, a category and a credit, and whether to include the original image and notes. The original is saved without location, camera or date information.
3. Claude shows you everything that will be published. Only after your yes does it open a pull request from your own GitHub account. You need the [GitHub CLI](https://cli.github.com), logged in with `gh auth login`.
4. After an automatic check and a maintainer's review, the film appears in the [gallery](https://lemomo-ai.github.io/lemo-wake/).

**Rules**

- Only share images you have the rights to, such as your own photo, your own artwork or an image you are allowed to share. If other people are in a photo, ask them first.
- No private details, such as other people's faces, names, phone numbers, addresses, chat contents, documents or licence plates.
- Films are published under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/): others may share and adapt them with credit, but not for commercial use. By sharing, you agree that the project may show your film in this README, the gallery and posts about the project.
- Films always go to the official repository, even if you installed the plugin from a fork or a copy.
- To remove your film, open an issue or a pull request that deletes its folder.

Full rules: [CONTRIBUTING.md](https://github.com/lemomo-ai/lemo-wake/blob/gallery/CONTRIBUTING.md).

## License

- Code and docs: [MIT](LICENSE).
- Gallery films, including samples, community films and any originals shown with them, are licensed by their authors under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/): attribution, non-commercial.
- Local models are downloaded from their own sources and used under their own licenses. They are not part of this repository.

Versions: [CHANGELOG.md](CHANGELOG.md).

## About

lemo-wake is made by [Lemomo](https://github.com/lemomo-ai) together with Claude. The official repository is https://github.com/lemomo-ai/lemo-wake and the official gallery is https://lemomo-ai.github.io/lemo-wake/. Forks and copies are welcome under the license. Please keep a link back here.

If you use lemo-wake in your work, you can cite it with [CITATION.cff](CITATION.cff).

## Examples

One film from each category, original on the left and film on the right. See the [gallery](https://lemomo-ai.github.io/lemo-wake/) for more.

<table>
<tr>
<td align="center" valign="top" width="50%"><b>绘画作品</b> Paintings<br><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/thumbs/s10-crayon.jpg" height="112" alt="Crayon drawing, original"> <img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/films/s10-crayon/preview.webp" height="112" alt="Crayon drawing, animated"><br><sub>小孩蜡笔画 彩虹落地<br>A child's crayon drawing, the rainbow lands</sub></td>
<td align="center" valign="top" width="50%"><b>海报广告</b> Posters<br><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/thumbs/paris.jpg" height="112" alt="Paris poster, original"> <img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/films/paris/preview.webp" height="112" alt="Paris poster, animated"><br><sub>巴黎 套印合拢<br>Paris, the print plates snap into register</sub></td>
</tr>
<tr>
<td align="center" valign="top" width="50%"><b>人像合影</b> People<br><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/thumbs/h02-picnic.jpg" height="112" alt="Cherry-blossom picnic, original"> <img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/films/h02-picnic/preview.webp" height="112" alt="Cherry-blossom picnic, animated"><br><sub>樱花野餐 打开就跳出来<br>Cherry-blossom picnic, pops up as it opens</sub></td>
<td align="center" valign="top" width="50%"><b>生活随拍</b> Everyday<br><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/thumbs/s03-breakfast.jpg" height="112" alt="Breakfast by the window, original"> <img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/films/s03-breakfast/preview.webp" height="112" alt="Breakfast by the window, animated"><br><sub>窗边早餐 早餐蹦蹦<br>Breakfast by the window, breakfast hops</sub></td>
</tr>
<tr>
<td align="center" valign="top" width="50%"><b>社交分享</b> Social<br><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/thumbs/x02-reading.jpg" height="200" alt="52 books in a year, original"> <img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/films/x02-reading/preview.webp" height="200" alt="52 books in a year, animated"><br><sub>一年读完 52 本书 书飞进数字<br>52 books in a year, books fly into the number</sub></td>
<td align="center" valign="top" width="50%"><b>数据图表</b> Charts<br><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/thumbs/d05-island.jpg" height="200" alt="An island's four seasons, original"> <img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/films/d05-island/preview.webp" height="200" alt="An island's four seasons, animated"><br><sub>海岛的一年四季 太阳跳过一年<br>An island's four seasons, the sun hops through the year</sub></td>
</tr>
<tr>
<td align="center" valign="top" width="50%"><b>品牌标志</b> Logos<br><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/thumbs/b07-moongroove.jpg" height="180" alt="Moon Groove logo, original"> <img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/films/b07-moongroove/preview.webp" height="180" alt="Moon Groove logo, animated"><br><sub>Moon Groove Records 月亮落针<br>Moon Groove Records, the moon drops the needle</sub></td>
<td align="center" valign="top" width="50%"><b>表情问候</b> Stickers<br><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/thumbs/e03-duck.jpg" height="180" alt="Go duck sticker, original"> <img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/films/e03-duck/preview.webp" height="180" alt="Go duck sticker, animated"><br><sub>冲鸭 冲出去再冲回来<br>Go, duck! Dash out and dash back</sub></td>
</tr>
</table>

