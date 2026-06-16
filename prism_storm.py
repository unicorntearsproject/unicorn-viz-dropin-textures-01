"""Prism Lattice drop-in effect.

An audio-reactive crystal lattice that spins a refractive core and paints the
scene with prism facets, laser arcs, and electric haze.
"""
from __future__ import annotations

import moderngl

from unicornviz.effects.base import BaseEffect, AudioData

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
uniform float iTime;
uniform vec2 iResolution;
uniform float iBass;
uniform float iMid;
uniform float iTreble;
uniform float iSpeed;
uniform float iShardCount;
uniform float iGlow;
uniform float iBeamCount;
uniform float iZoom;

in vec2 v_uv;
out vec4 fragColor;

#define PI 3.14159265
#define TAU 6.28318530

float hash11(float p) { return fract(sin(p * 127.1) * 43758.5453123); }
float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123); }

mat3 rotX(float a) {
    float s = sin(a), c = cos(a);
    return mat3(1, 0, 0, 0, c, -s, 0, s, c);
}

mat3 rotY(float a) {
    float s = sin(a), c = cos(a);
    return mat3(c, 0, s, 0, 1, 0, -s, 0, c);
}

mat3 rotZ(float a) {
    float s = sin(a), c = cos(a);
    return mat3(c, -s, 0, s, c, 0, 0, 0, 1);
}

float sdSphere(vec3 p, float r) { return length(p) - r; }

float sdPrism(vec3 p, float h, float r, int n) {
    // Hex/prism-like radial distance, good enough for a crystal core.
    float a = atan(p.x, p.z);
    float sector = TAU / float(n);
    float slice = abs(mod(a + sector * 0.5, sector) - sector * 0.5);
    float radial = length(p.xz) * cos(slice);
    vec2 d = vec2(radial - r, abs(p.y) - h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

vec3 palette(float t) {
    vec3 a = vec3(0.45, 0.48, 0.52);
    vec3 b = vec3(0.55, 0.42, 0.45);
    vec3 c = vec3(1.0);
    vec3 d = vec3(0.12, 0.28, 0.38);
    return a + b * cos(TAU * (c * t + d));
}

float mapScene(vec3 p, out float matId) {
    float t = iTime * iSpeed;
    matId = 0.0;

    vec3 q = p;
    q = rotY(t * 0.55) * rotX(sin(t * 0.32) * 0.35) * q;
    float core = sdPrism(q, 0.85, 0.24 + iBass * 0.05, int(max(5.0, iShardCount)));
    float ring = sdTorus(p, vec2(1.25 + iBass * 0.06, 0.08 + iTreble * 0.02));
    float shell = sdSphere(p, 1.55 + iMid * 0.05);

    float d = shell;
    matId = 1.0;
    if (core < d) { d = core; matId = 2.0; }
    if (ring < d) { d = ring; matId = 3.0; }

    // Electric storm bands around the core.
    vec3 sp = p;
    sp = rotZ(t * 1.1) * sp;
    float band = abs(length(sp.xy) - (0.7 + 0.06 * sin(t * 2.0 + sp.z * 3.0)));
    float arc = band - (0.05 + 0.02 * iBass);
    if (arc < d) { d = arc; matId = 4.0; }

    return d;
}

vec3 calcNormal(vec3 p) {
    float e = 0.0015;
    float m;
    return normalize(vec3(
        mapScene(p + vec3(e, 0, 0), m) - mapScene(p - vec3(e, 0, 0), m),
        mapScene(p + vec3(0, e, 0), m) - mapScene(p - vec3(0, e, 0), m),
        mapScene(p + vec3(0, 0, e), m) - mapScene(p - vec3(0, 0, e), m)
    ));
}

float softShadow(vec3 ro, vec3 rd, float mint, float maxt) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < 36; i++) {
        float m;
        float h = mapScene(ro + rd * t, m);
        res = min(res, 12.0 * h / t);
        t += clamp(h, 0.02, 0.18);
        if (res < 0.001 || t > maxt) break;
    }
    return clamp(res, 0.0, 1.0);
}

vec3 shade(vec3 ro, vec3 rd, vec3 p, float matId, vec3 n) {
    float t = iTime * iSpeed;
    vec3 col = vec3(0.0);
    vec3 lp = vec3(2.2 * sin(t * 0.8), 1.6 + 0.6 * sin(t * 0.6), 2.2 * cos(t * 0.74));
    vec3 ldir = normalize(lp - p);
    float diff = max(dot(n, ldir), 0.0);
    float spec = pow(max(dot(reflect(-ldir, n), -rd), 0.0), 32.0);
    float sh = softShadow(p + n * 0.015, ldir, 0.02, 6.0);
    vec3 fres = palette(length(p) * 0.1 + t * 0.04 + n.y * 0.2);

    if (matId < 1.5) {
        col = vec3(0.01, 0.02, 0.04);
    } else if (matId < 2.5) {
        // Crystal prism core.
        float fr = pow(1.0 - max(dot(-rd, n), 0.0), 3.0);
        vec3 refr = palette(t * 0.08 + p.y * 0.7 + p.x * 0.5);
        col = refr * (0.25 + 0.75 * fr);
        col += diff * vec3(0.4, 0.8, 1.0) * sh;
        col += spec * vec3(1.0, 0.8, 1.0) * (1.0 + iTreble * 1.2);
        col += fr * fres * (0.5 + iGlow);
    } else if (matId < 3.5) {
        // Halo ring.
        float fr = pow(1.0 - max(dot(-rd, n), 0.0), 5.0);
        col = vec3(0.08, 0.12, 0.18) + diff * vec3(0.35, 0.5, 0.9) * sh;
        col += fr * vec3(0.8, 0.95, 1.0) * (0.8 + iMid);
        col += spec * vec3(1.0, 0.85, 1.0);
    } else {
        // Electric storm arcs.
        float pulse = smoothstep(0.0, 1.0, 0.55 + 0.45 * sin(t * 2.2 + p.z * 7.0));
        col = pulse * vec3(0.35, 0.95, 1.0) + pulse * vec3(1.0, 0.35, 0.95) * 0.6;
        col *= 1.0 + iTreble * 2.0;
    }

    // Beam hits: occasional refractive laser cuts across the scene.
    float beamAmt = 0.0;
    float beamCount = max(1.0, iBeamCount);
    for (int i = 0; i < 8; i++) {
        if (float(i) >= beamCount) break;
        float fi = float(i);
        float phase = t * (0.8 + 0.17 * fi) + fi * 1.7;
        vec3 dir = normalize(vec3(sin(phase), 0.18 * cos(phase * 1.3), cos(phase * 0.91)));
        float align = pow(max(dot(rd, dir), 0.0), 48.0);
        beamAmt += align * (0.45 + 0.55 * hash11(fi * 13.1));
    }
    col += beamAmt * vec3(0.35, 0.95, 1.0) * (0.8 + iTreble);
    col += beamAmt * vec3(1.0, 0.35, 0.65) * 0.5;

    // Fog + vignette.
    float fog = exp(-0.08 * length(p - ro));
    col = mix(vec3(0.01, 0.01, 0.03), col, fog);
    vec2 v = v_uv * 2.0 - 1.0;
    float vig = 1.0 - dot(v, v) * 0.22;
    return col * vig;
}

void main() {
    vec2 uv = v_uv * 2.0 - 1.0;
    uv.x *= iResolution.x / max(iResolution.y, 1.0);
    uv /= max(iZoom, 0.01);
    float t = iTime * iSpeed;

    vec3 ro = vec3(
        0.0 + 0.15 * sin(t * 0.9),
        0.2 + 0.12 * sin(t * 0.7),
        4.4 + 0.2 * cos(t * 0.5)
    );
    vec3 ta = vec3(0.0, 0.0, 0.0);
    vec3 fwd = normalize(ta - ro);
    vec3 rgt = normalize(cross(fwd, vec3(0.0, 1.0, 0.0)));
    vec3 up = cross(rgt, fwd);
    vec3 rd = normalize(fwd + uv.x * rgt + uv.y * up);

    // Small camera drift and a beat-reactive kick.
    ro += vec3(sin(t * 0.35), cos(t * 0.29), 0.0) * (0.06 + 0.04 * iBass);

    float total = 0.0;
    float matId = 0.0;
    bool hit = false;
    vec3 p = ro;

    for (int i = 0; i < 96; i++) {
        p = ro + rd * total;
        float d = mapScene(p, matId);
        if (d < 0.001) {
            hit = true;
            break;
        }
        total += d;
        if (total > 14.0) break;
    }

    vec3 col = vec3(0.0);
    if (hit) {
        vec3 n = calcNormal(p);
        col = shade(ro, rd, p, matId, n);
    } else {
        // Background sky + prism lattice haze.
        float horizon = smoothstep(-0.2, 0.8, rd.y);
        col = mix(vec3(0.02, 0.02, 0.05), vec3(0.08, 0.0, 0.12), horizon);
        col += 0.06 * palette(t * 0.05 + uv.y * 0.1 + uv.x * 0.05);
        col += 0.03 * vec3(0.2, 0.9, 1.0) * pow(max(0.0, 1.0 - length(uv)), 2.0);
        vec2 l = abs(fract(uv * 7.0) - 0.5);
        float facet = smoothstep(0.49, 0.42, max(l.x, l.y));
        col += palette(t * 0.03 + uv.x * 0.2 - uv.y * 0.2) * facet * 0.08;
    }

    // Audio-driven bloom / saturation push.
    float bloom = 0.1 + iBass * 0.2 + iTreble * 0.1 + iGlow * 0.15;
    col += bloom * vec3(0.12, 0.18, 0.22);
    col = col / (col + 0.85);
    col = pow(max(col, 0.0), vec3(0.88));

    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
"""


class PrismStorm(BaseEffect):
    """Audio-reactive prism lattice with refractive beams and electric haze."""

    NAME = 'Prism Lattice'
    AUTHOR = 'unicorn-viz drop-in'
    TAGS = ['crystal', 'prism', 'lattice', 'audio', 'drop-in']
    PING_PONG_FRIENDS = [
        'Unicorn Tears',
        'Kaleidoscope',
        'Copper Bars',
        'Hexy Stars',
        'Metaballs',
        'Plasma',
        'Psychedelic',
        'Sine Scroller 3.1',
        'Tunnel',
        'Van Gogh',
        'Wavey Gravy',
        'Tron Grid',
        'Hacker Terminal',
        'Cyber War',
    ]

    def _init(self) -> None:
        self.parameters = {
            'speed': 1.0,
            'shard_count': float(self.rng.integers(5, 11)),
            'glow': float(self.rng.uniform(0.7, 1.4)),
            'beam_count': float(self.rng.integers(3, 7)),
            'zoom': 1.0,
        }

        self._prog = self._make_program(_VERT, _FRAG)
        self._vao, self._vbo = self._fullscreen_quad(self._prog)

        self._bass = 0.0
        self._mid = 0.0
        self._treble = 0.0

    def update(self, dt: float, audio: AudioData) -> None:
        super().update(dt, audio)
        self._bass = audio.bass_n
        self._mid = audio.mid_n
        self._treble = audio.treble_n

    def _set(self, name: str, value) -> None:
        try:
            self._prog[name].value = value
        except KeyError:
            pass

    def render(self) -> None:
        self._set('iTime', self.time)
        self._set('iResolution', (float(self.width), float(self.height)))
        self._set('iBass', self._bass)
        self._set('iMid', self._mid)
        self._set('iTreble', self._treble)
        self._set('iSpeed', max(0.05, self.parameters['speed']))
        self._set('iShardCount', max(5.0, self.parameters['shard_count']))
        self._set('iGlow', max(0.0, self.parameters['glow']))
        self._set('iBeamCount', max(1.0, self.parameters['beam_count']))
        self._set('iZoom', max(0.1, self.parameters['zoom']))
        self._vao.render(moderngl.TRIANGLE_STRIP)

    def destroy(self) -> None:
        self._vao.release()
        self._vbo.release()
        self._prog.release()