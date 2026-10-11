// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/main.js — FPS-GRAYBOX-0's page: input, the fixed-tick loop, the HUD, the self-test and the bench.
//
// Input is gathered from the browser and handed to the simulation one tick at a time; the renderer draws the state
// after the ticks of a frame. The timings shown are this page's own software timings: they stop at the browser's
// hand-off to the compositor and are not input-to-photon. Two renderers draw the same state: render.js (FPS-VISUAL-0,
// the default) and render_flat.js (the graybox as first built, `?renderer=flat`).

(function () {
  "use strict";
  const Sim = window.GrayboxSim;
  const RENDERERS = { lit: window.GrayboxRenderer, flat: window.GrayboxRendererFlat };
  const q = new URLSearchParams(location.search);
  const name = q.get("map") || "tactical";
  const kind = q.get("renderer") === "flat" ? "flat" : "lit", R = RENDERERS[kind];
  const $ = function (id) { return document.getElementById(id); };

  function post(path, body) {
    return fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).catch(function () {});
  }

  function selftestMode(map, table) {
    document.body.classList.add("selftest");
    const t0 = performance.now(), ctx = { inputCases: table }, measurements = [];
    let results;
    try { results = Sim.selftest(map, ctx); } catch (e) { results = [{ name: "selftest", ok: false, detail: String(e && e.stack || e) }]; }
    for (const m of ctx.measurements || []) measurements.push(m);
    renderChecks(map, results);
    $("results").textContent = "running the self-test in a second realm…";
    realmChecks(map, ctx, results, measurements).catch(function (e) {
      results.push({ name: "resume-realm", ok: false, detail: String(e && e.stack || e) });
    }).then(function () {
      const ok = results.every(function (r) { return r.ok; });
      const ms = Math.round(performance.now() - t0);
      $("results").textContent = results.map(function (r) { return (r.ok ? "PASS " : "FAIL ") + r.name + " — " + r.detail; }).join("\n")
        + (measurements.length ? "\n\n" + measurements.map(function (m) { return "MEASURED " + m.name + " — " + m.detail; }).join("\n") : "")
        + "\n\n" + (ok ? "GRAYBOX SELFTEST PASSED" : "GRAYBOX SELFTEST FAILED") + "  " + results.filter(function (r) { return r.ok; }).length + " / " + results.length + "  (" + ms + " ms)";
      window.GRAYBOX_SELFTEST = { map: name, ok: ok, results: results, measurements: measurements, manifest: map.manifest };
      post("/selftest", window.GRAYBOX_SELFTEST);
    });
  }

  // ---------------------------------------------------------------- a second realm
  // The simulation again, in a worker: a JavaScript realm with its own globals, its own Math and its own copy of
  // sim.js. resume-realm resumes the walk there from a snapshot and requires every later tick's state to be this page's
  // bit for bit; a snapshot with one bit changed must come apart at once, so the comparison is shown able to fail.
  // Then the measurements: each run again, under rules 0, in counterfactual engines whose Math.sin, Math.cos or
  // Math.hypot (the ones a rules-0 tick calls whose results the language does not fix to the last bit) is off by its
  // last bit at every call. They show, in this browser, how far a last-bit difference between two engines' Math would
  // carry a run under the old rules. Then rules 1 in an engine whose sin, cos, hypot, atan2 and sqrt are all off: the
  // same state at every tick, since rules 1 call none of them. They are measurements, not checks: nothing passes or
  // fails on them (the self-test's math-fence is the check), and a real engine differs on some inputs, not on all.
  function inWorker(msg) {
    return new Promise(function (resolve) {
      let w;
      try { w = new Worker("sim_worker.js"); } catch (e) { resolve({ error: "no worker: " + String(e && e.message || e) }); return; }
      const timer = setTimeout(function () { w.terminate(); resolve({ error: "the worker did not answer in 60 s" }); }, 60000);
      w.onmessage = function (ev) { clearTimeout(timer); w.terminate(); resolve(ev.data); };
      w.onerror = function (ev) { clearTimeout(timer); w.terminate(); if (ev.preventDefault) ev.preventDefault(); resolve({ error: "the worker failed: " + (ev.message || "an error") }); };
      w.postMessage(msg);
    });
  }
  function realmChecks(map, ctx, results, measurements) {
    const runs = ctx.runs || [];
    if (!runs.length) { results.push({ name: "resume-realm", ok: false, detail: "no run to resume" }); return Promise.resolve(); }
    const world = new Sim.World(map), c = map.collision.cell;
    const trails = runs.map(function (run) {
      const s = Sim.restore(run.start), trail = [];
      for (const inp of run.inputs) { Sim.step(world, s, inp); trail.push(Sim.snapshot(s)); }
      return trail;
    });
    const run = runs[0], trail = trails[0], k = Math.floor(run.inputs.length / 3), rest = run.inputs.slice(k + 1);
    const apart = function (snaps, tr, from) { for (let m = 0; m < snaps.length; m++) if (snaps[m] !== tr[from + m]) return m; return snaps.length === tr.length - from ? -1 : snaps.length; };
    const flipped = (function () { const t = Sim.restore(trail[k]); t.shots = Sim.nudge(t.shots); return Sim.snapshot(t); })();
    return inWorker({ map: map, snap: trail[k], inputs: rest }).then(function (a) {
      return inWorker({ map: map, snap: flipped, inputs: rest }).then(function (b) {
        if (a.error || b.error) { results.push({ name: "resume-realm", ok: false, detail: a.error || b.error }); return; }
        const pa = apart(a.snaps, trail, k + 1), pb = apart(b.snaps, trail, k + 1);
        results.push({ name: "resume-realm", ok: pa < 0 && pb === 0,
          detail: run.name + " resumed in a worker, a realm of its own, after tick " + (k + 1) + ": "
            + (pa < 0 ? "the same state as this page's at each of the " + rest.length + " later ticks" : "APART at tick " + (k + 2 + pa))
            + "; a snapshot with one bit changed " + (pb === 0 ? "apart at the first tick" : "NOT told apart") });
      });
    }).then(function () {
      const S0 = Sim.withRules(0), w0 = new S0.World(map);
      const trails0 = runs.map(function (run) {
        const s = S0.restore(run.start), trail = [];
        for (const inp of run.inputs) { S0.step(w0, s, inp); trail.push(S0.snapshot(s)); }
        return trail;
      });
      const sets = [[0, ["sin"]], [0, ["cos"]], [0, ["hypot"]], [0, ["sin", "cos", "hypot"]], [1, ["sin", "cos", "hypot", "atan2", "sqrt"]]];
      let chain = Promise.resolve();
      for (const [rules, set] of sets) chain = chain.then(function () {
        return Promise.all(runs.map(function (r) { return inWorker({ map: map, snap: r.start, inputs: r.inputs, offByOne: set, rules: rules }); })).then(function (outs) {
          const parts = outs.map(function (o, i) {
            if (o.error) return runs[i].name + ": " + o.error;
            const tr = (rules === 0 ? trails0 : trails)[i], first = apart(o.snaps, tr, 0);
            if (first < 0) return runs[i].name + ": the same state at every one of its " + tr.length + " ticks";
            let gap = 0, end = 0, changed = 0;
            for (let m = 0; m < tr.length; m++) {
              const x = Sim.restore(tr[m]), y = Sim.restore(o.snaps[m]);
              const g = Math.hypot(x.x - y.x, x.z - y.z, x.feet - y.feet);
              gap = Math.max(gap, g); end = g;
              if (Math.floor(x.x / c) !== Math.floor(y.x / c) || Math.floor(x.z / c) !== Math.floor(y.z / c) || x.onGround !== y.onGround
                  || x.score !== y.score || x.shots !== y.shots || x.targets.some(function (t, j) { return t.up !== y.targets[j].up; })) changed++;
            }
            return runs[i].name + ": the state apart from tick " + (first + 1) + " of " + tr.length + "; the player at most " + gap.toExponential(1)
              + " m from this page's, " + end.toExponential(1) + " m at the end; " + (changed ? changed + " ticks with a different cell, footing or hit" : "the same cell, footing and hits at every tick");
          });
          measurements.push({ name: "rules " + rules + ", counterfactual Math." + set.join(", Math."), detail: "off by its last bit at every call, in a worker: " + parts.join("; ") + " (this browser, this machine)" });
        });
      });
      return chain;
    });
  }

  // ---------------------------------------------------------------- the renderers, checked
  // Each renderer is built and drawn from the canonical world: a scene that cannot be built is a failure. Then three
  // properties of the owner's rule that the render world may decorate and may not decide: drawing writes nothing in
  // the state; every solid the lit renderer draws in the map is a column of the collision world, face by face; and
  // its decoration stays out of the volume where play happens.
  function canvasFor(id) {
    let c = document.getElementById(id);
    if (!c) { c = document.createElement("canvas"); c.id = id; c.className = "aux"; document.body.appendChild(c); }
    return c;
  }
  function renderChecks(map, results) {
    const world = new Sim.World(map);
    const built = {};
    for (const k of ["lit", "flat"]) {
      const label = k === "lit" ? "render" : "render-flat";
      try {
        const r = new RENDERERS[k].Renderer(k === "lit" ? $("view") : canvasFor("view-flat"), map, Sim);
        const s = Sim.newState(world, "A");
        r.draw(s, {});
        const px = new Uint8Array(4); r.gl.readPixels(1, 1, 1, 1, r.gl.RGBA, r.gl.UNSIGNED_BYTE, px);
        const err = r.gl.getError();
        built[k] = r;
        results.push({ name: label, ok: r.triangles > 0 && err === r.gl.NO_ERROR,
                       detail: r.triangles + " triangles from the canonical world, one frame drawn" + (err ? ", GL error " + err : "") });
      } catch (e) { results.push({ name: label, ok: false, detail: String(e && e.message || e) }); }
    }
    // drawing writes nothing in the state: the whole state, before and after frames at rest, mid-shot and mid-fall
    try {
      const s = Sim.newState(world, "A");
      Sim.step(world, s, { fire: true }); Sim.step(world, s, {});
      const before = JSON.stringify(s), h0 = Sim.hash(s);
      let frames = 0;
      for (const k in built) for (let n = 0; n < 3; n++) { built[k].draw(s, { look: [0.02, -0.01], moving: true }); frames++; }
      const ok = JSON.stringify(s) === before && Sim.hash(s) === h0;
      results.push({ name: "render-readonly", ok: ok && frames === 6, detail: frames + " frames by both renderers; the state " + (ok ? "unchanged, hash " + h0 : "CHANGED") });
    } catch (e) { results.push({ name: "render-readonly", ok: false, detail: String(e && e.message || e) }); }
    // the lit renderer's solids are the collision world's columns; its decoration is out of play
    try {
      const r = built.lit;
      if (!r) throw new Error("the lit renderer was not built");
      const C = map.collision, c = C.cell, w = C.w, h = C.h, tops = C.tops, f = Math.fround;
      const P = r.worldMesh.P, N = r.worldMesh.N, topFaces = new Int32Array(w * h), sideFaces = new Map();
      const bad = [];
      for (let v = 0; v < P.length; v += 9) {
        const nx = N[v], ny = N[v + 1], nz = N[v + 2];
        const ys = [P[v + 1], P[v + 4], P[v + 7]], cx = (P[v] + P[v + 3] + P[v + 6]) / 3, cz = (P[v + 2] + P[v + 5] + P[v + 8]) / 3;
        if (ny === 1 && nx === 0 && nz === 0) {
          const i = Math.floor(cx / c), j = Math.floor(cz / c);
          if (i < 0 || j < 0 || i >= w || j >= h || ys.some(function (y) { return y !== f(tops[j * w + i]); })) bad.push("top at " + cx.toFixed(2) + "," + cz.toFixed(2));
          else topFaces[j * w + i]++;
        } else if (ny === 0 && Math.abs(nx) + Math.abs(nz) === 1) {
          const i = Math.floor((cx - nx * 0.01) / c), j = Math.floor((cz - nz * 0.01) / c), a = i + nx, b = j + nz;
          const lo = Math.min.apply(null, ys), hi = Math.max.apply(null, ys);
          if (i < 0 || j < 0 || i >= w || j >= h || a < 0 || b < 0 || a >= w || b >= h
              || hi !== f(tops[j * w + i]) || lo !== f(tops[b * w + a]) || !(tops[j * w + i] > tops[b * w + a])) bad.push("side at " + cx.toFixed(2) + "," + cz.toFixed(2));
          else { const key = (j * w + i) * 4 + (nx < 0 ? 0 : nx > 0 ? 1 : nz < 0 ? 2 : 3); sideFaces.set(key, (sideFaces.get(key) || 0) + 1); }
        } else bad.push("a face of normal " + [nx, ny, nz].join(","));
      }
      let steps = 0;
      for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
        if (topFaces[j * w + i] !== 2) bad.push("cell " + i + "," + j + " has " + topFaces[j * w + i] / 2 + " tops");
        const D = [[-1, 0], [1, 0], [0, -1], [0, 1]];
        for (let d = 0; d < 4; d++) {
          const a = i + D[d][0], b = j + D[d][1];
          if (a < 0 || b < 0 || a >= w || b >= h) continue;
          const want = tops[j * w + i] > tops[b * w + a] ? 2 : 0, got = sideFaces.get((j * w + i) * 4 + d) || 0;
          if (want) steps++;
          if (got !== want) bad.push("cell " + i + "," + j + " side " + d + ": " + got / 2 + " faces, " + want / 2 + " wanted");
        }
      }
      // the play ceiling, by its own search: the highest top reachable from a spawn, rising at most a jump and a step
      const Pm = Sim.P, apex = Pm.jump * Pm.jump / (2 * Pm.gravity), seen = new Set(), stack = [];
      for (const sd in map.canonical.spawns) { const sp = map.canonical.spawns[sd]; seen.add(sp.z * w + sp.x); stack.push(sp.z * w + sp.x); }
      let reach = 0;
      while (stack.length) {
        const k = stack.pop(), i = k % w, j = (k - i) / w;
        reach = Math.max(reach, tops[k]);
        for (let b = j - 1; b <= j + 1; b++) for (let a = i - 1; a <= i + 1; a++) {
          if (a < 0 || b < 0 || a >= w || b >= h || seen.has(b * w + a) || tops[b * w + a] - tops[k] > apex + Pm.step) continue;
          seen.add(b * w + a); stack.push(b * w + a);
        }
      }
      const ceiling = reach + apex + Pm.eye;
      let beams = 0, outside = 0;
      for (const b of r.decor) {
        const out = b.max[0] <= 0 || b.min[0] >= w * c || b.max[2] <= 0 || b.min[2] >= h * c;
        if (out) outside++; else if (b.min[1] >= ceiling) beams++; else bad.push(b.kind + " inside the map below the play ceiling, at y " + b.min[1].toFixed(2));
      }
      const tb = r.targetBounds, tr = Pm.targetRadius;
      if (tb.min[0] < -tr || tb.max[0] > tr || tb.min[2] < -tr || tb.max[2] > tr || tb.min[1] < 0 || tb.max[1] > Pm.targetHeight) bad.push("the target drawn outside its hit box");
      results.push({ name: "render-conforms", ok: bad.length === 0,
        detail: bad.length ? bad.slice(0, 4).join("; ") + (bad.length > 4 ? " (and " + (bad.length - 4) + " more)" : "")
          : w * h + " tops and " + steps + " steps drawn at the collision world's heights, no other solid; " + beams + " beams above the play ceiling (" + ceiling.toFixed(3) + " m), "
            + outside + " skyline blocks outside the map; the target inside its hit box" });
    } catch (e) { results.push({ name: "render-conforms", ok: false, detail: String(e && e.message || e) }); }
  }

  // ---------------------------------------------------------------- the bench: both renderers, the same poses
  // Each pose is drawn by both renderers at the same size, alternating. A sample is the mean of a batch of draws, each
  // followed by a one-pixel readback, which waits for the frame's work: the browser's own time on this machine, not a
  // frame rate and not input-to-photon. A browser may round its clock (to 1 ms, in some): the batch divides that
  // rounding, and the clock's step as the page sees it is reported. A screenshot of every pose by each renderer goes
  // back with the timings.
  function benchPoses(world, map) {
    const W = map.canonical, c = W.cell, out = [];
    const at = function (label, x, z, yaw, pitch, fire) {
      const s = Sim.newState(world, "A");
      s.x = (x + 0.5) * c; s.z = (z + 0.5) * c; s.feet = 0; s.yaw = yaw; s.pitch = pitch || 0;
      Sim.step(world, s, {});
      if (fire) Sim.step(world, s, { fire: true });
      out.push({ label: label, s: s });
    };
    for (const side of Object.keys(W.spawns).sort()) { const sp = W.spawns[side]; at("spawn " + side, sp.x, sp.z, sp.yaw * Math.PI / 180, 0); }
    for (const rn of Object.keys(W.routes).sort()) {
      const p = W.routes[rn].cells, k = Math.floor(p.length / 2), a = p[k - 1], b = p[k];
      at("route " + rn, a[0], a[1], Math.atan2(b[0] - a[0], -(b[1] - a[1])), -0.05);
    }
    const sp = W.spawns.A;
    at("firing", sp.x, sp.z, sp.yaw * Math.PI / 180, 0.02, true);
    return out;
  }
  function benchMode(map) {
    document.body.classList.add("selftest");
    const world = new Sim.World(map), poses = benchPoses(world, map);
    const n = Math.max(3, Math.min(200, parseInt(q.get("samples") || "20", 10) || 20));
    const K = Math.max(1, Math.min(100, parseInt(q.get("batch") || "10", 10) || 10));
    let step = Infinity, seen = 0;
    for (let a = performance.now(), t0 = a; seen < 20 && a - t0 < 200;) { const b = performance.now(); if (b > a) { step = Math.min(step, b - a); seen++; a = b; } }
    const rs = {};
    for (const k of ["flat", "lit"]) rs[k] = new RENDERERS[k].Renderer(canvasFor("bench-" + k), map, Sim);
    const gl = rs.lit.gl, dbg = gl.getExtension("WEBGL_debug_renderer_info");
    const out = { map: name, samples: n, batch: K, clock: step, isolated: !!self.crossOriginIsolated, ua: navigator.userAgent,
                  gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER), poses: [], shots: {}, size: null,
                  note: "the mean of " + K + " draws, each followed by a one-pixel readback; this browser on this machine; not a frame rate, not input-to-photon" };
    const px = new Uint8Array(4);
    let p = 0;
    $("results").textContent = "bench: " + poses.length + " poses, " + n + " samples each, two renderers…";
    function next() {
      if (p >= poses.length) {
        out.size = [rs.lit.canvas.width, rs.lit.canvas.height];
        $("results").textContent = "bench done; the results went back to serve.py";
        window.GRAYBOX_BENCH = out;
        post("/bench", out);
        return;
      }
      const pose = poses[p++], row = { label: pose.label, ms: { flat: [], lit: [] } };
      for (const k of ["flat", "lit"]) for (let w = 0; w < 3; w++) { rs[k].draw(pose.s, {}); rs[k].gl.readPixels(0, 0, 1, 1, rs[k].gl.RGBA, rs[k].gl.UNSIGNED_BYTE, px); }
      for (let i = 0; i < n; i++) {
        const order = i % 2 ? ["flat", "lit"] : ["lit", "flat"];
        for (const k of order) {
          const r = rs[k], t0 = performance.now();
          for (let b = 0; b < K; b++) { r.draw(pose.s, {}); r.gl.readPixels(0, 0, 1, 1, r.gl.RGBA, r.gl.UNSIGNED_BYTE, px); }
          row.ms[k].push((performance.now() - t0) / K);
        }
      }
      for (const k of ["flat", "lit"]) { rs[k].draw(pose.s, {}); out.shots[k + "/" + pose.label.replace(/[^a-z0-9]+/gi, "-")] = rs[k].canvas.toDataURL("image/png"); }
      out.poses.push(row);
      $("results").textContent = "bench: pose " + p + " / " + poses.length + " (" + pose.label + ")";
      setTimeout(next, 0);
    }
    setTimeout(next, 0);
  }

  function playMode(map) {
    const world = new Sim.World(map);
    const s = Sim.newState(world, "A");
    const canvas = $("view");
    let renderer;
    try { renderer = new R.Renderer(canvas, map, Sim); } catch (e) { $("overlay").textContent = "The scene could not be built: " + e; return; }
    renderer.grid = !!q.get("grid");
    window.GRAYBOX = { world: world, state: s, step: function (inp) { return Sim.step(world, s, inp); } };   // for tests and the console: null, or the refusal
    const keys = {}, pending = { reset: false, side: null, jump: false }, refusals = {};
    let mdx = 0, mdy = 0, fire = false, minimap = true;
    const evTimes = [];
    const SENS = 0.0022;
    const locked = function () { return document.pointerLockElement === canvas; };
    // The overlay covers the view until the mouse is captured, so it is the overlay that takes the first click: both
    // ask for the lock. A refusal is shown, not swallowed (a browser may refuse a request made just after Esc).
    const overlay = $("overlay"), prompt = overlay.textContent;
    const refused = function (why) {
      if (!why && overlay.textContent.indexOf("The browser did not capture") === 0) return;   // keep a reason already shown
      overlay.textContent = "The browser did not capture the mouse" + (why ? ": " + why : "") + ".\nClick to try again.";
    };
    const lock = function () {
      if (locked()) return;
      let p;
      try { p = canvas.requestPointerLock(); } catch (e) { refused(String(e && e.message || e)); return; }
      if (p && typeof p.catch === "function") p.catch(function (e) { refused(String(e && e.message || e)); });
    };
    overlay.addEventListener("click", lock);
    canvas.addEventListener("click", lock);
    document.addEventListener("pointerlockchange", function () { overlay.style.display = locked() ? "none" : "flex"; if (locked()) overlay.textContent = prompt; });
    document.addEventListener("pointerlockerror", function () { refused(""); });
    document.addEventListener("mousemove", function (e) { if (locked()) { mdx += e.movementX; mdy += e.movementY; evTimes.push(e.timeStamp); } });
    document.addEventListener("mousedown", function (e) { if (locked() && e.button === 0) { fire = true; evTimes.push(e.timeStamp); } });
    document.addEventListener("mouseup", function (e) { if (e.button === 0) fire = false; });
    document.addEventListener("keydown", function (e) {
      keys[e.code] = true; evTimes.push(e.timeStamp);
      if (e.code === "KeyR") pending.reset = true;
      if (e.code === "Digit1") pending.side = "A";
      if (e.code === "Digit2") pending.side = "B";
      if (e.code === "Space") { pending.jump = true; e.preventDefault(); }
      if (e.code === "KeyM") minimap = !minimap;
      if (e.code === "KeyG") renderer.grid = !renderer.grid;
    });
    document.addEventListener("keyup", function (e) { keys[e.code] = false; });
    window.addEventListener("blur", function () { for (const k in keys) keys[k] = false; fire = false; });

    // rolling software timings, each its own boundary
    const T = { frame: [], sim: [], draw: [], input: [] };
    const push = function (a, v) { a.push(v); if (a.length > 240) a.shift(); };
    const pct = function (a, p) { if (!a.length) return 0; const b = a.slice().sort(function (x, y) { return x - y; }); return b[Math.min(b.length - 1, Math.floor(p * b.length))]; };
    let last = performance.now(), acc = 0;

    const mm = $("minimap"), mctx = mm.getContext("2d");
    const W = map.canonical;
    function drawMinimap() {
      const k = 4; mm.width = W.w * k; mm.height = W.h * k;
      for (let j = 0; j < W.h; j++) for (let i = 0; i < W.w; i++) {
        const cl = W.cells[j * W.w + i];
        mctx.fillStyle = cl[1] === "wall" ? "#2b2e33" : cl[1] === "cover" ? "#c8955a" : cl[1] === "raised" ? "#8a97a8" : "#6b6f75";
        mctx.fillRect(i * k, j * k, k, k);
      }
      if (W.objective) { const o = W.objective.rect; mctx.fillStyle = "rgba(240,200,60,0.55)"; mctx.fillRect(o[0] * k, o[1] * k, (o[2] - o[0] + 1) * k, (o[3] - o[1] + 1) * k); }
      for (const t of s.targets) { mctx.fillStyle = t.up ? "#e03030" : "#602020"; mctx.fillRect(t.x / W.cell * k - 2, t.z / W.cell * k - 2, 4, 4); }
      const px = s.x / W.cell * k, pz = s.z / W.cell * k;
      mctx.strokeStyle = "#fff"; mctx.lineWidth = 2; mctx.beginPath(); mctx.moveTo(px, pz);
      mctx.lineTo(px + Math.sin(s.yaw) * 12, pz - Math.cos(s.yaw) * 12); mctx.stroke();
      mctx.fillStyle = "#40c0ff"; mctx.beginPath(); mctx.arc(px, pz, 3, 0, 7); mctx.fill();
    }

    function frame(now) {
      const dt = Math.min(0.25, (now - last) / 1000);
      push(T.frame, now - last); last = now; acc += dt;
      const t0 = performance.now();
      let first = true, ticks = 0, look = [0, 0];
      while (acc >= Sim.TICK) {
        // a record the input contract admits: flags true or false, a side only when one was asked for (RULES-1.md)
        const inp = {
          f: !!(keys.KeyW || keys.ArrowUp), b: !!(keys.KeyS || keys.ArrowDown), l: !!(keys.KeyA || keys.ArrowLeft), r: !!(keys.KeyD || keys.ArrowRight),
          jump: !!(keys.Space || pending.jump), fire: !!fire, reset: !!pending.reset,
          dyaw: first ? mdx * SENS : 0, dpitch: first ? -mdy * SENS : 0,
        };
        if (pending.side) inp.side = pending.side;
        if (first) { look = [inp.dyaw, inp.dpitch]; mdx = 0; mdy = 0; const tn = performance.now(); while (evTimes.length) push(T.input, tn - evTimes.shift()); }
        pending.reset = false; pending.side = null; pending.jump = false;
        const refused = Sim.step(world, s, inp); first = false; acc -= Sim.TICK; ticks += 1;
        if (refused && !refusals[refused]) { refusals[refused] = true; console.warn("graybox: an input was refused (" + refused + "); the state is unchanged", inp); }
        if (s.fx.lastShot) s.fx.lastShot.age += Sim.TICK;
      }
      const t1 = performance.now();
      renderer.draw(s, { moving: !!(keys.KeyW || keys.KeyA || keys.KeyS || keys.KeyD), look: look });
      const t2 = performance.now();
      push(T.sim, t1 - t0); push(T.draw, t2 - t1);
      if (minimap) drawMinimap();
      mm.style.display = minimap ? "block" : "none";
      $("hit").style.opacity = s.fx.hitMarker > 0 ? 1 : 0;
      const up = s.targets.filter(function (t) { return t.up; }).length;
      $("hud").textContent = [
        "VERÐANDI · FPS-GRAYBOX-0 · " + W.name + " · renderer " + kind + (renderer.grid ? " + grid" : "") + "   cell " + Math.floor(s.x / W.cell) + "," + Math.floor(s.z / W.cell) + "   feet " + s.feet.toFixed(2) + " m" + (s.onGround ? "" : "  (air)"),
        "hits " + s.score + " / shots " + s.shots + "   targets up " + up + " / " + s.targets.length + (s.onObjective ? "   ON OBJECTIVE" : ""),
        "frame p50 " + pct(T.frame, 0.5).toFixed(1) + " p95 " + pct(T.frame, 0.95).toFixed(1) + " ms · sim " + pct(T.sim, 0.5).toFixed(2) + " · draw submit " + pct(T.draw, 0.5).toFixed(2)
          + " · input→tick p95 " + pct(T.input, 0.95).toFixed(1) + " ms   (this page's software timings; not input-to-photon)",
        "canonical " + map.manifest.canonical_sha256.slice(0, 12) + " · collision " + map.manifest.collision_sha256.slice(0, 12) + " · state " + Sim.hash(s),
      ].join("\n");
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  fetch("/map/" + encodeURIComponent(name) + ".json").then(function (r) {
    if (!r.ok) throw new Error("the map " + name + " could not be loaded: " + r.status);
    return r.json();
  }).then(function (map) {
    // the self-test also takes the input contract's table of cases (web/input_cases.json)
    if (!q.get("selftest")) return [map, null];
    return fetch("/input_cases.json").then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })
      .then(function (table) { return [map, table]; });
  }).then(function (got) {
    const map = got[0];
    document.title = "Verðandi graybox — " + name;
    if (q.get("selftest")) selftestMode(map, got[1]); else if (q.get("bench")) benchMode(map); else playMode(map);
  }).catch(function (e) {
    $("overlay").textContent = String(e);
    post(q.get("bench") ? "/bench" : "/selftest", { map: name, ok: false, error: String(e), results: [{ name: "load", ok: false, detail: String(e) }] });
  });
})();
