"""Texture Showcase drop-in effect.

Loads texture assets from configurable directories and presents them in an
animated, audio-reactive montage with pan/zoom, color grading, and filmic
transitions.
"""
from __future__ import annotations

import logging
from pathlib import Path

import moderngl
from PIL import Image

from unicornviz.effects.base import BaseEffect, AudioData

log = logging.getLogger(__name__)

_VERT = """
#version 330
in vec2 in_vert;
out vec2 v_uv;
void main() {
    v_uv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

_FRAG = """
#version 330
uniform sampler2D texA;
uniform sampler2D texB;
uniform float iTime;
uniform float iBass;
uniform float iMid;
uniform float iTreble;
uniform float iMix;
uniform vec2  iResolution;
in vec2 v_uv;
out vec4 fragColor;

vec3 palette(float t) {
    vec3 a = vec3(0.5);
    vec3 b = vec3(0.5);
    vec3 c = vec3(1.0);
    vec3 d = vec3(0.22, 0.1, 0.3);
    return a + b * cos(6.28318 * (c * t + d));
}

vec2 cover_uv(vec2 uv, vec2 texSize, vec2 outSize) {
    float inAspect = texSize.x / max(texSize.y, 1.0);
    float outAspect = outSize.x / max(outSize.y, 1.0);
    vec2 st = uv;
    if (inAspect > outAspect) {
        float s = outAspect / inAspect;
        st.x = (uv.x - 0.5) * s + 0.5;
    } else {
        float s = inAspect / outAspect;
        st.y = (uv.y - 0.5) * s + 0.5;
    }
    return st;
}

vec3 sampleWarped(sampler2D tex, vec2 uv, float t, float amp, float phase) {
    vec2 w = uv;
    w += vec2(
        sin((uv.y + phase) * 8.0 + t * 1.2),
        cos((uv.x + phase) * 9.0 - t * 1.0)
    ) * amp;
    return texture(tex, w).rgb;
}

void main() {
    vec2 uv = v_uv;
    float t = iTime;

    vec2 panA = vec2(sin(t * 0.31), cos(t * 0.27)) * (0.05 + iBass * 0.03);
    vec2 panB = vec2(cos(t * 0.23), sin(t * 0.29)) * (0.05 + iMid * 0.03);
    float zoomA = 1.0 + 0.08 * sin(t * 0.21) + iTreble * 0.04;
    float zoomB = 1.0 + 0.08 * cos(t * 0.19) + iBass * 0.04;

    vec2 uA = (uv - 0.5) / zoomA + 0.5 + panA;
    vec2 uB = (uv - 0.5) / zoomB + 0.5 + panB;

    vec3 a = sampleWarped(texA, uA, t, 0.004 + iTreble * 0.008, 0.1);
    vec3 b = sampleWarped(texB, uB, t, 0.004 + iBass * 0.008, 0.3);

    float wipe = smoothstep(0.0, 1.0, iMix);
    float noise = fract(sin(dot(uv * 200.0, vec2(12.9898, 78.233))) * 43758.5453);
    float blend = smoothstep(wipe - 0.15, wipe + 0.15, uv.x + (noise - 0.5) * 0.07);

    vec3 col = mix(a, b, blend);

    // subtle grade + audio tint
    float grade = 0.08 + iBass * 0.08 + iTreble * 0.05;
    col = mix(col, col * palette(t * 0.05 + uv.y * 0.3), grade);

    // vignette
    vec2 p = uv * 2.0 - 1.0;
    float vig = 1.0 - dot(p, p) * 0.22;
    col *= vig;

    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
"""


class TextureShowcase(BaseEffect):
    NAME = "Texture Showcase"
    AUTHOR = "unicorn-viz drop-in"
    TAGS = ["textures", "audio", "modern", "drop-in"]

    def _init(self) -> None:
        self.parameters = {
            "speed": 1.0,
            "mix_time": 7.0,
        }

        self._prog = self._make_program(_VERT, _FRAG)
        self._vao, self._vbo = self._fullscreen_quad(self._prog)

        self._textures: list[moderngl.Texture] = []
        self._current = 0
        self._next = 1
        self._timer = 0.0
        self._mix = 0.0
        self._bass = 0.0
        self._mid = 0.0
        self._treble = 0.0

        self._load_textures()

    def _texture_dirs(self) -> list[Path]:
        default_dir = Path(__file__).resolve().parent / "assets" / "textures"
        dirs_raw = self.config.get("texture_dirs", "")
        dirs: list[Path] = [default_dir]
        if isinstance(dirs_raw, str) and dirs_raw.strip():
            for d in dirs_raw.split(","):
                p = Path(d.strip()).expanduser()
                if p.exists():
                    dirs.append(p)
        # de-dup preserving order
        seen = set()
        uniq: list[Path] = []
        for d in dirs:
            key = str(d.resolve()) if d.exists() else str(d)
            if key not in seen:
                seen.add(key)
                uniq.append(d)
        return uniq

    def _load_textures(self) -> None:
        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tga"}
        files: list[Path] = []
        for d in self._texture_dirs():
            if not d.exists():
                continue
            for p in sorted(d.iterdir()):
                if p.is_file() and p.suffix.lower() in exts:
                    files.append(p)

        if not files:
            log.warning("TextureShowcase: no textures found")
            # fallback 1x1 magenta so effect still renders
            tex = self.ctx.texture((1, 1), 3, bytes([255, 0, 255]))
            tex.filter = moderngl.LINEAR, moderngl.LINEAR
            self._textures = [tex]
            self._current = 0
            self._next = 0
            return

        for path in files:
            try:
                img = Image.open(path).convert("RGB")
                tex = self.ctx.texture(img.size, 3, img.tobytes())
                tex.filter = moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR
                tex.build_mipmaps()
                self._textures.append(tex)
            except Exception as exc:
                log.warning("TextureShowcase: failed to load %s: %s", path, exc)

        if not self._textures:
            tex = self.ctx.texture((1, 1), 3, bytes([255, 0, 255]))
            tex.filter = moderngl.LINEAR, moderngl.LINEAR
            self._textures = [tex]
        self._current = 0
        self._next = 1 if len(self._textures) > 1 else 0
        log.info("TextureShowcase: loaded %d textures", len(self._textures))

    def update(self, dt: float, audio: AudioData) -> None:
        super().update(dt, audio)
        self._bass = audio.bass
        self._mid = audio.mid
        self._treble = audio.treble

        self._timer += dt * max(0.1, self.parameters["speed"])
        mix_time = max(1.0, self.parameters["mix_time"])
        phase = self._timer / mix_time

        if phase >= 1.0:
            self._timer = 0.0
            self._current = self._next
            self._next = (self._next + 1) % len(self._textures)
            self._mix = 0.0
        else:
            self._mix = phase

    def render(self) -> None:
        tex_a = self._textures[self._current]
        tex_b = self._textures[self._next]
        tex_a.use(location=0)
        tex_b.use(location=1)

        def set_uniform(name: str, value) -> None:
            try:
                self._prog[name].value = value
            except KeyError:
                pass

        set_uniform("texA", 0)
        set_uniform("texB", 1)
        set_uniform("iTime", self.time)
        set_uniform("iBass", self._bass)
        set_uniform("iMid", self._mid)
        set_uniform("iTreble", self._treble)
        set_uniform("iMix", self._mix)
        set_uniform("iResolution", (float(self.width), float(self.height)))

        self._vao.render(moderngl.TRIANGLE_STRIP)

    def destroy(self) -> None:
        for tex in self._textures:
            tex.release()
        self._vao.release()
        self._vbo.release()
        self._prog.release()
