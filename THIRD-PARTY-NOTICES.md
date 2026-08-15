# Third-Party Notices

## Related author-maintained project

The editor and renderer originated in [Speech-Bubble-Layer](https://github.com/ukr8b3g-cmyk/Speech-Bubble-Layer), a related project maintained by the same author.

This repository is a standalone desktop adaptation. It does not redistribute or require a separate image-generation application.

## Repository content

Unless otherwise stated, the source code, built-in speech bubbles, SFX assets, comic stamps, frames, icons, and related artwork in this repository are original works maintained by the repository owner. The repository audit found no bundled third-party library, font, icon set, or separately licensed image package.

## Runtime and platform components

Python, FastAPI, pywebview, Pillow, browser APIs, system fonts, and other runtime components remain subject to their respective licenses and terms. They are not redistributed by this repository as separately bundled dependencies.

## AI background removal

The Windows build includes [ONNX Runtime](https://github.com/microsoft/onnxruntime) for local CPU inference. ONNX Runtime is licensed under the MIT License.

The optional `isnet-anime.onnx` model is not bundled in the installer. After explicit user consent, the app downloads it from the [rembg model release](https://github.com/danielgatis/rembg/releases/tag/v0.0.0), verifies its expected file size and SHA-256, and stores it locally. The model originates from [SkyTNT/anime-segmentation](https://github.com/SkyTNT/anime-segmentation) and is identified there as Apache-2.0 licensed. No rembg Python code is included or executed by this application.

- Model: `isnet-anime.onnx`
- Expected SHA-256: `f15622d853e8260172812b657053460e20806f04b9e05147d49af7bed31a6e99`
- Model source/license: Apache-2.0
- ONNX Runtime license: MIT
