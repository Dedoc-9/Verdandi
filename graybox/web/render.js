// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/render.js — FPS-VISUAL-0's renderer, WebGL 1: a sky, a sun with shadows, materials, a weapon in hand.
//
// Three worlds, kept apart (the owner's rule, 2026-10-09): the canonical world W says what the map is, the collision
// world C what blocks movement and shots, and this file only how it looks. Every solid it draws inside the map is a
// column of W, at W's height, so of C; a self-test holds the mesh to C face by face. What it adds is decoration —
// materials, trim, windows painted on walls, beams resting on the wall tops, a skyline outside the map, effects, the
// weapon — and the decoration stays out of the volume where play happens: above the highest eye a player can reach,
// or outside the map. It reads the state and writes none of it. The shot is the simulation's, from the eye along
// Sim.aim; the weapon is drawn apart from it and moves only for the eye.
//
// The previous renderer is render_flat.js (`?renderer=flat`). The 1 m grid is a debug overlay here (G, or ?grid=1).

(function (root) {
  "use strict";

  // ---------------------------------------------------------------- the light
  const SUN_ELEVATION = 40 * Math.PI / 180, SUN_AZIMUTH = 25 * Math.PI / 180;   // azimuth from +z (south) toward +x (east)
  const SUN = [Math.cos(SUN_ELEVATION) * Math.sin(SUN_AZIMUTH), Math.sin(SUN_ELEVATION), Math.cos(SUN_ELEVATION) * Math.cos(SUN_AZIMUTH)];
  const FOV = 75 * Math.PI / 180, FOV_HAND = 55 * Math.PI / 180;

  // materials, by number (the shader's ids)
  const M = {
    CONCRETE: 1, TREAD: 2, DECK: 3, MARK: 4, WALL: 5, WALL_TOP: 6, RISER: 7, CRATE: 8, OLIVE: 9, BARRIER: 10,
    PILLAR: 11, BEAM: 12, SKYLINE: 13, TARGET: 14, TARGET_HEAD: 15, STEEL_DARK: 16, GUN_METAL: 17, POLYMER: 18,
    TAN: 19, STEEL: 20, SIGHT: 21,
  };

  // ---------------------------------------------------------------- shaders
  const FS_HEAD = [
    "#ifdef GL_FRAGMENT_PRECISION_HIGH",
    "precision highp float;",
    "#else",
    "precision mediump float;",
    "#endif",
    ""].join("\n");

  const COMMON = `
uniform vec3 uSun;
float h12(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vnoise(vec2 p) {
  vec2 i = floor(p); vec2 f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(h12(i), h12(i + vec2(1.0, 0.0)), u.x), mix(h12(i + vec2(0.0, 1.0)), h12(i + vec2(1.0, 1.0)), u.x), u.y);
}
float fbm(vec2 p) {
  float s = 0.0; float a = 0.5;
  for (int k = 0; k < 4; k++) { s += a * vnoise(p); p = p * 2.03 + vec2(17.1, 9.3); a *= 0.5; }
  return s / 0.9375;
}
vec3 L(vec3 c) { return pow(c, vec3(2.2)); }
vec3 skyCol(vec3 d) {
  float y = d.y;
  vec3 c = mix(vec3(0.56, 0.64, 0.74), vec3(0.085, 0.20, 0.48), pow(clamp(y, 0.0, 1.0), 0.45));
  c = mix(c, vec3(0.34, 0.34, 0.35), clamp(-y * 2.5, 0.0, 1.0));
  float sd = max(dot(d, uSun), 0.0);
  c += vec3(1.0, 0.78, 0.52) * (0.30 * pow(sd, 5.0) + 0.85 * pow(sd, 90.0));
  return c;
}
vec3 tonemap(vec3 c) {
  c = max(c, vec3(0.0));
  c = (c * (2.51 * c + 0.03)) / (c * (2.43 * c + 0.59) + 0.14);
  return pow(clamp(c, 0.0, 1.0), vec3(1.0 / 2.2));
}
`;

  const VS_SKY = `
attribute vec2 aP;
uniform vec3 uRight; uniform vec3 uUp; uniform vec3 uFwd; uniform vec2 uTan;
varying vec3 vD;
void main() { vD = uFwd + aP.x * uTan.x * uRight + aP.y * uTan.y * uUp; gl_Position = vec4(aP, 0.9999, 1.0); }
`;
  const FS_SKY = `
varying vec3 vD;
void main() {
  vec3 d = normalize(vD);
  vec3 c = skyCol(d);
  if (d.y > 0.0) {
    vec2 q = d.xz / (d.y + 0.12) * 1.4;
    float cl = smoothstep(0.55, 0.80, fbm(q + vec2(3.1, 7.7))) * smoothstep(0.0, 0.22, d.y);
    vec3 cc = vec3(1.0, 0.97, 0.93) * (0.85 + 0.6 * pow(max(dot(d, uSun), 0.0), 4.0));
    c = mix(c, cc, cl * 0.5);
  }
  c += vec3(14.0, 12.0, 9.0) * smoothstep(0.99955, 0.99975, dot(d, uSun));
  gl_FragColor = vec4(tonemap(c), 1.0);
}
`;

  const VS_WORLD = `
attribute vec3 aPos; attribute vec3 aNor; attribute vec2 aUV; attribute vec4 aInfo; attribute vec2 aSize;
uniform mat4 uVP; uniform mat4 uModel;
varying vec3 vW; varying vec3 vN; varying vec2 vUV; varying vec4 vInfo; varying vec2 vSize;
void main() {
  vec4 w = uModel * vec4(aPos, 1.0);
  vW = w.xyz; vN = (uModel * vec4(aNor, 0.0)).xyz; vUV = aUV; vInfo = aInfo; vSize = aSize;
  gl_Position = uVP * w;
}
`;

  const FS_WORLD = `
varying vec3 vW; varying vec3 vN; varying vec2 vUV; varying vec4 vInfo; varying vec2 vSize;
uniform vec3 uEye; uniform sampler2D uHF; uniform vec2 uHFSize; uniform float uCell; uniform float uHScale;
uniform float uMaxH; uniform float uWall;
uniform float uGrid; uniform float uAOOn; uniform float uShadowFix; uniform float uFogOn; uniform float uPix;
uniform vec4 uObj; uniform vec4 uSpawn; uniform vec4 uFlash; uniform vec4 uTint; uniform vec4 uBlob[8];

// the heightfield of the canonical world: one texel a cell, its top; outside the map, open ground
float hAt(vec2 c) {
  if (c.x < 0.0 || c.y < 0.0 || c.x >= uHFSize.x || c.y >= uHFSize.y) return 0.0;
  return texture2D(uHF, (c + 0.5) / uHFSize).r * uHScale;
}

// the sun: a walk of the cells the ray toward the sun crosses; in each, the column [0, top] is solid
float sunShadow(vec3 p, vec3 n) {
  vec3 o = p + n * 0.02 + uSun * 0.01;
  float tExit = (uMaxH - o.y) / uSun.y;
  if (tExit <= 0.0) return 1.0;
  vec2 ro = o.xz / uCell;
  vec2 rd = uSun.xz / uCell;
  rd = vec2(rd.x >= 0.0 ? max(rd.x, 1e-4) : min(rd.x, -1e-4), rd.y >= 0.0 ? max(rd.y, 1e-4) : min(rd.y, -1e-4));
  vec2 cell = floor(ro);
  vec2 st = vec2(rd.x > 0.0 ? 1.0 : -1.0, rd.y > 0.0 ? 1.0 : -1.0);
  vec2 tD = abs(1.0 / rd);
  vec2 tM = ((cell + max(st, 0.0)) - ro) / rd;
  float t = 0.0; float vis = 1.0;
  for (int k = 0; k < 24; k++) {
    float hh = hAt(cell);
    float y = o.y + uSun.y * t;
    if (y < hh) return 0.0;
    if (t > 0.0) vis = min(vis, clamp((y - hh) / (0.055 * t), 0.0, 1.0));
    if (tM.x < tM.y) { t = tM.x; tM.x += tD.x; cell.x += st.x; } else { t = tM.y; tM.y += tD.y; cell.y += st.y; }
    if (t > tExit) break;
  }
  return vis;
}

// contact darkening from the heightfield: taller neighbours, and the floor at the foot of a face
float occ(float h, float y) { return clamp((h - y) * 2.0, 0.0, 1.0); }
float aoAt(vec3 p, vec3 n) {
  vec2 c = p.xz / uCell + n.xz * 0.01;
  vec2 ci = floor(c); vec2 f = (c - ci) * uCell;
  float y = p.y + 0.01; float R = 0.5;
  float wx = 1.0 - abs(n.x); float wz = 1.0 - abs(n.z); float wd = wx * wz * 0.7;
  float o = 0.0;
  o += wx * occ(hAt(ci + vec2(-1.0, 0.0)), y) * exp(-f.x / R);
  o += wx * occ(hAt(ci + vec2(1.0, 0.0)), y) * exp(-(uCell - f.x) / R);
  o += wz * occ(hAt(ci + vec2(0.0, -1.0)), y) * exp(-f.y / R);
  o += wz * occ(hAt(ci + vec2(0.0, 1.0)), y) * exp(-(uCell - f.y) / R);
  o += wd * occ(hAt(ci + vec2(-1.0, -1.0)), y) * exp(-length(f) / R);
  o += wd * occ(hAt(ci + vec2(1.0, -1.0)), y) * exp(-length(f - vec2(uCell, 0.0)) / R);
  o += wd * occ(hAt(ci + vec2(-1.0, 1.0)), y) * exp(-length(f - vec2(0.0, uCell)) / R);
  o += wd * occ(hAt(ci + vec2(1.0, 1.0)), y) * exp(-length(f - vec2(uCell)) / R);
  o += (1.0 - abs(n.y)) * 0.9 * exp(-max(p.y - hAt(ci), 0.0) / 0.32);
  return clamp(1.0 - 0.5 * o, 0.3, 1.0);
}

float bit(float v, float b) { return mod(floor(v / b + 0.001), 2.0); }
float lineAA(float d, float w, float aa) { return 1.0 - smoothstep(w - aa, w + aa, d); }
vec3 teamCol(float t) { return t < 1.5 ? L(vec3(0.16, 0.42, 0.85)) : L(vec3(0.86, 0.22, 0.14)); }

void main() {
  vec3 n = normalize(vN);
  // every per-face number arrives as a whole number, and is rounded here: an interpolated constant is not exact, and
  // a hash of it would change from pixel to pixel
  float mat = floor(vInfo.x + 0.5); float seed = floor(vInfo.y + 0.5) / 1000.0; float flags = floor(vInfo.z + 0.5); float team = floor(vInfo.w + 0.5);
  vec2 uv = vUV; vec2 sz = vSize;
  vec3 V = uEye - vW; float dist = length(V); V /= max(dist, 1e-4);
  float aa = max(dist * uPix, 0.003);
  float fade = clamp(1.3 - dist / 55.0, 0.0, 1.0);
  bool top = n.y > 0.5;
  vec3 alb = vec3(0.5); float spec = 0.04; float shin = 16.0; float metal = 0.0; vec3 emis = vec3(0.0);

  if (mat < 4.5) {
    // ---- floors: a module a cell
    vec2 f = fract(uv / uCell) * uCell; vec2 ci = floor(uv / uCell);
    float sid = h12(ci * 1.37 + 0.5);
    float e = min(min(f.x, uCell - f.x), min(f.y, uCell - f.y));
    float drop = 9.0;
    if (bit(flags, 1.0) > 0.5) drop = min(drop, f.x);
    if (bit(flags, 2.0) > 0.5) drop = min(drop, uCell - f.x);
    if (bit(flags, 4.0) > 0.5) drop = min(drop, f.y);
    if (bit(flags, 8.0) > 0.5) drop = min(drop, uCell - f.y);
    float zb = 9.0;
    if (bit(flags, 16.0) > 0.5) zb = min(zb, f.x);
    if (bit(flags, 32.0) > 0.5) zb = min(zb, uCell - f.x);
    if (bit(flags, 64.0) > 0.5) zb = min(zb, f.y);
    if (bit(flags, 128.0) > 0.5) zb = min(zb, uCell - f.y);
    if (mat < 1.5 || mat > 3.5) {
      // poured concrete slabs, each module sawn once across
      alb = L(vec3(0.50, 0.50, 0.48)) * (0.86 + 0.24 * sid) * (0.80 + 0.34 * fbm(uv * 0.9)) * (0.95 + 0.10 * vnoise(uv * 23.0));
      alb *= 1.0 - 0.32 * smoothstep(0.58, 0.76, fbm(uv * 0.23 + 11.0));
      float j = sid > 0.5 ? abs(f.x - uCell * 0.5) : abs(f.y - uCell * 0.5);
      alb *= 1.0 - 0.22 * lineAA(j, 0.005, aa) * fade;
      if (mat > 3.5) {
        float b = abs(e - 0.17);
        alb = mix(alb, L(vec3(0.86, 0.66, 0.12)) * (0.8 + 0.2 * vnoise(uv * 9.0)), lineAA(b, 0.05, aa) * 0.9);
      }
    } else if (mat < 2.5) {
      // steel tread plate at the bases
      vec2 q = uv * 5.0; vec2 g = fract(q) - 0.5; vec2 gi = floor(q);
      vec2 r = mod(gi.x + gi.y, 2.0) > 0.5 ? vec2(g.x + g.y, g.x - g.y) : vec2(g.x - g.y, g.x + g.y);
      float bump = 1.0 - smoothstep(0.10, 0.14 + aa * 5.0, length(r * vec2(1.0, 4.0)) * 0.5);
      alb = L(vec3(0.43, 0.44, 0.45)) * (0.82 + 0.25 * fbm(uv * 0.7)) * (1.0 + 0.30 * bump * fade);
      metal = 0.8; spec = 0.45; shin = 36.0;
    } else {
      // the platform: a painted steel deck, plates welded every metre, a hazard edge where it drops
      alb = L(vec3(0.34, 0.37, 0.40)) * (0.84 + 0.25 * fbm(uv * 0.8));
      float w = abs(fract(uv.x + 0.5) - 0.5);
      alb *= 1.0 - 0.30 * lineAA(w, 0.006, aa) * fade;
      metal = 0.5; spec = 0.30; shin = 28.0;
      if (drop < 0.30) {
        float hz = step(0.5, fract((vW.x + vW.z) * 1.4));
        alb = mix(L(vec3(0.07, 0.07, 0.07)), L(vec3(0.88, 0.64, 0.10)), hz) * (0.75 + 0.3 * vnoise(uv * 7.0));
        metal = 0.0; spec = 0.08;
      }
    }
    // the module seam, with a worn bevel
    alb *= 1.0 - 0.45 * lineAA(e, 0.016, aa) * fade;
    alb *= 1.0 + 0.10 * (lineAA(e, 0.042, aa) - lineAA(e, 0.018, aa)) * fade;
    // the base's border, and its spawn pad, in the team's colour
    if (team > 0.5) {
      float pad = length(vW.xz - (team < 1.5 ? uSpawn.xy : uSpawn.zw));
      float paint = max(lineAA(abs(zb - 0.10), 0.03, aa), lineAA(abs(pad - 0.9), 0.04, aa));
      alb = mix(alb, teamCol(team) * (0.75 + 0.25 * vnoise(uv * 8.0)), paint * 0.75);
      if (paint > 0.5) { metal = 0.0; spec = 0.06; }
    }
    // the objective: a ring, a dashed inner ring and corner marks, painted on the deck
    if (vW.x > uObj.x && vW.x < uObj.z && vW.z > uObj.y && vW.z < uObj.w) {
      vec2 oc = (uObj.xy + uObj.zw) * 0.5; vec2 hs = (uObj.zw - uObj.xy) * 0.5; vec2 dv = vW.xz - oc;
      float r = length(dv); float R = min(hs.x, hs.y) * 0.78;
      float ring = lineAA(abs(r - R), 0.08, aa);
      float ring2 = lineAA(abs(r - R * 0.62), 0.035, aa) * step(0.5, fract(atan(dv.y, dv.x) * 24.0 / 6.2831853));
      vec2 qc = abs(dv) - (hs - 0.25);
      float corner = (qc.x > -0.10 && qc.x < 0.0 && qc.y > -0.9 && qc.y < 0.0) || (qc.y > -0.10 && qc.y < 0.0 && qc.x > -0.9 && qc.x < 0.0) ? 1.0 : 0.0;
      float paint = max(max(ring, ring2), corner) * (0.75 + 0.25 * vnoise(vW.xz * 6.0));
      alb = mix(alb, L(vec3(0.95, 0.50, 0.10)), paint);
      if (paint > 0.5) { metal = 0.0; spec = 0.08; }
    }
  } else if (mat < 5.5) {
    // ---- walls: formed concrete, a baseboard, a cap, tie holes, windows on some panels, guards at the corners
    float u = uv.x; float v = uv.y; float Wd = sz.x; float H = sz.y; float ytop = H - v;
    float pid = h12(vec2(seed * 91.7, floor(vW.y / 1.35)));
    alb = L(vec3(0.60, 0.60, 0.58)) * (0.88 + 0.16 * pid) * (0.82 + 0.30 * fbm(vec2(u + seed * 37.0, vW.y) * 1.1));
    float yj = abs(fract(vW.y / 1.35 + 0.5) - 0.5) * 1.35;
    alb *= 1.0 - 0.28 * lineAA(yj, 0.007, aa) * fade;
    alb *= 1.0 - 0.45 * lineAA(min(u, Wd - u), 0.011, aa) * fade;
    vec2 th = vec2(abs(abs(u - Wd * 0.5) - Wd * 0.3), abs(fract(vW.y / 1.35) - 0.5) * 1.35);
    alb *= 1.0 - 0.55 * (1.0 - smoothstep(0.022, 0.03 + aa, length(th))) * fade;
    if (H > uWall - 0.01 && h12(vec2(seed * 13.1, 4.0)) < 0.22) {
      vec2 wq = vec2(u - Wd * 0.5, v - 2.75); vec2 dq = abs(wq) - vec2(Wd * 0.5 - 0.32, 0.60);
      float inside = max(dq.x, dq.y);
      if (inside < 0.0) {
        if (inside > -0.06 || abs(wq.x) < 0.025) {
          alb = L(vec3(0.68, 0.69, 0.68)); metal = 0.9; spec = 0.5; shin = 40.0;
        } else {
          alb = L(vec3(0.04, 0.05, 0.06)); spec = 0.6; shin = 120.0;
          float fr = pow(1.0 - max(dot(n, V), 0.0), 3.0);
          emis = skyCol(reflect(-V, n)) * (0.10 + 0.5 * fr) * smoothstep(0.0, 0.18, 0.60 - wq.y);
        }
      }
    }
    if (v < 0.30 && bit(flags, 4.0) < 0.5) {
      alb = L(vec3(0.23, 0.24, 0.25)) * (0.9 + 0.2 * fbm(uv * 3.0));
      alb *= 1.0 + 0.25 * lineAA(abs(v - 0.29), 0.008, aa);
      spec = 0.10;
    }
    if (ytop < 0.20) { alb = L(vec3(0.56, 0.57, 0.57)) * (0.9 + 0.1 * vnoise(uv * 4.0)); metal = 1.0; spec = 0.4; shin = 30.0; }
    else if (ytop < 0.26) alb *= 0.65;
    bool guard = (bit(flags, 1.0) > 0.5 && u < 0.09) || (bit(flags, 2.0) > 0.5 && Wd - u < 0.09);
    if (guard && ytop >= 0.20) {
      alb = L(vec3(0.62, 0.64, 0.65)) * (0.85 + 0.15 * vnoise(vec2(u, v) * 12.0)); metal = 1.0; spec = 0.5; shin = 40.0;
      if (v < 0.30) alb = mix(L(vec3(0.07, 0.07, 0.07)), L(vec3(0.88, 0.64, 0.10)), step(0.5, fract((v + u) * 5.0)));
    }
    if (team > 0.5 && v > 1.10 && v < 1.16 && !guard) { alb = mix(alb, teamCol(team) * (0.8 + 0.2 * vnoise(uv * 6.0)), 0.8); spec = 0.08; metal = 0.0; }
  } else if (mat < 6.5) {
    alb = L(vec3(0.36, 0.36, 0.35)) * (0.8 + 0.3 * fbm(uv * 1.5));
  } else if (mat < 7.5) {
    // ---- the platform's risers: hazard stripes, a steel lip
    float hz = step(0.5, fract((vW.x + vW.z + vW.y) * 1.6));
    alb = mix(L(vec3(0.07, 0.07, 0.07)), L(vec3(0.88, 0.64, 0.10)), hz) * (0.75 + 0.3 * vnoise(vW.xz * 6.0 + vW.y));
    if (sz.y - uv.y < 0.05) { alb = L(vec3(0.5, 0.52, 0.53)); metal = 1.0; spec = 0.4; }
  } else if (mat < 11.5) {
    // ---- cover: the column's own box, dressed; never smaller or larger than what blocks
    float Wd = top ? uCell : sz.x; float H = top ? uCell : sz.y;
    vec2 q = top ? fract(uv / uCell) * uCell : uv;
    float be = min(min(q.x, Wd - q.x), min(q.y, H - q.y));
    if (mat < 8.5) {
      float grain = fbm(vec2(q.x * 0.7, q.y * 14.0) + seed * 17.0);
      alb = L(vec3(0.58, 0.42, 0.25)) * (0.75 + 0.45 * grain);
      float pl = abs(fract(q.y / 0.25) - 0.5) * 0.25;
      alb *= 1.0 - 0.45 * lineAA(pl, 0.006, aa) * fade;
      bool frame = be < 0.10;
      bool brace = !top && abs(q.x / Wd - q.y / H) * min(Wd, H) < 0.07;
      if (frame || brace) alb = L(vec3(0.46, 0.31, 0.17)) * (0.8 + 0.4 * grain);
      alb *= 1.0 - 0.35 * lineAA(abs(be - 0.10), 0.006, aa) * fade;
      spec = 0.05; shin = 10.0;
    } else if (mat < 9.5) {
      alb = L(vec3(0.30, 0.33, 0.20)) * (0.85 + 0.25 * fbm(q * 1.7 + seed * 11.0));
      float rb = top ? 9.0 : min(abs(q.y - H * 0.3), abs(q.y - H * 0.7));
      if (rb < 0.05) alb *= 1.12;
      alb *= 1.0 - 0.35 * lineAA(abs(rb - 0.05), 0.006, aa) * fade;
      if (!top && H > 2.0) alb *= 1.0 - 0.5 * lineAA(abs(q.y - H * 0.5), 0.012, aa);
      if (be < 0.035 + 0.03 * vnoise(q * 20.0)) alb = L(vec3(0.46, 0.46, 0.42));
      if (!top && h12(vec2(seed * 7.3, 1.0)) > 0.4 && abs(q.x - Wd * 0.5) < 0.45 && abs(q.y - H * 0.5) < 0.07) {
        if (step(0.38, fract(q.x * 9.0)) * step(0.3, vnoise(q * 30.0)) > 0.5) alb = L(vec3(0.78, 0.72, 0.46));
      }
      metal = 0.6; spec = 0.22; shin = 22.0;
    } else if (mat < 10.5) {
      alb = L(vec3(0.66, 0.66, 0.63)) * (0.82 + 0.28 * fbm(q * 2.0 + seed * 5.0));
      if (!top && H - q.y < 0.22 && H - q.y > 0.06) alb = mix(L(vec3(0.07, 0.07, 0.07)), L(vec3(0.88, 0.64, 0.10)), step(0.5, fract((vW.x + vW.z + vW.y) * 2.2)));
      if (!top) alb *= 1.0 - 0.35 * exp(-q.y / 0.15);
      if (!top && abs(q.x - Wd * 0.5) < 0.06 && abs(q.y - H * 0.55) < 0.03) emis = L(vec3(0.9, 0.35, 0.05)) * 0.6;
    } else {
      alb = L(vec3(0.58, 0.57, 0.55)) * (0.84 + 0.25 * fbm(vec2(q.x, vW.y) * 1.4 + seed * 9.0));
      alb *= 1.0 - 0.25 * lineAA(abs(fract(vW.y / 0.65 + 0.5) - 0.5) * 0.65, 0.006, aa) * fade;
      if (!top && q.y < 0.45) alb = mix(L(vec3(0.07, 0.07, 0.07)), L(vec3(0.88, 0.64, 0.10)), step(0.5, fract((vW.x + vW.z + vW.y) * 2.0)));
      if (!top && H - q.y < 0.12) { alb = L(vec3(0.55, 0.56, 0.57)); metal = 1.0; spec = 0.4; }
      if (!top && ((bit(flags, 1.0) > 0.5 && q.x < 0.03) || (bit(flags, 2.0) > 0.5 && Wd - q.x < 0.03))) alb *= 1.25;
    }
  } else if (mat < 12.5) {
    alb = L(vec3(0.20, 0.21, 0.22)) * (0.85 + 0.2 * vnoise(uv * 3.0)); metal = 1.0; spec = 0.3; shin = 24.0;
  } else if (mat < 13.5) {
    // ---- the distant skyline: facades with rows of windows, some lit
    alb = L(vec3(0.42, 0.44, 0.47)) * (0.75 + 0.5 * seed);
    if (!top) {
      vec2 g = vec2(uv.x / 3.0, uv.y / 3.5); vec2 gi = floor(g); vec2 gf = fract(g);
      if (gf.x > 0.2 && gf.x < 0.8 && gf.y > 0.3 && gf.y < 0.75 && uv.y > 2.0 && sz.y - uv.y > 1.0) {
        alb = L(vec3(0.12, 0.14, 0.17));
        if (h12(gi + seed * 31.0) < 0.08) emis = L(vec3(1.0, 0.85, 0.6)) * 0.6;
      }
    } else alb = L(vec3(0.30, 0.30, 0.31));
  } else if (mat < 14.5) {
    alb = L(vec3(0.78, 0.10, 0.08));
    if (!top) {
      float r = length(uv - sz * 0.5);
      if (lineAA(abs(r - 0.22), 0.035, aa) > 0.5 || r < 0.06) alb = L(vec3(0.92, 0.92, 0.90));
    }
    spec = 0.2; shin = 30.0;
  } else if (mat < 15.5) {
    alb = L(vec3(0.92, 0.92, 0.90)); spec = 0.2; shin = 30.0;
    if (!top && length(uv - sz * 0.5) < 0.05) alb = L(vec3(0.78, 0.10, 0.08));
  } else if (mat < 16.5) {
    alb = L(vec3(0.15, 0.15, 0.16)); metal = 1.0; spec = 0.3; shin = 24.0;
  } else if (mat < 17.5) {
    alb = L(vec3(0.36, 0.37, 0.38)); metal = 0.45; spec = 0.35; shin = 48.0;
    if (seed > 0.5 && abs(fract((sz.x > sz.y ? uv.x : uv.y) / 0.01) - 0.5) < 0.2) alb *= 0.6;
  } else if (mat < 18.5) {
    alb = L(vec3(0.13, 0.13, 0.14)); spec = 0.12; shin = 18.0;
    if (seed > 0.5 && sz.x > sz.y && fract(uv.x / 0.03) < 0.45 && abs(uv.y - sz.y * 0.5) < sz.y * 0.22) alb *= 0.35;
  } else if (mat < 19.5) {
    alb = L(vec3(0.64, 0.54, 0.40)) * (0.9 + 0.1 * vnoise(uv * 60.0)); spec = 0.08; shin = 12.0;
    if (seed > 0.5 && sz.x > sz.y && fract(uv.x / 0.03) < 0.45 && abs(uv.y - sz.y * 0.5) < sz.y * 0.22) alb *= 0.45;
  } else if (mat < 20.5) {
    alb = L(vec3(0.46, 0.46, 0.47)); metal = 0.6; spec = 0.5; shin = 80.0;
  } else {
    alb = L(vec3(1.0, 0.45, 0.1)); emis = vec3(2.6, 0.9, 0.2);
  }

  // ---- light: the sun (with its shadow), the sky above and the ground below, the muzzle's flash
  float ndl = max(dot(n, uSun), 0.0);
  float sh = uShadowFix >= 0.0 ? uShadowFix : (ndl > 0.0 ? sunShadow(vW, n) : 0.0);
  float ao = uAOOn > 0.5 ? aoAt(vW, n) : 1.0;
  if (top && uAOOn > 0.5) {
    for (int k = 0; k < 8; k++) {
      vec4 b = uBlob[k];
      if (b.w > 0.0) {
        ao *= 1.0 - b.w * (1.0 - smoothstep(b.z * 0.3, b.z, length(vW.xz - b.xy)));
        vec2 sc = b.xy - uSun.xz / uSun.y * 0.95;
        sh *= 1.0 - 0.8 * (1.0 - smoothstep(0.22, 0.55, length(vW.xz - sc)));
      }
    }
  }
  vec3 SUNC = vec3(1.0, 0.91, 0.78) * 2.6;
  vec3 amb = mix(vec3(0.26, 0.24, 0.21) * 0.75, vec3(0.30, 0.38, 0.52) * 1.05, 0.5 + 0.5 * n.y) * ao;
  vec3 Hh = normalize(uSun + V);
  float sp = pow(max(dot(n, Hh), 0.0), shin) * (shin + 8.0) / 25.0;
  vec3 F0 = mix(vec3(spec), alb * (0.5 + spec), metal);
  vec3 col = alb * (1.0 - 0.7 * metal) * (SUNC * ndl * sh + amb) + SUNC * F0 * sp * ndl * sh * 0.25 + amb * F0 * 0.35 + emis;
  if (uFlash.w > 0.0) {
    vec3 l = uFlash.xyz - vW; float d2 = dot(l, l);
    col += alb * vec3(1.0, 0.72, 0.38) * uFlash.w * max(dot(n, normalize(l)), 0.0) / (1.0 + d2 * 1.2);
  }
  if (uGrid > 0.5) {
    vec3 a = abs(n);
    vec2 g = a.y > 0.5 ? vW.xz : (a.x > 0.5 ? vW.zy : vW.xy);
    vec2 gg = abs(fract(g) - 0.5);
    col = mix(col, vec3(0.05, 0.75, 0.9), 0.75 * step(0.475, max(gg.x, gg.y)));
  }
  col *= 0.82;
  col = mix(col, skyCol(-V) * 0.95, uFogOn * (1.0 - exp(-dist * 0.004)));
  col = mix(col, uTint.rgb * 2.5, uTint.w);
  gl_FragColor = vec4(tonemap(col), 1.0);
}
`;

  const VS_FX = `
attribute vec3 aP; attribute vec4 aC; attribute vec2 aT;
uniform mat4 uVP;
varying vec4 vC; varying vec2 vT;
void main() { vC = aC; vT = aT; gl_Position = uVP * vec4(aP, 1.0); }
`;
  const FS_FX = `
precision mediump float;
varying vec4 vC; varying vec2 vT;
void main() { float a = clamp(1.0 - length(vT), 0.0, 1.0); gl_FragColor = vec4(vC.rgb * vC.a * a * a, 1.0); }
`;

  // ---------------------------------------------------------------- matrices, column-major
  function mul(a, b) {
    const o = new Float32Array(16);
    for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
      let s = 0; for (let k = 0; k < 4; k++) s += a[k * 4 + r] * b[c * 4 + k];
      o[c * 4 + r] = s;
    }
    return o;
  }
  function perspective(fovy, aspect, near, far) {
    const f = 1 / Math.tan(fovy / 2), o = new Float32Array(16);
    o[0] = f / aspect; o[5] = f; o[10] = (far + near) / (near - far); o[11] = -1; o[14] = 2 * far * near / (near - far);
    return o;
  }
  function basis(d) {   // right, up, forward of a camera looking along d
    let r = [-d[2], 0, d[0]]; const l = Math.hypot(r[0], r[2]) || 1; r = [r[0] / l, 0, r[2] / l];
    const u = [r[1] * d[2] - r[2] * d[1], r[2] * d[0] - r[0] * d[2], r[0] * d[1] - r[1] * d[0]];
    return { r: r, u: u, f: d };
  }
  function viewOf(e, B) {
    const r = B.r, u = B.u, z = [-B.f[0], -B.f[1], -B.f[2]];
    return new Float32Array([r[0], u[0], z[0], 0, r[1], u[1], z[1], 0, r[2], u[2], z[2], 0,
      -(r[0] * e[0] + r[1] * e[1] + r[2] * e[2]), -(u[0] * e[0] + u[1] * e[1] + u[2] * e[2]), -(z[0] * e[0] + z[1] * e[1] + z[2] * e[2]), 1]);
  }
  function cameraToWorld(e, B) {
    return new Float32Array([B.r[0], B.r[1], B.r[2], 0, B.u[0], B.u[1], B.u[2], 0, -B.f[0], -B.f[1], -B.f[2], 0, e[0], e[1], e[2], 1]);
  }
  function translate(x, y, z) { return new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1]); }
  function rotX(a) { const c = Math.cos(a), s = Math.sin(a); return new Float32Array([1, 0, 0, 0, 0, c, s, 0, 0, -s, c, 0, 0, 0, 0, 1]); }
  function rotY(a) { const c = Math.cos(a), s = Math.sin(a); return new Float32Array([c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, 0, 0, 0, 1]); }
  function rotZ(a) { const c = Math.cos(a), s = Math.sin(a); return new Float32Array([c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]); }
  function apply(m, p) { return [m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12], m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13], m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14]]; }
  const ID = translate(0, 0, 0);

  function seedOf(i, j, k) { return Math.floor(hash(i, j, k) * 1000); }   // a face's seed: a whole number below 1000
  function hash(i, j, k) {
    let h = (Math.imul(i | 0, 73856093) ^ Math.imul(j | 0, 19349663) ^ Math.imul(k | 0, 83492791)) >>> 0;
    h = Math.imul(h ^ (h >>> 15), 2246822519) >>> 0; h = Math.imul(h ^ (h >>> 13), 3266489917) >>> 0;
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  }

  // ---------------------------------------------------------------- meshes
  function Mesh() { this.P = []; this.N = []; this.UV = []; this.I = []; this.S = []; }
  Mesh.prototype.quad = function (a, b, c, d, n, ta, tb, tc, td, info, size) {
    const vs = [[a, ta], [b, tb], [c, tc], [a, ta], [c, tc], [d, td]];
    for (const v of vs) {
      this.P.push(v[0][0], v[0][1], v[0][2]); this.N.push(n[0], n[1], n[2]); this.UV.push(v[1][0], v[1][1]);
      this.I.push(info[0], info[1], info[2], info[3]); this.S.push(size[0], size[1]);
    }
  };
  // an upright box, optionally turned about its own x axis (the weapon's parts); face-local coordinates in metres
  Mesh.prototype.box = function (c, s, mat, seed, rx, skipBottom) {
    const hx = s[0] / 2, hy = s[1] / 2, hz = s[2] / 2, cr = Math.cos(rx || 0), sr = Math.sin(rx || 0);
    const T = function (p) { return [c[0] + p[0], c[1] + p[1] * cr - p[2] * sr, c[2] + p[1] * sr + p[2] * cr]; };
    const R = function (n) { return [n[0], n[1] * cr - n[2] * sr, n[1] * sr + n[2] * cr]; };
    const info = [mat, seed, 0, 0];
    const self = this;
    const face = function (n, pa, pb, pc, pd, w, h) {
      self.quad(T(pa), T(pb), T(pc), T(pd), R(n), [0, 0], [w, 0], [w, h], [0, h], info, [w, h]);
    };
    face([1, 0, 0], [hx, -hy, hz], [hx, -hy, -hz], [hx, hy, -hz], [hx, hy, hz], s[2], s[1]);
    face([-1, 0, 0], [-hx, -hy, -hz], [-hx, -hy, hz], [-hx, hy, hz], [-hx, hy, -hz], s[2], s[1]);
    face([0, 0, 1], [-hx, -hy, hz], [hx, -hy, hz], [hx, hy, hz], [-hx, hy, hz], s[0], s[1]);
    face([0, 0, -1], [hx, -hy, -hz], [-hx, -hy, -hz], [-hx, hy, -hz], [hx, hy, -hz], s[0], s[1]);
    face([0, 1, 0], [-hx, hy, -hz], [hx, hy, -hz], [hx, hy, hz], [-hx, hy, hz], s[0], s[2]);
    if (!skipBottom) face([0, -1, 0], [-hx, -hy, hz], [hx, -hy, hz], [hx, -hy, -hz], [-hx, -hy, -hz], s[0], s[2]);
  };
  Mesh.prototype.arrays = function () {
    return { P: new Float32Array(this.P), N: new Float32Array(this.N), UV: new Float32Array(this.UV),
             I: new Float32Array(this.I), S: new Float32Array(this.S), count: this.P.length / 3 };
  };

  // the render world's solids: one column a cell, at the canonical world's top, and its steps
  function buildWorld(W) {
    const c = W.cell, w = W.w, h = W.h, cells = W.cells;
    const inside = function (i, j) { return i >= 0 && j >= 0 && i < w && j < h; };
    const topAt = function (i, j) { return inside(i, j) ? cells[j * w + i][2] : null; };
    const kindAt = function (i, j) { return inside(i, j) ? cells[j * w + i][1] : "wall"; };
    // the bases: open cells within four of a spawn
    const zone = new Int8Array(w * h);
    for (const side of Object.keys(W.spawns).sort()) {
      const sp = W.spawns[side], t = side === "A" ? 1 : 2;
      for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
        if (kindAt(i, j) !== "wall" && Math.max(Math.abs(i - sp.x), Math.abs(j - sp.z)) <= 4) zone[j * w + i] = t;
      }
    }
    const zoneAt = function (i, j) { return inside(i, j) ? zone[j * w + i] : 0; };
    // cover: a group is the connected cells of one height; its look is chosen once for the group
    const group = new Int32Array(w * h).fill(-1);
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
      const k = j * w + i;
      if (kindAt(i, j) !== "cover" || group[k] >= 0) continue;
      const stack = [[i, j]]; group[k] = k;
      while (stack.length) {
        const p = stack.pop();
        for (const d of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const a = p[0] + d[0], b = p[1] + d[1];
          if (kindAt(a, b) === "cover" && group[b * w + a] < 0 && topAt(a, b) === topAt(i, j)) { group[b * w + a] = k; stack.push([a, b]); }
        }
      }
    }
    const mesh = new Mesh();
    const DIRS = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
      const k = j * w + i, kind = cells[k][1], top = cells[k][2];
      const x0 = i * c, x1 = x0 + c, z0 = j * c, z1 = z0 + c;
      let topMat, sideMat;
      if (kind === "wall") { topMat = M.WALL_TOP; sideMat = M.WALL; }
      else if (kind === "cover") {
        const g = group[k], gs = hash(g % w, Math.floor(g / w), 7);
        if (top > 1.2) topMat = gs < 0.5 ? M.PILLAR : M.OLIVE;
        else topMat = [M.CRATE, M.OLIVE, M.BARRIER][Math.min(2, Math.floor(gs * 3))];
        sideMat = topMat;
      } else if (kind === "raised") { topMat = M.DECK; sideMat = M.RISER; }
      else if (kind === "stair") { topMat = M.MARK; sideMat = M.RISER; }
      else { topMat = zone[k] ? M.TREAD : M.CONCRETE; sideMat = M.RISER; }
      let fl = 0;
      for (let d = 0; d < 4; d++) {
        const a = i + DIRS[d][0], b = j + DIRS[d][1], nt = topAt(a, b);
        if (nt !== null && nt < top - 0.01) fl |= 1 << d;
        if (zone[k] && zoneAt(a, b) !== zone[k]) fl |= 16 << d;
      }
      mesh.quad([x0, top, z0], [x1, top, z0], [x1, top, z1], [x0, top, z1], [0, 1, 0],
                [x0, z0], [x1, z0], [x1, z1], [x0, z1], [topMat, seedOf(i, j, 1), fl, zone[k]], [c, c]);
      // a face wherever the neighbour stands lower; none toward the outside of the map
      for (let d = 0; d < 4; d++) {
        const a = i + DIRS[d][0], b = j + DIRS[d][1], nt = topAt(a, b);
        if (nt === null || nt >= top) continue;
        const n = [DIRS[d][0], 0, DIRS[d][1]];
        let p0, p1, t0, t1;   // the face's two ends, along u
        if (d < 2) { const x = d === 0 ? x0 : x1; p0 = [x, z0]; p1 = [x, z1]; t0 = [i, j - 1]; t1 = [i, j + 1]; }
        else { const z = d === 2 ? z0 : z1; p0 = [x0, z]; p1 = [x1, z]; t0 = [i - 1, j]; t1 = [i + 1, j]; }
        let cf = 0;
        const ta = topAt(t0[0], t0[1]), tb = topAt(t1[0], t1[1]);
        if (ta !== null && ta < top - 0.01) cf |= 1;
        if (tb !== null && tb < top - 0.01) cf |= 2;
        if (nt > 0.05) cf |= 4;   // the face stands on something raised, not on the floor
        const hh = top - nt;
        mesh.quad([p0[0], nt, p0[1]], [p1[0], nt, p1[1]], [p1[0], top, p1[1]], [p0[0], top, p0[1]], n,
                  [0, 0], [c, 0], [c, hh], [0, hh], [sideMat, seedOf(i, j, 10 + d), cf, zoneAt(a, b)], [c, hh]);
      }
    }
    return mesh;
  }

  // the highest eye a player can reach: an upper bound, from the movement's own numbers. From each spawn, a cell is
  // reached if some neighbour (diagonals included) was, and it rises above that neighbour by at most a jump and a step.
  function playCeiling(W, P) {
    const w = W.w, h = W.h, top = function (i, j) { return W.cells[j * w + i][2]; };
    const apex = P.jump * P.jump / (2 * P.gravity), rise = apex + P.step;
    const seen = new Uint8Array(w * h), q = [];
    for (const side of Object.keys(W.spawns)) { const sp = W.spawns[side]; seen[sp.z * w + sp.x] = 1; q.push([sp.x, sp.z]); }
    let hi = 0;
    while (q.length) {
      const p = q.pop(), t = top(p[0], p[1]);
      if (t > hi) hi = t;
      for (let dj = -1; dj <= 1; dj++) for (let di = -1; di <= 1; di++) {
        const a = p[0] + di, b = p[1] + dj;
        if (a < 0 || b < 0 || a >= w || b >= h || seen[b * w + a] || top(a, b) - t > rise) continue;
        seen[b * w + a] = 1; q.push([a, b]);
      }
    }
    return hi + apex + P.eye;
  }

  // decoration: beams resting on the wall tops across short runs of open cells, and a skyline outside the map.
  // Each is a box; none enters the map below the play ceiling.
  function buildDecor(W, ceiling) {
    const c = W.cell, w = W.w, h = W.h, boxes = [];
    const wallAt = function (i, j) { return W.cells[j * w + i][2] >= W.wall - 1e-9; };
    if (W.wall >= ceiling + 0.1) {
      const y0 = W.wall + 0.002, y1 = W.wall + 0.30;
      for (let i = 2; i < w; i += 4) {
        for (let j = 0; j < h;) {
          if (wallAt(i, j)) { j++; continue; }
          let j1 = j; while (j1 + 1 < h && !wallAt(i, j1 + 1)) j1++;
          if (j > 0 && j1 + 1 < h && j1 - j + 1 <= 5) boxes.push({ kind: "beam", min: [(i + 0.5) * c - 0.11, y0, j * c - 0.45], max: [(i + 0.5) * c + 0.11, y1, (j1 + 1) * c + 0.45] });
          j = j1 + 1;
        }
      }
      for (let j = 2; j < h; j += 4) {
        for (let i = 0; i < w;) {
          if (wallAt(i, j)) { i++; continue; }
          let i1 = i; while (i1 + 1 < w && !wallAt(i1 + 1, j)) i1++;
          if (i > 0 && i1 + 1 < w && i1 - i + 1 <= 5) boxes.push({ kind: "beam", min: [i * c - 0.45, y0 + 0.31, (j + 0.5) * c - 0.11], max: [(i1 + 1) * c + 0.45, y1 + 0.31, (j + 0.5) * c + 0.11] });
          i = i1 + 1;
        }
      }
    }
    const cx = w * c / 2, cz = h * c / 2, R0 = Math.hypot(cx, cz) + 30;
    for (let k = 0; k < 44; k++) {
      const a = (k + hash(k, 3, 11) * 0.6) / 44 * 2 * Math.PI, r = R0 + 60 + hash(k, 5, 13) * 180;
      const fw = 12 + hash(k, 7, 17) * 24, fd = 12 + hash(k, 9, 19) * 24, ht = 8 + Math.pow(hash(k, 11, 23), 2.0) * 34;
      const x = cx + Math.cos(a) * r, z = cz + Math.sin(a) * r;
      const b = { kind: "skyline", min: [x - fw / 2, 0, z - fd / 2], max: [x + fw / 2, ht, z + fd / 2], seed: seedOf(k, 13, 29) };
      if (b.max[0] > -10 && b.min[0] < w * c + 10 && b.max[2] > -10 && b.min[2] < h * c + 10) continue;
      boxes.push(b);
    }
    return boxes;
  }

  // a target: inside its hit box (sim.js: radius 0.4, height 1.9), the whole of it
  function targetMesh() {
    const m = new Mesh();
    m.box([0, 0.01, 0], [0.76, 0.02, 0.76], M.STEEL_DARK, 0);
    m.box([0, 0.32, 0], [0.09, 0.60, 0.09], M.STEEL_DARK, 0);
    m.box([0, 1.035, 0], [0.68, 0.83, 0.50], M.TARGET, 0);
    m.box([0, 1.475, 0], [0.16, 0.05, 0.16], M.STEEL_DARK, 0);
    m.box([0, 1.70, 0], [0.40, 0.40, 0.40], M.TARGET_HEAD, 0);
    return m;
  }

  // the weapon in the hand, in its own frame: -z forward, +y up; metres
  const MUZZLE = [0, 0.012, -0.555];
  function gunMesh() {
    const m = new Mesh();
    const G = M.GUN_METAL, Pm = M.POLYMER, T = M.TAN, S = M.STEEL;
    m.box([0, 0, 0], [0.052, 0.072, 0.30], G, 0);                 // receiver
    m.box([0, 0.044, -0.02], [0.026, 0.016, 0.30], G, 999);       // rail
    m.box([0, -0.004, -0.255], [0.060, 0.064, 0.21], T, 999);     // handguard
    m.box([0, 0.012, -0.43], [0.020, 0.020, 0.15], S, 0);         // barrel
    m.box([0, 0.012, -0.375], [0.030, 0.030, 0.03], G, 0);        // gas block
    m.box([0, 0.012, -0.525], [0.030, 0.030, 0.05], G, 0);        // muzzle device
    m.box([0, 0.060, -0.33], [0.024, 0.024, 0.02], G, 0);         // front sight base
    m.box([0, 0.083, -0.33], [0.006, 0.026, 0.008], S, 0);        // front post
    m.box([0, 0.097, -0.33], [0.0075, 0.0075, 0.0085], M.SIGHT, 0);
    m.box([-0.011, 0.068, 0.10], [0.008, 0.024, 0.02], G, 0);     // rear sight
    m.box([0.011, 0.068, 0.10], [0.008, 0.024, 0.02], G, 0);
    m.box([0, 0.054, 0.10], [0.034, 0.008, 0.026], G, 0);
    m.box([0, -0.045, -0.045], [0.044, 0.03, 0.08], G, 0);        // magazine well
    m.box([0, -0.112, -0.05], [0.032, 0.15, 0.068], T, 0, 0.16);  // magazine, raked forward
    m.box([0, -0.088, 0.088], [0.034, 0.10, 0.042], Pm, 0, -0.30); // grip, raked back
    m.box([0, -0.050, 0.035], [0.010, 0.008, 0.07], G, 0);        // trigger guard
    m.box([0, -0.040, 0.030], [0.006, 0.02, 0.006], S, 0);        // trigger
    m.box([0, 0.0, 0.20], [0.030, 0.030, 0.12], G, 0);            // buffer tube
    m.box([0, -0.012, 0.29], [0.044, 0.085, 0.10], Pm, 0);        // stock
    m.box([0, -0.012, 0.345], [0.046, 0.09, 0.012], T, 0);        // butt pad
    m.box([0, 0.038, 0.13], [0.040, 0.010, 0.02], G, 0);          // charging handle
    m.box([0.027, 0.012, -0.02], [0.003, 0.022, 0.07], S, 0);     // ejection port cover
    return m;
  }

  function boundsOf(a) {
    const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (let k = 0; k < a.P.length; k += 3) for (let d = 0; d < 3; d++) { lo[d] = Math.min(lo[d], a.P[k + d]); hi[d] = Math.max(hi[d], a.P[k + d]); }
    return { min: lo, max: hi };
  }

  // ---------------------------------------------------------------- GL plumbing
  function program(gl, vs, fs) {
    const sh = function (type, src) {
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    };
    const p = gl.createProgram();
    gl.attachShader(p, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    const loc = {};
    const na = gl.getProgramParameter(p, gl.ACTIVE_ATTRIBUTES), nu = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (let k = 0; k < na; k++) { const a = gl.getActiveAttrib(p, k); loc[a.name] = gl.getAttribLocation(p, a.name); }
    for (let k = 0; k < nu; k++) { const u = gl.getActiveUniform(p, k); loc[u.name.replace(/\[0\]$/, "")] = gl.getUniformLocation(p, u.name); }
    return { p: p, loc: loc };
  }
  function upload(gl, a) {
    const b = { count: a.count };
    for (const k of ["P", "N", "UV", "I", "S"]) { b[k] = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b[k]); gl.bufferData(gl.ARRAY_BUFFER, a[k], gl.STATIC_DRAW); }
    return b;
  }
  function attribs(gl, list) {   // only the attributes a draw uses are enabled
    for (let k = 0; k < 8; k++) gl.disableVertexAttribArray(k);
    for (const x of list) {
      if (x[0] === undefined || x[0] < 0) continue;
      gl.bindBuffer(gl.ARRAY_BUFFER, x[1]); gl.enableVertexAttribArray(x[0]);
      gl.vertexAttribPointer(x[0], x[2], gl.FLOAT, false, x[3] || 0, x[4] || 0);
    }
  }

  // ---------------------------------------------------------------- the renderer
  function Renderer(canvas, map, Sim) {
    const gl = canvas.getContext("webgl", { antialias: true, preserveDrawingBuffer: true });
    if (!gl) throw new Error("WebGL is not available in this browser");
    this.gl = gl; this.canvas = canvas; this.W = map.canonical; this.Sim = Sim; this.name = "lit"; this.grid = false;
    const W = this.W;
    this.world = program(gl, VS_WORLD, FS_HEAD + COMMON + FS_WORLD);
    this.sky = program(gl, VS_SKY, FS_HEAD + COMMON + FS_SKY);
    this.fx = program(gl, VS_FX, FS_FX);
    const wm = buildWorld(W).arrays();
    this.worldMesh = { P: wm.P, N: wm.N };   // kept for the self-test, which holds it to the collision world
    this.worldBuf = upload(gl, wm);
    this.ceiling = playCeiling(W, Sim.P);
    this.decor = buildDecor(W, this.ceiling);
    const dm = new Mesh();
    for (const b of this.decor) {
      const s = [b.max[0] - b.min[0], b.max[1] - b.min[1], b.max[2] - b.min[2]];
      dm.box([(b.min[0] + b.max[0]) / 2, (b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2], s,
             b.kind === "beam" ? M.BEAM : M.SKYLINE, b.kind === "beam" ? 0 : b.seed, 0, true);
    }
    const da = dm.arrays();
    this.decorBuf = upload(gl, da);
    const tm = targetMesh().arrays();
    this.targetBounds = boundsOf(tm);
    this.targetBuf = upload(gl, tm);
    this.gunBuf = upload(gl, gunMesh().arrays());
    // the heightfield: one byte a cell, the top as a fraction of the highest
    let maxH = 0.01; for (const q of W.cells) maxH = Math.max(maxH, q[2]);
    this.maxH = maxH;
    const hb = new Uint8Array(W.w * W.h);
    for (let k = 0; k < hb.length; k++) hb[k] = Math.round(W.cells[k][2] / maxH * 255);
    this.hf = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this.hf);
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, W.w, W.h, 0, gl.LUMINANCE, gl.UNSIGNED_BYTE, hb);
    for (const p of [gl.TEXTURE_MIN_FILTER, gl.TEXTURE_MAG_FILTER]) gl.texParameteri(gl.TEXTURE_2D, p, gl.NEAREST);
    for (const p of [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T]) gl.texParameteri(gl.TEXTURE_2D, p, gl.CLAMP_TO_EDGE);
    this.skyQuad = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, this.skyQuad);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    this.fxVerts = gl.createBuffer();
    this.triangles = (wm.count + da.count) / 3;
    this.vis = { dist: 0, prev: null, sx: 0, sy: 0, move: 0 };
    gl.enable(gl.DEPTH_TEST);   // no face culling: a few thousand quads, drawn from both sides
  }

  // the sun's shadow at one point, as the shader computes it: for the weapon, which is not in the world
  Renderer.prototype.shadowAt = function (x, y, z) {
    const W = this.W, c = W.cell, w = W.w, h = W.h;
    const hAt = function (i, j) { return (i < 0 || j < 0 || i >= w || j >= h) ? 0 : W.cells[j * w + i][2]; };
    const tExit = (this.maxH - y) / SUN[1];
    if (tExit <= 0) return 1;
    const rx = SUN[0] / c, rz = SUN[2] / c, ox = x / c, oz = z / c;
    let i = Math.floor(ox), j = Math.floor(oz);
    const si = rx > 0 ? 1 : -1, sj = rz > 0 ? 1 : -1, tdx = Math.abs(1 / rx), tdz = Math.abs(1 / rz);
    let tmx = ((i + (si > 0 ? 1 : 0)) - ox) / rx, tmz = ((j + (sj > 0 ? 1 : 0)) - oz) / rz, t = 0, vis = 1;
    for (let k = 0; k < 24; k++) {
      const hh = hAt(i, j), yy = y + SUN[1] * t;
      if (yy < hh) return 0;
      if (t > 0) vis = Math.min(vis, Math.max(0, Math.min(1, (yy - hh) / (0.055 * t))));
      if (tmx < tmz) { t = tmx; tmx += tdx; i += si; } else { t = tmz; tmz += tdz; j += sj; }
      if (t > tExit) break;
    }
    return vis;
  };

  Renderer.prototype.bindMesh = function (b) {
    const gl = this.gl, L = this.world.loc;
    attribs(gl, [[L.aPos, b.P, 3], [L.aNor, b.N, 3], [L.aUV, b.UV, 2], [L.aInfo, b.I, 4], [L.aSize, b.S, 2]]);
  };

  // additive sprites: a disc facing the eye, or a streak from c to `to`
  Renderer.prototype.drawFx = function (vp, B, quads) {
    if (!quads.length) return;
    const gl = this.gl, F = this.fx, v = [];
    for (const q of quads) {
      const c = q.c, a = q.a;
      if (q.to) {
        const d = [q.to[0] - c[0], q.to[1] - c[1], q.to[2] - c[2]];
        let s = [d[1] * B.f[2] - d[2] * B.f[1], d[2] * B.f[0] - d[0] * B.f[2], d[0] * B.f[1] - d[1] * B.f[0]];
        const l = Math.hypot(s[0], s[1], s[2]) || 1; s = [s[0] / l * q.s, s[1] / l * q.s, s[2] / l * q.s];
        const P = [[c[0] - s[0], c[1] - s[1], c[2] - s[2], -1], [q.to[0] - s[0], q.to[1] - s[1], q.to[2] - s[2], -1],
                   [q.to[0] + s[0], q.to[1] + s[1], q.to[2] + s[2], 1], [c[0] + s[0], c[1] + s[1], c[2] + s[2], 1]];
        for (const k of [0, 1, 2, 0, 2, 3]) v.push(P[k][0], P[k][1], P[k][2], q.col[0], q.col[1], q.col[2], a, 0, P[k][3]);
        continue;
      }
      const ax = [B.r[0] * q.s, B.r[1] * q.s, B.r[2] * q.s], ay = [B.u[0] * q.s, B.u[1] * q.s, B.u[2] * q.s];
      const P = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
      for (const k of [0, 1, 2, 0, 2, 3]) {
        const p = P[k];
        v.push(c[0] + ax[0] * p[0] + ay[0] * p[1], c[1] + ax[1] * p[0] + ay[1] * p[1], c[2] + ax[2] * p[0] + ay[2] * p[1], q.col[0], q.col[1], q.col[2], a, p[0], p[1]);
      }
    }
    gl.useProgram(F.p);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.fxVerts); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(v), gl.DYNAMIC_DRAW);
    attribs(gl, [[F.loc.aP, this.fxVerts, 3, 36, 0], [F.loc.aC, this.fxVerts, 4, 36, 12], [F.loc.aT, this.fxVerts, 2, 36, 28]]);
    gl.uniformMatrix4fv(F.loc.uVP, false, vp);
    gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE); gl.depthMask(false);
    gl.drawArrays(gl.TRIANGLES, 0, v.length / 9);
    gl.disable(gl.BLEND); gl.depthMask(true);
  };

  Renderer.prototype.draw = function (s, opts) {
    opts = opts || {};
    const gl = this.gl, Sim = this.Sim, P = Sim.P, W = this.W, G = this.world, U = G.loc, vis = this.vis;
    const dpr = window.devicePixelRatio || 1;
    const cw = Math.floor(this.canvas.clientWidth * dpr), ch = Math.floor(this.canvas.clientHeight * dpr);
    if (this.canvas.width !== cw || this.canvas.height !== ch) { this.canvas.width = cw; this.canvas.height = ch; }
    gl.viewport(0, 0, cw, ch);
    const aspect = cw / Math.max(ch, 1);
    const eye = [s.x, s.feet + P.eye, s.z], d = Sim.aim(s), B = basis(d);
    const view = viewOf(eye, B), vp = mul(perspective(FOV, aspect, 0.05, 1500), view);

    // the shot as the eye sees it, read from the state: the time since the trigger, from the cooldown
    const since = s.cooldown > 0 ? P.fireCooldown - s.cooldown : 1;
    const kick = since < P.fireCooldown ? (since / 0.018) * Math.exp(1 - since / 0.018) : 0;
    const flash = since < 0.04 ? 1 - since / 0.04 : 0;
    // the hand's own motion: bob with the distance walked, sway with the look; kept here, for the view only
    if (vis.prev) {
      const m = Math.hypot(s.x - vis.prev[0], s.z - vis.prev[1]);
      if (m < 1 && s.onGround) vis.dist += m;
      vis.move += ((m > 1e-4 && m < 1 ? 1 : 0) - vis.move) * 0.15;
    }
    vis.prev = [s.x, s.z];
    const look = opts.look || [0, 0];
    vis.sx += (Math.max(-0.05, Math.min(0.05, -look[0] * 0.5)) - vis.sx) * 0.2;
    vis.sy += (Math.max(-0.05, Math.min(0.05, -look[1] * 0.5)) - vis.sy) * 0.2;
    const bob = vis.move * Math.sin(vis.dist * Math.PI / 1.7) * 0.007, bobx = vis.move * Math.cos(vis.dist * Math.PI / 3.4) * 0.006;
    const hand = mul(cameraToWorld(eye, B), mul(translate(0.165 + bobx - vis.sx * 0.4, -0.19 + bob + 0.006 * kick - vis.sy * 0.4, -0.62 + 0.040 * kick),
                     mul(rotY(0.06 + vis.sx), mul(rotX(0.065 * kick + vis.sy), rotZ(0.03 - 0.04 * kick)))));
    const muzzle = apply(hand, MUZZLE);

    gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    // the sky
    gl.disable(gl.DEPTH_TEST); gl.depthMask(false);
    gl.useProgram(this.sky.p);
    const SL = this.sky.loc, th = Math.tan(FOV / 2);
    attribs(gl, [[SL.aP, this.skyQuad, 2]]);
    gl.uniform3fv(SL.uSun, SUN); gl.uniform3fv(SL.uRight, B.r); gl.uniform3fv(SL.uUp, B.u); gl.uniform3fv(SL.uFwd, B.f);
    gl.uniform2f(SL.uTan, th * aspect, th);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    gl.enable(gl.DEPTH_TEST); gl.depthMask(true);

    // the world, its decoration, the targets
    gl.useProgram(G.p);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, this.hf); gl.uniform1i(U.uHF, 0);
    gl.uniformMatrix4fv(U.uVP, false, vp); gl.uniformMatrix4fv(U.uModel, false, ID);
    gl.uniform3fv(U.uEye, eye); gl.uniform3fv(U.uSun, SUN);
    gl.uniform2f(U.uHFSize, W.w, W.h); gl.uniform1f(U.uCell, W.cell);
    gl.uniform1f(U.uHScale, this.maxH); gl.uniform1f(U.uMaxH, this.maxH); gl.uniform1f(U.uWall, W.wall);
    gl.uniform1f(U.uGrid, this.grid ? 1 : 0); gl.uniform1f(U.uAOOn, 1); gl.uniform1f(U.uShadowFix, -1); gl.uniform1f(U.uFogOn, 1);
    gl.uniform1f(U.uPix, 2 * Math.tan(FOV / 2) / Math.max(ch, 1));
    const o = W.objective ? W.objective.rect : null, c = W.cell;
    gl.uniform4fv(U.uObj, o ? [o[0] * c, o[1] * c, (o[2] + 1) * c, (o[3] + 1) * c] : [1, 1, -1, -1]);
    const sa = W.spawns.A, sb = W.spawns.B;
    gl.uniform4fv(U.uSpawn, [sa ? (sa.x + 0.5) * c : -99, sa ? (sa.z + 0.5) * c : -99, sb ? (sb.x + 0.5) * c : -99, sb ? (sb.z + 0.5) * c : -99]);
    gl.uniform4fv(U.uFlash, [muzzle[0], muzzle[1], muzzle[2], flash * 2.5]);
    gl.uniform4fv(U.uTint, [0, 0, 0, 0]);
    const blobs = new Float32Array(32);
    let nb = 0;
    for (const t of s.targets) { if (t.up && nb < 8) { blobs.set([t.x, t.z, 0.6, 0.45], nb * 4); nb++; } }
    gl.uniform4fv(U.uBlob, blobs);
    this.bindMesh(this.worldBuf); gl.drawArrays(gl.TRIANGLES, 0, this.worldBuf.count);
    this.bindMesh(this.decorBuf); gl.drawArrays(gl.TRIANGLES, 0, this.decorBuf.count);
    this.bindMesh(this.targetBuf);
    for (const t of s.targets) {
      let sink = 0;
      if (!t.up) sink = -1.72 * Math.max(0, Math.min(1, (P.targetDown - t.downFor) / 0.12, t.downFor / 0.12));
      const f = s.fx.flash[t.id] || 0;
      gl.uniform4fv(U.uTint, [1, 1, 1, Math.min(0.8, f * 4)]);
      gl.uniformMatrix4fv(U.uModel, false, translate(t.x, t.y + sink, t.z));
      gl.drawArrays(gl.TRIANGLES, 0, this.targetBuf.count);
    }
    gl.uniform4fv(U.uTint, [0, 0, 0, 0]);

    // effects: where the last shot ended, and its streak
    const fx = [], ls = s.fx.lastShot;
    if (ls && ls.age < 0.3) {
      const k = 1 - ls.age / 0.3;
      fx.push({ c: ls.h, s: 0.12 + ls.age * 0.8, col: ls.hit ? [1.0, 0.55, 0.45] : [0.9, 0.75, 0.5], a: 0.9 * k });
      if (since < 0.05) {
        const st = [0, 1, 2].map(function (a) { return eye[a] + d[a] * 1.5 + B.r[a] * 0.12 - B.u[a] * 0.10; });
        fx.push({ c: st, to: ls.h, s: 0.012, col: [1.0, 0.85, 0.5], a: 0.8 * (1 - since / 0.05) });
      }
    }
    this.drawFx(vp, B, fx);

    // the weapon: its own projection, over the world, lit by the sun where the eye is
    gl.clear(gl.DEPTH_BUFFER_BIT);
    const vpHand = mul(perspective(FOV_HAND, aspect, 0.01, 10), view);
    gl.useProgram(G.p);
    gl.uniformMatrix4fv(U.uVP, false, vpHand); gl.uniformMatrix4fv(U.uModel, false, hand);
    gl.uniform1f(U.uAOOn, 0); gl.uniform1f(U.uFogOn, 0); gl.uniform1f(U.uGrid, 0);
    gl.uniform1f(U.uShadowFix, this.shadowAt(eye[0], eye[1] - 0.15, eye[2]));
    this.bindMesh(this.gunBuf); gl.drawArrays(gl.TRIANGLES, 0, this.gunBuf.count);
    if (flash > 0) {
      this.drawFx(vpHand, B, [{ c: muzzle, s: 0.09 + 0.05 * flash, col: [1.0, 0.75, 0.35], a: 1.6 * flash },
                              { c: muzzle, s: 0.035, col: [1.0, 0.95, 0.8], a: 2.0 * flash }]);
    }
  };

  root.GrayboxRenderer = { Renderer: Renderer, buildWorld: buildWorld, playCeiling: playCeiling, buildDecor: buildDecor, SUN: SUN };
})(typeof self !== "undefined" ? self : this);
