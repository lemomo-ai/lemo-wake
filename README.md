<div align="center">

# lemo-wake

**Wake your image. · 把你的照片叫醒**

Turn one picture into a ~5 second seamless loop, right inside Claude Code.<br>
在 Claude Code 里，把一张图做成约 5 秒、无缝循环的动图。

![version](https://img.shields.io/badge/version-1.0.0-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-d97757)

[Gallery · 作品墙](https://lemomo-ai.github.io/lemo-wake/) · [Install · 安装](#install--安装) · [Share · 投稿](#share-your-film--投稿)

<sub>Official repository · 官方仓库：<a href="https://github.com/lemomo-ai/lemo-wake">github.com/lemomo-ai/lemo-wake</a></sub>

</div>

<table>
<tr><th>Before · 原图</th><th>After · 动图</th></tr>
<tr><td><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/thumbs/s03-breakfast.jpg" width="380" alt="Breakfast by the window, original"></td><td><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/films/s03-breakfast/preview.webp" width="380" alt="Breakfast by the window, animated"></td></tr>
<tr><td colspan="2" align="center"><sub>Breakfast hops off the plates and lands back · 早餐蹦出盘子，再一个个落回来</sub></td></tr>
<tr><td><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/thumbs/paris.jpg" width="380" alt="Paris poster, original"></td><td><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/films/paris/preview.webp" width="380" alt="Paris poster, animated"></td></tr>
<tr><td colspan="2" align="center"><sub>The print plates snap into register · 分色版一下合拢套准</sub></td></tr>
<tr><td><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/thumbs/s10-crayon.jpg" width="380" alt="Crayon drawing, original"></td><td><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/films/s10-crayon/preview.webp" width="380" alt="Crayon drawing, animated"></td></tr>
<tr><td colspan="2" align="center"><sub>A child's crayon rainbow lands · 蜡笔彩虹落到地上</sub></td></tr>
</table>

<p align="center">44 sample films in 11 kinds of images: <a href="https://lemomo-ai.github.io/lemo-wake/">see the gallery</a> · 11 类图片、44 支样片：<a href="https://lemomo-ai.github.io/lemo-wake/">去作品墙看看</a></p>

## What it does · 它做什么

Give Claude Code one picture - a photo, portrait, poster, illustration, logo, chart, sticker, Xiaohongshu cover or chat screenshot - and say "make it move". It is not a filter: Claude reads the image, takes it apart (text, shapes, objects, people, light), rebuilds the pieces in code and choreographs a short film that belongs to this one picture. It then renders the frames in a headless browser, joins the end back to the start and encodes the result.

把一张图交给 Claude Code（照片、人像、海报、插画、Logo、图表、表情包、小红书封面、聊天截图都行），说一句"让它动起来"。这不是套滤镜：Claude 会读懂画面，把文字、图形、物体、人物和光拆开，用代码重建，再为这张图编排一段专属的动作；然后在无头浏览器里逐帧渲染，把结尾接回开头，最后编码出片。

- **No image generation · 不生图** - everything comes from your picture, from code and from small local models. 素材只来自你的图、代码和本地小模型。
- **No API keys · 不用 API key** - no cloud services; everything runs on your machine. 不连云服务，全部在你的电脑上完成。
- **Same size · 同尺寸** - every film keeps your image's exact pixel size and aspect ratio. 成片和原图尺寸、比例完全一致。

## Install · 安装

**As a Claude Code plugin (recommended) · 作为 Claude Code 插件安装（推荐）**

```
/plugin marketplace add lemomo-ai/lemo-wake
/plugin install lemo-wake@lemo-wake
```

**As a plain skill (no upload command) · 作为普通 skill 安装（没有投稿命令）**

```bash
git clone --depth 1 https://github.com/lemomo-ai/lemo-wake
cp -R lemo-wake/skills/wake ~/.claude/skills/lemo-wake      # or .claude/skills/lemo-wake in a project
```

## Use · 使用

Give Claude an image and say "make it move" - no command needed. Or use the commands:

把图给 Claude，说"让它动起来"就行，不用记命令。也可以直接用命令：

| Command · 命令 | What it does · 作用 |
|---|---|
| `/lemo-wake:wake <image>` | Make a film from an image · 把一张图做成动图 |
| `/lemo-wake:upload` | Share a film to the gallery · 把动图投稿到作品墙 |

With a plain-skill install the command is `/lemo-wake <image>`. 普通 skill 安装时，命令是 `/lemo-wake <图片>`。

## What you get · 你会拿到什么

Every film comes as four files, all from the same frames · 每支片子交付 4 个文件，来自同一组画面：

| File · 文件 | Size · 尺寸 | For · 用途 |
|---|---|---|
| `<name>.mp4` | original size, no audio · 原图尺寸，无声 | posts: WeChat Moments, Xiaohongshu, Douyin, Instagram, X · 发朋友圈、小红书、抖音、Instagram、X |
| `<name>.gif` | ≤ 5 MB, width < 1080 · ≤ 5MB，宽 < 1080 | chats: WeChat, QQ, Weibo · 发微信、QQ 聊天和微博 |
| `<name>.webp` | original size, ~8 MB target · 原图尺寸，目标约 8MB | web pages, GitHub, galleries · 网页、GitHub、作品墙 |
| `<name>-sticker.gif` | long side 240 px, ≤ 500 KB · 长边 240，≤ 500KB | WeChat custom sticker · 拖进微信直接存成表情 |

Why four: most chat apps and phone galleries don't play animated WebP, social platforms want MP4 for posts, and GIF works everywhere but is heavy. Tell Claude if a platform has another limit (e.g. "GIF under 2 MB"). Photos with a long side over 2560 px are scaled to 2560 first to keep rendering fast; ask for full resolution if you need it.

为什么是 4 个：多数聊天软件和手机相册不播放动态 WebP，社交平台发帖要 MP4，GIF 哪里都能放但体积大。某个平台有别的限制（比如"GIF 要小于 2MB"）直接告诉 Claude。长边超过 2560 像素的照片会先缩到 2560 以保证渲染速度，需要原分辨率可以说一声。

## First run · 第一次使用

On first use Claude runs `node scripts/doctor.mjs` in the skill folder (`skills/wake/`); with `--fix` it installs what is missing. 第一次使用时 Claude 会在 skill 文件夹里运行自检，`--fix` 会补装缺的东西。

| Needs · 需要 | Size · 大小 | How · 怎么装 |
|---|---|---|
| Node.js ≥ 18 | - | install it yourself · 自己安装 |
| ffmpeg (+ ffprobe) | - | `brew install ffmpeg` / `sudo apt install ffmpeg` / `winget install Gyan.FFmpeg` |
| uv (runs the Python scripts · 运行 Python 脚本) | - | `brew install uv` / https://docs.astral.sh/uv/ |
| headless Chromium + `playwright-core` · 无头浏览器 | ~190 MB | `node scripts/doctor.mjs --fix` (or an installed Chrome: `CHROME=<path>` · 也可以用已装的 Chrome) |
| Python packages · Python 包 (Pillow, NumPy, OpenCV, onnxruntime) | ~150 MB | automatic on first use · 首次使用自动下载 |

Tested on macOS. Linux and Windows should work; if a step fails, Claude works out what is missing. 在 macOS 上测试过；Linux 和 Windows 应该也能用，哪一步出错 Claude 会自己排查。

## Local models (optional) · 本地模型（可选）

Some images benefit from small models that run locally on the CPU. They are **downloaded only when a film needs one**, after you say yes once. Many films use none.

有些图会用到在本机 CPU 上运行的小模型。**只有某支片子真的需要时才下载**，并且只在第一次问你一次。很多片子一个都用不到。

| Model · 模型 | What it does · 作用 | Size · 大小 | Source · 来源 | License · 授权 |
|---|---|---|---|---|
| Depth Anything V2 Small | depth map for 3D parallax · 景深，做立体视差 | 99 MB | [onnx-community/depth-anything-v2-small](https://huggingface.co/onnx-community/depth-anything-v2-small) | Apache-2.0 |
| BiRefNet-lite | cuts out the main subject · 抠出主体 | 224 MB | [onnx-community/BiRefNet_lite-ONNX](https://huggingface.co/onnx-community/BiRefNet_lite-ONNX) | MIT |
| MODNet | portrait matting, fine hair · 人像抠图，保留发丝 | 26 MB | [Xenova/modnet](https://huggingface.co/Xenova/modnet) | Apache-2.0 |
| MobileSAM (2 files · 2 个文件) | picks one element by point or box · 点选单个元素 | 44 MB | [Acly/MobileSAM](https://huggingface.co/Acly/MobileSAM) | MIT |
| LaMa | fills the hole behind a moved object · 补上物体移走后的空洞 | 208 MB | [Carve/LaMa-ONNX](https://huggingface.co/Carve/LaMa-ONNX) | Apache-2.0 |

About 600 MB in all, every file checked by sha256. 合计约 600MB，每个文件都核对 sha256。

- **Asked once · 只问一次** - the first time a film needs a model, Claude tells you which one, what for, how big, from where and where it goes, and asks once. Your answer is saved and never asked again. If you say no, Claude finds a compromise with code and still finishes the film. 第一次需要模型时，Claude 会说明下哪个、干什么、多大、从哪下、存哪里，只问这一次，答案会记住。不同意也没关系，Claude 会用代码想办法折中，照样把片子做完。
- **Stored in · 存在哪** - plugin install: `~/.claude/plugins/data/<plugin-id>/models/` (kept across updates, removed on uninstall); plain skill: `models/` in the skill folder; override with `LEMO_WAKE_MODELS=<folder>`. 插件安装存在插件数据目录（更新保留、卸载删除）；普通 skill 存在 skill 文件夹的 `models/`；也可以用环境变量指定。
- **Commands · 命令** (in `skills/wake/`, or just ask Claude · 在 `skills/wake/` 里运行，或者直接让 Claude 做):

```bash
scripts/models.py                     # status · 状态
scripts/models.py fetch all --yes     # download everything now · 现在全部下载
scripts/models.py consent yes|no      # change your answer · 改主意
```

## Mainland China · 中国大陆用户

Hugging Face is often unreachable from mainland China. Use the mirror; files are still checked against the same sha256. Hugging Face 在国内常常连不上，用镜像即可，sha256 校验不变：

```bash
HF_ENDPOINT=https://hf-mirror.com scripts/models.py fetch all --yes
```

To use the mirror for every download, add it to `~/.claude/settings.json` · 想让所有下载都走镜像，加到 Claude Code 设置里：

```json
{ "env": { "HF_ENDPOINT": "https://hf-mirror.com" } }
```

If a download fails, Claude also tries a mirror on its own. Other slow downloads · 其他下载慢的情况：
- Python packages · Python 包: `UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple`
- npm: `npm config set registry https://registry.npmmirror.com`
- Headless browser · 无头浏览器: an installed Google Chrome works too · 本机装的 Chrome 也能用 (`CHROME=<path>`)
- Models by hand · 手动下载模型: put the files from the links above into the models folder as `depth_anything_v2_small.onnx`, `birefnet_lite.onnx`, `modnet.onnx`, `mobile_sam_image_encoder.onnx`, `sam_mask_decoder_multi.onnx`, `lama_fp32.onnx` · 从上表链接下载，按这些文件名放进模型文件夹

## Share your film · 投稿

Made something you like? Run `/lemo-wake:upload` (plugin install). Claude checks the film (animated WebP or GIF, at most 8 MB), makes a small preview, asks for a title, category and credit, and whether to include the original (saved without location or other metadata) and notes. It shows you exactly what will be published, and only after your yes opens a pull request from **your own GitHub account** (needs the [GitHub CLI](https://cli.github.com), logged in with `gh auth login`). After an automatic check and a maintainer's review, it appears in the [gallery](https://lemomo-ai.github.io/lemo-wake/).

做得满意就运行 `/lemo-wake:upload`（插件安装）。Claude 会检查片子（动态 WebP 或 GIF，≤ 8MB）、做一张小预览，问你标题、类别和署名，以及要不要附原图（会去掉位置等元数据）和制作笔记；把要公开的内容全部给你看，你点头后才用**你自己的 GitHub 账号**提一个 PR（需要装好 [GitHub CLI](https://cli.github.com) 并 `gh auth login`）。自动检查通过、维护者审核合并后，就会出现在[作品墙](https://lemomo-ai.github.io/lemo-wake/)。

Only share images you have the rights to, and ask the people in a photo first. 只投你有权分享的图；照片里有别人，先问过他们。

## License · 授权

- Code and docs: [MIT](LICENSE). 代码和文档：MIT。
- Gallery films (samples, community films and any originals shown with them): [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) by their authors; submitting also means the project may show the film in this README, the gallery and posts about the project. 作品墙里的片子（样片、社区投稿和附带的原图）按 CC BY-NC 4.0 授权（署名、非商业）；投稿即同意项目在 README、作品墙和项目宣传中展示。
- Local models are downloaded from their own sources under their own licenses (see the table above); they are not part of this repository. 本地模型从各自来源下载、按各自授权使用，不在本仓库里。

Versions · 版本记录: [CHANGELOG.md](CHANGELOG.md)

## About · 关于

lemo-wake is made by [Lemomo](https://github.com/lemomo-ai). The official repository is **https://github.com/lemomo-ai/lemo-wake** and the official gallery is **https://lemomo-ai.github.io/lemo-wake/**. Forks and copies are welcome under the license; please keep a link back here. Films shared with `/lemo-wake:upload` always go to the official gallery, wherever the plugin was installed from.

lemo-wake 由 [Lemomo](https://github.com/lemomo-ai) 制作。官方仓库是 **https://github.com/lemomo-ai/lemo-wake**，官方作品墙是 **https://lemomo-ai.github.io/lemo-wake/**。欢迎在授权范围内 fork 和转载，请保留指向这里的链接。无论从哪里安装，用 `/lemo-wake:upload` 投稿的片子都会进入官方作品墙。

If you use lemo-wake in your work, you can cite it with [CITATION.cff](CITATION.cff). 在作品或文章里用到 lemo-wake，可以按 CITATION.cff 引用。
