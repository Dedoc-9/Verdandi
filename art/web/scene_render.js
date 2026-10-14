// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// art/web/scene_render.js — the native renderer of an art scene (VERDANDI-ART-SCENE 0), in WebGL 2.
//
// It draws what the scene says and decides nothing: the scene's play boxes (C, as the exporter laid it out) and its
// dressing, in their materials, under its moon, its lamps and its neon, in its fog and rain. It reads the scene and a
// camera; it writes no state of the game and has no say in where a wall is (art/play.py serves it beside the graybox's
// simulation, which moves against C alone).
//
// The look, by pass:
//   - a shadow map of the moon, drawn once (the scene does not move);
//   - a mirror image of the scene under the floor's plane, at half size, for the wet floor and the puddles;
//   - the scene: a GGX specular and Lambert diffuse under the moon (shadowed) and every point light (each seen only
//     from the cells it can see across the grid, so no light leaks through a wall), surfaces patterned by what they
//     are (board-formed concrete, stone setts, black water, steel, neon), light thrown up from the lit floor onto the
//     undersides of slabs, the sky's light dimmed by the masses around and above, height fog, and the glow each lamp
//     makes in the fog along the line of sight;
//   - rain, as streaks;
//   - bloom, and a tone curve.
// Nothing hashes its pixels: a person judges what it draws. load(S) changes the scene it draws in place (a live edit);
// dispose() frees the renderer, so that a newer copy of this file can take the canvas over.
// Movers (0226): setMovers(boxes) gives the boxes where the simulation has put the scene's movers this frame; they are
// drawn each frame in their materials beside the targets (the first MAX_MOVERS of them; art/quality.py reads the cap
// from here). They cast no moon shadow (the shadow map is drawn once) and light no cell's line of sight.

(function (root) {
  "use strict";

  const MAX_MOVERS = 64;

  // ---------------------------------------------------------------- matrices (column-major)
  function mul(a, b) {
    const o = new Float32Array(16);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += a[k * 4 + i] * b[j * 4 + k];
      o[j * 4 + i] = s;
    }
    return o;
  }
  function persp(fovy, asp, n, f) {
    const t = 1 / Math.tan(fovy / 2);
    return new Float32Array([t / asp, 0, 0, 0, 0, t, 0, 0, 0, 0, (f + n) / (n - f), -1, 0, 0, 2 * f * n / (n - f), 0]);
  }
  function ortho(l, r, b, t, n, f) {
    return new Float32Array([2 / (r - l), 0, 0, 0, 0, 2 / (t - b), 0, 0, 0, 0, -2 / (f - n), 0,
      -(r + l) / (r - l), -(t + b) / (t - b), -(f + n) / (f - n), 1]);
  }
  function lookAt(e, c, up) {
    let fx = c[0] - e[0], fy = c[1] - e[1], fz = c[2] - e[2];
    let fl = Math.hypot(fx, fy, fz); fx /= fl; fy /= fl; fz /= fl;
    let sx = fy * up[2] - fz * up[1], sy = fz * up[0] - fx * up[2], sz = fx * up[1] - fy * up[0];
    const sl = Math.hypot(sx, sy, sz); sx /= sl; sy /= sl; sz /= sl;
    const ux = sy * fz - sz * fy, uy = sz * fx - sx * fz, uz = sx * fy - sy * fx;
    return new Float32Array([sx, ux, -fx, 0, sy, uy, -fy, 0, sz, uz, -fz, 0,
      -(sx * e[0] + sy * e[1] + sz * e[2]), -(ux * e[0] + uy * e[1] + uz * e[2]), fx * e[0] + fy * e[1] + fz * e[2], 1]);
  }
  // a camera: x, y, z in metres; yaw (0 north, -z; pi/2 east, +x) and pitch in radians
  function viewOf(c) {
    const fx = Math.sin(c.yaw) * Math.cos(c.pitch), fy = Math.sin(c.pitch), fz = -Math.cos(c.yaw) * Math.cos(c.pitch);
    return lookAt([c.x, c.y, c.z], [c.x + fx, c.y + fy, c.z + fz], [0, 1, 0]);
  }
  const MIRROR = new Float32Array([1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);   // y -> -y

  const lin = function (c) { return c.map(function (v) { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); };

  // ---------------------------------------------------------------- shaders
  const COMMON = `#version 300 es
precision highp float; precision highp int; precision highp sampler2D;
`;
  const VS_SCENE = COMMON + `
in vec3 aP; in vec3 aN; in vec4 aA; in vec4 aE; in float aK;
uniform mat4 uVP; uniform float uMirror;
out vec3 wP; out vec3 wN; out vec4 vA; out vec4 vE; flat out int vK;
void main() {
  wP = aP; wN = aN; vA = aA; vE = aE; vK = int(aK + 0.5);
  gl_Position = uVP * vec4(aP, 1.0);
}`;
  const VS_DEPTH = COMMON + `
in vec3 aP; uniform mat4 uVP;
void main() { gl_Position = uVP * vec4(aP, 1.0); }`;
  const FS_DEPTH = COMMON + `
out vec4 o; void main() { o = vec4(1.0); }`;

  const FS_SCENE = COMMON + `
in vec3 wP; in vec3 wN; in vec4 vA; in vec4 vE; flat in int vK;
out vec4 o;
uniform vec3 uEye; uniform float uTime; uniform float uMirror; uniform vec2 uView;
uniform vec3 uMoonDir; uniform vec3 uMoonCol; uniform vec3 uSkyCol; uniform vec3 uFogCol; uniform float uFogD; uniform float uRain;
uniform mat4 uShadowVP; uniform sampler2D uShadow; uniform float uShadowTexel;
uniform sampler2D uLights; uniform int uNL; uniform sampler2D uVis; uniform sampler2D uHeight; uniform sampler2D uRoof;
uniform vec4 uGrid;   // w, h, cell, wall
uniform sampler2D uRefl; uniform float uHasRefl; uniform float uLightScale; uniform float uGlow;

const float PI = 3.14159265;
float hash12(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float noise(vec2 p) { vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash12(i), hash12(i + vec2(1, 0)), u.x), mix(hash12(i + vec2(0, 1)), hash12(i + vec2(1, 1)), u.x), u.y); }
float fbm(vec2 p) { float s = 0.0, a = 0.5; for (int i = 0; i < 4; i++) { s += a * noise(p); p *= 2.03; a *= 0.5; } return s; }

int cellIndex(vec2 xz) {
  ivec2 c = ivec2(floor(xz / uGrid.z));
  c = clamp(c, ivec2(0), ivec2(int(uGrid.x) - 1, int(uGrid.y) - 1));
  return c.y * int(uGrid.x) + c.x;
}
float heightAt(vec2 xz) {
  vec2 g = xz / uGrid.z;
  if (g.x < 0.0 || g.y < 0.0 || g.x >= uGrid.x || g.y >= uGrid.y) return uGrid.w;
  return texelFetch(uHeight, ivec2(floor(g)), 0).r;
}
// the sky's share left over a point: the masses around it, sampled on the heightfield, and any slab above it
float skyAO(vec3 p, vec3 n) {
  float occ = 0.0;
  for (int i = 0; i < 8; i++) {
    float a = float(i) * PI / 4.0 + 0.3;
    vec2 d = vec2(cos(a), sin(a));
    if (dot(vec3(d.x, 0.0, d.y), n) < -0.3) { occ += 1.0; continue; }
    float best = 0.0;
    for (int j = 1; j <= 3; j++) {
      float r = float(j * j) * 1.2;
      float hh = heightAt(p.xz + d * r + n.xz * 0.3) - p.y;
      best = max(best, clamp(hh / sqrt(hh * hh + r * r), 0.0, 1.0));
    }
    occ += best;
  }
  float ao = 1.0 - occ / 8.0;
  float roof = texelFetch(uRoof, ivec2(clamp(floor(p.xz / uGrid.z), vec2(0.0), uGrid.xy - 1.0)), 0).r;
  if (roof > p.y + 0.05) ao *= 0.35;
  return ao;
}
float shadowAt(vec3 p, vec3 n) {
  vec4 s = uShadowVP * vec4(p + n * 0.06, 1.0);
  vec3 q = s.xyz / s.w * 0.5 + 0.5;
  if (q.x < 0.0 || q.y < 0.0 || q.x > 1.0 || q.y > 1.0) return 1.0;
  float sum = 0.0;
  for (int i = -1; i <= 1; i++) for (int j = -1; j <= 1; j++) {
    float d = texture(uShadow, q.xy + vec2(i, j) * uShadowTexel * 1.5).r;
    sum += q.z - 0.0015 <= d ? 1.0 : 0.0;
  }
  return sum / 9.0;
}
float D_GGX(float nh, float a) { float a2 = a * a; float d = nh * nh * (a2 - 1.0) + 1.0; return a2 / (PI * d * d); }
float V_SmithJoint(float nv, float nl, float a) { float a2 = a * a;
  float gv = nl * sqrt(nv * nv * (1.0 - a2) + a2), gl = nv * sqrt(nl * nl * (1.0 - a2) + a2); return 0.5 / max(gv + gl, 1e-4); }
vec3 F_Schlick(vec3 f0, float vh) { return f0 + (1.0 - f0) * pow(1.0 - vh, 5.0); }
vec3 brdf(vec3 n, vec3 v, vec3 l, vec3 base, float rough, float metal) {
  float nl = max(dot(n, l), 0.0); if (nl <= 0.0) return vec3(0.0);
  vec3 h = normalize(l + v); float nv = max(dot(n, v), 1e-3), nh = max(dot(n, h), 0.0), vh = max(dot(v, h), 0.0);
  float a = max(rough * rough, 0.002);
  vec3 f0 = mix(vec3(0.04), base, metal), F = F_Schlick(f0, vh);
  vec3 spec = D_GGX(nh, a) * V_SmithJoint(nv, nl, a) * F;
  vec3 diff = (1.0 - F) * (1.0 - metal) * base / PI;
  return (diff + spec) * nl;
}
// one point light's radiance onto a point, or nothing if the light cannot see the point's cell
vec3 pointLight(int i, vec3 p, vec3 n, vec3 v, vec3 base, float rough, float metal, int cell, bool spec) {
  vec4 a = texelFetch(uLights, ivec2(i, 0), 0), b = texelFetch(uLights, ivec2(i, 1), 0);
  vec3 dl = a.xyz - p; float d2 = dot(dl, dl);
  if (d2 > a.w * a.w) return vec3(0.0);
  if (texelFetch(uVis, ivec2(cell, i), 0).r < 0.5) return vec3(0.0);
  float d = sqrt(d2); vec3 l = dl / d;
  float win = pow(clamp(1.0 - pow(d / a.w, 4.0), 0.0, 1.0), 2.0);
  vec3 rad = b.rgb * uLightScale * win / (d2 + 0.3);
  if (b.a > 0.5) rad *= 0.55 + 0.45 * max(dot(-l, vec3(0.0, -1.0, 0.0)), 0.0);   // downlights: brighter below
  return spec ? brdf(n, v, l, base, rough, metal) * rad : base / PI * max(dot(n, l), 0.0) * rad;
}
// the glow a light makes in the fog along the ray from the eye to the surface (single scattering, closed form)
vec3 fogGlow(vec3 ro, vec3 rd, float t) {
  vec3 sum = vec3(0.0);
  for (int i = 0; i < 160; i++) {
    if (i >= uNL) break;
    vec4 a = texelFetch(uLights, ivec2(i, 0), 0), b = texelFetch(uLights, ivec2(i, 1), 0);
    vec3 q = a.xyz - ro; float s = dot(q, rd); float h2 = max(dot(q, q) - s * s, 0.36);
    if (h2 > a.w * a.w * 0.25) continue;
    float h = sqrt(h2);
    float I = (atan((t - s) / h) - atan(-s / h)) / h;
    sum += b.rgb * I;
  }
  return sum * uLightScale * uFogD * uGlow;
}

void main() {
  vec3 n = normalize(wN);
  if (uMirror > 0.5 && wP.y < 0.02) discard;    // the mirror image holds only what stands above the floor
  vec3 base = vA.rgb; float rough = vA.a; float metal = vE.a; vec3 em = vE.rgb;
  int kind = vK;   // 0 concrete, 1 floor stone, 2 water, 3 neon, 4 steel
  vec2 uv = abs(n.y) > 0.5 ? wP.xz : (abs(n.x) > 0.5 ? wP.zy : wP.xy);
  float wet = uRain;
  vec3 pn = n;
  if (kind == 0) {
    // board-formed concrete: boards 0.3 m high, tie holes on a 0.6 by 0.9 m grid, mottling, rain streaks
    float m = fbm(uv * 0.35) * 0.6 + fbm(uv * 3.1) * 0.4;
    base *= 0.72 + 0.5 * m;
    if (abs(n.y) < 0.5) {
      float board = fract(wP.y / 0.3);
      base *= 0.92 + 0.08 * smoothstep(0.0, 0.08, board) * smoothstep(1.0, 0.92, board);
      vec2 tie = vec2(fract(uv.x / 0.6), fract(wP.y / 0.9));
      base *= 1.0 - 0.55 * (1.0 - smoothstep(0.02, 0.035, length((tie - 0.5) * vec2(0.6, 0.9))));
      // runoff: a few dark drips down from the edges, not a pattern over the whole face
      float col = floor(uv.x * 2.5);
      float drip = smoothstep(0.62, 0.9, hash12(vec2(col, floor(wP.y / 7.0)))) * smoothstep(0.2, 0.0, abs(fract(uv.x * 2.5) - 0.5) - 0.1);
      float fall = smoothstep(0.0, 0.6, fract(-wP.y / 7.0 + hash12(vec2(col, 5.0))));
      base *= 1.0 - 0.4 * drip * fall * wet;
      rough = mix(rough, rough * 0.7, wet * 0.6);
    } else {
      base *= 1.0 - 0.3 * wet;
      rough = mix(rough, 0.35, wet);
    }
  } else if (kind == 1) {
    // stone setts on a 1 m grid, jointed; wet: darker and polished, water standing in the joints
    vec2 g = fract(uv); vec2 id = floor(uv);
    float joint = 1.0 - smoothstep(0.015, 0.04, min(min(g.x, 1.0 - g.x), min(g.y, 1.0 - g.y)));
    base *= (0.8 + 0.35 * hash12(id)) * (0.85 + 0.3 * fbm(uv * 2.2));
    base *= 1.0 - 0.45 * joint;
    base *= 1.0 - 0.35 * wet;
    rough = mix(rough, mix(0.06, rough, joint), wet);
    if (uRain > 0.0) {
      // rain on the floor: rings that grow and fade, one drop a cell of 0.7 m, each at its own time
      vec2 rc = floor(wP.xz / 0.7); vec2 rf = fract(wP.xz / 0.7) - 0.5;
      float ph = fract(uTime * 0.9 + hash12(rc));
      vec2 off = vec2(hash12(rc + 7.1), hash12(rc + 3.3)) - 0.5;
      float r = length(rf - off * 0.5);
      float ring = sin((r - ph * 0.45) * 60.0) * smoothstep(0.1, 0.0, abs(r - ph * 0.45)) * (1.0 - ph);
      pn = normalize(n + vec3(rf.x, 0.0, rf.y) * ring * 0.35 * uRain);
    }
  } else if (kind == 2) {
    base = vA.rgb; rough = vA.a;
    if (uRain > 0.0) {
      vec2 rc = floor(wP.xz / 0.45); vec2 rf = fract(wP.xz / 0.45) - 0.5;
      float ph = fract(uTime * 1.1 + hash12(rc));
      float r = length(rf);
      float ring = sin((r - ph * 0.4) * 70.0) * smoothstep(0.08, 0.0, abs(r - ph * 0.4)) * (1.0 - ph);
      pn = normalize(n + vec3(rf.x, 0.0, rf.y) * ring * 0.5 * uRain);
    }
  } else if (kind == 4) {
    base *= 0.9 + 0.2 * noise(uv * 8.0);
  }
  vec3 v = normalize(uEye - wP);
  int cell = cellIndex(wP.xz + n.xz * 0.12);
  vec3 col = vec3(0.0);
  // the moon, shadowed
  float sh = uMirror > 0.5 ? 1.0 : shadowAt(wP, n);
  col += brdf(pn, v, uMoonDir, base, rough, metal) * uMoonCol * sh;
  // the sky's light, dimmed by what stands around and above
  float ao = skyAO(wP, n);
  col += base * uSkyCol * (0.6 + 0.4 * n.y) * ao;
  // every point light
  for (int i = 0; i < 160; i++) {
    if (i >= uNL) break;
    col += pointLight(i, wP, pn, v, base, rough, metal, cell, true);
  }
  // light thrown up from the lit floor onto what faces down (the undersides of slabs, a cornice)
  if (n.y < -0.5) {
    vec3 fp = vec3(wP.x, 0.0, wP.z); int fc = cellIndex(fp.xz); vec3 up = vec3(0.0, 1.0, 0.0);
    vec3 irr = vec3(0.0);
    for (int i = 0; i < 160; i++) { if (i >= uNL) break; irr += pointLight(i, fp, up, up, vec3(1.0), 1.0, 0.0, fc, false); }
    irr += uMoonCol * max(uMoonDir.y, 0.0) / PI;
    col += base * irr * 0.22 * exp(-wP.y / 9.0);
  }
  col += em;
  // the floor's mirror: the scene above, through the rain's rings, as wet as the surface is smooth
  if (uHasRefl > 0.5 && n.y > 0.9 && wP.y < 0.05 && (kind == 1 || kind == 2)) {
    vec2 suv = gl_FragCoord.xy / uView + pn.xz * 0.06;
    float lod = clamp(rough * 7.0, 0.0, 6.0);
    vec3 r = textureLod(uRefl, suv, lod).rgb;
    float fres = 0.02 + 0.98 * pow(1.0 - max(dot(pn, v), 0.0), 5.0);
    float k = kind == 2 ? 1.0 : mix(0.2, 1.0, wet) * (1.0 - rough);
    col += r * clamp(fres * k + (kind == 2 ? 0.35 : 0.12) * wet * (1.0 - rough), 0.0, 1.0);
  }
  // height fog, and the lamps' glow in it
  float dist = length(uEye - wP);
  float fh = exp(-max(wP.y, 0.0) * 0.06);
  float fog = 1.0 - exp(-uFogD * dist * (0.4 + 0.6 * fh));
  vec3 fogLit = uFogCol + uMoonCol * 0.05;
  col = mix(col, fogLit, fog);
  col += fogGlow(uEye, -v, dist);
  o = vec4(col, 1.0);
}`;

  const VS_FULL = COMMON + `
out vec2 vUV; void main() { vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2); vUV = p; gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0); }`;
  const FS_SKY = COMMON + `
in vec2 vUV; out vec4 o;
uniform mat4 uInvVP; uniform vec3 uMoonDir; uniform vec3 uMoonCol; uniform vec3 uFogCol; uniform vec3 uSkyCol; uniform float uMirror;
float hash12(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
void main() {
  vec4 a = uInvVP * vec4(vUV * 2.0 - 1.0, 1.0, 1.0); vec3 d = normalize(a.xyz / a.w);
  if (uMirror > 0.5) d.y = -d.y;
  float up = clamp(d.y, -0.2, 1.0);
  vec3 col = mix(uFogCol * 1.3, uSkyCol * 0.6, smoothstep(0.0, 0.5, up));
  // the city's glow on the low cloud, warm, strongest low in the north-east
  col += vec3(0.055, 0.03, 0.025) * exp(-max(up, 0.0) * 9.0) * (0.6 + 0.4 * max(dot(normalize(d.xz), normalize(vec2(0.7, -0.7))), 0.0));
  float md = dot(d, uMoonDir);
  col += uMoonCol * (smoothstep(0.9993, 0.9996, md) * 30.0 + pow(max(md, 0.0), 300.0) * 0.6 + pow(max(md, 0.0), 12.0) * 0.06);
  if (up > 0.05) { vec2 s = floor(d.xz / (d.y + 0.2) * 240.0); float st = step(0.9985, hash12(s)); col += st * 0.03 * smoothstep(0.05, 0.4, up); }
  o = vec4(col, 1.0);
}`;
  const VS_RAIN = COMMON + `
in vec2 aQ; in vec4 aSeed;
uniform mat4 uVP; uniform vec3 uEye; uniform float uTime; uniform vec3 uWind;
out float vA; out vec2 vQ;
void main() {
  const float R = 26.0, H = 22.0;
  vec3 p = aSeed.xyz * vec3(2.0 * R, H, 2.0 * R);
  float speed = 9.0 + 3.0 * aSeed.w;
  p.y = mod(p.y - uTime * speed, H);
  p.xz += uWind.xz * (H - p.y) * 0.08;
  vec3 c = vec3(uEye.x - R, 0.0, uEye.z - R);
  p.xz = c.xz + mod(p.xz - c.xz, 2.0 * R);
  vec3 dir = normalize(vec3(uWind.x * 0.08, -1.0, uWind.z * 0.08));
  float len = 0.45 + 0.35 * aSeed.w;
  vec3 tip = p + dir * len * aQ.y;
  vec3 toEye = normalize(uEye - tip); vec3 side = normalize(cross(dir, toEye));
  tip += side * aQ.x * 0.006;
  // fading out far away, at the floor, and very near the eye, where a single drop would fill the view
  vA = smoothstep(R, R * 0.4, length(uEye.xz - p.xz)) * smoothstep(0.0, 1.5, p.y) * smoothstep(0.6, 2.5, length(uEye - p));
  vQ = aQ;
  gl_Position = uVP * vec4(tip, 1.0);
}`;
  const FS_RAIN = COMMON + `
in float vA; in vec2 vQ; out vec4 o; uniform vec3 uRainCol; uniform float uRain;
void main() { float e = 1.0 - abs(vQ.x); o = vec4(uRainCol * vA * e * uRain, 1.0); }`;
  const FS_BRIGHT = COMMON + `
in vec2 vUV; out vec4 o; uniform sampler2D uSrc; uniform float uExpo;
void main() { vec3 c = texture(uSrc, vUV).rgb * uExpo; float l = max(max(c.r, c.g), c.b); o = vec4(c * smoothstep(1.0, 4.0, l), 1.0); }`;
  const FS_BLUR = COMMON + `
in vec2 vUV; out vec4 o; uniform sampler2D uSrc; uniform vec2 uDir;
void main() {
  vec3 s = texture(uSrc, vUV).rgb * 0.227;
  s += (texture(uSrc, vUV + uDir * 1.385).rgb + texture(uSrc, vUV - uDir * 1.385).rgb) * 0.316;
  s += (texture(uSrc, vUV + uDir * 3.231).rgb + texture(uSrc, vUV - uDir * 3.231).rgb) * 0.070;
  o = vec4(s, 1.0);
}`;
  const FS_FINAL = COMMON + `
in vec2 vUV; out vec4 o; uniform sampler2D uSrc; uniform sampler2D uBloom1; uniform sampler2D uBloom2; uniform float uExpo; uniform float uBloom; uniform float uTime;
vec3 aces(vec3 x) { return clamp(x * (2.51 * x + 0.03) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0); }
float hash12(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
void main() {
  vec3 c = texture(uSrc, vUV).rgb * uExpo;
  c += (texture(uBloom1, vUV).rgb * 0.6 + texture(uBloom2, vUV).rgb * 0.8) * uBloom;
  vec2 q = vUV - 0.5; c *= 1.0 - 0.35 * dot(q, q) * 1.6;
  c = aces(c);
  c = pow(c, vec3(1.0 / 2.2));
  c += (hash12(gl_FragCoord.xy + fract(uTime) * 91.0) - 0.5) * 0.012;
  o = vec4(c, 1.0);
}`;

  function compile(gl, vs, fs) {
    const mk = function (t, s) {
      const x = gl.createShader(t); gl.shaderSource(x, s); gl.compileShader(x);
      if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) throw new Error("shader: " + gl.getShaderInfoLog(x));
      return x;
    };
    const p = gl.createProgram();
    gl.attachShader(p, mk(gl.VERTEX_SHADER, vs)); gl.attachShader(p, mk(gl.FRAGMENT_SHADER, fs));
    gl.bindAttribLocation(p, 0, "aP"); gl.bindAttribLocation(p, 1, "aN"); gl.bindAttribLocation(p, 2, "aA");
    gl.bindAttribLocation(p, 3, "aE"); gl.bindAttribLocation(p, 4, "aK");
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error("program: " + gl.getProgramInfoLog(p));
    const u = {};
    const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (let i = 0; i < n; i++) { const a = gl.getActiveUniform(p, i); u[a.name] = gl.getUniformLocation(p, a.name); }
    return { p: p, u: u };
  }

  // ---------------------------------------------------------------- the scene, as triangles
  // the pattern a face is drawn with, from what the piece is: never from a material's name
  function kindOf(piece, S) {
    const id = piece.id || "", m = S.materials[piece.material];
    if (m && m.emissive_strength > 0) return 3;
    if (id.indexOf("puddle:") === 0) return 2;
    if (id.indexOf("lamp:") === 0 || id.indexOf(":light") > 0 || (m && m.metallic > 0.5)) return 4;
    if (piece.kind && piece.kind !== "wall" && piece.kind !== "cover") return 1;   // ground, floor, stair, raised
    return 0;
  }
  function geometry(S) {
    const P = [], N = [], A = [], E = [], K = [];
    const lens = {};
    for (const L of S.lights) if (L.type === "point") lens[L.id] = lin(L.color).map(function (v) { return v * Math.min(L.candela, 2000) * 0.012; });
    const add = function (b, m, kind, id) {
      const [x0, y0, z0, x1, y1, z1] = b, base = lin(m.base), em0 = lin(m.emissive).map(function (v) { return v * m.emissive_strength * 0.12; });
      const faces = [[[1, 0, 0], [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]]], [[-1, 0, 0], [[x0, y0, z1], [x0, y1, z1], [x0, y1, z0], [x0, y0, z0]]],
        [[0, 1, 0], [[x0, y1, z0], [x0, y1, z1], [x1, y1, z1], [x1, y1, z0]]], [[0, -1, 0], [[x0, y0, z1], [x0, y0, z0], [x1, y0, z0], [x1, y0, z1]]],
        [[0, 0, 1], [[x1, y0, z1], [x1, y1, z1], [x0, y1, z1], [x0, y0, z1]]], [[0, 0, -1], [[x0, y0, z0], [x0, y1, z0], [x1, y1, z0], [x1, y0, z0]]]];
      for (const [nrm, v] of faces) {
        // a floor-like piece is stone on its top and concrete on its sides; a lamp's housing glows below, its lens
        const k = kind === 1 && nrm[1] !== 1 ? 0 : kind;
        const em = nrm[1] === -1 && lens[id] ? lens[id] : em0;
        for (const i of [0, 1, 2, 0, 2, 3]) { P.push(v[i][0], v[i][1], v[i][2]); N.push(nrm[0], nrm[1], nrm[2]); A.push(base[0], base[1], base[2], m.roughness); E.push(em[0], em[1], em[2], m.metallic); K.push(k); }
      }
    };
    for (const b of S.collision) add(b.box, S.materials[b.material], kindOf(b, S), b.id);
    for (const v of S.visuals) add(v.box, S.materials[v.material], kindOf(v, S), v.id);
    return { P: new Float32Array(P), N: new Float32Array(N), A: new Float32Array(A), E: new Float32Array(E), K: new Float32Array(K), count: P.length / 3 };
  }

  // which cells each light can see across the grid: a 2D line of sight that rock (a top at the wall's height) stops
  function visibility(S, lights) {
    const g = S.grid, w = g.w, h = g.h, c = g.cell, rock = function (x, z) { return x < 0 || z < 0 || x >= w || z >= h || S.tops[z * w + x] >= g.wall; };
    const out = new Uint8Array(w * h * Math.max(lights.length, 1));
    lights.forEach(function (L, li) {
      const lx = L.pos[0] / c, lz = L.pos[2] / c, high = L.pos[1] > g.wall + 0.5;
      for (let z = 0; z < h; z++) for (let x = 0; x < w; x++) {
        let seen = true;
        if (!high) {
          const tx = x + 0.5, tz = z + 0.5, dx = tx - lx, dz = tz - lz, n = Math.ceil(Math.hypot(dx, dz) * 3);
          for (let s = 1; s < n && seen; s++) {
            const px = Math.floor(lx + dx * s / n), pz = Math.floor(lz + dz * s / n);
            if ((px !== x || pz !== z) && (px !== Math.floor(lx) || pz !== Math.floor(lz)) && rock(px, pz)) seen = false;
          }
        }
        out[li * w * h + z * w + x] = seen ? 255 : 0;
      }
    });
    return out;
  }

  // ---------------------------------------------------------------- the renderer
  // The context, the programs, the targets' boxes and the rain are the renderer's own; everything drawn from the scene
  // (its triangles, lights, line-of-sight grid, heightfield, roof, environment and the moon's shadow) is made by load(S),
  // which a live edit calls again with the new scene: the old scene's objects are freed and nothing else is touched.
  function Renderer(canvas, S, opts) {
    opts = opts || {};
    const gl = canvas.getContext("webgl2", { antialias: false, preserveDrawingBuffer: true, alpha: false });
    if (!gl) throw new Error("WebGL 2 is not available in this browser");
    if (!gl.getExtension("EXT_color_buffer_float")) throw new Error("this browser cannot render to floating-point targets (EXT_color_buffer_float)");
    gl.getExtension("OES_texture_float_linear");
    this.gl = gl; this.canvas = canvas; this.opts = opts;
    this.progScene = compile(gl, VS_SCENE, FS_SCENE);
    this.progDepth = compile(gl, VS_DEPTH, FS_DEPTH);
    this.progSky = compile(gl, VS_FULL, FS_SKY);
    this.progBright = compile(gl, VS_FULL, FS_BRIGHT);
    this.progBlur = compile(gl, VS_FULL, FS_BLUR);
    this.progFinal = compile(gl, VS_FULL, FS_FINAL);
    this.progRain = compile(gl, VS_RAIN, FS_RAIN);
    this.own = [];   // [kind, object]: what dispose() frees besides the scene's and the targets'
    // dynamic boxes (the targets), drawn with the same program
    this.dynVao = gl.createVertexArray(); this.dynBufs = [];
    gl.bindVertexArray(this.dynVao);
    for (let i = 0; i < 5; i++) { const b = gl.createBuffer(); this.dynBufs.push(b); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.enableVertexAttribArray(i); gl.vertexAttribPointer(i, [3, 3, 4, 4, 1][i], gl.FLOAT, false, 0, 0); }
    // rain
    const NR = opts.rainDrops || 7000, seeds = new Float32Array(NR * 4);
    let st = 12345;
    const rnd = function () { st = (st * 1103515245 + 12345) & 0x7fffffff; return st / 0x7fffffff; };
    for (let i = 0; i < NR * 4; i++) seeds[i] = rnd();
    this.rainVao = gl.createVertexArray(); gl.bindVertexArray(this.rainVao);
    const qb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, qb);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, 0, 1, 0, 1, 1, -1, 0, 1, 1, -1, 1]), gl.STATIC_DRAW);
    const qa = gl.getAttribLocation(this.progRain.p, "aQ"), sa = gl.getAttribLocation(this.progRain.p, "aSeed");
    gl.enableVertexAttribArray(qa); gl.vertexAttribPointer(qa, 2, gl.FLOAT, false, 0, 0);
    const sb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, sb); gl.bufferData(gl.ARRAY_BUFFER, seeds, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(sa); gl.vertexAttribPointer(sa, 4, gl.FLOAT, false, 0, 0); gl.vertexAttribDivisor(sa, 1);
    this.nRain = NR;
    this.emptyVao = gl.createVertexArray();
    gl.bindVertexArray(null);
    this.own.push(["vao", this.dynVao], ["vao", this.rainVao], ["vao", this.emptyVao], ["buf", qb], ["buf", sb]);
    this.dynBufs.forEach(function (b) { this.own.push(["buf", b]); }, this);
    this.shadowSize = Math.min(4096, gl.getParameter(gl.MAX_TEXTURE_SIZE));
    this.sceneObjs = []; this.targetObjs = [];
    this.targets = null; this.size = [0, 0]; this.nDyn = 0;
    this.load(S);
  }
  // free a list of [kind, object]
  Renderer.prototype.free = function (list) {
    const gl = this.gl;
    for (const [k, o] of list) {
      if (k === "buf") gl.deleteBuffer(o); else if (k === "vao") gl.deleteVertexArray(o); else if (k === "tex") gl.deleteTexture(o);
      else if (k === "fb") gl.deleteFramebuffer(o); else if (k === "rb") gl.deleteRenderbuffer(o); else if (k === "prog") gl.deleteProgram(o);
    }
    list.length = 0;
  };
  // draw this scene from now on: everything made from the previous scene is freed first
  Renderer.prototype.load = function (S) {
    const gl = this.gl, own = this.sceneObjs, opts = this.opts;
    this.free(own);
    this.S = S;
    // static geometry
    const G = geometry(S);
    this.count = G.count; this.triangles = G.count / 3;
    this.vao = gl.createVertexArray(); gl.bindVertexArray(this.vao); own.push(["vao", this.vao]);
    [[G.P, 3], [G.N, 3], [G.A, 4], [G.E, 4], [G.K, 1]].forEach(function (a, i) {
      const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, a[0], gl.STATIC_DRAW);
      gl.enableVertexAttribArray(i); gl.vertexAttribPointer(i, a[1], gl.FLOAT, false, 0, 0);
      own.push(["buf", b]);
    });
    gl.bindVertexArray(null);
    // the lights, as a texture: (position, radius) and (colour times intensity, downlight)
    const lights = S.lights.slice(0, 160);
    this.nl = lights.length;
    const NL = Math.max(this.nl, 1), lt = new Float32Array(NL * 8);
    lights.forEach(function (L, i) {
      const c = lin(L.color), k = L.candela * (L.type === "rect" ? 2.2 : 1.0);
      lt.set([L.pos[0], L.pos[1], L.pos[2], L.radius], i * 4);
      lt.set([c[0] * k, c[1] * k, c[2] * k, L.dir && L.dir[1] < -0.5 && L.id.indexOf(":light") > 0 ? 1 : 0], (NL + i) * 4);
    });
    this.texLights = this.tex2D(gl.RGBA32F, NL, 2, gl.RGBA, gl.FLOAT, lt, gl.NEAREST);
    const g = S.grid, wh = g.w * g.h;
    this.texVis = this.tex2D(gl.R8, wh, NL, gl.RED, gl.UNSIGNED_BYTE, visibility(S, lights), gl.NEAREST);
    // the heightfield (the highest solid over each cell) and the roof (the lowest slab hanging over it)
    const height = new Float32Array(wh), roof = new Float32Array(wh).fill(1e4);
    for (let k = 0; k < wh; k++) height[k] = S.tops[k];
    const over = function (b, fn) {
      for (let z = Math.max(0, Math.floor(b[2] / g.cell)); z < Math.min(g.h, Math.ceil(b[5] / g.cell)); z++)
        for (let x = Math.max(0, Math.floor(b[0] / g.cell)); x < Math.min(g.w, Math.ceil(b[3] / g.cell)); x++) fn(z * g.w + x);
    };
    for (const v of S.visuals) {
      const b = v.box;
      over(b, function (k) {
        if (b[1] <= S.tops[k] + 0.05) height[k] = Math.max(height[k], b[4]);
        else if (b[1] > (S.reach[k] || 0) - 0.5 && b[3] - b[0] > 1 && b[5] - b[2] > 1) roof[k] = Math.min(roof[k], b[1]);
      });
    }
    this.texHeight = this.tex2D(gl.R32F, g.w, g.h, gl.RED, gl.FLOAT, height, gl.NEAREST);
    this.texRoof = this.tex2D(gl.R32F, g.w, g.h, gl.RED, gl.FLOAT, roof, gl.NEAREST);
    own.push(["tex", this.texLights], ["tex", this.texVis], ["tex", this.texHeight], ["tex", this.texRoof]);
    // the environment
    const env = S.environment || {}, L = env.light, fog = env.fog;
    const az = (L ? L.azimuth : 215) * Math.PI / 180, el = (L ? L.elevation : 25) * Math.PI / 180;
    this.moonDir = [Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el)];
    // the moon is toward the azimuth; its light comes from there
    const mc = L ? lin(L.color) : [0.6, 0.65, 1];
    const lux = L ? L.lux : 0.3;
    this.moonCol = mc.map(function (v) { return v * lux * 5.0; });
    this.fogCol = fog ? lin(fog.color).map(function (v) { return v * 0.55; }) : [0.01, 0.012, 0.016];
    this.skyCol = this.fogCol.map(function (v) { return v * 3.0 + 0.02; });
    this.fogD = fog ? fog.density * 0.55 : 0.01;
    this.rain = env.rain || 0;
    this.expo = Math.pow(2, env.exposure || 0) * 0.42;
    this.bloom = env.bloom === undefined ? 0.6 : env.bloom;
    this.lightScale = opts.lightScale || 0.05;
    this.glow = opts.glow === undefined ? 0.008 : opts.glow;
    this.buildShadow();
  };
  // free everything this renderer made; it draws nothing after
  Renderer.prototype.dispose = function () {
    this.free(this.sceneObjs); this.free(this.targetObjs); this.free(this.own);
    for (const k of ["progScene", "progDepth", "progSky", "progBright", "progBlur", "progFinal", "progRain"]) this.gl.deleteProgram(this[k].p);
    this.size = [0, 0];
  };
  Renderer.prototype.tex2D = function (ifmt, w, h, fmt, type, data, filter) {
    const gl = this.gl, t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texImage2D(gl.TEXTURE_2D, 0, ifmt, w, h, 0, fmt, type, data);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return t;
  };
  Renderer.prototype.target = function (w, h, mips) {
    const gl = this.gl, t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    const levels = mips ? Math.floor(Math.log2(Math.max(w, h))) + 1 : 1;
    gl.texStorage2D(gl.TEXTURE_2D, levels, gl.RGBA16F, w, h);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, mips ? gl.LINEAR_MIPMAP_LINEAR : gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
    this.targetObjs.push(["tex", t], ["fb", f]);
    return { tex: t, fb: f, w: w, h: h };
  };
  Renderer.prototype.buildShadow = function () {
    const gl = this.gl, S = this.S, n = this.shadowSize;
    let x0 = 1e9, z0 = 1e9, x1 = -1e9, z1 = -1e9, y1 = 0;
    for (const b of S.collision.concat(S.visuals)) { x0 = Math.min(x0, b.box[0]); z0 = Math.min(z0, b.box[2]); x1 = Math.max(x1, b.box[3]); z1 = Math.max(z1, b.box[5]); y1 = Math.max(y1, b.box[4]); }
    const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, R = Math.hypot(x1 - x0, z1 - z0, y1) / 2 + 2, d = this.moonDir;
    const V = lookAt([cx + d[0] * R * 2, d[1] * R * 2, cz + d[2] * R * 2], [cx, 0, cz], [0, 1, 0]);
    this.shadowVP = mul(ortho(-R, R, -R, R, 0.1, R * 4), V);
    const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texStorage2D(gl.TEXTURE_2D, 1, gl.DEPTH_COMPONENT32F, n, n);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.TEXTURE_2D, t, 0);
    gl.drawBuffers([gl.NONE]); gl.readBuffer(gl.NONE);
    gl.viewport(0, 0, n, n); gl.clear(gl.DEPTH_BUFFER_BIT); gl.enable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE);
    gl.useProgram(this.progDepth.p); gl.uniformMatrix4fv(this.progDepth.u.uVP, false, this.shadowVP);
    gl.bindVertexArray(this.vao); gl.drawArrays(gl.TRIANGLES, 0, this.count);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    this.texShadow = t;
    this.sceneObjs.push(["tex", t], ["fb", f]);
  };
  Renderer.prototype.resize = function (w, h) {
    if (this.size[0] === w && this.size[1] === h) return;
    const gl = this.gl, own = this.targetObjs;
    this.free(own);
    this.size = [w, h];
    // the scene: multisampled, in half floats, then resolved
    this.msFb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, this.msFb); own.push(["fb", this.msFb]);
    const samples = Math.min(4, gl.getParameter(gl.MAX_SAMPLES));
    const rc = gl.createRenderbuffer(); gl.bindRenderbuffer(gl.RENDERBUFFER, rc); gl.renderbufferStorageMultisample(gl.RENDERBUFFER, samples, gl.RGBA16F, w, h); own.push(["rb", rc]);
    gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.RENDERBUFFER, rc);
    const rd = gl.createRenderbuffer(); gl.bindRenderbuffer(gl.RENDERBUFFER, rd); gl.renderbufferStorageMultisample(gl.RENDERBUFFER, samples, gl.DEPTH_COMPONENT24, w, h); own.push(["rb", rd]);
    gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.RENDERBUFFER, rd);
    this.color = this.target(w, h, false);
    // the mirror, at half size, with depth, and mipmapped for the rougher surfaces
    const rw = Math.max(2, w >> 1), rh = Math.max(2, h >> 1);
    this.refl = this.target(rw, rh, true);
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.refl.fb);
    const rdd = gl.createRenderbuffer(); gl.bindRenderbuffer(gl.RENDERBUFFER, rdd); gl.renderbufferStorage(gl.RENDERBUFFER, gl.DEPTH_COMPONENT24, rw, rh); own.push(["rb", rdd]);
    gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.RENDERBUFFER, rdd);
    // bloom at a quarter and an eighth
    this.b1 = this.target(Math.max(2, w >> 2), Math.max(2, h >> 2), false); this.b1b = this.target(this.b1.w, this.b1.h, false);
    this.b2 = this.target(Math.max(2, w >> 3), Math.max(2, h >> 3), false); this.b2b = this.target(this.b2.w, this.b2.h, false);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  };
  // the movers' boxes this frame ([x0, y0, z0, x1, y1, z1] each, in the scene's order), drawn with the next setTargets
  Renderer.prototype.setMovers = function (boxes) { this.moverBoxes = (boxes || []).slice(0, MAX_MOVERS); };
  Renderer.prototype.setTargets = function (boxes) {
    // the targets (gameplay marks, not art): upright boxes in a plain red, drawn as the simulation places them
    const gl = this.gl, P = [], N = [], A = [], E = [], K = [];
    // the movers, in their materials: stone on top and concrete on their sides, as a floor is
    const ms = (this.S && this.S.movers) || [], mb = this.moverBoxes || [];
    for (let i = 0; i < Math.min(ms.length, mb.length); i++) {
      const m = this.S.materials[ms[i].material], [x0, y0, z0, x1, y1, z1] = mb[i], base = lin(m.base), em = lin(m.emissive).map(function (v) { return v * m.emissive_strength * 0.12; });
      const faces = [[[1, 0, 0], [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]]], [[-1, 0, 0], [[x0, y0, z1], [x0, y1, z1], [x0, y1, z0], [x0, y0, z0]]],
        [[0, 1, 0], [[x0, y1, z0], [x0, y1, z1], [x1, y1, z1], [x1, y1, z0]]], [[0, -1, 0], [[x0, y0, z1], [x0, y0, z0], [x1, y0, z0], [x1, y0, z1]]],
        [[0, 0, 1], [[x1, y0, z1], [x1, y1, z1], [x0, y1, z1], [x0, y0, z1]]], [[0, 0, -1], [[x0, y0, z0], [x0, y1, z0], [x1, y1, z0], [x1, y0, z0]]]];
      for (const [nrm, v] of faces) for (const j of [0, 1, 2, 0, 2, 3]) {
        P.push(...v[j]); N.push(...nrm); A.push(base[0], base[1], base[2], m.roughness); E.push(em[0], em[1], em[2], m.metallic); K.push(nrm[1] === 1 ? 1 : 0);
      }
    }
    for (const b of boxes) {
      const [x0, y0, z0, x1, y1, z1] = b.box, col = b.up ? [0.35, 0.04, 0.03] : [0.08, 0.02, 0.02], em = b.up ? [0.05, 0.004, 0.002] : [0, 0, 0];
      const faces = [[[1, 0, 0], [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]]], [[-1, 0, 0], [[x0, y0, z1], [x0, y1, z1], [x0, y1, z0], [x0, y0, z0]]],
        [[0, 1, 0], [[x0, y1, z0], [x0, y1, z1], [x1, y1, z1], [x1, y1, z0]]], [[0, 0, 1], [[x1, y0, z1], [x1, y1, z1], [x0, y1, z1], [x0, y0, z1]]], [[0, 0, -1], [[x0, y0, z0], [x0, y1, z0], [x1, y1, z0], [x1, y0, z0]]]];
      for (const [nrm, v] of faces) for (const i of [0, 1, 2, 0, 2, 3]) { P.push(...v[i]); N.push(...nrm); A.push(col[0], col[1], col[2], 0.5); E.push(em[0], em[1], em[2], 0); K.push(4); }
    }
    [P, N, A, E, K].forEach(function (a, i) { gl.bindBuffer(gl.ARRAY_BUFFER, this.dynBufs[i]); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(a), gl.DYNAMIC_DRAW); }, this);
    this.nDyn = P.length / 3;
  };
  Renderer.prototype.sceneUniforms = function (pr, eye, time, mirror, vw, vh) {
    const gl = this.gl, u = pr.u, g = this.S.grid;
    gl.uniform3fv(u.uEye, eye); gl.uniform1f(u.uTime, time); gl.uniform1f(u.uMirror, mirror ? 1 : 0); gl.uniform2f(u.uView, vw, vh);
    gl.uniform3fv(u.uMoonDir, this.moonDir); gl.uniform3fv(u.uMoonCol, this.moonCol); gl.uniform3fv(u.uSkyCol, this.skyCol);
    gl.uniform3fv(u.uFogCol, this.fogCol); gl.uniform1f(u.uFogD, this.fogD); gl.uniform1f(u.uRain, this.rain);
    gl.uniformMatrix4fv(u.uShadowVP, false, this.shadowVP); gl.uniform1f(u.uShadowTexel, 1 / this.shadowSize);
    gl.uniform1i(u.uNL, this.nl); gl.uniform4f(u.uGrid, g.w, g.h, g.cell, g.wall); gl.uniform1f(u.uLightScale, this.lightScale); gl.uniform1f(u.uGlow, this.glow);
    gl.uniform1f(u.uHasRefl, mirror ? 0 : 1);
    const bind = function (unit, tex, name) { gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, tex); gl.uniform1i(u[name], unit); };
    bind(0, this.texShadow, "uShadow"); bind(1, this.texLights, "uLights"); bind(2, this.texVis, "uVis");
    bind(3, this.texHeight, "uHeight"); bind(4, this.texRoof, "uRoof"); bind(5, mirror ? this.texHeight : this.refl.tex, "uRefl");
  };
  Renderer.prototype.drawSky = function (vp, mirror) {
    const gl = this.gl, pr = this.progSky;
    gl.useProgram(pr.p); gl.depthMask(false); gl.disable(gl.DEPTH_TEST);
    gl.uniformMatrix4fv(pr.u.uInvVP, false, invert(vp)); gl.uniform3fv(pr.u.uMoonDir, this.moonDir); gl.uniform3fv(pr.u.uMoonCol, this.moonCol);
    gl.uniform3fv(pr.u.uFogCol, this.fogCol); gl.uniform3fv(pr.u.uSkyCol, this.skyCol); gl.uniform1f(pr.u.uMirror, mirror ? 1 : 0);
    gl.bindVertexArray(this.emptyVao); gl.drawArrays(gl.TRIANGLES, 0, 3);
    gl.depthMask(true); gl.enable(gl.DEPTH_TEST);
  };
  Renderer.prototype.drawGeometry = function (vp, eye, time, mirror, vw, vh) {
    const gl = this.gl, pr = this.progScene;
    gl.useProgram(pr.p); this.sceneUniforms(pr, eye, time, mirror, vw, vh);
    gl.uniformMatrix4fv(pr.u.uVP, false, vp);
    gl.bindVertexArray(this.vao); gl.drawArrays(gl.TRIANGLES, 0, this.count);
    if (this.nDyn) { gl.bindVertexArray(this.dynVao); gl.drawArrays(gl.TRIANGLES, 0, this.nDyn); }
  };
  Renderer.prototype.fullscreen = function (pr, dst, w, h) {
    const gl = this.gl;
    gl.bindFramebuffer(gl.FRAMEBUFFER, dst); gl.viewport(0, 0, w, h); gl.useProgram(pr.p);
    gl.bindVertexArray(this.emptyVao); gl.drawArrays(gl.TRIANGLES, 0, 3);
  };
  Renderer.prototype.bindTex = function (pr, unit, tex, name) { const gl = this.gl; gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, tex); gl.uniform1i(pr.u[name], unit); };
  // draw one frame from a camera; time in seconds (the rain and its rings)
  Renderer.prototype.draw = function (cam, time) {
    const gl = this.gl, cv = this.canvas, w = cv.width, h = cv.height;
    this.resize(w, h);
    const fov = (cam.fov || 66) * Math.PI / 180, Pm = persp(fov, w / h, 0.08, 900), V = viewOf(cam), VP = mul(Pm, V);
    const eye = [cam.x, cam.y, cam.z];
    gl.enable(gl.DEPTH_TEST); gl.depthFunc(gl.LEQUAL);
    // 1. the mirror: the scene reflected in the floor's plane
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.refl.fb); gl.viewport(0, 0, this.refl.w, this.refl.h);
    gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    const VPm = mul(VP, MIRROR);
    gl.enable(gl.CULL_FACE); gl.cullFace(gl.FRONT);
    this.drawSky(VP, true);
    this.drawGeometry(VPm, [cam.x, -cam.y, cam.z], time, true, this.refl.w, this.refl.h);
    gl.cullFace(gl.BACK);
    gl.bindTexture(gl.TEXTURE_2D, this.refl.tex); gl.generateMipmap(gl.TEXTURE_2D);
    // 2. the scene
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.msFb); gl.viewport(0, 0, w, h);
    gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    this.drawSky(VP, false);
    this.drawGeometry(VP, eye, time, false, w, h);
    // 3. rain
    if (this.rain > 0) {
      const pr = this.progRain;
      gl.useProgram(pr.p); gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE); gl.depthMask(false); gl.disable(gl.CULL_FACE);
      gl.uniformMatrix4fv(pr.u.uVP, false, VP); gl.uniform3fv(pr.u.uEye, eye); gl.uniform1f(pr.u.uTime, time);
      gl.uniform3f(pr.u.uWind, 2.0, 0, -1.0); gl.uniform3f(pr.u.uRainCol, 0.035, 0.04, 0.05); gl.uniform1f(pr.u.uRain, this.rain);
      gl.bindVertexArray(this.rainVao); gl.drawArraysInstanced(gl.TRIANGLES, 0, 6, this.nRain);
      gl.disable(gl.BLEND); gl.depthMask(true); gl.enable(gl.CULL_FACE);
    }
    gl.disable(gl.CULL_FACE);
    gl.bindFramebuffer(gl.READ_FRAMEBUFFER, this.msFb); gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, this.color.fb);
    gl.blitFramebuffer(0, 0, w, h, 0, 0, w, h, gl.COLOR_BUFFER_BIT, gl.NEAREST);
    gl.disable(gl.DEPTH_TEST);
    // 4. bloom
    let pr = this.progBright; gl.useProgram(pr.p); this.bindTex(pr, 0, this.color.tex, "uSrc"); gl.uniform1f(pr.u.uExpo, this.expo);
    this.fullscreen(pr, this.b1.fb, this.b1.w, this.b1.h);
    pr = this.progBlur;
    const blur = function (self, src, tmp, n) {
      for (let k = 0; k < n; k++) {
        gl.useProgram(pr.p); self.bindTex(pr, 0, src.tex, "uSrc"); gl.uniform2f(pr.u.uDir, 1 / src.w, 0); self.fullscreen(pr, tmp.fb, tmp.w, tmp.h);
        gl.useProgram(pr.p); self.bindTex(pr, 0, tmp.tex, "uSrc"); gl.uniform2f(pr.u.uDir, 0, 1 / tmp.h); self.fullscreen(pr, src.fb, src.w, src.h);
      }
    };
    blur(this, this.b1, this.b1b, 2);
    gl.useProgram(pr.p); this.bindTex(pr, 0, this.b1.tex, "uSrc"); gl.uniform2f(pr.u.uDir, 0, 0); this.fullscreen(pr, this.b2.fb, this.b2.w, this.b2.h);
    blur(this, this.b2, this.b2b, 3);
    // 5. the tone curve, to the screen
    pr = this.progFinal; gl.useProgram(pr.p);
    this.bindTex(pr, 0, this.color.tex, "uSrc"); this.bindTex(pr, 1, this.b1.tex, "uBloom1"); this.bindTex(pr, 2, this.b2.tex, "uBloom2");
    gl.uniform1f(pr.u.uExpo, this.expo); gl.uniform1f(pr.u.uBloom, this.bloom * 0.6); gl.uniform1f(pr.u.uTime, time);
    this.fullscreen(pr, null, w, h);
    gl.enable(gl.DEPTH_TEST);
  };

  function invert(m) {
    const inv = new Float32Array(16);
    inv[0] = m[5] * m[10] * m[15] - m[5] * m[11] * m[14] - m[9] * m[6] * m[15] + m[9] * m[7] * m[14] + m[13] * m[6] * m[11] - m[13] * m[7] * m[10];
    inv[4] = -m[4] * m[10] * m[15] + m[4] * m[11] * m[14] + m[8] * m[6] * m[15] - m[8] * m[7] * m[14] - m[12] * m[6] * m[11] + m[12] * m[7] * m[10];
    inv[8] = m[4] * m[9] * m[15] - m[4] * m[11] * m[13] - m[8] * m[5] * m[15] + m[8] * m[7] * m[13] + m[12] * m[5] * m[11] - m[12] * m[7] * m[9];
    inv[12] = -m[4] * m[9] * m[14] + m[4] * m[10] * m[13] + m[8] * m[5] * m[14] - m[8] * m[6] * m[13] - m[12] * m[5] * m[10] + m[12] * m[6] * m[9];
    inv[1] = -m[1] * m[10] * m[15] + m[1] * m[11] * m[14] + m[9] * m[2] * m[15] - m[9] * m[3] * m[14] - m[13] * m[2] * m[11] + m[13] * m[3] * m[10];
    inv[5] = m[0] * m[10] * m[15] - m[0] * m[11] * m[14] - m[8] * m[2] * m[15] + m[8] * m[3] * m[14] + m[12] * m[2] * m[11] - m[12] * m[3] * m[10];
    inv[9] = -m[0] * m[9] * m[15] + m[0] * m[11] * m[13] + m[8] * m[1] * m[15] - m[8] * m[3] * m[13] - m[12] * m[1] * m[11] + m[12] * m[3] * m[9];
    inv[13] = m[0] * m[9] * m[14] - m[0] * m[10] * m[13] - m[8] * m[1] * m[14] + m[8] * m[2] * m[13] + m[12] * m[1] * m[10] - m[12] * m[2] * m[9];
    inv[2] = m[1] * m[6] * m[15] - m[1] * m[7] * m[14] - m[5] * m[2] * m[15] + m[5] * m[3] * m[14] + m[13] * m[2] * m[7] - m[13] * m[3] * m[6];
    inv[6] = -m[0] * m[6] * m[15] + m[0] * m[7] * m[14] + m[4] * m[2] * m[15] - m[4] * m[3] * m[14] - m[12] * m[2] * m[7] + m[12] * m[3] * m[6];
    inv[10] = m[0] * m[5] * m[15] - m[0] * m[7] * m[13] - m[4] * m[1] * m[15] + m[4] * m[3] * m[13] + m[12] * m[1] * m[7] - m[12] * m[3] * m[5];
    inv[14] = -m[0] * m[5] * m[14] + m[0] * m[6] * m[13] + m[4] * m[1] * m[14] - m[4] * m[2] * m[13] - m[12] * m[1] * m[6] + m[12] * m[2] * m[5];
    inv[3] = -m[1] * m[6] * m[11] + m[1] * m[7] * m[10] + m[5] * m[2] * m[11] - m[5] * m[3] * m[10] - m[9] * m[2] * m[7] + m[9] * m[3] * m[6];
    inv[7] = m[0] * m[6] * m[11] - m[0] * m[7] * m[10] - m[4] * m[2] * m[11] + m[4] * m[3] * m[10] + m[8] * m[2] * m[7] - m[8] * m[3] * m[6];
    inv[11] = -m[0] * m[5] * m[11] + m[0] * m[7] * m[9] + m[4] * m[1] * m[11] - m[4] * m[3] * m[9] - m[8] * m[1] * m[7] + m[8] * m[3] * m[5];
    inv[15] = m[0] * m[5] * m[10] - m[0] * m[6] * m[9] - m[4] * m[1] * m[10] + m[4] * m[2] * m[9] + m[8] * m[1] * m[6] - m[8] * m[2] * m[5];
    let det = m[0] * inv[0] + m[1] * inv[4] + m[2] * inv[8] + m[3] * inv[12];
    det = 1 / det;
    for (let i = 0; i < 16; i++) inv[i] *= det;
    return inv;
  }

  root.VerdandiScene = { Renderer: Renderer, viewOf: viewOf, persp: persp, mul: mul };
})(typeof self !== "undefined" ? self : this);
