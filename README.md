# textures-01 — Texture Showcase

A drop-in effect for [unicorn-viz](https://github.com/iDoMeteor/unicorn-viz).

## Description

Loads image assets from configurable directories and presents them in an animated, audio-reactive montage with pan/zoom, colour grading, and filmic post-processing. Works as a live wallpaper engine that reacts to music.

Also includes `Prism Storm`, a separate drop-in effect with a spinning crystal core, refractive beams, and electric haze.

## Visual Features

- Smooth pan/zoom Ken Burns motion on each image
- Audio-reactive colour grade (hue shift driven by mid frequencies)
- Beat-triggered cross-dissolve between images
- Configurable asset directories — point at any folder of images
- Vignette and light-leak post-processing
- Prism Storm crystal core + refractive laser effect

## Audio Reactivity

| Signal  | Effect |
|---------|--------|
| `mid`   | Hue shift / colour grade intensity |
| `beat`  | Cross-dissolve to next image |
| `bass`  | Zoom pulse |

## Config

```toml
[effects.TextureShowcase]
speed          = 1.0            # pan/zoom animation rate
slide_time     = 8.0            # seconds per image before beat-advance
texture_dirs   = "assets/textures"  # comma-separated list of image directories
```

## Adding Images

Place `.png`, `.jpg`, or `.webp` files in any directory listed in `texture_dirs`. They will be picked up automatically on the next run.

## Hotkeys

No dedicated hotkeys.  Standard `+`/`-` adjust `speed`.

## Tags

`textures` · `audio` · `modern` · `drop-in`

`Prism Storm` uses the same drop-in repo and will appear as a separate playlist effect alongside `Texture Showcase`.

## 2026-05-22 Update

- `Prism Storm` now uses normalized band dynamics (`bass_n/mid_n/treble_n`) for smoother audio-reactive intensity.
- `Texture Showcase` remains intentionally gentle/ambient and keeps its existing response profile.
