# Sharing a film

This is the official lemo-wake gallery (https://github.com/lemomo-ai/lemo-wake, branch `gallery`; page: https://lemomo-ai.github.io/lemo-wake/). Submit here, not to a fork.

The easiest way: install the [lemo-wake plugin](https://github.com/lemomo-ai/lemo-wake#install), make a film, and run `/lemo-wake:upload`. Claude checks the film, shows you exactly what will be published, and opens a pull request from your own GitHub account after you say yes.

## What a submission is

One new folder `films/<id>/` on this `gallery` branch, where `<id>` is `<yyyymmdd>-<github-login>-<slug>` (lowercase letters, digits and dashes):

| File | Required | Limit |
|---|---|---|
| `film.webp` or `film.gif` | yes | animated, at most 8 MB |
| `preview.webp` | yes | animated, long side at most 480 px (360 recommended), at most 1 MB |
| `meta.json` | yes | see below |
| `source.jpg` | no | the original image, no metadata (EXIF / XMP), at most 2 MB |
| `notes.md` | no | how it was made, at most 20 KB |

```json
{
  "title": "炉边三花猫 · 炉火醒来",
  "title_en": "Calico by the fire · The fire wakes up",
  "category": "photo",
  "author": "your-name",
  "author_url": "https://github.com/your-login",
  "license": "CC-BY-NC-4.0",
  "consent": true,
  "created": "2026-10-03",
  "lemo_wake": "1.0.0",
  "width": 1086, "height": 1448, "seconds": 5.2
}
```

`title_en` is optional (the gallery shows both languages). `category` is one of `photo`, `portrait`, `multi`, `poster`, `illustration`, `clay`, `ui`, `chart`, `logo`, `sticker`, `xhs`.

## Rules

- Only images you have the rights to: your own photo or artwork, or one you are allowed to share. People shown in a photo agreed to it being published.
- No private details: other people's faces without consent, names, phone numbers, addresses, chat contents, documents, licence plates.
- `consent: true` means you publish the film (and the original, if included) under [CC BY-NC 4.0](LICENSE), and agree that the lemo-wake project may show it in its README, this gallery and posts about the project.
- A pull request only adds film folders. An automatic check verifies the files; a maintainer reviews every submission and may decline any film.
- To remove your film later, open an issue or a pull request that deletes your folder.

The gallery page (`README.md`) is rebuilt automatically after a merge - don't edit it in a submission.
