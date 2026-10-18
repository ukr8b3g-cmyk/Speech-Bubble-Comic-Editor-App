# Third-Party Notices

## Related author-maintained project

The editor and renderer originated in [Speech-Bubble-Layer](https://github.com/ukr8b3g-cmyk/Speech-Bubble-Layer), a related project maintained by the same author.

This repository is a standalone desktop adaptation. It does not redistribute or require a separate image-generation application.

## Repository content

Unless otherwise stated, the source code, built-in speech bubbles, SFX assets, comic stamps, frames, icons, and related artwork in this repository are original works maintained by the repository owner. Third-party source adaptations and packaged dependencies are identified below; system fonts are not bundled.

## Runtime and platform components

Python, FastAPI, pywebview, Pillow, browser APIs, system fonts, and other runtime components remain subject to their respective licenses and terms. Windows distributions package the required Python runtime and application dependencies; browser APIs and system fonts are supplied by the platform.

## AI background removal

The Windows build includes [ONNX Runtime](https://github.com/microsoft/onnxruntime) for local CPU inference. ONNX Runtime is licensed under the MIT License.

The optional `isnet-anime.onnx` model is not bundled in the installer. After explicit user consent, the app downloads it from the [rembg model release](https://github.com/danielgatis/rembg/releases/tag/v0.0.0), verifies its expected file size and SHA-256, and stores it locally. The model originates from [SkyTNT/anime-segmentation](https://github.com/SkyTNT/anime-segmentation) and is identified there as Apache-2.0 licensed. No rembg Python code is included or executed by this application.

- Model: `isnet-anime.onnx`
- Expected SHA-256: `f15622d853e8260172812b657053460e20806f04b9e05147d49af7bed31a6e99`
- Model source/license: Apache-2.0
- ONNX Runtime license: MIT

## Manga Finish

Derived from [MangaScreen](https://github.com/ashukae/ComfyUI-MangaScreen) and [Mangazin](https://github.com/arthur-cma/Mangazin), mangazin_core.py. Changes include tiled screen rendering, validated image input, preserved alpha and Desktop integration.

Manga Finish uses `opencv-python-headless` 4.13.0.92. Windows builds include its package metadata and license notices, including the OpenCV and bundled-component notices supplied with that distribution.

A standalone copy of the following license is included as `licenses/MangaScreen-MIT.txt` (under `_internal` in the Windows application).

MIT License

Copyright (c) 2026 ashukae

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
