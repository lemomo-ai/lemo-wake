# Changelog

## 1.0.0 - first public release

- `/lemo-wake:wake`: turns one image into a ~5 second seamless loop. It first asks for the output size (default: the source's own size) and the formats: MP4 (posts) and GIF (chats) by default, WebP (web), a WeChat sticker GIF and, on macOS, an Apple Live Photo on request; more formats can be added later without re-rendering.
- It takes the picture apart with the local models before planning (cut-outs, plates, depth; `sheet.py --parts` shows the parts), then directs the film around two core rules: imagine what the picture could become, and direct it as a whole film.
- Guidance for 11 kinds of images (photo, portrait, several photos, poster, illustration, clay / paper-cut / 3D, screenshots, charts, logos, stickers, Xiaohongshu covers), a shared quality bar, 49 effect blocks and 27 loop transitions.
- Five optional local models (depth, subject cut-out, portrait matting, element picking, hole filling), downloaded only after asking once; Hugging Face mirror support; films are still finished when a model is unavailable.
- `/lemo-wake:upload`: share a film to the community gallery through a pull request from your own GitHub account.
- Built and tuned for Claude Code; other agents can read the skill, but results are not guaranteed.
- License: code, docs and gallery films under CC BY-NC 4.0 (attribution, non-commercial).
