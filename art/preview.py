# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/preview.py — a provisional first-person look at a scene, for a person's judgment between admissions.
#
#   python art/preview.py BRIEF            writes art/build/BRIEF/preview.html: open it in a browser
#
# PROVISIONAL_PREVIEW. A sketch: the scene's boxes in their materials' colours, the moon, every lamp and neon light
# as a point light, height fog, a tone curve. It is not the Unreal look (no global illumination, no reflections, no
# textures), it decides nothing, and nothing hashes its pixels. It exists so that "more imposing" can be judged from
# where a player stands before the engine is installed, not as evidence of anything.
#
# In the page: keys 1-9 jump to the brief's views; W A S D and the mouse (click to capture) move; Q and E go down
# and up. ?view=NAME opens at a view, ?cam=x,y,z,yaw,pitch anywhere (metres, degrees); ?shot=1 hides the overlay
# (for stills). Standalone: the scene is inside the file.

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dress  # noqa: E402

PAGE = r"""<!doctype html><meta charset=utf-8><title>%(title)s — PROVISIONAL_PREVIEW</title>
<style>html,body{margin:0;height:100%%;background:#05070a;overflow:hidden}canvas{display:block;width:100%%;height:100%%}
#hud{position:fixed;left:10px;top:8px;color:#cfd6dd;font:12px/1.4 system-ui,sans-serif;text-shadow:0 1px 2px #000;pointer-events:none}
#hud b{color:#ff8a3d}body.shot #hud{display:none}</style>
<canvas id=c></canvas><div id=hud><b>PROVISIONAL_PREVIEW</b> · a sketch for judgment, not the Unreal look; nothing hashes it<br>
<span id=v></span><br>1–9 views · click, then W A S D, mouse, Q/E</div>
<script>
"use strict";
const S = %(scene)s;
const q = new URLSearchParams(location.search);
if (q.get("shot")) document.body.classList.add("shot");
const cv = document.getElementById("c"), gl = cv.getContext("webgl2", {antialias: true, preserveDrawingBuffer: true});
if (!gl) { document.body.innerHTML = "<p style='color:#fff'>WebGL 2 is not available in this browser.</p>"; throw 0; }
const lin = c => c.map(v => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
// geometry: every box, with its material, as 36 vertices
const P = [], N = [], A = [], M = [];
function box(b, m) {
  const [x0, y0, z0, x1, y1, z1] = b, base = lin(m.base), em = lin(m.emissive).map(v => v * m.emissive_strength / 20);
  const f = [[[1,0,0],[[x1,y0,z0],[x1,y1,z0],[x1,y1,z1],[x1,y0,z1]]], [[-1,0,0],[[x0,y0,z1],[x0,y1,z1],[x0,y1,z0],[x0,y0,z0]]],
             [[0,1,0],[[x0,y1,z0],[x0,y1,z1],[x1,y1,z1],[x1,y1,z0]]], [[0,-1,0],[[x0,y0,z1],[x0,y0,z0],[x1,y0,z0],[x1,y0,z1]]],
             [[0,0,1],[[x1,y0,z1],[x1,y1,z1],[x0,y1,z1],[x0,y0,z1]]], [[0,0,-1],[[x0,y0,z0],[x0,y1,z0],[x1,y1,z0],[x1,y0,z0]]]];
  for (const [n, v] of f) for (const i of [0, 1, 2, 0, 2, 3]) {
    P.push(...v[i]); N.push(...n); A.push(...base, m.roughness); M.push(...em, m.metallic);
  }
}
for (const b of S.collision) box(b.box, S.materials[b.material]);
for (const v of S.visuals) box(v.box, S.materials[v.material]);
const L = S.lights.map(l => [l.pos[0], l.pos[1], l.pos[2], l.radius, ...lin(l.color).map(c => c * l.candela / 900), 0]);
const NL = L.length;
const vs = `#version 300 es
in vec3 p; in vec3 n; in vec4 a; in vec4 m; uniform mat4 vp; out vec3 wp; out vec3 wn; out vec4 al; out vec4 em;
void main(){ wp=p; wn=n; al=a; em=m; gl_Position=vp*vec4(p,1.0); }`;
const fs = `#version 300 es
precision highp float; in vec3 wp; in vec3 wn; in vec4 al; in vec4 em; out vec4 o;
uniform vec3 eye; uniform vec3 moonDir; uniform vec3 moonCol; uniform vec3 fogCol; uniform float fogD; uniform float expo;
uniform sampler2D lt; uniform int nl;
void main(){
  vec3 n=normalize(wn), v=normalize(eye-wp), c=al.rgb; float r=max(al.a,0.04), sh=2.0/(r*r)-2.0;
  vec3 col=c*(vec3(0.020,0.026,0.040)+0.012*n.y);
  float d=max(dot(n,moonDir),0.0); vec3 h=normalize(moonDir+v);
  col+=moonCol*(c*d+pow(max(dot(n,h),0.0),sh)*(1.0-r)*0.4*d);
  for(int i=0;i<128;i++){ if(i>=nl) break;
    vec4 a=texelFetch(lt,ivec2(i,0),0), b=texelFetch(lt,ivec2(i,1),0);
    vec3 dl=a.xyz-wp; float dist=length(dl); vec3 l=dl/dist; float att=pow(clamp(1.0-dist/a.w,0.0,1.0),2.0)/(1.0+dist*dist*0.25);
    float nd=max(dot(n,l),0.0); vec3 hh=normalize(l+v);
    col+=b.rgb*att*(c*nd+pow(max(dot(n,hh),0.0),sh)*(1.0-r)*nd*1.5);
  }
  col+=em.rgb;
  float dz=length(eye-wp); float fog=1.0-exp(-pow(fogD*dz,1.15));
  col=mix(col,fogCol,fog);
  col*=expo; col=col*(2.51*col+0.03)/(col*(2.43*col+0.59)+0.14);
  o=vec4(pow(clamp(col,0.0,1.0),vec3(1.0/2.2)),1.0);
}`;
function sh(t, s) { const x = gl.createShader(t); gl.shaderSource(x, s); gl.compileShader(x); if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) throw gl.getShaderInfoLog(x); return x; }
const pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(pr); gl.useProgram(pr);
for (const [name, data, k] of [["p", P, 3], ["n", N, 3], ["a", A, 4], ["m", M, 4]]) {
  const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(data), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(pr, name); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, k, gl.FLOAT, false, 0, 0);
}
const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
const td = new Float32Array(Math.max(NL, 1) * 8);
L.forEach((l, i) => { td.set(l.slice(0, 4), i * 4); td.set(l.slice(4, 8), (Math.max(NL, 1) + i) * 4); });
gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, Math.max(NL, 1), 2, 0, gl.RGBA, gl.FLOAT, td);
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
const U = n => gl.getUniformLocation(pr, n);
const env = S.environment, lt = env.light, fogc = env.fog ? lin(env.fog.color) : [0, 0, 0];
const az = (lt ? lt.azimuth : 200) * Math.PI / 180, el = (lt ? lt.elevation : 25) * Math.PI / 180;
gl.uniform3f(U("moonDir"), Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));
const mc = lt ? lin(lt.color).map(c => c * Math.min(lt.lux, 2) * 0.35) : [0.05, 0.05, 0.06];
gl.uniform3fv(U("moonCol"), mc); gl.uniform3fv(U("fogCol"), fogc.map(c => c * 0.6)); gl.uniform1f(U("fogD"), env.fog ? env.fog.density : 0.01);
gl.uniform1f(U("expo"), Math.pow(2, env.exposure || 0) * 0.55); gl.uniform1i(U("nl"), Math.min(NL, 128)); gl.uniform1i(U("lt"), 0);
gl.enable(gl.DEPTH_TEST); gl.enable(gl.CULL_FACE);
const views = Object.keys(S.views).sort();
let cam = {x: S.spawns.A.x, y: S.spawns.A.y + 1.62, z: S.spawns.A.z, yaw: S.spawns.A.yaw, pitch: 0};
function go(name) { const v = S.views[name]; if (!v) return; cam = {x: v.x, y: v.y, z: v.z, yaw: v.yaw, pitch: v.pitch}; label = name; }
let label = "spawn A";
if (q.get("view")) go(q.get("view"));
if (q.get("cam")) { const c = q.get("cam").split(",").map(Number); cam = {x: c[0], y: c[1], z: c[2], yaw: c[3], pitch: c[4]}; label = "cam " + q.get("cam"); }
function mat4(fovy, asp, near, far, c) {
  const f = 1 / Math.tan(fovy / 2), yaw = c.yaw * Math.PI / 180, pit = c.pitch * Math.PI / 180;
  const fx = Math.sin(yaw) * Math.cos(pit), fy = Math.sin(pit), fz = -Math.cos(yaw) * Math.cos(pit);
  let rx = -fz, rz = fx; const rl = Math.hypot(rx, rz); rx /= rl; rz /= rl;
  const ux = -rz * fy, uy = rz * fx - rx * fz, uz = rx * fy;
  const ex = c.x, ey = c.y, ez = c.z;
  const V = [rx, ux, -fx, 0, 0, uy, -fy, 0, rz, uz, -fz, 0, -(rx * ex + rz * ez), -(ux * ex + uy * ey + uz * ez), (fx * ex + fy * ey + fz * ez), 1];
  const Pm = [f / asp, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) / (near - far), -1, 0, 0, 2 * far * near / (near - far), 0];
  const o = new Array(16).fill(0);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) for (let k = 0; k < 4; k++) o[j * 4 + i] += Pm[k * 4 + i] * V[j * 4 + k];
  return o;
}
const keys = {};
addEventListener("keydown", e => { keys[e.key.toLowerCase()] = true; const n = parseInt(e.key); if (n >= 1 && n <= views.length) go(views[n - 1]); });
addEventListener("keyup", e => { keys[e.key.toLowerCase()] = false; });
cv.addEventListener("click", () => cv.requestPointerLock && cv.requestPointerLock());
addEventListener("mousemove", e => { if (document.pointerLockElement === cv) { cam.yaw += e.movementX * 0.12; cam.pitch = Math.max(-85, Math.min(85, cam.pitch - e.movementY * 0.12)); } });
let last = performance.now(), frames = 0;
function frame(t) {
  const dt = Math.min(0.05, (t - last) / 1000); last = t;
  const yaw = cam.yaw * Math.PI / 180, sp = 6 * dt;
  if (keys.w) { cam.x += Math.sin(yaw) * sp; cam.z -= Math.cos(yaw) * sp; label = "free"; }
  if (keys.s) { cam.x -= Math.sin(yaw) * sp; cam.z += Math.cos(yaw) * sp; label = "free"; }
  if (keys.a) { cam.x -= Math.cos(yaw) * sp; cam.z -= Math.sin(yaw) * sp; label = "free"; }
  if (keys.d) { cam.x += Math.cos(yaw) * sp; cam.z += Math.sin(yaw) * sp; label = "free"; }
  if (keys.q) cam.y -= sp; if (keys.e) cam.y += sp;
  const w = cv.clientWidth, h = cv.clientHeight;
  if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
  gl.viewport(0, 0, w, h); gl.clearColor(Math.pow(fogc[0], 0.6) * 0.35, Math.pow(fogc[1], 0.6) * 0.35, Math.pow(fogc[2], 0.6) * 0.42, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.uniformMatrix4fv(U("vp"), false, mat4(62 * Math.PI / 180, w / h, 0.05, 600, cam)); gl.uniform3f(U("eye"), cam.x, cam.y, cam.z);
  gl.drawArrays(gl.TRIANGLES, 0, P.length / 3);
  document.getElementById("v").textContent = "view: " + label + " · " + views.map((v, i) => (i + 1) + " " + v).join(" · ");
  if (++frames === 2) window.PREVIEW_READY = true;
  if (!(q.get("shot") && frames >= 2)) requestAnimationFrame(frame);   // a still renders twice and stops
}
requestAnimationFrame(frame);
</script>
"""


def write(name, dest=None, art_path=None):
    out = dress.export(dress.load(name, art_path))
    S = out["scene"]
    keep = {k: S[k] for k in ("title", "collision", "visuals", "lights", "materials", "environment", "views", "spawns")}
    page = PAGE % {"title": (S["title"] or name).replace("<", "&lt;"), "scene": json.dumps(keep, separators=(",", ":")).replace("</", "<\\/")}
    dest = dest or os.path.join(dress.BUILD, name)
    os.makedirs(dest, exist_ok=True)
    p = os.path.join(dest, "preview.html")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    return p, sorted(S["views"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python art/preview.py BRIEF")
        sys.exit(2)
    p, views = write(sys.argv[1])
    print("%s  (PROVISIONAL_PREVIEW; views: %s)" % (os.path.relpath(p, os.path.dirname(HERE)), ", ".join(views)))
