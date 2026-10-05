<div align="center">

# lemo-wake

**把你的照片叫醒**<br>
**Wake your image.**

一张图进去，一段约 5 秒、无缝循环的动图出来。<br>
One picture in, a seamless loop of about five seconds out.

<img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/assets/readme/cover.webp" width="100%" alt="lemo-wake: one picture in, a seamless loop out">

[**▶ 去作品墙看看 See the gallery**](https://lemomo-ai.github.io/lemo-wake/)

[English](README.md) | **中文**

![version](https://img.shields.io/badge/version-1.1.0-blue) ![license](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey) ![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-d97757)

</div>

> **English readers: see [README.md](README.md) for the full English guide.**<br>
> 中文用户：往下看就是完整的中文说明。

## 它做什么 What it does

把一张图交给 Claude Code，说一句“让它动起来”，就能拿到一段约 5 秒、首尾无缝相接的动图。照片、人像、海报、插画、Logo、图表、表情包、小红书封面、聊天截图都可以。

这不是套滤镜。Claude 会先读懂画面，把文字、图形、物体、人物和光拆开，用代码重建，再为这张图编排一段专属的动作。最后在无头浏览器里逐帧渲染，把结尾接回开头，编码出片。

- **不生图**：素材只来自你的图、代码和本地小模型。
- **不用 API key**：不连云服务，全部在你的电脑上完成。
- **尺寸和格式你来选**：开始前问一次，保持原图尺寸还是换个比例，要哪几种格式。

**English overview**

Give Claude Code one picture and say "make it move". You get a loop of about 5 seconds whose end joins its start seamlessly. Photos, portraits, posters, illustrations, logos, charts, stickers, Xiaohongshu covers and chat screenshots all work.

It is not a filter. Claude first reads the image, takes it apart into text, shapes, objects, people and light, rebuilds the pieces in code and choreographs a short film for this one picture. It then renders the frames in a headless browser, joins the end back to the start and encodes the result.

- **No image generation.** Everything comes from your picture, from code and from small local models.
- **No API keys.** No cloud services. Everything runs on your machine.
- **Your size, your formats.** It asks once: keep your image's size or pick another ratio, and which formats you want.

**流程 How it works**

<p align="center"><img src="https://github.com/lemomo-ai/lemo-wake/raw/gallery/assets/readme/flow-zh.webp" width="100%" alt="流程：一张图，Claude 读图、拆开、用代码重建并让它动起来、逐帧渲染、自检接缝，最后拿到你选的格式：默认是发帖用的 MP4 和聊天用的 GIF，WebP、微信表情 GIF 和实况照片要了才出"></p>

## 安装

为 Claude Code 设计和调校。其他 agent（比如 Codex）也能读这个 skill，但不保证效果。

作为 Claude Code 插件安装（推荐）。在终端里运行（两行可以一起粘贴）：

```bash
claude plugin marketplace add lemomo-ai/lemo-wake
claude plugin install lemo-wake@lemo-wake
```

或者在 Claude Code 里输入，**一次一行**，第一行跑完再输第二行：

```
/plugin marketplace add lemomo-ai/lemo-wake
/plugin install lemo-wake@lemo-wake
```

装好后重启 Claude Code，或者运行 `/reload-plugins`。

作为普通 skill 安装（没有投稿和图层命令）：

```bash
git clone --depth 1 https://github.com/lemomo-ai/lemo-wake
cp -R lemo-wake/skills/wake ~/.claude/skills/lemo-wake
```

也可以放进项目里的 `.claude/skills/lemo-wake`。

## 使用

把图给 Claude，说“让它动起来”就行，不用记命令。也可以直接用命令：

| 命令 | 作用 |
|---|---|
| `/lemo-wake:wake <图片>` | 把一张图做成动图 |
| `/lemo-wake:layers <图片>` | 把一张图拆成图层（PSD + PNG） |
| `/lemo-wake:upload` | 把动图投稿到作品墙 |

普通 skill 安装时，命令是 `/lemo-wake <图片>`。

**拆图层。** 用 `/lemo-wake:layers`，或者直接说“拆成图层”“给我 PSD”：每个人、每个物件、每块文字各占一个透明图层，后面的背景补干净，再附一张景深图。你会拿到 `layers.psd`（Photoshop、Affinity、Procreate 都能打开，也可以在浏览器里用免费的 Photopea）、按大小裁好的 PNG 图层，以及记录位置和叠放顺序的 `layers.json`（方便导入 After Effects、Figma、游戏引擎）。人物整体保留，文字是像素不是可编辑文字；因为不生成新内容，被大面积遮住的地方补出来会偏糊。做过动图的图，也能直接复用里面已经抠好的零件。

能拆得多干净取决于图片本身，所以分层效果不作保证。哪里不满意，直接告诉 agent 你想怎么改就行，比如“把两个人分成两层”“花和花瓶放在一起”“头发边缘再修干净一点”，它会重做那一部分。

## 你会拿到什么

开始前 Claude 会问一次：要多大（默认和原图一样，也可以选 16:9、9:16、1:1 等比例），要哪几种格式。直接说“开始”就用默认。所有格式都来自同一组画面，做完还能追加，不用重新渲染。

| 文件 | 默认 | 尺寸 | 用途 |
|---|---|---|---|
| `<名字>.mp4` | 出 | 输出尺寸，无声 | 发朋友圈、小红书、抖音、Instagram、X |
| `<名字>.gif` | 出 | 不超过 5MB，宽度小于 1080 | 发微信、QQ 聊天和微博 |
| `<名字>.webp` | 要了才出 | 输出尺寸，目标约 8MB | 网页、GitHub、作品墙 |
| `<名字>-sticker.gif` | 要了才出 | 长边 240 像素，不超过 500KB | 拖进微信直接存成表情 |
| `<名字>.pvt` | 要了才出，只限 Mac | 3 秒实况照片，封面是输出尺寸 | 存进 iPhone 相册，再发小红书或朋友圈 |

为什么有好几种：多数聊天软件和手机相册不播放动态 WebP，社交平台发帖要 MP4，GIF 哪里都能放但体积大。某个平台有别的限制，比如“GIF 要小于 2MB”，直接告诉 Claude。

实况照片是一个 `.pvt` 包，在 Finder 里看起来是一个文件。把这一个文件隔空投送到 iPhone，就会以实况照片存进相册。把里面的照片和视频分开发，只会得到一张图和一段视频。

长边超过 2560 像素的照片会按 2560 渲染，保证速度。需要原分辨率可以说一声。

## 第一次使用

第一次使用时，Claude 会在 skill 文件夹（`skills/wake/`）里运行 `node scripts/doctor.mjs` 自检，加上 `--fix` 会补装缺的东西。

| 需要 | 大小 | 怎么装 |
|---|---|---|
| Node.js 18 或更高 | | 自己安装 |
| ffmpeg 和 ffprobe | | `brew install ffmpeg`，`sudo apt install ffmpeg`，或 `winget install Gyan.FFmpeg` |
| uv（运行 Python 脚本） | | `brew install uv`，或见 https://docs.astral.sh/uv/ |
| 无头浏览器和 `playwright-core` | 约 190MB | `node scripts/doctor.mjs --fix`，也可以用已装的 Chrome：`CHROME=<路径>` |
| Python 包（Pillow、NumPy、OpenCV、onnxruntime） | 约 150MB | 第一次使用时自动下载 |
| Xcode 命令行工具（只有实况照片要用，限 Mac） | | `xcode-select --install` |

在 macOS 上测试过。Linux 和 Windows 应该也能用，哪一步出错，Claude 会自己排查。

## 本地模型（可选）

几个在本机 CPU 上运行的小模型，用来抠出物体和人、补出它们背后的空位、估算景深。大多数片子用了会更好：东西能离开原位，才能真的动起来。**你同意之前什么都不下载**，通常在出片前的第一个问题里顺带问一次。

| 模型 | 作用 | 大小 | 来源 | 授权 |
|---|---|---|---|---|
| Depth Anything V2 Small | 估算景深，做立体视差 | 99MB | [onnx-community/depth-anything-v2-small](https://huggingface.co/onnx-community/depth-anything-v2-small) | Apache-2.0 |
| BiRefNet-lite | 抠出画面主体 | 224MB | [onnx-community/BiRefNet_lite-ONNX](https://huggingface.co/onnx-community/BiRefNet_lite-ONNX) | MIT |
| MODNet | 人像抠图，保留发丝 | 26MB | [Xenova/modnet](https://huggingface.co/Xenova/modnet) | Apache-2.0 |
| MobileSAM（2 个文件） | 点选或框选单个元素 | 44MB | [Acly/MobileSAM](https://huggingface.co/Acly/MobileSAM) | MIT |
| LaMa | 补上物体移走后的空洞 | 208MB | [Carve/LaMa-ONNX](https://huggingface.co/Carve/LaMa-ONNX) | Apache-2.0 |

合计约 600MB，每个文件都会核对 sha256。

**只问一次。** 第一支要用模型的片子开始前，Claude 会说明要下哪个、做什么用、多大、从哪下、存在哪，只问这一次，你的回答会被记住。不同意也没关系，Claude 会用代码折中，照样把片子做完。

**存在哪里。** 插件安装时存在 `~/.claude/plugins/data/<插件 id>/models/`，更新时保留，卸载时删除。普通 skill 安装时存在 skill 文件夹的 `models/`。也可以用 `LEMO_WAKE_MODELS=<文件夹>` 指定。

**常用命令。** 在 `skills/wake/` 里运行，或者直接让 Claude 做：

```bash
scripts/models.py                     # 查看状态
scripts/models.py fetch all --yes     # 现在全部下载
scripts/models.py consent yes|no      # 修改之前的回答
```

## 中国大陆用户

Hugging Face 在国内常常连不上，用镜像即可，sha256 校验不变：

```bash
HF_ENDPOINT=https://hf-mirror.com scripts/models.py fetch all --yes
```

想让所有下载都走镜像，加到 `~/.claude/settings.json`：

```json
{ "env": { "HF_ENDPOINT": "https://hf-mirror.com" } }
```

下载失败时，Claude 也会自己换镜像重试。其他下载慢的情况：

- Python 包：`UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple`
- npm：`npm config set registry https://registry.npmmirror.com`
- 无头浏览器：本机装的 Google Chrome 也能用，设置 `CHROME=<路径>`
- 手动下载模型：从上表的链接下载，改名为 `depth_anything_v2_small.onnx`、`birefnet_lite.onnx`、`modnet.onnx`、`mobile_sam_image_encoder.onnx`、`sam_mask_decoder_multi.onnx`、`lama_fp32.onnx`，放进模型文件夹

## 社区共创

作品墙不只放我们做的样片，也欢迎你把自己做的动图放上来。社区作品和样片放在同一面墙上，卡片右上角有橙色的“社区共创”标签，并写明作者。作品墙的分类里也有“社区共创”一项，可以只看大家的投稿。

**怎么投稿**

1. 用插件做好一支满意的动图，运行 `/lemo-wake:upload`。这个命令只在插件安装时可用。
2. Claude 会检查片子（动态 WebP 或 GIF，不超过 8MB），做一张小预览，再问你标题、分类、署名，以及要不要附上原图和制作笔记。原图会去掉位置、相机、时间等信息。
3. Claude 把要公开的全部内容给你看，你同意后，才用你自己的 GitHub 账号提交一个 PR。需要先装好 [GitHub CLI](https://cli.github.com) 并运行 `gh auth login` 登录。
4. 自动检查通过、维护者审核合并后，作品就会出现在[作品墙](https://lemomo-ai.github.io/lemo-wake/)上。

**投稿规则**

- 只投你有权分享的图，比如自己拍的照片、自己画的作品，或者已经获得授权的图。照片里有其他人，先征得他们同意。
- 不要包含隐私信息，比如他人的脸、姓名、电话、地址、聊天内容、证件和车牌。
- 作品按 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) 授权：别人可以署名转载和改编，但不能用于商业用途。投稿即同意本项目在 README、作品墙和项目宣传中展示你的作品。
- 投稿只会进入官方仓库。即使你是从 fork 或副本安装的插件，也一样。
- 想撤下作品，提一个 issue，或者提一个删除对应文件夹的 PR。

完整规则见 [CONTRIBUTING.md](https://github.com/lemomo-ai/lemo-wake/blob/gallery/CONTRIBUTING.md)。

## 授权

- 代码和文档采用 [CC BY-NC 4.0](LICENSE) 许可证：署名即可免费使用、转载和修改，不能商用。商用请联系 [Lemomo](https://github.com/lemomo-ai)。
- 作品墙里的片子，包括样片、社区作品和附带的原图，同样由各自作者按 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) 授权，即署名、非商业。
- 本地模型从各自来源下载，按各自的授权使用，不在本仓库里。

版本记录见 [Releases](https://github.com/lemomo-ai/lemo-wake/releases)。

## 关于

lemo-wake 由 [Lemomo](https://github.com/lemomo-ai) 和 Claude 一起制作。官方仓库是 https://github.com/lemomo-ai/lemo-wake ，官方作品墙是 https://lemomo-ai.github.io/lemo-wake/ 。欢迎在授权范围内 fork 和转载，请保留指向这里的链接。

在作品或文章里用到 lemo-wake，可以按 [CITATION.cff](CITATION.cff) 引用。

## 作品示例

每个分类一支，左边原图，右边动图。更多作品见[作品墙](https://lemomo-ai.github.io/lemo-wake/)。

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

