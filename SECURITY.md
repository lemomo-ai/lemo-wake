# lemo-wake 安全问题报告 · Security policy

[中文](#中文) · [English](#english)

## 中文

### 怎么报告

发现安全问题，请不要开公开 issue。在本仓库的 **Security** 页点 **Report a vulnerability** 私下提交（[直达链接](https://github.com/lemomo-ai/lemo-wake/security/advisories/new)）。写上版本号、用的哪个命令、怎么复现。

### 哪些算安全问题

- 你的图片、做出来的动图或照片信息被发到本机以外。投稿到作品墙是唯一会上传的地方，而且要你确认后才发。
- 投稿时照片的元数据（拍摄地点、设备等）没有去掉。
- 你没同意就下载了本地模型，或者从别的地方下载。
- 在你的项目文件夹以外写文件、删文件，或者别人能借一张图片在你的电脑上运行命令。

做出来不好看、功能 bug 照常开 issue。

### 支持的版本

只修最新发布的版本。修好后发新版，在发布说明里写清楚修了什么。

## English

### How to report

Please don't open a public issue for a security problem. Report it privately: on this repo's **Security** page, click **Report a vulnerability** ([direct link](https://github.com/lemomo-ai/lemo-wake/security/advisories/new)). Include the version, which command you ran, and how to reproduce it.

### What counts

- Your pictures, your films or their photo data leaving your computer. Sharing to the gallery is the only upload, and it only happens after you confirm it.
- Photo metadata (location, camera and so on) not being stripped when you share a film.
- A local model being downloaded before you said yes, or from somewhere else.
- Files written or deleted outside your project folder, or a way for someone to run commands on your computer through a picture.

Open a normal issue for films that look wrong and for feature bugs.

### Supported versions

Only the latest release gets fixes. A fix ships as a new release, and the release notes say what was fixed.
