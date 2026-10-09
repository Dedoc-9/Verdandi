// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/render.js — FPS-GRAYBOX-0's renderer: WebGL 1, one shader, flat graybox colours, a 1 m grid.
//
// It builds its mesh from the canonical world W (each cell's kind and top) and draws the state the simulation gives
// it. It reads; it writes nothing the simulation reads. Nothing here decides whether a wall is there: collision is
// the collision world's, in sim.js.

(function (root) {
  "use strict";

  const VS = [
    "attribute vec3 aPos; attribute vec3 aNor; attribute vec3 aCol;",
    "uniform mat4 uVP; uniform mat4 uModel; uniform vec3 uTint; uniform float uTintMix;",
    "varying vec3 vCol; varying vec3 vNor; varying vec3 vW;",
    "void main() {",
    "  vec4 w = uModel * vec4(aPos, 1.0);",
    "  vW = w.xyz; vNor = aNor; vCol = mix(aCol, uTint, uTintMix);",
    "  gl_Position = uVP * w;",
    "}"].join("\n");
  const FS = [
    "precision mediump float;",
    "varying vec3 vCol; varying vec3 vNor; varying vec3 vW;",
    "uniform vec3 uEye; uniform float uGrid; uniform vec3 uFog; uniform float uFogOn;",
    "void main() {",
    "  vec3 n = normalize(vNor);",
    "  float l = 0.40 + 0.55 * max(dot(n, normalize(vec3(0.45, 0.85, 0.30))), 0.0)",
    "            + 0.12 * max(dot(n, normalize(vec3(-0.5, 0.3, -0.6))), 0.0);",
    "  vec3 c = vCol * l;",
    "  if (uGrid > 0.5) {",
    "    vec3 a = abs(n);",
    "    vec2 q = a.y > 0.5 ? vW.xz : (a.x > 0.5 ? vW.zy : vW.xy);",
    "    vec2 f = abs(fract(q) - 0.5);",
    "    c *= 1.0 - 0.16 * step(0.475, max(f.x, f.y));",
    "  }",
    "  float fog = uFogOn * clamp((length(vW - uEye) - 30.0) / 110.0, 0.0, 0.6);",
    "  gl_FragColor = vec4(mix(c, uFog, fog), 1.0);",
    "}"].join("\n");

  const SKY = [0.64, 0.71, 0.78];

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
  function lookAt(e, t, u) {
    let zx = e[0] - t[0], zy = e[1] - t[1], zz = e[2] - t[2]; let l = Math.hypot(zx, zy, zz); zx /= l; zy /= l; zz /= l;
    let xx = u[1] * zz - u[2] * zy, xy = u[2] * zx - u[0] * zz, xz = u[0] * zy - u[1] * zx; l = Math.hypot(xx, xy, xz); xx /= l; xy /= l; xz /= l;
    const yx = zy * xz - zz * xy, yy = zz * xx - zx * xz, yz = zx * xy - zy * xx;
    return new Float32Array([xx, yx, zx, 0, xy, yy, zy, 0, xz, yz, zz, 0,
      -(xx * e[0] + xy * e[1] + xz * e[2]), -(yx * e[0] + yy * e[1] + yz * e[2]), -(zx * e[0] + zy * e[1] + zz * e[2]), 1]);
  }
  function box(cx, cy, cz, sx, sy, sz) {
    return new Float32Array([sx, 0, 0, 0, 0, sy, 0, 0, 0, 0, sz, 0, cx, cy, cz, 1]);
  }
  const ID = box(0, 0, 0, 1, 1, 1);

  // ---------------------------------------------------------------- the mesh of the canonical world
  function colourOf(kind, top, i, j, wall) {
    const v = ((i * 73856093) ^ (j * 19349663)) & 7;
    const jit = 1 + (v - 3.5) * 0.008;
    let c;
    if (kind === "wall") c = [0.66, 0.67, 0.70];
    else if (kind === "cover") c = top > 2 ? [0.74, 0.47, 0.30] : [0.82, 0.62, 0.34];
    else if (kind === "raised") c = top >= 1 ? [0.52, 0.58, 0.66] : [0.58, 0.63, 0.70];
    else if (kind === "stair") c = [0.60, 0.55, 0.40];
    else c = ((i + j) & 1) ? [0.44, 0.45, 0.47] : [0.48, 0.49, 0.51];
    return [c[0] * jit, c[1] * jit, c[2] * jit];
  }

  function buildMesh(W) {
    const P = [], N = [], C = [];
    const c = W.cell, w = W.w, h = W.h;
    const cellAt = function (i, j) { return (i < 0 || j < 0 || i >= w || j >= h) ? null : W.cells[j * w + i]; };
    const topAt = function (i, j) { const q = cellAt(i, j); return q ? q[2] : W.wall; };
    const tint = function (i, j, col) {
      const o = W.objective;
      if (o && i >= o.rect[0] && i <= o.rect[2] && j >= o.rect[1] && j <= o.rect[3]) return [col[0] * 0.5 + 0.45, col[1] * 0.5 + 0.40, col[2] * 0.5 + 0.08];
      for (const side in W.spawns) {
        const s = W.spawns[side];
        if (Math.abs(i - s.x) <= 1 && Math.abs(j - s.z) <= 2) return side === "A" ? [col[0] * 0.6, col[1] * 0.65, col[2] * 0.6 + 0.3] : [col[0] * 0.6 + 0.3, col[1] * 0.6, col[2] * 0.6];
      }
      return col;
    };
    const quad = function (a, b, cc, d, n, col) {
      for (const v of [a, b, cc, a, cc, d]) { P.push(v[0], v[1], v[2]); N.push(n[0], n[1], n[2]); C.push(col[0], col[1], col[2]); }
    };
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
      const q = W.cells[j * w + i], kind = q[1], top = q[2];
      const x0 = i * c, x1 = (i + 1) * c, z0 = j * c, z1 = (j + 1) * c;
      let col = colourOf(kind, top, i, j, W.wall);
      if (kind !== "wall") col = tint(i, j, col);
      const topCol = kind === "wall" ? [col[0] * 0.8, col[1] * 0.8, col[2] * 0.8] : col;
      quad([x0, top, z0], [x0, top, z1], [x1, top, z1], [x1, top, z0], [0, 1, 0], topCol);
      const sides = [[1, 0, [x1, z1], [x1, z0], [1, 0, 0]], [-1, 0, [x0, z0], [x0, z1], [-1, 0, 0]],
                     [0, 1, [x0, z1], [x1, z1], [0, 0, 1]], [0, -1, [x1, z0], [x0, z0], [0, 0, -1]]];
      for (const s of sides) {
        const nt = topAt(i + s[0], j + s[1]);
        if (nt >= top) continue;
        const sideCol = kind === "wall" ? col : [col[0] * 0.92, col[1] * 0.92, col[2] * 0.92];
        quad([s[2][0], nt, s[2][1]], [s[2][0], top, s[2][1]], [s[3][0], top, s[3][1]], [s[3][0], nt, s[3][1]], s[4], sideCol);
      }
    }
    return { P: new Float32Array(P), N: new Float32Array(N), C: new Float32Array(C), count: P.length / 3 };
  }

  function cube() {
    const P = [], N = [];
    const f = [[[1, 0, 0], [0, 1, 0], [0, 0, 1]], [[-1, 0, 0], [0, 0, 1], [0, 1, 0]], [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
               [[0, -1, 0], [1, 0, 0], [0, 0, 1]], [[0, 0, 1], [1, 0, 0], [0, 1, 0]], [[0, 0, -1], [0, 1, 0], [1, 0, 0]]];
    for (const [n, u, v] of f) {
      const p = function (a, b) { return [n[0] * 0.5 + (u[0] * a + v[0] * b) * 0.5, n[1] * 0.5 + (u[1] * a + v[1] * b) * 0.5, n[2] * 0.5 + (u[2] * a + v[2] * b) * 0.5]; };
      for (const q of [p(-1, -1), p(1, -1), p(1, 1), p(-1, -1), p(1, 1), p(-1, 1)]) { P.push(q[0], q[1], q[2]); N.push(n[0], n[1], n[2]); }
    }
    const C = new Float32Array(P.length).fill(1);
    return { P: new Float32Array(P), N: new Float32Array(N), C: C, count: P.length / 3 };
  }

  // ---------------------------------------------------------------- the renderer
  function Renderer(canvas, map, Sim) {
    const gl = canvas.getContext("webgl", { antialias: true, preserveDrawingBuffer: true });
    if (!gl) throw new Error("WebGL is not available in this browser");
    this.gl = gl; this.canvas = canvas; this.W = map.canonical; this.Sim = Sim;
    const sh = function (type, src) {
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    };
    const prog = gl.createProgram();
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
    this.prog = prog;
    this.loc = {};
    for (const a of ["aPos", "aNor", "aCol"]) this.loc[a] = gl.getAttribLocation(prog, a);
    for (const u of ["uVP", "uModel", "uTint", "uTintMix", "uEye", "uGrid", "uFog", "uFogOn"]) this.loc[u] = gl.getUniformLocation(prog, u);
    const upload = function (m) {
      const b = {};
      for (const k of ["P", "N", "C"]) { b[k] = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b[k]); gl.bufferData(gl.ARRAY_BUFFER, m[k], gl.STATIC_DRAW); }
      b.count = m.count; return b;
    };
    this.world = upload(buildMesh(this.W));
    this.cube = upload(cube());
    this.triangles = this.world.count / 3;
    gl.enable(gl.DEPTH_TEST);   // no face culling: a graybox's few thousand quads, drawn from both sides
  }

  Renderer.prototype.bind = function (b) {
    const gl = this.gl, L = this.loc;
    const at = function (loc, buf) { gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 3, gl.FLOAT, false, 0, 0); };
    at(L.aPos, b.P); at(L.aNor, b.N); at(L.aCol, b.C);
  };

  Renderer.prototype.draw = function (s, opts) {
    opts = opts || {};
    const gl = this.gl, L = this.loc, Sim = this.Sim, P = Sim.P;
    const dpr = window.devicePixelRatio || 1;
    const cw = Math.floor(this.canvas.clientWidth * dpr), ch = Math.floor(this.canvas.clientHeight * dpr);
    if (this.canvas.width !== cw || this.canvas.height !== ch) { this.canvas.width = cw; this.canvas.height = ch; }
    gl.viewport(0, 0, cw, ch);
    gl.clearColor(SKY[0], SKY[1], SKY[2], 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(this.prog);
    const eye = [s.x, s.feet + P.eye, s.z], d = Sim.aim(s);
    const proj = perspective(75 * Math.PI / 180, cw / ch, 0.05, 400);
    const vp = mul(proj, lookAt(eye, [eye[0] + d[0], eye[1] + d[1], eye[2] + d[2]], [0, 1, 0]));
    gl.uniformMatrix4fv(L.uVP, false, vp); gl.uniform3fv(L.uEye, eye); gl.uniform3fv(L.uFog, SKY); gl.uniform1f(L.uFogOn, 1);
    // the world
    gl.uniformMatrix4fv(L.uModel, false, ID); gl.uniform1f(L.uTintMix, 0); gl.uniform1f(L.uGrid, 1);
    this.bind(this.world); gl.drawArrays(gl.TRIANGLES, 0, this.world.count);
    // targets, the impact of the last shot
    this.bind(this.cube); gl.uniform1f(L.uGrid, 0); gl.uniform1f(L.uTintMix, 1);
    for (const t of s.targets) {
      const flash = s.fx.flash[t.id] || 0;
      if (t.up) {
        gl.uniform3fv(L.uTint, [0.86, 0.18, 0.16]);
        gl.uniformMatrix4fv(L.uModel, false, box(t.x, t.y + 0.75, t.z, 0.7, 1.5, 0.7)); gl.drawArrays(gl.TRIANGLES, 0, this.cube.count);
        gl.uniform3fv(L.uTint, [0.95, 0.9, 0.85]);
        gl.uniformMatrix4fv(L.uModel, false, box(t.x, t.y + 1.68, t.z, 0.44, 0.4, 0.44)); gl.drawArrays(gl.TRIANGLES, 0, this.cube.count);
      } else {
        gl.uniform3fv(L.uTint, flash > 0 ? [1, 1, 1] : [0.35, 0.12, 0.12]);
        gl.uniformMatrix4fv(L.uModel, false, box(t.x, t.y + 0.08, t.z, 0.9, 0.16, 0.9)); gl.drawArrays(gl.TRIANGLES, 0, this.cube.count);
      }
    }
    const ls = s.fx.lastShot;
    if (ls && ls.age < 0.35) {
      gl.uniform3fv(L.uTint, ls.hit ? [1, 1, 1] : [1, 0.85, 0.2]);
      gl.uniformMatrix4fv(L.uModel, false, box(ls.h[0], ls.h[1], ls.h[2], 0.12, 0.12, 0.12)); gl.drawArrays(gl.TRIANGLES, 0, this.cube.count);
    }
    // the weapon placeholder, in view space, over the world
    gl.clear(gl.DEPTH_BUFFER_BIT);
    gl.uniformMatrix4fv(L.uVP, false, proj); gl.uniform3fv(L.uEye, [0, 0, 0]); gl.uniform1f(L.uFogOn, 0);
    const kick = Math.max(0, s.cooldown - (P.fireCooldown - 0.06)) * 1.2;
    const bob = opts.moving ? Math.sin(s.tick / 10) * 0.012 : 0;
    gl.uniform3fv(L.uTint, [0.22, 0.23, 0.25]);
    gl.uniformMatrix4fv(L.uModel, false, box(0.17, -0.15 + bob, -0.46 + kick, 0.04, 0.05, 0.30)); gl.drawArrays(gl.TRIANGLES, 0, this.cube.count);
    gl.uniform3fv(L.uTint, [0.32, 0.33, 0.35]);
    gl.uniformMatrix4fv(L.uModel, false, box(0.17, -0.20 + bob, -0.36 + kick, 0.035, 0.08, 0.05)); gl.drawArrays(gl.TRIANGLES, 0, this.cube.count);
    if (kick > 0.03) {
      gl.uniform3fv(L.uTint, [1, 0.8, 0.3]);
      gl.uniformMatrix4fv(L.uModel, false, box(0.17, -0.14 + bob, -0.64 + kick, 0.05, 0.05, 0.05)); gl.drawArrays(gl.TRIANGLES, 0, this.cube.count);
    }
  };

  root.GrayboxRenderer = { Renderer: Renderer, buildMesh: buildMesh };
})(typeof self !== "undefined" ? self : this);
