// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/sim.js — FPS-GRAYBOX-0's simulation: the player, collision, gravity, the weapon and the targets.
//
// It reads the collision world C (each cell's solid top, in metres) for movement and the canonical world's gameplay
// marks (spawns, targets, the objective, probes, routes) and nothing of the render mesh. Fixed tick, 120 per second;
// inputs are given per tick, so a recorded input sequence replays to the same states on the same build. The renderer
// reads the state and writes none of it. No DOM here: the same file runs in the page and under node.

(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.GrayboxSim = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const TICK = 1 / 120;
  const P = {
    radius: 0.35, eye: 1.62, step: 0.55, speed: 6.0, gravity: 20.0, jump: 7.0,
    fireCooldown: 0.12, targetRadius: 0.4, targetHeight: 1.9, targetDown: 2.5, range: 200,
  };

  // ---------------------------------------------------------------- the world
  function World(map) {
    const C = map.collision, W = map.canonical;
    if (C.w !== W.w || C.h !== W.h || C.tops.length !== C.w * C.h) throw new Error("the collision world is not the canonical world's size");
    this.w = C.w; this.h = C.h; this.cell = C.cell; this.tops = C.tops; this.wall = W.wall;
    this.spawns = W.spawns; this.objective = W.objective; this.targetDefs = W.targets;
    this.probes = W.probes; this.routes = W.routes;
  }
  World.prototype.top = function (i, j) {
    if (i < 0 || j < 0 || i >= this.w || j >= this.h) return Infinity;
    return this.tops[j * this.w + i];
  };

  // the cells a circle of radius r at (x, z) overlaps, strictly
  function touching(world, x, z, r, fn) {
    const c = world.cell;
    const i0 = Math.floor((x - r) / c), i1 = Math.floor((x + r) / c);
    const j0 = Math.floor((z - r) / c), j1 = Math.floor((z + r) / c);
    for (let j = j0; j <= j1; j++) {
      for (let i = i0; i <= i1; i++) {
        const px = Math.max(i * c, Math.min(x, (i + 1) * c)), pz = Math.max(j * c, Math.min(z, (j + 1) * c));
        const dx = x - px, dz = z - pz;
        if (dx * dx + dz * dz < r * r) fn(i, j);
      }
    }
  }

  function blocked(world, s, x, z, feet) {
    let b = false;
    touching(world, x, z, P.radius, function (i, j) { if (world.top(i, j) > feet + P.step) b = true; });
    if (b) return true;
    for (const t of s.targets) {
      if (!t.up) continue;
      const dx = x - t.x, dz = z - t.z, rr = P.radius + P.targetRadius;
      if (dx * dx + dz * dz < rr * rr && feet < t.y + P.targetHeight) return true;
    }
    return false;
  }

  function groundAt(world, x, z) {
    let g = 0;
    touching(world, x, z, P.radius, function (i, j) { const t = world.top(i, j); if (t > g) g = t; });
    return g;
  }

  // ---------------------------------------------------------------- the state
  function newState(world, side) {
    const s = {
      tick: 0, side: side || "A", x: 0, z: 0, feet: 0, vy: 0, yaw: 0, pitch: 0, onGround: true,
      cooldown: 0, score: 0, shots: 0, onObjective: false,
      targets: world.targetDefs.map(function (t) {
        const c = world.cell;
        return { id: t.id, x: (t.x + 0.5) * c, z: (t.z + 0.5) * c, y: world.top(t.x, t.z), up: true, downFor: 0 };
      }),
      fx: { hitMarker: 0, flash: {}, lastShot: null },   // feedback for the view: not part of the authoritative state
    };
    spawn(world, s, s.side);
    return s;
  }

  function spawn(world, s, side) {
    const sp = world.spawns[side];
    const c = world.cell;
    s.side = side; s.x = (sp.x + 0.5) * c; s.z = (sp.z + 0.5) * c;
    s.feet = groundAt(world, s.x, s.z); s.vy = 0; s.onGround = true;
    s.yaw = sp.yaw * Math.PI / 180; s.pitch = 0;
  }

  function wrap(a) { const t = 2 * Math.PI; return ((a % t) + t) % t; }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

  // ---------------------------------------------------------------- one tick
  // inp: {f, b, l, r, jump, fire, reset, side, dyaw, dpitch}; every field optional
  function step(world, s, inp) {
    inp = inp || {};
    s.tick += 1;
    if (inp.side) spawn(world, s, inp.side);
    else if (inp.reset) spawn(world, s, s.side);
    s.yaw = wrap(s.yaw + (inp.dyaw || 0));
    s.pitch = clamp(s.pitch + (inp.dpitch || 0), -1.45, 1.45);
    // walking: forward is -z at yaw 0 and +x at yaw 90 degrees; right is +x at yaw 0
    const fwd = (inp.f ? 1 : 0) - (inp.b ? 1 : 0), side = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
    const sy = Math.sin(s.yaw), cy = Math.cos(s.yaw);
    let mx = fwd * sy + side * cy, mz = -fwd * cy + side * sy;
    const len = Math.hypot(mx, mz);
    if (len > 0) {
      mx = mx / len * P.speed * TICK; mz = mz / len * P.speed * TICK;
      moveAxis(world, s, mx, 0);
      moveAxis(world, s, 0, mz);
    }
    // gravity, the jump, the ground
    const wasOnGround = s.onGround;
    if (inp.jump && s.onGround) { s.vy = P.jump; s.onGround = false; }
    s.vy -= P.gravity * TICK;
    s.feet += s.vy * TICK;
    const g = groundAt(world, s.x, s.z);
    if (s.feet <= g || (wasOnGround && s.vy <= 0 && s.feet - g <= P.step)) {
      s.feet = g; s.vy = 0; s.onGround = true;
    } else {
      s.onGround = false;
    }
    // the weapon and the targets
    s.cooldown = Math.max(0, s.cooldown - TICK);
    if (inp.fire && s.cooldown === 0) { s.cooldown = P.fireCooldown; fire(world, s); }
    for (const t of s.targets) {
      if (!t.up) { t.downFor -= TICK; if (t.downFor <= 1e-9) { t.up = true; t.downFor = 0; } }
    }
    s.onObjective = inObjective(world, s);
    s.fx.hitMarker = Math.max(0, s.fx.hitMarker - TICK);
    for (const k in s.fx.flash) s.fx.flash[k] = Math.max(0, s.fx.flash[k] - TICK);
  }

  // move along one axis; when blocked, close the gap by halving
  function moveAxis(world, s, dx, dz) {
    if (!blocked(world, s, s.x + dx, s.z + dz, s.feet)) { s.x += dx; s.z += dz; return; }
    for (let k = 0; k < 6; k++) {
      dx /= 2; dz /= 2;
      if (!blocked(world, s, s.x + dx, s.z + dz, s.feet)) { s.x += dx; s.z += dz; }
    }
  }

  function inObjective(world, s) {
    const o = world.objective;
    if (!o) return false;
    const i = Math.floor(s.x / world.cell), j = Math.floor(s.z / world.cell);
    return i >= o.rect[0] && i <= o.rect[2] && j >= o.rect[1] && j <= o.rect[3];
  }

  // ---------------------------------------------------------------- rays
  // The first solid the ray meets: a 2D walk of the cells it crosses in x-z; in each cell the column [0, top] is solid.
  function rayWorld(world, ox, oy, oz, dx, dy, dz, maxT) {
    const c = world.cell;
    let i = Math.floor(ox / c), j = Math.floor(oz / c);
    const si = dx > 0 ? 1 : -1, sj = dz > 0 ? 1 : -1;
    const tdx = dx !== 0 ? Math.abs(c / dx) : Infinity, tdz = dz !== 0 ? Math.abs(c / dz) : Infinity;
    let tmx = dx !== 0 ? (dx > 0 ? (i + 1) * c - ox : ox - i * c) / Math.abs(dx) : Infinity;
    let tmz = dz !== 0 ? (dz > 0 ? (j + 1) * c - oz : oz - j * c) / Math.abs(dz) : Infinity;
    let t0 = 0;
    for (let guard = 0; guard < 10000 && t0 < maxT; guard++) {
      const t1 = Math.min(tmx, tmz, maxT);
      const top = world.top(i, j);
      if (top === Infinity) return { t: t0, i: i, j: j, what: "edge" };
      const y0 = oy + dy * t0, y1 = oy + dy * t1;
      if (y0 <= top) return { t: t0, i: i, j: j, what: "side" };
      if (y1 <= top) return { t: (top - oy) / dy, i: i, j: j, what: "top" };
      if (tmx < tmz) { i += si; t0 = tmx; tmx += tdx; } else { j += sj; t0 = tmz; tmz += tdz; }
    }
    return { t: maxT, i: i, j: j, what: "range" };
  }

  // a ray against an upright box; the entry distance, or Infinity
  function rayBox(ox, oy, oz, dx, dy, dz, x0, y0, z0, x1, y1, z1) {
    let tn = -Infinity, tf = Infinity;
    const o = [ox, oy, oz], d = [dx, dy, dz], lo = [x0, y0, z0], hi = [x1, y1, z1];
    for (let a = 0; a < 3; a++) {
      if (d[a] === 0) { if (o[a] < lo[a] || o[a] > hi[a]) return Infinity; continue; }
      let ta = (lo[a] - o[a]) / d[a], tb = (hi[a] - o[a]) / d[a];
      if (ta > tb) { const q = ta; ta = tb; tb = q; }
      if (ta > tn) tn = ta;
      if (tb < tf) tf = tb;
      if (tn > tf) return Infinity;
    }
    return tf < 0 ? Infinity : Math.max(tn, 0);
  }

  function aim(s) {
    const cp = Math.cos(s.pitch);
    return [cp * Math.sin(s.yaw), Math.sin(s.pitch), -cp * Math.cos(s.yaw)];
  }

  function fire(world, s) {
    s.shots += 1;
    const d = aim(s), ox = s.x, oy = s.feet + P.eye, oz = s.z;
    const wall = rayWorld(world, ox, oy, oz, d[0], d[1], d[2], P.range);
    let best = null, bt = wall.t;
    for (const t of s.targets) {
      if (!t.up) continue;
      const r = P.targetRadius;
      const tt = rayBox(ox, oy, oz, d[0], d[1], d[2], t.x - r, t.y, t.z - r, t.x + r, t.y + P.targetHeight, t.z + r);
      if (tt < bt) { bt = tt; best = t; }
    }
    if (best) {
      best.up = false; best.downFor = P.targetDown; s.score += 1;
      s.fx.hitMarker = 0.2; s.fx.flash[best.id] = 0.25;
    }
    s.fx.lastShot = { o: [ox, oy, oz], h: [ox + d[0] * bt, oy + d[1] * bt, oz + d[2] * bt], hit: best ? best.id : null, age: 0 };
    return best ? best.id : null;
  }

  // ---------------------------------------------------------------- the authoritative state's hash
  function hash(s) {
    const nums = [s.tick, s.x, s.z, s.feet, s.vy, s.yaw, s.pitch, s.onGround ? 1 : 0, s.cooldown, s.score, s.shots, s.onObjective ? 1 : 0];
    for (const t of s.targets) nums.push(t.up ? 1 : 0, t.downFor);
    const f = new Float64Array(nums), b = new Uint8Array(f.buffer);
    let h = 0x811c9dc5;
    for (let k = 0; k < b.length; k++) { h ^= b[k]; h = Math.imul(h, 0x01000193) >>> 0; }
    return ("00000000" + h.toString(16)).slice(-8) + s.side;
  }

  // ---------------------------------------------------------------- the runtime's conformance checks
  // Run against the runtime's own collision and movement, not a copy of them: probes, spawns, routes walked by a bot,
  // gravity, mounting cover, the weapon, occlusion, reset, and replay of recorded inputs, every tick hashed.
  function walkGraph(world) {
    const standing = new Set(world.targetDefs.map(function (t) { return t.z * world.w + t.x; }));
    const ok = function (i, j) { return world.top(i, j) < world.wall && !standing.has(j * world.w + i); };
    return function (a, b) {   // a breadth-first path of cells from a to b, each step up at most the step height
      const key = function (p) { return p[1] * world.w + p[0]; };
      const prev = new Map([[key(a), null]]), q = [a];
      while (q.length) {
        const p = q.shift();
        if (p[0] === b[0] && p[1] === b[1]) break;
        for (const d of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const n = [p[0] + d[0], p[1] + d[1]];
          if (!ok(n[0], n[1]) || prev.has(key(n))) continue;
          if (world.top(n[0], n[1]) - world.top(p[0], p[1]) > P.step) continue;
          prev.set(key(n), p); q.push(n);
        }
      }
      if (!prev.has(key(b))) return null;
      const path = [];
      for (let p = b; p; p = prev.get(key(p))) path.unshift(p);
      return path;
    };
  }

  // a bot that walks a path of cell centres through the real movement; returns its inputs and the outcome
  function walk(world, s, path, limitTicks) {
    const c = world.cell, inputs = [];
    let k = 1, best = Infinity, still = 0;
    for (let n = 0; n < limitTicks; n++) {
      if (k >= path.length) return { ok: true, inputs: inputs, ticks: n };
      const tx = (path[k][0] + 0.5) * c, tz = (path[k][1] + 0.5) * c;
      const dx = tx - s.x, dz = tz - s.z, dist = Math.hypot(dx, dz);
      if (dist < 0.3) { k += 1; best = Infinity; still = 0; continue; }
      const want = Math.atan2(dx, -dz);
      let dyaw = wrap(want - s.yaw); if (dyaw > Math.PI) dyaw -= 2 * Math.PI;
      const inp = { f: true, dyaw: dyaw };
      inputs.push(inp); step(world, s, inp);
      if (dist < best - 1e-6) { best = dist; still = 0; } else if (++still > 180) return { ok: false, inputs: inputs, ticks: n, at: path[k] };
    }
    return { ok: false, inputs: inputs, ticks: limitTicks, at: path[k] };
  }

  function overlaps(world, x, z, i, j) {
    let hit = false;
    touching(world, x, z, P.radius, function (a, b) { if (a === i && b === j) hit = true; });
    return hit;
  }

  function selftest(map) {
    const out = [];
    const check = function (name, ok, detail) { out.push({ name: name, ok: !!ok, detail: detail || "" }); };
    let world;
    try { world = new World(map); } catch (e) { check("load", false, String(e)); return out; }
    check("load", world.tops.length === world.w * world.h, world.w + " x " + world.h + " cells of " + world.cell + " m");
    const c = world.cell;
    // spawns
    for (const side of ["A", "B"]) {
      const s = newState(world, side); step(world, s, {});
      const sp = world.spawns[side];
      check("spawn " + side, s.onGround && Math.abs(s.x - (sp.x + 0.5) * c) < 1e-9 && Math.abs(s.z - (sp.z + 0.5) * c) < 1e-9
            && s.feet === world.top(sp.x, sp.z) && !blocked(world, s, s.x, s.z, s.feet),
            "cell " + sp.x + "," + sp.z + ", feet " + s.feet + " m, on the ground");
    }
    // probes, through the runtime's movement
    for (const p of world.probes) {
      const s = newState(world, "A");
      if (p.expect === "open") {
        s.x = (p.x + 0.5) * c; s.z = (p.z + 0.5) * c; s.feet = groundAt(world, s.x, s.z);
        const free = !blocked(world, s, s.x, s.z, s.feet);
        let moved = false;
        for (const yaw of [0, Math.PI / 2, Math.PI, 3 * Math.PI / 2]) {
          const t = newState(world, "A"); t.x = s.x; t.z = s.z; t.feet = s.feet; t.yaw = yaw;
          for (let n = 0; n < 30; n++) step(world, t, { f: true });
          if (Math.hypot(t.x - s.x, t.z - s.z) > 1.0) moved = true;
        }
        check("probe open " + p.x + "," + p.z, free && moved, free ? (moved ? "the player stands in it and walks out of it" : "the player cannot walk out of it") : "the player cannot stand in it");
      } else {
        let tried = 0, held = true;
        for (const d of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const ni = p.x + d[0], nj = p.z + d[1];
          if (world.top(ni, nj) > P.step) continue;
          tried += 1;
          const s2 = newState(world, "A");
          s2.x = (ni + 0.5) * c; s2.z = (nj + 0.5) * c; s2.feet = groundAt(world, s2.x, s2.z); s2.yaw = Math.atan2(-d[0], d[1]);
          for (let n = 0; n < 180; n++) {
            step(world, s2, { f: true, jump: n % 30 === 0 });
            if (overlaps(world, s2.x, s2.z, p.x, p.z)) { held = false; break; }
          }
        }
        check("probe wall " + p.x + "," + p.z, held, tried ? "walked and jumped at from " + tried + " side(s), never entered" : "no open side to walk at it from; held by its top alone");
      }
    }
    // routes, walked by a bot through the runtime's movement; the first one's inputs kept for the replay
    const graph = walkGraph(world);
    let recorded = null;
    for (const name of Object.keys(world.routes).sort()) {
      const pts = world.routes[name].cells;
      let path = [pts[0]], broken = null;
      for (let k = 1; k < pts.length && !broken; k++) {
        const seg = graph(pts[k - 1], pts[k]);
        if (!seg) broken = pts[k]; else path = path.concat(seg.slice(1));
      }
      if (broken) { check("route " + name, false, "no path to " + broken); continue; }
      const s = newState(world, "A");
      s.x = (pts[0][0] + 0.5) * c; s.z = (pts[0][1] + 0.5) * c; s.feet = groundAt(world, s.x, s.z);
      const r = walk(world, s, path, path.length * 120 + 600);
      const end = pts[pts.length - 1];
      const there = Math.floor(s.x / c) === end[0] && Math.floor(s.z / c) === end[1];
      check("route " + name, r.ok && there, r.ok ? path.length + " cells walked in " + (r.ticks / 120).toFixed(1) + " s" : "stuck before " + r.at);
      if (r.ok && !recorded) recorded = { start: pts[0], inputs: r.inputs };
    }
    // gravity and the jump
    {
      const s = newState(world, "A"); const g0 = s.feet; let top = g0, landed = -1;
      step(world, s, { jump: true });
      for (let n = 1; n < 240; n++) { step(world, s, {}); if (s.feet > top) top = s.feet; if (s.feet < g0 - 1e-9) break; if (s.onGround && landed < 0) landed = n; }
      check("gravity and jump", top - g0 > 1.1 && top - g0 < 1.4 && landed > 0 && s.feet === g0,
            "rose " + (top - g0).toFixed(3) + " m, landed after " + (landed / 120).toFixed(2) + " s, never below the floor");
    }
    // cover: blocked on foot, mounted with a jump
    {
      let found = null;
      for (let j = 0; j < world.h && !found; j++) for (let i = 0; i < world.w && !found; i++) {
        const t = world.top(i, j);
        if (t > P.step && t <= 1.0 + 1e-9) for (const d of [[1, 0], [-1, 0], [0, 1], [0, -1]]) if (!found && world.top(i - d[0], j - d[1]) === 0) found = [i, j, d];
      }
      if (!found) check("cover", true, "not applicable: the map has no cover of 1 m beside the floor");
      else {
        const [ci, cj, d] = found, yaw = Math.atan2(d[0], -d[1]);
        const a = newState(world, "A"); a.x = (ci - d[0] + 0.5) * c; a.z = (cj - d[1] + 0.5) * c; a.feet = 0; a.yaw = yaw;
        let entered = false;
        for (let n = 0; n < 120; n++) { step(world, a, { f: true }); if (overlaps(world, a.x, a.z, ci, cj)) entered = true; }
        const b = newState(world, "A"); b.x = (ci - d[0] + 0.5) * c; b.z = (cj - d[1] + 0.5) * c; b.feet = 0; b.yaw = yaw;
        for (let n = 0; n < 240; n++) {
          const dist = Math.hypot((ci + 0.5) * c - b.x, (cj + 0.5) * c - b.z);
          step(world, b, { f: dist > 0.2, jump: n === 0 });
        }
        check("cover", !entered && a.feet === 0 && b.feet === world.top(ci, cj) && b.onGround,
              "cover at " + ci + "," + cj + " (" + world.top(ci, cj) + " m): on foot never entered; with a jump stood on it at " + b.feet + " m");
      }
    }
    // the weapon: a hit in the open, a miss behind a wall, the target back up
    {
      let shot = null, hidden = null;
      const s0 = newState(world, "A");
      for (const t of s0.targets) {
        for (let j = 0; j < world.h; j++) for (let i = 0; i < world.w; i++) {
          if (world.top(i, j) !== 0) continue;
          const x = (i + 0.5) * c, z = (j + 0.5) * c, dist = Math.hypot(t.x - x, t.z - z);
          if (dist < 4 || dist > 30) continue;
          const oy = P.eye, ty = t.y + 1.2, dx = t.x - x, dz = t.z - z, dy = ty - oy, L = Math.hypot(dx, dy, dz);
          const w = rayWorld(world, x, oy, z, dx / L, dy / L, dz / L, P.range);
          if (!shot && w.t > L) shot = { t: t, x: x, z: z };
          if (!hidden && w.t < L - 1 && w.what === "side") hidden = { t: t, x: x, z: z };
        }
        if (shot && hidden) break;
      }
      const fireAt = function (spot) {
        const s = newState(world, "A");
        s.x = spot.x; s.z = spot.z; s.feet = 0;
        const tgt = s.targets.find(function (q) { return q.id === spot.t.id; });
        const dx = tgt.x - s.x, dz = tgt.z - s.z, dy = tgt.y + 1.2 - (s.feet + P.eye);
        s.yaw = wrap(Math.atan2(dx, -dz)); s.pitch = Math.atan2(dy, Math.hypot(dx, dz));
        step(world, s, { fire: true });
        return { s: s, tgt: tgt };
      };
      if (!shot) check("weapon hit", false, "no open line to any target");
      else {
        const r = fireAt(shot);
        const down = !r.tgt.up && r.s.score === 1;
        for (let n = 0; n < Math.ceil(P.targetDown / TICK) + 2; n++) step(world, r.s, {});
        check("weapon hit", down && r.tgt.up, "target " + r.tgt.id + " hit from " + (Math.hypot(r.tgt.x - shot.x, r.tgt.z - shot.z)).toFixed(1) + " m, down, and up again after " + P.targetDown + " s");
      }
      if (!hidden) check("weapon occlusion", false, "no target behind a wall to try");
      else {
        const r = fireAt(hidden);
        check("weapon occlusion", r.tgt.up && r.s.score === 0, "target " + r.tgt.id + " behind a wall: the shot stopped at the wall");
      }
    }
    // reset
    {
      const s = newState(world, "A"); const h0 = [s.x, s.z, s.feet, s.yaw];
      for (let n = 0; n < 60; n++) step(world, s, { f: true, r: true, dyaw: 0.01 });
      step(world, s, { reset: true });
      check("reset", s.x === h0[0] && s.z === h0[1] && s.feet === h0[2] && s.yaw === h0[3], "back at spawn A");
    }
    // replay: the recorded inputs from the same start reach the same state at every tick
    if (!recorded) check("replay", false, "no route was walked to record");
    else {
      const run = function () {
        const s = newState(world, "A");
        s.x = (recorded.start[0] + 0.5) * c; s.z = (recorded.start[1] + 0.5) * c; s.feet = groundAt(world, s.x, s.z);
        const hs = [];
        for (const inp of recorded.inputs) { step(world, s, inp); hs.push(hash(s)); }
        return hs;
      };
      const h1 = run(), h2 = run();
      let same = h1.length === h2.length;
      for (let k = 0; same && k < h1.length; k++) if (h1[k] !== h2[k]) same = false;
      check("replay", same && h1.length > 0, h1.length + " ticks, every tick's state hash the same in both runs (last " + h1[h1.length - 1] + ")");
    }
    return out;
  }

  return { TICK: TICK, P: P, World: World, newState: newState, step: step, spawn: spawn, fire: fire, aim: aim,
           rayWorld: rayWorld, blocked: blocked, groundAt: groundAt, hash: hash, selftest: selftest };
});
