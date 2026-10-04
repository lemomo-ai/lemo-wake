# Changelog

## 1.0.0 - first public release

- `/lemo-wake:wake`: turns one image into a ~5 second seamless loop. It first asks for the output size (default: the source's own size) and the formats: MP4 (posts) and GIF (chats) by default, WebP (web), a WeChat sticker GIF and, on macOS, an Apple Live Photo on request; more formats can be added later without re-rendering.
- Guidance for 11 kinds of images (photo, portrait, several photos, poster, illustration, clay / paper-cut / 3D, screenshots, charts, logos, stickers, Xiaohongshu covers), a shared quality bar, 49 effect blocks and 27 loop transitions.
- Five optional local models (depth, subject cut-out, portrait matting, element picking, hole filling), downloaded only when a film needs one, after asking once; Hugging Face mirror support; films are still finished when a model is unavailable.
- `/lemo-wake:upload`: share a film to the community gallery through a pull request from your own GitHub account.
