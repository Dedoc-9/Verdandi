// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// art/web/studio_ui.js — STUDIO-3 (0230): the studio shell's own pieces, which hold no state of the game or the world:
// its icons (inline SVG, drawn here; the page loads nothing from elsewhere), a small DOM builder, the view's arithmetic
// (the camera's basis, a point projected to the canvas, the ray through a pixel, where a ray enters a box and through
// which face), and the thumbnailer (a second renderer on a small canvas, drawing the scene as it is from a camera
// framed on one object). Everything here reads; nothing writes a scene, a source, a tag or the ledger.
//
// The arithmetic is the renderer's own (art/web/scene_render.js): a camera is x, y, z in metres, yaw (0 north, -z;
// pi/2 east, +x) and pitch in radians, a vertical field of view of 66 degrees unless the camera says otherwise.

(function (root) {
  "use strict";

  // ---------------------------------------------------------------- icons (24 x 24, stroked in the text's colour)
  const P = {
    logo: '<path d="M12 2 3 7v10l9 5 9-5V7z"/><path d="M12 2v20M3 7l9 5 9-5"/>',
    file: '<path d="M14 3H6v18h12V7z"/><path d="M14 3v4h4"/>',
    globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/>',
    overview: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
    layers: '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    bookmark: '<path d="M6 3h12v18l-6-4-6 4z"/>',
    camera: '<rect x="3" y="7" width="18" height="13" rx="2"/><circle cx="12" cy="13.5" r="3.5"/><path d="M8 7l2-3h4l2 3"/>',
    cube: '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/>',
    voxel: '<rect x="3" y="12" width="6" height="6"/><rect x="9" y="12" width="6" height="6"/><rect x="9" y="6" width="6" height="6"/><rect x="15" y="12" width="6" height="6"/>',
    brush: '<path d="M14 4 20 10 11 19H5v-6z"/><path d="M12 6l6 6"/>',
    decal: '<path d="M4 4h12l4 4v12H4z"/><path d="M16 4v4h4"/><circle cx="10" cy="13" r="3"/>',
    bulb: '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>',
    audio: '<path d="M4 9h4l5-4v14l-5-4H4z"/><path d="M16 9a4 4 0 0 1 0 6M18.5 6.5a8 8 0 0 1 0 11"/>',
    gamepad: '<rect x="2" y="7" width="20" height="11" rx="5"/><path d="M7 10v5M4.5 12.5h5"/><circle cx="16" cy="11" r="1"/><circle cx="18.5" cy="13.5" r="1"/>',
    agent: '<circle cx="12" cy="7" r="4"/><path d="M4 21c1-4.5 4.5-6.5 8-6.5s7 2 8 6.5"/>',
    volume: '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z" stroke-dasharray="3 2"/>',
    folder: '<path d="M3 6h7l2 2h9v11H3z"/>',
    folderopen: '<path d="M3 6h7l2 2h7v3"/><path d="M3 19 6 11h16l-3 8z"/>',
    sphere: '<circle cx="12" cy="12" r="9"/><path d="M3 12c3 2.5 15 2.5 18 0"/><path d="M8.5 6.5a5 5 0 0 1 4-1.5" />',
    prefab: '<path d="m12 3 8 4v10l-8 4-8-4V7z"/><path d="M4 7l8 4 8-4M12 11v10"/><path d="M8 5l8 4"/>',
    map: '<path d="M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15M15 6v15"/>',
    sparkle: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18"/>',
    template: '<rect x="4" y="4" width="11" height="11"/><path d="M9 20h11V9"/>',
    candidates: '<path d="M12 3l2.5 5.5L20 9l-4 4 1 6-5-3-5 3 1-6-4-4 5.5-.5z"/>',
    compare: '<rect x="3" y="4" width="18" height="16"/><path d="M12 4v16"/><path d="m8 10-2 2 2 2M16 10l2 2-2 2"/>',
    history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
    shield: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    select: '<path d="M5 3l14 8-6 1.5L10 19z"/>',
    move: '<path d="M12 3v18M3 12h18"/><path d="m9 6 3-3 3 3M9 18l3 3 3-3M6 9l-3 3 3 3M18 9l3 3-3 3"/>',
    rotate: '<path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/>',
    scale: '<rect x="3" y="11" width="10" height="10"/><path d="M13 11V3h8v8h-8"/><path d="m14 10 6-6"/>',
    pen: '<path d="M4 20l1-5L16 4l4 4L9 19z"/><path d="M14 6l4 4"/>',
    shape: '<path d="M5 5h10l4 7-6 7H6l-2-7z"/><circle cx="5" cy="5" r="1.4"/><circle cx="15" cy="5" r="1.4"/><circle cx="19" cy="12" r="1.4"/><circle cx="13" cy="19" r="1.4"/><circle cx="6" cy="19" r="1.4"/>',
    ruler: '<path d="M3 17 17 3l4 4L7 21z"/><path d="m7 13 2 2M10 10l2 2M13 7l2 2"/>',
    focus: '<path d="M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4"/><circle cx="12" cy="12" r="3"/>',
    play: '<path d="M7 4v16l13-8z"/>',
    check: '<path d="m4 12 5 5L20 6"/>',
    hammer: '<path d="M14 6 4 16l4 4 10-10"/><path d="m12 4 4-1 5 5-1 4-3-1-4-4z"/>',
    eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    eyeoff: '<path d="M3 3l18 18"/><path d="M10.5 5.1A10 10 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3 3.8M6.6 6.6C3.7 8.3 2 12 2 12s3.5 7 10 7c1.6 0 3-.4 4.3-1"/>',
    lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    chevron: '<path d="m6 9 6 6 6-6"/>',
    chevronr: '<path d="m9 6 6 6-6 6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    search: '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 5 5"/>',
    grid: '<path d="M3 9h18M3 15h18M9 3v18M15 3v18"/><rect x="3" y="3" width="18" height="18"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>',
    dot: '<circle cx="12" cy="12" r="5" fill="currentColor"/>',
    book: '<path d="M4 4h7a3 3 0 0 1 3 3v13a2 2 0 0 0-2-2H4z"/><path d="M20 4h-4a2 2 0 0 0-2 2"/><path d="M20 4v14h-6"/>',
    undo: '<path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-3"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    warn: '<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17v.5"/>',
    refresh: '<path d="M20 11a8 8 0 0 0-14-5L4 8"/><path d="M4 3v5h5M4 13a8 8 0 0 0 14 5l2-2"/><path d="M20 21v-5h-5"/>',
    wand: '<path d="m4 20 11-11"/><path d="m13 7 2 2"/><path d="M17 3v3M15.5 4.5h3M20 8v2M19 9h2M9 3v2M8 4h2"/>',
    dots: '<circle cx="5" cy="12" r="1.2"/><circle cx="12" cy="12" r="1.2"/><circle cx="19" cy="12" r="1.2"/>',
    point: '<circle cx="12" cy="12" r="3"/><path d="M12 3v4M12 17v4M3 12h4M17 12h4"/>',
    finish: '<path d="M5 21V4h11l-2 4 2 4H5"/>',
    persp: '<path d="M4 18 9 6h6l5 12z"/><path d="M4 18h16"/>',
    sliders: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
  };
  const NS = "http://www.w3.org/2000/svg";
  // an icon element; `name` one of the names above
  const icon = function (name, cls) {
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("aria-hidden", "true");
    s.setAttribute("class", "ic" + (cls ? " " + cls : ""));
    s.innerHTML = P[name] || P.dots;
    return s;
  };

  // ---------------------------------------------------------------- a small DOM builder
  // el("div.cls#id", {title: ..., onclick: fn, dataset: {...}}, child, "text", [children]...)
  const el = function (spec, attrs) {
    const m = /^([a-z0-9]+)?((?:[.#][A-Za-z0-9_-]+)*)$/.exec(spec) || [];
    const e = document.createElement(m[1] || "div");
    (m[2] || "").replace(/([.#])([A-Za-z0-9_-]+)/g, function (_x, k, v) { if (k === ".") e.classList.add(v); else e.id = v; return ""; });
    let rest = 1;
    if (attrs && typeof attrs === "object" && !(attrs instanceof Node) && !Array.isArray(attrs)) {
      rest = 2;
      for (const k in attrs) {
        const v = attrs[k];
        if (v === undefined || v === null || v === false) continue;
        if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), v);
        else if (k === "dataset") Object.assign(e.dataset, v);
        else if (k === "style" && typeof v === "object") Object.assign(e.style, v);
        else if (k === "text") e.textContent = v;
        else if (k in e && k !== "list" && typeof v !== "string") e[k] = v;
        else e.setAttribute(k, v === true ? "" : v);
      }
    }
    const add = function (c) {
      if (c === null || c === undefined || c === false) return;
      if (Array.isArray(c)) { c.forEach(add); return; }
      e.appendChild(c instanceof Node ? c : document.createTextNode(String(c)));
    };
    for (let i = rest; i < arguments.length; i++) add(arguments[i]);
    return e;
  };

  // ---------------------------------------------------------------- the view's arithmetic
  const deg = Math.PI / 180;
  // the camera's forward, right and up, as the renderer's viewOf and lookAt make them
  const basis = function (c) {
    const cp = Math.cos(c.pitch), f = [cp * Math.sin(c.yaw), Math.sin(c.pitch), -cp * Math.cos(c.yaw)], r = [Math.cos(c.yaw), 0, Math.sin(c.yaw)];
    const u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
    return { f: f, r: r, u: u };
  };
  const NEAR = 0.1;
  // a world point in the camera's frame: [right, up, forward] metres
  const toCam = function (c, B, p) {
    const d = [p[0] - c.x, p[1] - c.y, p[2] - c.z];
    return [d[0] * B.r[0] + d[1] * B.r[1] + d[2] * B.r[2], d[0] * B.u[0] + d[1] * B.u[1] + d[2] * B.u[2], d[0] * B.f[0] + d[1] * B.f[1] + d[2] * B.f[2]];
  };
  // a point of the camera's frame on a W x H canvas (CSS pixels), or null behind the near plane
  const toScreen = function (c, q, W, H) {
    if (q[2] < NEAR) return null;
    const th = Math.tan((c.fov || 66) * deg / 2), asp = W / H;
    return [(q[0] / (q[2] * th * asp) + 1) / 2 * W, (1 - q[1] / (q[2] * th)) / 2 * H];
  };
  const project = function (c, p, W, H) { return toScreen(c, toCam(c, basis(c), p), W, H); };
  // a segment of the world drawn on the canvas, clipped at the near plane; null if all of it is behind
  const segment = function (c, B, a, b, W, H) {
    let qa = toCam(c, B, a), qb = toCam(c, B, b);
    if (qa[2] < NEAR && qb[2] < NEAR) return null;
    if (qa[2] < NEAR || qb[2] < NEAR) {
      const t = (NEAR - qa[2]) / (qb[2] - qa[2]), m = [qa[0] + (qb[0] - qa[0]) * t, qa[1] + (qb[1] - qa[1]) * t, NEAR];
      if (qa[2] < NEAR) qa = m; else qb = m;
    }
    return [toScreen(c, qa, W, H), toScreen(c, qb, W, H)];
  };
  const EDGES = [[0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3], [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7]];
  const corners = function (b) {
    const out = [];
    for (let i = 0; i < 8; i++) out.push([b[i & 1 ? 3 : 0], b[i & 2 ? 4 : 1], b[i & 4 ? 5 : 2]]);
    return out;
  };
  // a box's twelve edges on the canvas, each [[x, y], [x, y]], those wholly behind the eye left out
  const boxEdges = function (c, b, W, H) {
    const B = basis(c), k = corners(b), out = [];
    for (const e of EDGES) { const s = segment(c, B, k[e[0]], k[e[1]], W, H); if (s) out.push(s); }
    return out;
  };
  // the ray through a canvas point (CSS pixels): origin and unit direction
  const rayAt = function (c, px, py, W, H) {
    const B = basis(c), th = Math.tan((c.fov || 66) * deg / 2), asp = W / H;
    const nx = (px / W) * 2 - 1, ny = 1 - (py / H) * 2;
    const d = [0, 1, 2].map(function (i) { return B.f[i] + B.r[i] * nx * th * asp + B.u[i] * ny * th; });
    const l = Math.hypot(d[0], d[1], d[2]);
    return { o: [c.x, c.y, c.z], d: [d[0] / l, d[1] / l, d[2] / l] };
  };
  // where a ray enters a box: {t, face} (face "+x", "-y", ...: the side it comes through), or null. A ray that starts
  // inside the box does not enter it (null): the eye inside a box sees out of it.
  const enterBox = function (o, d, b) {
    let near = -Infinity, far = Infinity, axis = -1;
    for (let a = 0; a < 3; a++) {
      const lo = b[a], hi = b[a + 3];
      if (d[a] === 0) { if (o[a] < lo || o[a] > hi) return null; continue; }
      let t1 = (lo - o[a]) / d[a], t2 = (hi - o[a]) / d[a];
      if (t1 > t2) { const t = t1; t1 = t2; t2 = t; }
      if (t1 > near) { near = t1; axis = a; }
      if (t2 < far) far = t2;
      if (near > far) return null;
    }
    if (far < 0 || near < 0 || axis < 0) return null;
    return { t: near, face: (d[axis] > 0 ? "-" : "+") + "xyz"[axis] };
  };
  // the face frames of MARK-0 (art/studio_marks.py, FRAMES): origin, u and v of a box's face, its width and height
  const FRAMES = {
    "+x": function (b) { return { o: [b[3], b[1], b[5]], u: [0, 0, -1], v: [0, 1, 0], W: b[5] - b[2], H: b[4] - b[1] }; },
    "-x": function (b) { return { o: [b[0], b[1], b[2]], u: [0, 0, 1], v: [0, 1, 0], W: b[5] - b[2], H: b[4] - b[1] }; },
    "+z": function (b) { return { o: [b[0], b[1], b[5]], u: [1, 0, 0], v: [0, 1, 0], W: b[3] - b[0], H: b[4] - b[1] }; },
    "-z": function (b) { return { o: [b[3], b[1], b[2]], u: [-1, 0, 0], v: [0, 1, 0], W: b[3] - b[0], H: b[4] - b[1] }; },
    "+y": function (b) { return { o: [b[0], b[4], b[5]], u: [1, 0, 0], v: [0, 0, -1], W: b[3] - b[0], H: b[5] - b[2] }; },
    "-y": function (b) { return { o: [b[0], b[1], b[2]], u: [1, 0, 0], v: [0, 0, 1], W: b[3] - b[0], H: b[5] - b[2] }; },
  };
  const NORMALS = { "+x": [1, 0, 0], "-x": [-1, 0, 0], "+y": [0, 1, 0], "-y": [0, -1, 0], "+z": [0, 0, 1], "-z": [0, 0, -1] };
  const toWorld = function (F, uv) { return [0, 1, 2].map(function (i) { return F.o[i] + F.u[i] * uv[0] + F.v[i] * uv[1]; }); };
  const toLocal = function (F, p) {
    const d = [p[0] - F.o[0], p[1] - F.o[1], p[2] - F.o[2]];
    return [d[0] * F.u[0] + d[1] * F.u[1] + d[2] * F.u[2], d[0] * F.v[0] + d[1] * F.v[1] + d[2] * F.v[2]];
  };
  const mm = function (x) { return Math.round(x * 1000) / 1000; };
  // a camera that frames a box: from the south-east above, at a distance its size asks for
  const frameCam = function (b, fov) {
    const cx = (b[0] + b[3]) / 2, cy = (b[1] + b[4]) / 2, cz = (b[2] + b[5]) / 2;
    const rad = Math.max(0.6, Math.hypot(b[3] - b[0], b[4] - b[1], b[5] - b[2]) / 2);
    const dist = rad / Math.tan(((fov || 66) * deg) / 2) * 1.15, yaw = -38 * deg, pitch = -24 * deg;
    const B = basis({ yaw: yaw, pitch: pitch });
    return { x: cx - B.f[0] * dist, y: Math.max(cy - B.f[1] * dist, 0.4), z: cz - B.f[2] * dist, yaw: yaw, pitch: Math.atan2(cy - Math.max(cy - B.f[1] * dist, 0.4), Math.hypot(B.f[0] * dist, B.f[2] * dist)), fov: fov || 66 };
  };

  // ---------------------------------------------------------------- the thumbnailer
  // One more renderer on a small canvas, kept for the page's life: it draws the scene it is given from a camera and
  // the picture is copied out as a data URL. A thumbnail is the scene as drawn, from that camera, at that moment.
  function Thumbs(w, h) {
    this.w = w; this.h = h; this.canvas = document.createElement("canvas"); this.canvas.width = w; this.canvas.height = h;
    this.R = null; this.sha = ""; this.queue = []; this.busy = false; this.error = "";
  }
  Thumbs.prototype.scene = function (S, sha) {
    if (this.error) return false;
    try {
      if (!this.R) this.R = new root.VerdandiScene.Renderer(this.canvas, S, { rainDrops: 400 });
      else if (this.sha !== sha) this.R.load(S);
      this.sha = sha; return true;
    } catch (e) { this.error = String(e && e.message || e); return false; }
  };
  // draw from `cam` and return a data URL (JPEG: a thumbnail is a picture, not evidence; PREVIEW-0's stills ask for
  // "image/png", which the host reads)
  Thumbs.prototype.shot = function (cam, movers, targets, type) {
    if (!this.R) return "";
    if (this.R.setMovers) this.R.setMovers(movers || []);
    this.R.setTargets(targets || []);
    this.R.draw(cam, 0);
    return type === "image/png" ? this.canvas.toDataURL("image/png") : this.canvas.toDataURL("image/jpeg", 0.82);
  };
  // queue work (a function returning nothing), a few each frame, so that the page goes on drawing
  Thumbs.prototype.later = function (fn, first) {
    if (first) this.queue.unshift(fn); else this.queue.push(fn);
    if (this.busy) return;
    this.busy = true;
    const self = this;
    const run = function () {
      const t0 = performance.now();
      while (self.queue.length && performance.now() - t0 < 12) { try { self.queue.shift()(); } catch (e) { /* a thumbnail is not worth a stop */ } }
      if (self.queue.length) requestAnimationFrame(run); else self.busy = false;
    };
    requestAnimationFrame(run);
  };
  Thumbs.prototype.clear = function () { this.queue.length = 0; };

  // a material's swatch: a lit disc drawn in 2D from its base colour, roughness, metallic and emission (a key to the
  // material, not the renderer's picture of it)
  const swatch = function (m, size) {
    const c = document.createElement("canvas"); c.width = c.height = size || 40;
    const g = c.getContext("2d"), s = c.width, base = m.base || [128, 128, 128], em = m.emissive_strength > 0 ? m.emissive : [0, 0, 0];
    const mix = function (a, b, t) { return [0, 1, 2].map(function (i) { return Math.round(a[i] + (b[i] - a[i]) * t); }); };
    const hi = mix(base, m.metallic > 0.5 ? base.map(function (v) { return Math.min(255, v * 1.6 + 40); }) : [255, 255, 255], 0.75 - 0.6 * (m.roughness || 0.5));
    const lo = base.map(function (v) { return Math.round(v * 0.25); });
    const grad = g.createRadialGradient(s * 0.36, s * 0.32, s * 0.04, s * 0.5, s * 0.5, s * 0.5);
    grad.addColorStop(0, "rgb(" + hi + ")"); grad.addColorStop(0.45, "rgb(" + base + ")"); grad.addColorStop(1, "rgb(" + lo + ")");
    g.fillStyle = "#0b1220"; g.fillRect(0, 0, s, s);
    g.beginPath(); g.arc(s / 2, s / 2, s * 0.44, 0, Math.PI * 2); g.fillStyle = grad; g.fill();
    if (em[0] + em[1] + em[2] > 0) { g.globalCompositeOperation = "lighter"; g.fillStyle = "rgba(" + em + ",0.55)"; g.fill(); g.globalCompositeOperation = "source-over"; }
    return c;
  };

  root.StudioUI = { icon: icon, el: el, basis: basis, project: project, segment: segment, boxEdges: boxEdges, corners: corners, rayAt: rayAt,
                    enterBox: enterBox, FRAMES: FRAMES, NORMALS: NORMALS, toWorld: toWorld, toLocal: toLocal, mm: mm, frameCam: frameCam,
                    Thumbs: Thumbs, swatch: swatch, deg: deg };
})(typeof self !== "undefined" ? self : this);
