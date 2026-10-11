// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// art/web/play.js — the native plaza: the graybox's simulation (sim.js, unchanged) and the art scene's renderer
// (scene_render.js), in one page served by art/play.py.
//
// The simulation moves the player against C, the collision world of the converted map, and nothing else; the
// renderer draws the dressed scene from where the player's eye is and writes no state. Input reaches the simulation
// only as a tick's input record. Two modes: play (the default), and the registered views (keys 1-9 jump to them; Tab
// goes back to play), which move a camera and leave the game where it was.
//
// For stills and walk-throughs: ?view=NAME opens at a view and renders it; ?cam=x,y,z,yaw,pitch (metres, degrees);
// window.PLAY.walkTo(tick) puts the player where the self-test's recorded walk is at that tick and renders it.

(function () {
  "use strict";
  const Sim = window.GrayboxSim, q = new URLSearchParams(location.search), $ = function (id) { return document.getElementById(id); };
  const brief = q.get("brief") || document.body.getAttribute("data-brief");
  const deg = Math.PI / 180;

  Promise.all([fetch("/scene/" + brief + ".json").then(function (r) { if (!r.ok) throw new Error("no scene " + brief); return r.json(); })]).then(function (got) {
    const S = got[0];
    return fetch("/map/" + S.map + ".json").then(function (r) { if (!r.ok) throw new Error("no map " + S.map); return r.json(); }).then(function (map) { start(S, map); });
  }).catch(function (e) { $("overlay").textContent = String(e && e.message || e); $("overlay").style.display = "flex"; });

  function start(S, map) {
    const world = new Sim.World(map), s = Sim.newState(world, "A"), canvas = $("view");
    let R;
    try { R = new window.VerdandiScene.Renderer(canvas, S); } catch (e) { $("overlay").textContent = "The scene could not be drawn: " + (e && e.message || e); return; }
    document.title = (S.title || brief) + " — Verðandi";
    const views = Object.keys(S.views).sort();
    let mode = "play", vcam = null, label = "play";
    const P = Sim.P;
    const targets = function (st) {
      return st.targets.map(function (t) {
        return { up: t.up, box: [t.x - P.targetRadius, t.y + (t.up ? 0 : -P.targetHeight + 0.1), t.z - P.targetRadius, t.x + P.targetRadius, t.y + (t.up ? P.targetHeight : 0.1), t.z + P.targetRadius] };
      });
    };
    const eyeOf = function (st) { return { x: st.x, y: st.feet + P.eye, z: st.z, yaw: st.yaw, pitch: st.pitch }; };
    const fit = function () {
      const w = parseInt(q.get("w") || "0", 10) || Math.round(canvas.clientWidth * Math.min(window.devicePixelRatio || 1, 1.5));
      const h = parseInt(q.get("h") || "0", 10) || Math.round(canvas.clientHeight * Math.min(window.devicePixelRatio || 1, 1.5));
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    };
    const render = function (cam, time, st) { fit(); R.setTargets(targets(st)); R.draw(cam, time); };
    const goView = function (name) {
      const v = S.views[name]; if (!v) return;
      mode = "view"; label = "view " + name; vcam = { x: v.x, y: v.y, z: v.z, yaw: v.yaw * deg, pitch: v.pitch * deg };
    };
    // the hooks a still or a walk-through uses
    let walk = null;
    window.PLAY = {
      renderer: R, scene: S, state: s, world: world,
      view: function (name, time) { goView(name); render(vcam, time || 0, s); },
      cam: function (x, y, z, yaw, pitch, time) { mode = "view"; vcam = { x: x, y: y, z: z, yaw: yaw * deg, pitch: pitch * deg }; render(vcam, time || 0, s); },
      walkTo: function (tick) {
        if (!walk) walk = Sim.record(map)[0];
        const st = Sim.restore(walk.start);
        for (let n = 0; n < Math.min(tick, walk.inputs.length); n++) Sim.step(world, st, walk.inputs[n]);
        render(eyeOf(st), tick / 120, st);
        return { ticks: walk.inputs.length, x: st.x, z: st.z };
      },
    };
    if (q.get("view") || q.get("cam") || q.get("still")) {
      document.body.classList.add("still");
      if (q.get("view")) window.PLAY.view(q.get("view"), parseFloat(q.get("t") || "0"));
      else if (q.get("cam")) { const c = q.get("cam").split(",").map(Number); window.PLAY.cam(c[0], c[1], c[2], c[3], c[4], parseFloat(q.get("t") || "0")); }
      window.PLAY_READY = true;
      return;
    }
    // play: the fixed tick, as the graybox runs it
    const keys = {}, pending = { reset: false, jump: false };
    let mdx = 0, mdy = 0, fire = false, acc = 0, last = performance.now(), t0 = last;
    const SENS = 0.0022;
    const locked = function () { return document.pointerLockElement === canvas; };
    const overlay = $("overlay");
    const lock = function () { if (!locked()) { try { const p = canvas.requestPointerLock(); if (p && p.catch) p.catch(function () {}); } catch (e) { /* shown below */ } } };
    overlay.addEventListener("click", lock); canvas.addEventListener("click", lock);
    document.addEventListener("pointerlockchange", function () { overlay.style.display = locked() || mode === "view" ? "none" : "flex"; });
    document.addEventListener("mousemove", function (e) {
      if (!locked()) return;
      if (mode === "view") { vcam.yaw += e.movementX * SENS; vcam.pitch = Math.max(-1.45, Math.min(1.45, vcam.pitch - e.movementY * SENS)); }
      else { mdx += e.movementX; mdy += e.movementY; }
    });
    document.addEventListener("mousedown", function (e) { if (locked() && e.button === 0 && mode === "play") fire = true; });
    document.addEventListener("mouseup", function (e) { if (e.button === 0) fire = false; });
    document.addEventListener("keydown", function (e) {
      keys[e.code] = true;
      const n = parseInt(e.key, 10);
      if (n >= 1 && n <= views.length) { goView(views[n - 1]); overlay.style.display = "none"; }
      if (e.code === "Tab") { mode = "play"; label = "play"; e.preventDefault(); }
      if (e.code === "KeyR") pending.reset = true;
      if (e.code === "Space") { pending.jump = true; e.preventDefault(); }
    });
    document.addEventListener("keyup", function (e) { keys[e.code] = false; });
    window.addEventListener("blur", function () { for (const k in keys) keys[k] = false; fire = false; });
    function frame(now) {
      const dt = Math.min(0.25, (now - last) / 1000); last = now;
      if (mode === "play") {
        acc += dt;
        let first = true;
        while (acc >= Sim.TICK) {
          Sim.step(world, s, { f: keys.KeyW || keys.ArrowUp, b: keys.KeyS || keys.ArrowDown, l: keys.KeyA || keys.ArrowLeft, r: keys.KeyD || keys.ArrowRight,
                               jump: keys.Space || pending.jump, fire: fire, reset: pending.reset, dyaw: first ? mdx * SENS : 0, dpitch: first ? -mdy * SENS : 0 });
          if (first) { mdx = 0; mdy = 0; }
          pending.reset = false; pending.jump = false; first = false; acc -= Sim.TICK;
        }
      }
      render(mode === "play" ? eyeOf(s) : vcam, (now - t0) / 1000, s);
      $("hud").textContent = (S.title || brief) + "  ·  " + label + "  ·  cell " + Math.floor(s.x / S.grid.cell) + "," + Math.floor(s.z / S.grid.cell)
        + "  ·  hits " + s.score + "\n" + views.map(function (v, i) { return (i + 1) + " " + v; }).join("  ") + "  ·  Tab play  ·  WASD, mouse, Space, R"
        + "\nmovement and collision: the graybox's simulation against C  ·  the look: scene " + (document.body.getAttribute("data-sha") || "").slice(0, 12);
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
})();
