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
// Live: the page asks /live twice a second what art/play.py serves. When the source it shows has a new scene (an edit
// that passed the checks), the scene's bytes are fetched, held to the digest /live gave, and handed to the renderer in
// place: the game is not touched, since nothing the renderer does reaches it. When the new scene's map differs, the
// collision world is new, and so is the game: the simulation's own new state at the spawn, nothing carried into it.
// A refusal is shown and the scene before it stays. A new scene_render.js takes the canvas over from the old one (if
// it fails to start, the old one goes on drawing); a new play.js or sim.js is announced and loaded by reloading the
// page. [ and ] step through the sources play.py was given (the brief and each --intent).
//
// For stills and walk-throughs: ?view=NAME opens at a view and renders it; ?cam=x,y,z,yaw,pitch (metres, degrees);
// ?slot=K picks the source; window.PLAY.walkTo(tick) puts the player where the self-test's recorded walk is at that
// tick and renders it.

(function () {
  "use strict";
  const Sim = window.GrayboxSim, q = new URLSearchParams(location.search), $ = function (id) { return document.getElementById(id); };
  const brief = q.get("brief") || document.body.getAttribute("data-brief");
  const deg = Math.PI / 180;
  const get = function (url) {
    return fetch(url, { cache: "no-store" }).then(function (r) { if (!r.ok) throw new Error(url + ": " + r.status); return r.arrayBuffer(); });
  };
  const hex = function (buf) {
    if (!(window.crypto && crypto.subtle)) return Promise.resolve(null);
    return crypto.subtle.digest("SHA-256", buf).then(function (d) { return Array.from(new Uint8Array(d), function (b) { return b.toString(16).padStart(2, "0"); }).join(""); });
  };
  const json = function (buf) { return JSON.parse(new TextDecoder().decode(buf)); };
  // a source's scene and map, as /live describes them; the bytes must hash to the digests given
  const fetchSlot = function (k, served) {
    return get("/scene/" + brief + ".json?slot=" + k).then(function (sb) {
      return hex(sb).then(function (d) {
        if (d !== null && d !== served.sha) throw new Error("raced: the scene changed while it was fetched");
        return get("/map/" + served.map + ".json?slot=" + k).then(function (mb) {
          return hex(mb).then(function (md) {
            if (md !== null && md !== served.map_sha) throw new Error("raced: the map changed while it was fetched");
            return { S: json(sb), map: json(mb), sha: served.sha, mapSha: served.map_sha };
          });
        });
      });
    });
  };
  const fail = function (e) { $("overlay").textContent = String(e && e.message || e); $("overlay").style.display = "flex"; };

  get("/live").then(json).then(function (live) {
    const n = live.slots.length;
    let k = q.get("slot") !== null ? parseInt(q.get("slot"), 10) : (n > 1 && live.slots[1].served ? 1 : 0);
    if (!(k >= 0 && k < n && live.slots[k].served)) k = 0;
    if (!live.slots[k].served) throw new Error(live.slots[k].message || "nothing is served");
    return fetchSlot(k, live.slots[k].served).then(function (got) { start(got, k, live); });
  }).catch(fail);

  function start(got, k0, live0) {
    const canvas = $("view"), P = Sim.P;
    let S = got.S, map = got.map, world = new Sim.World(map), s = Sim.newState(world, "A");
    let R;
    try { R = new window.VerdandiScene.Renderer(canvas, S); } catch (e) { fail("The scene could not be drawn: " + (e && e.message || e)); return; }
    const cur = { k: k0, sha: got.sha, mapSha: got.mapSha, version: live0.version, code: live0.code, slots: live0.slots,
                  note: "", noteAt: 0, swaps: 0, renderers: 1, games: 1, ms: 0 };
    document.title = (S.title || brief) + " — Verðandi";
    let views = Object.keys(S.views).sort();
    let mode = "play", vcam = null, label = "play", paused = false, walk = null;
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
    const say = function (text) { cur.note = text; cur.noteAt = performance.now(); };

    // ---------------------------------------------------------------- live
    // put a fetched source in place: the same map, the scene alone; another map, a new game
    const apply = function (k, g, t0) {
      const sameMap = g.mapSha === cur.mapSha, from = cur.sha;
      R.load(g.S);
      S = g.S; views = Object.keys(S.views).sort();
      if (!sameMap) { map = g.map; world = new Sim.World(map); s = Sim.newState(world, "A"); walk = null; cur.games += 1; }
      cur.k = k; cur.sha = g.sha; cur.mapSha = g.mapSha; cur.swaps += 1; cur.ms = Math.round(performance.now() - t0);
      say((from === g.sha ? "source " + k : "scene " + from.slice(0, 12) + " -> " + g.sha.slice(0, 12)) + " in " + cur.ms + " ms"
        + (sameMap ? "; the game goes on untouched" : "; a new map, so a new game at the spawn"));
    };
    const swapRenderer = function (sha) {
      const old = window.VerdandiScene, el = document.createElement("script");
      el.src = "/scene_render.js?v=" + sha;
      el.onload = function () {
        let R2;
        try { R2 = new window.VerdandiScene.Renderer(canvas, S); } catch (e) {
          window.VerdandiScene = old; say("scene_render.js changed, but the new one does not start (" + (e && e.message || e) + "); the old one draws");
          return;
        }
        R.dispose(); R = R2; cur.renderers += 1; say("scene_render.js changed: the new renderer draws; the game goes on untouched");
      };
      el.onerror = function () { say("scene_render.js could not be fetched; the old renderer draws"); };
      document.head.appendChild(el);
    };
    let busy = false;
    const sync = function (live, force) {
      cur.slots = live.slots;
      const info = live.slots[cur.k];
      if (live.code["scene_render.js"] !== cur.code["scene_render.js"]) swapRenderer(live.code["scene_render.js"]);
      if (live.code["play.js"] !== cur.code["play.js"] || live.code["sim.js"] !== cur.code["sim.js"])
        say((live.code["play.js"] !== cur.code["play.js"] ? "play.js" : "sim.js") + " changed on disk: reload the page (F5) to use it; the game restarts");
      cur.code = live.code;
      if (!info.ok && live.version !== cur.version) say("[" + cur.k + "] refused, the scene before it stays: " + info.message.split("\n").slice(0, 3).join(" "));
      cur.version = live.version;
      const sv = info.served;
      if (sv && (force || sv.sha !== cur.sha || sv.map_sha !== cur.mapSha)) {
        const t0 = performance.now(), k = cur.k;
        busy = true;
        return fetchSlot(k, sv).then(function (g) { if (k === cur.k) apply(k, g, t0); })
          .catch(function (e) { cur.version = -1; say(String(e && e.message || e)); })
          .then(function () { busy = false; });
      }
      return Promise.resolve();
    };
    const poll = function () {
      if (busy) return;
      busy = true;
      get("/live").then(json).then(function (live) {
        busy = false;
        if (live.version !== cur.version || JSON.stringify(live.code) !== JSON.stringify(cur.code)) return sync(live, false);
      }).catch(function () { busy = false; say("play.py does not answer; the last scene stays"); });
    };
    const pick = function (k) { cur.k = k; return sync({ version: cur.version, code: cur.code, slots: cur.slots }, true); };
    const step = function (d) {
      const n = cur.slots.length;
      for (let i = 1; i <= n; i++) {
        const k = (cur.k + d * i + n * 4) % n;
        if (cur.slots[k].served) return pick(k);
      }
    };

    // the hooks a still, a walk-through or a test uses
    window.PLAY = {
      get renderer() { return R; }, get scene() { return S; }, get state() { return s; }, get world() { return world; },
      live: cur, sim: Sim,
      pause: function (on) { paused = !!on; },
      slot: pick,
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
    setInterval(poll, 500);

    // play: the fixed tick, as the graybox runs it
    const keys = {}, pending = { reset: false, jump: false }, refusals = {};
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
      if (e.code === "BracketLeft") step(-1);
      if (e.code === "BracketRight") step(1);
    });
    document.addEventListener("keyup", function (e) { keys[e.code] = false; });
    window.addEventListener("blur", function () { for (const k in keys) keys[k] = false; fire = false; });
    function frame(now) {
      const dt = Math.min(0.25, (now - last) / 1000); last = now;
      if (mode === "play" && !paused) {
        acc += dt;
        let first = true;
        while (acc >= Sim.TICK) {
          // a record the input contract admits: every flag true or false (graybox/RULES-1.md, The input)
          const refused = Sim.step(world, s, { f: !!(keys.KeyW || keys.ArrowUp), b: !!(keys.KeyS || keys.ArrowDown), l: !!(keys.KeyA || keys.ArrowLeft),
                               r: !!(keys.KeyD || keys.ArrowRight), jump: !!(keys.Space || pending.jump), fire: !!fire, reset: !!pending.reset,
                               dyaw: first ? mdx * SENS : 0, dpitch: first ? -mdy * SENS : 0 });
          if (refused && !refusals[refused]) { refusals[refused] = true; console.warn("plaza: an input was refused (" + refused + "); the state is unchanged"); }
          if (first) { mdx = 0; mdy = 0; }
          pending.reset = false; pending.jump = false; first = false; acc -= Sim.TICK;
        }
      } else acc = 0;
      render(mode === "play" ? eyeOf(s) : vcam, (now - t0) / 1000, s);
      const info = cur.slots[cur.k] || {}, sv = info.served || {};
      $("hud").textContent = (S.title || brief) + "  ·  " + label + "  ·  cell " + Math.floor(s.x / S.grid.cell) + "," + Math.floor(s.z / S.grid.cell)
        + "  ·  hits " + s.score + "\n" + views.map(function (v, i) { return (i + 1) + " " + v; }).join("  ") + "  ·  Tab play  ·  WASD, mouse, Space, R"
        + "\nsource [" + cur.k + "] " + (info.label || "") + (sv.verdict ? "  ·  " + sv.verdict : "")
        + "  ·  scene " + cur.sha.slice(0, 12) + (cur.slots.length > 1 ? "  ·  [ ] steps through the " + cur.slots.length + " sources" : "")
        + "\nmovement and collision: the graybox's simulation against C  ·  live: play.py v" + cur.version
        + (cur.note && now - cur.noteAt < 8000 ? "\n" + cur.note : "");
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
})();
