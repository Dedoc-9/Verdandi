// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/main.js — FPS-GRAYBOX-0's page: input, the fixed-tick loop, the HUD, and the self-test mode.
//
// Input is gathered from the browser and handed to the simulation one tick at a time; the renderer draws the state
// after the ticks of a frame. The timings shown are this page's own software timings: they stop at the browser's
// hand-off to the compositor and are not input-to-photon.

(function () {
  "use strict";
  const Sim = window.GrayboxSim, R = window.GrayboxRenderer;
  const q = new URLSearchParams(location.search);
  const name = q.get("map") || "tactical";
  const $ = function (id) { return document.getElementById(id); };

  function post(path, body) {
    return fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).catch(function () {});
  }

  function selftestMode(map) {
    document.body.classList.add("selftest");
    const t0 = performance.now();
    let results;
    try { results = Sim.selftest(map); } catch (e) { results = [{ name: "selftest", ok: false, detail: String(e && e.stack || e) }]; }
    // the renderer, built and drawn once from the canonical world: a scene that cannot be built is a failure here too
    try {
      const r = new R.Renderer($("view"), map, Sim);
      const world = new Sim.World(map), s = Sim.newState(world, "A");
      r.draw(s, {});
      const px = new Uint8Array(4); r.gl.readPixels(1, 1, 1, 1, r.gl.RGBA, r.gl.UNSIGNED_BYTE, px);
      results.push({ name: "render", ok: r.triangles > 0, detail: r.triangles + " triangles from the canonical world, one frame drawn" });
    } catch (e) { results.push({ name: "render", ok: false, detail: String(e) }); }
    const ok = results.every(function (r) { return r.ok; });
    const ms = Math.round(performance.now() - t0);
    $("results").textContent = results.map(function (r) { return (r.ok ? "PASS " : "FAIL ") + r.name + " — " + r.detail; }).join("\n")
      + "\n\n" + (ok ? "GRAYBOX SELFTEST PASSED" : "GRAYBOX SELFTEST FAILED") + "  " + results.filter(function (r) { return r.ok; }).length + " / " + results.length + "  (" + ms + " ms)";
    window.GRAYBOX_SELFTEST = { map: name, ok: ok, results: results, manifest: map.manifest };
    post("/selftest", window.GRAYBOX_SELFTEST);
  }

  function playMode(map) {
    const world = new Sim.World(map);
    const s = Sim.newState(world, "A");
    const canvas = $("view");
    let renderer;
    try { renderer = new R.Renderer(canvas, map, Sim); } catch (e) { $("overlay").textContent = "The scene could not be built: " + e; return; }
    window.GRAYBOX = { world: world, state: s, step: function (inp) { Sim.step(world, s, inp); } };   // for tests and the console
    const keys = {}, pending = { reset: false, side: null, jump: false };
    let mdx = 0, mdy = 0, fire = false, minimap = true;
    const evTimes = [];
    const SENS = 0.0022;
    const locked = function () { return document.pointerLockElement === canvas; };
    canvas.addEventListener("click", function () { if (!locked()) canvas.requestPointerLock(); });
    document.addEventListener("pointerlockchange", function () { $("overlay").style.display = locked() ? "none" : "flex"; });
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
      let first = true, ticks = 0;
      while (acc >= Sim.TICK) {
        const inp = {
          f: keys.KeyW || keys.ArrowUp, b: keys.KeyS || keys.ArrowDown, l: keys.KeyA || keys.ArrowLeft, r: keys.KeyD || keys.ArrowRight,
          jump: keys.Space || pending.jump, fire: fire, reset: pending.reset, side: pending.side,
          dyaw: first ? mdx * SENS : 0, dpitch: first ? -mdy * SENS : 0,
        };
        if (first) { mdx = 0; mdy = 0; const tn = performance.now(); while (evTimes.length) push(T.input, tn - evTimes.shift()); }
        pending.reset = false; pending.side = null; pending.jump = false;
        Sim.step(world, s, inp); first = false; acc -= Sim.TICK; ticks += 1;
        if (s.fx.lastShot) s.fx.lastShot.age += Sim.TICK;
      }
      const t1 = performance.now();
      renderer.draw(s, { moving: !!(keys.KeyW || keys.KeyA || keys.KeyS || keys.KeyD) });
      const t2 = performance.now();
      push(T.sim, t1 - t0); push(T.draw, t2 - t1);
      if (minimap) drawMinimap();
      mm.style.display = minimap ? "block" : "none";
      $("hit").style.opacity = s.fx.hitMarker > 0 ? 1 : 0;
      const up = s.targets.filter(function (t) { return t.up; }).length;
      $("hud").textContent = [
        "VERÐANDI · FPS-GRAYBOX-0 · " + W.name + "   cell " + Math.floor(s.x / W.cell) + "," + Math.floor(s.z / W.cell) + "   feet " + s.feet.toFixed(2) + " m" + (s.onGround ? "" : "  (air)"),
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
    document.title = "Verðandi graybox — " + name;
    if (q.get("selftest")) selftestMode(map); else playMode(map);
  }).catch(function (e) {
    $("overlay").textContent = String(e);
    post("/selftest", { map: name, ok: false, results: [{ name: "load", ok: false, detail: String(e) }] });
  });
})();
