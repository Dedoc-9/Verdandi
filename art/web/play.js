// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// art/web/play.js — the native plaza: the graybox's simulation (sim.js, unchanged) and the art scene's renderer
// (scene_render.js), in one page served by art/play.py; since STUDIO-3 (0230) inside the studio's shell.
//
// The simulation moves the player against C, the collision world of the converted map, and nothing else; the
// renderer draws the dressed scene from where the player's eye is and writes no state. Input reaches the simulation
// only as a tick's input record. Two modes: the editor (the default since 0230: a free camera, the cursor picks what
// it is over, the panels say what it is) and play (the mouse captured, the game's keys; Esc goes back to the editor at
// the player's eye). The registered views (keys 1-9) move the editor's camera; neither the editor nor a view moves the
// game, which waits while it is not played.
//
// Live: the page asks /live twice a second what art/play.py serves. When the source it shows has a new scene (an edit
// that passed the checks), the scene's bytes are fetched, held to the digest /live gave, and handed to the renderer in
// place: the game is not touched, since nothing the renderer does reaches it. When the new scene's map differs, the
// collision world is new, and so is the game: the simulation's own new state at the spawn, nothing carried into it.
// A refusal is shown and the scene before it stays. A new scene_render.js takes the canvas over from the old one (if
// it fails to start, the old one goes on drawing); a new play.js, studio_ui.js or sim.js is announced and loaded by
// reloading the page. [ and ] step through the sources play.py was given (the brief and each --intent).
//
// For stills and walk-throughs: ?view=NAME opens at a view and renders it; ?cam=x,y,z,yaw,pitch (metres, degrees);
// ?slot=K picks the source; window.PLAY.walkTo(tick) puts the player where the self-test's recorded walk is at that
// tick and renders it. A still is the picture alone, without the shell.
//
// The studio (STUDIO-0, art/studio.py): Enter opens the director's drawer. The prompt and the camera go to play.py, whose
// gateway asks the configured provider for at most three candidates and has the director evaluate each; those it
// draws are sources this page switches to in place, the game untouched, exactly as [ and ] do. Nothing here admits,
// rejects or undoes: the buttons ask play.py, which does it through the director's ledger. A failure of the provider
// is shown, and the world goes on.
//
// The references (STUDIO-1): E makes the selected object (in play, the one under the crosshair) the target, R pins it
// as a reference (or unpins it), up to four; play.py gives each a tag (@1, @2, ...) that names that object for as long
// as it runs, and says whether it is as tagged, changed, or gone. Each tagged object is framed and labelled.
//
// The shell (STUDIO-3, 0230; art/STUDIO.md, "The shell"): a menu bar, the scene, layer and selection, a navigator, the
// viewport with its tools, pills and measured statistics, an inspector of what is selected (GET /object.json: read
// from the scene served, nothing bound), the layers, the world's settings, an asset browser with thumbnails drawn by a
// second renderer, the candidates, and the world's ledger (GET /history.json). What is not built says so, and why.
// Everything the shell shows is read from what play.py serves; everything it changes goes through play.py's routes.

(function () {
  "use strict";
  // 0226: a scene with movers names the rules it is played under (rules 2, graybox/RULES-2.md), and the page plays it
  // under those and no other: a scene naming rules this page does not play is not played (the handshake). 0229: the
  // exporter names rules 3 (graybox/RULES-3.md) on every scene, with movers or without: walls hold a body at any height,
  // a target has a top and waits for its column to clear, a mover may push. A scene that names no rules (an exporter
  // before 0226) is played under rules 1, and one with movers under rules 2, as before.
  const Base = window.GrayboxSim, q = new URLSearchParams(location.search), $ = function (id) { return document.getElementById(id); };
  const U = window.StudioUI, el = U.el, icon = U.icon;
  let Sim = Base;
  const simFor = function (S) {
    if (S.rules === undefined && !S.movers) return Base;
    if (S.rules === 2 && Array.isArray(S.movers)) return Base.withRules(2);
    if (S.rules === 3 && (S.movers === undefined || Array.isArray(S.movers))) return Base.withRules(3);
    throw new Error("this scene names rules " + JSON.stringify(S.rules) + ", which this page does not play (it plays rules 3, and rules 1 and 2 as scenes before 0229 named them)");
  };
  // the movers as rules 2 take them, and a key that changes when the game would: the map, the rules, and any mover's
  // box, axis, travel, speed or policy (a mover's material is its look, and changes nothing of the game)
  const moversOf = function (S) {
    return (S.movers || []).map(function (m) { return { id: m.id, box: m.box, axis: m.axis, len: m.len, speed: m.speed, policy: m.policy }; });
  };
  const worldOf = function (S, map) { return new Sim.World(S.movers ? Object.assign({}, map, { movers: moversOf(S) }) : map); };
  const gameKey = function (S, mapSha) { return mapSha + "|" + JSON.stringify([S.rules === undefined ? 1 : S.rules, moversOf(S)]); };
  const brief = q.get("brief") || document.body.getAttribute("data-brief");
  const deg = Math.PI / 180;
  // STUDIO-2: the page shows one world; every read and every request names it (play.html?world=NAME)
  const W = encodeURIComponent(brief);
  const live_url = "/live?world=" + W;
  const get = function (url) {
    return fetch(url, { cache: "no-store" }).then(function (r) { if (!r.ok) throw new Error(url + ": " + r.status); return r.arrayBuffer(); });
  };
  const hex = function (buf) {
    if (!(window.crypto && crypto.subtle)) return Promise.resolve(null);
    return crypto.subtle.digest("SHA-256", buf).then(function (d) { return Array.from(new Uint8Array(d), function (b) { return b.toString(16).padStart(2, "0"); }).join(""); });
  };
  const json = function (buf) { return JSON.parse(new TextDecoder().decode(buf)); };
  const getJSON = function (url) { return fetch(url, { cache: "no-store" }).then(function (r) { return r.json(); }); };
  // a source's scene and map, as /live describes them; the bytes must hash to the digests given
  const fetchSlot = function (k, served) {
    return get("/scene/" + brief + ".json?slot=" + k).then(function (sb) {
      return hex(sb).then(function (d) {
        if (d !== null && d !== served.sha) throw new Error("raced: the scene changed while it was fetched");
        return get("/map/" + served.map + ".json?slot=" + k + "&world=" + W).then(function (mb) {
          return hex(mb).then(function (md) {
            if (md !== null && md !== served.map_sha) throw new Error("raced: the map changed while it was fetched");
            return { S: json(sb), map: json(mb), sha: served.sha, mapSha: served.map_sha };
          });
        });
      });
    });
  };
  const fail = function (e) { const o = $("overlay"); o.textContent = String(e && e.message || e); o.style.display = "flex"; };

  get(live_url).then(json).then(function (live) {
    const n = live.slots.length;
    let k = q.get("slot") !== null ? parseInt(q.get("slot"), 10) : (n > 1 && live.slots[1].served ? 1 : 0);
    if (!(k >= 0 && k < n && live.slots[k].served)) k = 0;
    if (!live.slots[k].served) throw new Error(live.slots[k].message || "nothing is served");
    return fetchSlot(k, live.slots[k].served).then(function (got) { start(got, k, live); });
  }).catch(fail);

  function start(got, k0, live0) {
    const canvas = $("view"), ov = $("ov"), vp = $("vp"), P = Sim.P;
    let S = got.S, map = got.map, world, s;
    try { Sim = simFor(S); world = worldOf(S, map); s = Sim.newState(world, "A"); } catch (e) { fail("The scene could not be played: " + (e && e.message || e)); return; }
    // ---------------------------------------------------------------- the shell's state (a view's: none of it is the world)
    const ui = { mode: "edit", tool: "select", sel: null, info: null, infoErr: "", hover: null, layer: "all", hidden: {}, locked: {},
                 show: { grid: false, regions: false, spawns: true, tags: true, rain: true, wire: false, collision: false, stats: true },
                 rtab: "inspector", nav: "overview", folder: "dressing", measure: [], saved: [], connected: true, history: null, histKey: "",
                 statsAt: 0, frames: 0, fps: 0, frameMs: 0, cpuMs: 0, calls: 0, callsShown: 0, lastFrame: 0, cursor: null, rmb: false, drag: null };
    // what the renderer is given: the scene with the hidden layers left out (a view of it; the game is not touched)
    const viewScene = function (S0) {
      const h = ui.hidden;
      if (!Object.keys(h).some(function (k) { return h[k]; })) return S0;
      return Object.assign({}, S0, {
        visuals: S0.visuals.filter(function (v) { return !h[v.id.split(":")[0]]; }),
        collision: h.play ? [] : S0.collision,
        lights: h.lights ? [] : S0.lights.filter(function (L) { return !h[L.id.split(":")[0]]; }),
      });
    };
    let R;
    try { R = new window.VerdandiScene.Renderer(canvas, viewScene(S)); } catch (e) { fail("The scene could not be drawn: " + (e && e.message || e)); return; }
    const cur = { k: k0, sha: got.sha, mapSha: got.mapSha, version: live0.version, code: live0.code, slots: live0.slots,
                  note: "", noteAt: 0, swaps: 0, renderers: 1, games: 1, ms: 0 };
    document.title = (S.title || brief) + " — Verðandi Studio";
    let views = Object.keys(S.views).sort();
    let label = "editor", paused = false, walk = null;
    const targets = function (st) {
      return st.targets.map(function (t) {
        return { up: t.up, box: [t.x - P.targetRadius, t.y + (t.up ? 0 : -P.targetHeight + 0.1), t.z - P.targetRadius, t.x + P.targetRadius, t.y + (t.up ? P.targetHeight : 0.1), t.z + P.targetRadius] };
      });
    };
    const eyeOf = function (st) { return { x: st.x, y: st.feet + P.eye, z: st.z, yaw: st.yaw, pitch: st.pitch }; };
    // the editor's camera: the first registered view, or the player's eye at the spawn
    let ecam = views.length ? (function (v) { return { x: v.x, y: v.y, z: v.z, yaw: v.yaw * deg, pitch: v.pitch * deg, fov: 66 }; })(S.views[views[0]]) : Object.assign(eyeOf(s), { fov: 66 });
    const dpr = function () { return Math.min(window.devicePixelRatio || 1, 1.5); };
    const fit = function () {
      const full = document.body.classList.contains("playfull");
      const w = parseInt(q.get("w") || "0", 10) || (full ? 1920 : Math.max(2, Math.round(canvas.clientWidth * dpr())));
      const h = parseInt(q.get("h") || "0", 10) || (full ? 1080 : Math.max(2, Math.round(canvas.clientHeight * dpr())));
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
      const ow = Math.max(2, Math.round(ov.clientWidth * dpr())), oh = Math.max(2, Math.round(ov.clientHeight * dpr()));
      if (ov.width !== ow || ov.height !== oh) { ov.width = ow; ov.height = oh; }
    };
    // where the simulation has put each mover in this state (phase 0 in a state that has none, a walk's)
    const moverBoxes = function (st) {
      return world.movers.map(function (m, i) {
        const b = Sim.poseOf(m, st.movers && st.movers[i] ? st.movers[i].phase : 0);
        return [b.x0, b.y0, b.z0, b.x1, b.y1, b.z1];
      });
    };
    // the renderer's draw calls, counted (the stats box says what it measured, and only that)
    const countCalls = function (r) {
      const gl = r.gl;
      if (gl.__counted) return;
      gl.__counted = true;
      const a = gl.drawArrays.bind(gl), b = gl.drawArraysInstanced.bind(gl);
      gl.drawArrays = function (x, y, z) { ui.calls++; return a(x, y, z); };
      gl.drawArraysInstanced = function (x, y, z, w) { ui.calls++; return b(x, y, z, w); };
    };
    countCalls(R);
    const render = function (cam, time, st) {
      fit();
      if (R.setMovers) R.setMovers(ui.hidden.movers ? [] : moverBoxes(st));
      R.setTargets(ui.hidden.targets ? [] : targets(st));
      if (!ui.show.rain) R.rain = 0;
      R.draw(cam, time);
    };
    const goView = function (name) {
      const v = S.views[name]; if (!v) return;
      if (ui.mode === "play") leavePlay();
      label = "view " + name; ecam = { x: v.x, y: v.y, z: v.z, yaw: v.yaw * deg, pitch: v.pitch * deg, fov: 66 };
    };
    const say = function (text) { cur.note = text; cur.noteAt = performance.now(); };
    let toast = function () {};

    // ---------------------------------------------------------------- live
    // put a fetched source in place: the same map, the scene alone; another map, a new game
    const apply = function (k, g, t0) {
      const sameMap = g.mapSha === cur.mapSha, sameGame = gameKey(g.S, g.mapSha) === gameKey(S, cur.mapSha), from = cur.sha;
      let Sim2, world2, s2;
      if (!sameGame) {
        try { Sim2 = simFor(g.S); const keep = Sim; Sim = Sim2; try { world2 = worldOf(g.S, g.map); } finally { Sim = keep; } s2 = Sim2.newState(world2, "A"); }
        catch (e) { say("the new scene is not played (" + (e && e.message || e) + "); the old one goes on"); return; }
      }
      R.load(viewScene(g.S));
      S = g.S; views = Object.keys(S.views).sort(); S._ids = null; objIndex = null;
      if (!sameGame) { Sim = Sim2; map = g.map; world = world2; s = s2; walk = null; cur.games += 1; }
      cur.k = k; cur.sha = g.sha; cur.mapSha = g.mapSha; cur.swaps += 1; cur.ms = Math.round(performance.now() - t0);
      say((from === g.sha ? "source " + k : "scene " + from.slice(0, 12) + " -> " + g.sha.slice(0, 12)) + " in " + cur.ms + " ms"
        + (sameGame ? "; the game goes on untouched" : sameMap ? "; the movers or the rules changed, so a new game at the spawn" : "; a new map, so a new game at the spawn"));
      shell.sceneChanged();
    };
    const swapRenderer = function (sha) {
      const old = window.VerdandiScene, e2 = document.createElement("script");
      e2.src = "/scene_render.js?v=" + sha;
      e2.onload = function () {
        let R2;
        try { R2 = new window.VerdandiScene.Renderer(canvas, viewScene(S)); } catch (e) {
          window.VerdandiScene = old; say("scene_render.js changed, but the new one does not start (" + (e && e.message || e) + "); the old one draws");
          return;
        }
        R.dispose(); R = R2; countCalls(R); cur.renderers += 1; say("scene_render.js changed: the new renderer draws; the game goes on untouched");
      };
      e2.onerror = function () { say("scene_render.js could not be fetched; the old renderer draws"); };
      document.head.appendChild(e2);
    };
    let busy = false;
    const sync = function (live, force) {
      cur.slots = live.slots;
      const info = live.slots[cur.k];
      if (live.code["scene_render.js"] !== cur.code["scene_render.js"]) swapRenderer(live.code["scene_render.js"]);
      for (const f of ["play.js", "studio_ui.js", "sim.js"]) {
        if (live.code[f] !== undefined && live.code[f] !== cur.code[f]) { say(f + " changed on disk: reload the page (F5) to use it; the game restarts"); break; }
      }
      cur.code = live.code;
      if (!info.ok && live.version !== cur.version) say("[" + cur.k + "] refused, the scene before it stays: " + info.message.split("\n").slice(0, 3).join(" "));
      cur.version = live.version;
      shell.slotsChanged();
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
      get(live_url).then(json).then(function (live) {
        busy = false;
        ui.connected = true;
        studioShow(live.studio);
        worldsShow(live.worlds);
        queueShow(live.queue);
        if (live.version !== cur.version || JSON.stringify(live.code) !== JSON.stringify(cur.code)) return sync(live, false);
      }).catch(function () { busy = false; ui.connected = false; say("play.py does not answer; the last scene stays"); });
    };
    const pick = function (k) { cur.k = k; return sync({ version: cur.version, code: cur.code, slots: cur.slots }, true); };
    const step = function (d) {
      const n = cur.slots.length;
      for (let i = 1; i <= n; i++) {
        const k = (cur.k + d * i + n * 4) % n;
        if (cur.slots[k].served) return pick(k);
      }
    };

    // ---------------------------------------------------------------- what the view knows of the scene (read, never written)
    // the object a box belongs to (art/studio_refs.py's rule): its own id, or the id of the object it extends
    const ids = function () { if (!S._ids) S._ids = new Set(S.visuals.map(function (v) { return v.id; })); return S._ids; };
    const rootOf = function (id) {
      let r = id;
      while (r.split(":").length >= 3 && ids().has(r.slice(0, r.lastIndexOf(":")))) r = r.slice(0, r.lastIndexOf(":"));
      return r;
    };
    const addressOf = function (v) { const i = v.id.indexOf(":"); return (v.region === "*" ? "city" : v.region) + "/" + v.id.slice(0, i) + "/" + v.id.slice(i + 1); };
    // the scene's objects, by kind: {id, kind, region, boxes, material}
    let objIndex = null;
    const objects = function () {
      if (objIndex) return objIndex;
      const out = {};
      for (const v of S.visuals) {
        const r = rootOf(v.id);
        const o = out[r] || (out[r] = { id: r, kind: r.split(":")[0], region: v.region === "*" ? "city" : v.region, boxes: [], material: "" });
        o.boxes.push(v.box);
        if (v.id === r) o.material = v.material;
      }
      objIndex = out;
      return out;
    };
    const union = function (boxes) {
      let b = null;
      for (const x of boxes) b = b ? [Math.min(b[0], x[0]), Math.min(b[1], x[1]), Math.min(b[2], x[2]), Math.max(b[3], x[3]), Math.max(b[4], x[4]), Math.max(b[5], x[5])] : x.slice();
      return b;
    };
    // the boxes of a piece as the shell names it: an art object (its own and its parts'), play:ID, mover:ID, target:ID
    const pieceBoxes = function (piece) {
      if (!piece) return [];
      if (piece.indexOf("play:") === 0) { const c = S.collision.find(function (x) { return x.id === piece.slice(5); }); return c ? [c.box] : []; }
      if (piece.indexOf("mover:") === 0) { const i = world.movers.findIndex(function (m) { return m.id === piece.slice(6); }); return i >= 0 ? [moverBoxes(s)[i]] : []; }
      if (piece.indexOf("target:") === 0) { const t = (S.targets || {})[piece.slice(7)]; return t ? [[t.x - P.targetRadius, t.y, t.z - P.targetRadius, t.x + P.targetRadius, t.y + P.targetHeight, t.z + P.targetRadius]] : []; }
      const o = objects()[rootOf(piece)];
      return o ? o.boxes : [];
    };
    const objectBox = function (piece) { const b = pieceBoxes(piece); return b.length ? union(b) : null; };
    const layerOf = function (piece) {
      return piece.indexOf("play:") === 0 ? "play" : piece.indexOf("mover:") === 0 ? "movers" : piece.indexOf("target:") === 0 ? "targets" : piece.split(":")[0];
    };
    const nameOf = function (piece) {
      if (!piece) return "none";
      if (piece.indexOf("play:") === 0) { const c = S.collision.find(function (x) { return x.id === piece.slice(5); }); return c ? "play/" + c.kind + "/" + c.id : piece; }
      if (piece.indexOf("mover:") === 0) return "play/mover/" + piece.slice(6);
      if (piece.indexOf("target:") === 0) return "play/target/" + piece.slice(7);
      const o = objects()[rootOf(piece)];
      return o ? o.region + "/" + o.kind + "/" + o.id.slice(o.kind.length + 1) : piece;
    };

    // ---------------------------------------------------------------- the eye, the ray, the pick
    const eye = function () { return ui.mode === "play" ? eyeOf(s) : ecam; };
    // the nearest box a ray meets, of the layers shown: the art's dressing, the play geometry, the movers and the targets.
    // A layer shown but locked hides what is behind it and is not picked (a wall in front is the map's).
    const hitRay = function (o, d) {
      let best = null;
      const consider = function (box, piece, layer) {
        if (ui.hidden[layer]) return;
        const h = U.enterBox(o, d, box);
        if (h && (!best || h.t < best.t)) best = { t: h.t, face: h.face, piece: piece, layer: layer, box: box };
      };
      for (const v of S.visuals) consider(v.box, v.id, v.id.split(":")[0]);
      for (const c of S.collision) consider(c.box, "play:" + c.id, "play");
      moverBoxes(s).forEach(function (b, i) { consider(b, "mover:" + world.movers[i].id, "movers"); });
      for (const t of targets(s)) { if (t.up) consider(t.box, "target:" + Object.keys(S.targets || {})[s.targets.indexOf(t)], "targets"); }
      if (!best) return null;
      best.point = [o[0] + d[0] * best.t, o[1] + d[1] * best.t, o[2] + d[2] * best.t];
      best.selectable = !ui.locked[best.layer] && (ui.layer === "all" || ui.layer === best.layer);
      return best;
    };
    const hitCentre = function () { const c = eye(), B = U.basis(c); return hitRay([c.x, c.y, c.z], B.f); };
    const hitAt = function (px, py) { const r = U.rayAt(eye(), px, py, canvas.clientWidth, canvas.clientHeight); return hitRay(r.o, r.d); };
    // the art piece under the crosshair, as the references take it: the nearest box, and nothing if that is not the art's
    const pickPiece = function () {
      const h = hitCentre();
      if (!h || h.piece.indexOf(":") < 0 || /^(play|mover|target):/.test(h.piece)) return null;
      return S.visuals.find(function (v) { return v.id === h.piece; }) || null;
    };

    // ---------------------------------------------------------------- the studio
    const token = document.body.getAttribute("data-studio") || "";
    const studio = { open: false, refs: { target: null, pins: [], items: [] }, last: "", req: null, hover: null, provider: {} };
    const panel = $("studio"), promptEl = $("st-prompt");
    const post = function (path, body) {
      body = Object.assign({ world: brief }, body || {});
      return fetch(path, { method: "POST", headers: { "Content-Type": "application/json", "X-Studio-Token": token }, body: JSON.stringify(body) })
        .then(function (r) { return r.json().catch(function () { return { ok: false, message: "HTTP " + r.status }; }); })
        .catch(function (e) { return { ok: false, message: "play.py does not answer (" + (e && e.message || e) + ")" }; });
    };
    // a box's frame on the canvas (CSS pixels), or null when it is behind the eye (the view's own arithmetic)
    const frameOf = function (b) {
      const c = eye(), W0 = canvas.clientWidth, H0 = canvas.clientHeight;
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, seen = 0;
      for (const p of U.corners(b)) {
        const sp = U.project(c, p, W0, H0);
        if (!sp) continue;
        seen++;
        x0 = Math.min(x0, sp[0]); x1 = Math.max(x1, sp[0]); y0 = Math.min(y0, sp[1]); y1 = Math.max(y1, sp[1]);
      }
      if (!seen) return null;
      const cl = function (v, a, b2) { return Math.max(a, Math.min(b2, v)); };
      const L = cl(x0, -2, W0 + 2), Rr = cl(x1, -2, W0 + 2), T = cl(y0, -2, H0 + 2), B = cl(y1, -2, H0 + 2);
      return Rr - L > 1 && B - T > 1 ? { L: L, T: T, W: Rr - L, H: B - T } : null;
    };
    const tagOf = function (piece) { const it = (studio.refs.items || []).find(function (x) { return x.piece === piece; }); return it ? it.tag : ""; };
    const knownTag = function (piece) { const it = (studio.refs.known || []).find(function (x) { return x.piece === piece; }); return it ? it.tag : ""; };
    const showRefs = function () {
      const box = $("st-refs");
      box.innerHTML = "";
      const items = studio.refs.items || [];
      const known = studio.refs.known || [];
      // B1: every tag of this project, kept across restarts; a click puts it into the prompt (a tag named there must
      // also be the target or a pin, which the gateway checks and says)
      if (known.length) {
        const row = document.createElement("div");
        row.className = "tags";
        row.appendChild(document.createTextNode("tags: "));
        for (const k of known) {
          const b = document.createElement("button");
          b.className = "tag" + (k.present === false ? " gone" : "") + (items.some(function (x) { return x.tag === k.tag; }) ? " active" : "");
          b.textContent = k.tag;
          b.title = k.kind + " " + k.address + (k.present === false ? " (not in the scene now)" : "") + " · click to put " + k.tag + " into the prompt";
          b.onclick = function () {
            const at = promptEl.selectionStart || promptEl.value.length, v = promptEl.value;
            const ins = (at > 0 && v[at - 1] !== " " ? " " : "") + k.tag + " ";
            promptEl.value = v.slice(0, at) + ins + v.slice(at);
            promptEl.focus(); promptEl.selectionStart = promptEl.selectionEnd = at + ins.length;
          };
          row.appendChild(b);
        }
        box.appendChild(row);
      }
      if (studio.refs.tags_error) { const e = document.createElement("div"); e.className = "ref gone"; e.textContent = studio.refs.tags_error; box.appendChild(e); }
      if (!items.length) { const e = document.createElement("div"); e.textContent = "No target: the prompt is for the whole world. E makes the selected object the target; R pins a reference."; box.appendChild(e); return; }
      for (const it of items) {
        const e = document.createElement("div");
        e.className = "ref " + it.status;
        const st = it.statement;
        e.textContent = it.tag + " " + it.role + " · " + it.address + " · " + it.size_m.join(" × ") + " m" + (st ? " · line " + st.line : "")
          + (it.status === "changed" ? " · changed since tagged" : it.status === "gone" ? " · gone: no such object in this scene" : "");
        if (it.role === "pin") {
          const b = document.createElement("button"); b.textContent = "unpin";
          b.onclick = function () { post("/studio/unpin", { tag: it.tag }).then(function (r) { if (r.ok) { studio.refs = r.refs; showRefs(); shell.inspector(); } note(r, "unpinned " + it.tag); }); };
          e.appendChild(b);
        }
        box.appendChild(e);
      }
    };
    const setRefs = function (refs) { if (refs) { studio.refs = refs; showRefs(); shell.inspector(); } };
    // E and R: in play, the art piece under the crosshair; in the editor, the selected object if it is the art's
    const subject = function () {
      if (ui.mode === "play") return pickPiece();
      if (!ui.sel || /^(play|mover|target):/.test(ui.sel)) return null;
      return S.visuals.find(function (v) { return v.id === ui.sel; }) || S.visuals.find(function (v) { return rootOf(v.id) === rootOf(ui.sel); }) || null;
    };
    const select = function () {
      const v = subject();
      return post("/studio/select", { piece: v ? v.id : null }).then(function (r) {
        setRefs(r.refs);
        const t = studio.refs.target;
        say(r.ok ? (v ? "target " + t + ": " + addressOf({ id: rootOf(v.id), region: v.region }) : "nothing of the art " + (ui.mode === "play" ? "under the crosshair" : "selected") + "; no target")
          : (r.code || "") + " " + (r.message || ""));
        if (r.ok) toast(v ? "Target " + t + " · " + addressOf({ id: rootOf(v.id), region: v.region }) : "No target: the prompt is for the whole world");
        else toast((r.code || "") + " " + (r.message || ""), true);
        return r;
      });
    };
    const pin = function () {
      const v = subject();
      if (!v) { say("nothing of the art " + (ui.mode === "play" ? "under the crosshair" : "selected") + " to pin"); toast("Nothing of the art to pin: a play box is the map's, not a tag's", true); return Promise.resolve({ ok: false }); }
      const before = tagOf(rootOf(v.id)), was = (studio.refs.pins || []).indexOf(before) >= 0;
      return post("/studio/pin", { piece: v.id }).then(function (r) {
        setRefs(r.refs);
        const t = tagOf(rootOf(v.id));
        const m = r.ok ? (was ? "unpinned " + before : "pinned " + t + ": " + addressOf({ id: rootOf(v.id), region: v.region })) : (r.code || "") + ": " + (r.message || "");
        say(m); toast(m, !r.ok);
        return r;
      });
    };
    const openPanel = function () {
      studio.open = true; panel.classList.add("open");
      if (document.pointerLockElement) document.exitPointerLock();
      showRefs();
      setTimeout(function () { promptEl.focus(); }, 0);
    };
    // closed, the panel keeps no focus: a button or a list of the panel still focused would take the game's keys
    // (STUDIO-2's browser run: Queue clicked, Esc, and W did not walk)
    const closePanel = function () {
      studio.open = false; panel.classList.remove("open"); promptEl.blur();
      if (document.activeElement && panel.contains(document.activeElement)) document.activeElement.blur();
    };
    $("st-close").onclick = closePanel;
    const note = function (r, what) { $("st-status").innerHTML = ""; const e = document.createElement("span"); e.className = r.ok ? "good" : "bad"; e.textContent = r.ok ? what : (r.code ? r.code + ": " : "") + (r.message || "failed"); $("st-status").appendChild(e); };
    const camNow = function () { const c = eye(); return { x: c.x, y: c.y, z: c.z, yaw_deg: c.yaw / deg, pitch_deg: c.pitch / deg }; };
    const ask = function () {
      post("/studio/ask", { prompt: promptEl.value, camera: camNow() })
        .then(function (r) { note(r, "asked: request " + (r.id || "")); studio.last = ""; });
    };
    const decide = function (what, rid, letter, extra) {
      post("/studio/" + what, Object.assign({ id: rid, candidate: letter }, extra || {})).then(function (r) {
        note(r, what === "admit" ? "admitted: ledger #" + (r.ledger || []).join(", #") : "rejected: ledger #" + (r.ledger || []).join(", #"));
        toast(r.ok ? (what === "admit" ? "Admitted " + letter + " · ledger #" + (r.ledger || []).join(", #") : "Rejected " + letter) : (r.code || "") + " " + (r.message || ""), !r.ok);
        if (r.ok && what === "admit") pick(0);
        studio.last = ""; ui.histKey = "";
      });
    };
    // ADMISSION-0 (0222): an admission brings a still of the candidate as drawn. Admit draws it (if another source is
    // shown), waits two frames, takes the canvas as PNG and gives it to play.py, which keeps it and reads its detectors;
    // with no flag the candidate is admitted with that still, and with a flag nothing is admitted and the flag is shown,
    // with "Admit despite" beside it. The page decides nothing: the host reads the still and the director admits.
    const twoFrames = function () { return new Promise(function (res) { requestAnimationFrame(function () { requestAnimationFrame(res); }); }); };
    // The still is a copy at most 960 pixels wide (the host reads its detectors in Python: a smaller still is a quicker
    // read and a smaller piece of evidence), encoded at once with toDataURL: toBlob encodes when the page is idle, and a
    // page that draws every frame on a slow renderer was not idle for minutes (OBSERVED in the container, SwiftShader).
    const takeStill = function (rid, letter) {
      return twoFrames().then(function () {
        const k = Math.min(1, 960 / canvas.width), c2 = document.createElement("canvas");
        c2.width = Math.max(1, Math.round(canvas.width * k)); c2.height = Math.max(1, Math.round(canvas.height * k));
        c2.getContext("2d").drawImage(canvas, 0, 0, c2.width, c2.height);
        const u = c2.toDataURL("image/png"), bin = atob(u.slice(u.indexOf(",") + 1)), a = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
        return fetch("/studio/still?world=" + encodeURIComponent(brief) + "&id=" + encodeURIComponent(rid) + "&candidate=" + encodeURIComponent(letter),
          { method: "POST", headers: { "Content-Type": "image/png", "X-Studio-Token": token }, body: a }).then(function (r) { return r.json(); });
      });
    };
    const admitWithStill = function (rid, c) {
      $("st-status").textContent = "taking a still of " + c.letter + " as drawn…";
      (c.slot !== cur.k ? pick(c.slot) : Promise.resolve()).then(function () { return takeStill(rid, c.letter); }).then(function (st) {
        if (!st.ok) { note(st, ""); toast((st.code || "") + " " + (st.message || ""), true); return; }
        if (st.flags && st.flags.length) {
          note({ ok: false, code: "THE STILL IS FLAGGED", message: st.flags.join("; ") + ". A detector proves nothing: look, then Admit despite, or Reject" }, "");
          toast("The still of " + c.letter + " is flagged: " + st.flags.join("; "), true);
          studio.last = "";
          return;
        }
        decide("admit", rid, c.letter, { still: st.still });
      }).catch(function (e) { note({ ok: false, code: "NO STILL", message: String(e && e.message || e) }, ""); });
    };
    $("st-ask").onclick = ask;
    $("st-cancel").onclick = function () { if (studio.req) post("/studio/cancel", { id: studio.req.id }).then(function (r) { note({ ok: true }, r.ok ? "cancelled" : "nothing to cancel"); }); };
    $("st-original").onclick = function () { pick(0); };
    const undo = function () { post("/studio/undo", {}).then(function (r) { note(r, "undone: ledger #" + (r.ledger || []).join(", #")); toast(r.ok ? "Undone · ledger #" + (r.ledger || []).join(", #") : (r.code || "") + " " + (r.message || ""), !r.ok); if (r.ok) pick(0); ui.histKey = ""; }); };
    $("st-undo").onclick = undo;
    const studioShow = function (st) {
      if (!st) return;
      const key = JSON.stringify([st, cur.k]);
      if (key === studio.last) return;
      studio.last = key;
      if (st.refs) setRefs(st.refs);
      const pv = st.provider || {};
      studio.provider = pv;
      $("st-provider").textContent = pv.configured ? "provider: " + pv.model + " (" + pv.config + ")" : "no director: " + (pv.error || "play.py was started without --director");
      $("st-ask").disabled = !pv.configured;
      const r = st.request;
      studio.req = r;
      if (st.last && st.last.what && JSON.stringify(st.last) !== studio.lastDecision) { studio.lastDecision = JSON.stringify(st.last); ui.histKey = ""; }
      $("st-cancel").disabled = !(r && r.state === "running");
      const box = $("st-cands");
      box.innerHTML = "";
      if (r) {
        const head = document.createElement("div");
        head.className = r.state === "failed" ? "bad" : "dim";
        head.textContent = "request " + r.id + ": " + r.state + (r.message ? " — " + (r.code ? r.code + ": " : "") + r.message : "") + "  (" + Math.round(r.elapsed_ms / 100) / 10 + " s)";
        box.appendChild(head);
        // 0220: why there are no candidates, when there are none; the model's words shown as text, never carried out
        const d = r.disposition;
        if (d && d.kind !== "REALIZED") {
          const e = document.createElement("div");
          e.className = "disp " + (d.kind === "FAILED" ? "bad" : "dim");
          const k = document.createElement("div");
          k.textContent = d.kind + " · decided by " + (d.decided_by === "host" ? "the studio" : "the provider (its own account)");
          e.appendChild(k);
          if (d.unmet && d.unmet.length) { const u = document.createElement("div"); u.textContent = "not made yet: " + d.unmet.join(", "); e.appendChild(u); }
          if (d.questions && d.questions.length) {
            for (const qq of d.questions) { const q2 = document.createElement("div"); q2.className = "q"; q2.textContent = "? " + qq; e.appendChild(q2); }
          }
          if (d.note) { const n = document.createElement("div"); n.className = "dim"; n.textContent = d.note; e.appendChild(n); }
          box.appendChild(e);
        }
        for (const c of r.candidates || []) {
          const e = document.createElement("div");
          e.className = "cand" + (c.slot !== null && c.slot === cur.k ? " shown" : "");
          const t = document.createElement("div");
          t.textContent = c.letter + " · " + c.title + " · " + (c.verdict || "?") + (c.codes && c.codes.length ? " " + c.codes.join(",") : "") + (c.decided ? " · " + c.decided : "");
          t.className = c.verdict === "CLEAN" ? "good" : c.verdict === "REFUSED" ? "bad" : "";
          e.appendChild(t);
          if (c.message) { const m = document.createElement("div"); m.className = "dim"; m.textContent = c.message.slice(0, 300); e.appendChild(m); }
          if (c.touches) {
            const tt = c.touches, m = document.createElement("div"), parts = [];
            for (const tag of Object.keys(tt.tags).sort()) parts.push(tag + " " + tt.tags[tag]);
            parts.push(tt.others_count ? tt.others_count + " other object" + (tt.others_count === 1 ? "" : "s") + " changed (" + tt.others.slice(0, 3).join(", ") + (tt.others_count > 3 ? ", …" : "") + ")" : "no other object changed");
            if (tt.added_count) parts.push(tt.added_count + " new (" + tt.added.slice(0, 3).join(", ") + (tt.added_count > 3 ? ", …" : "") + ")");
            m.className = tt.others_count ? "bad" : "dim"; m.textContent = "touches: " + parts.join(" · "); e.appendChild(m);
          }
          const btn = function (lab, fn, on) { const b = document.createElement("button"); b.textContent = lab; b.disabled = !on; b.onclick = fn; e.appendChild(b); };
          // ADMISSION-0 (0222): the rung the host computed, what an admission needs, what was not checked, and the still
          if (c.record) {
            const rr = document.createElement("div");
            rr.className = "dim";
            rr.textContent = "rung " + c.record.rung + " (computed by the studio from what changed) · an admission needs: " + c.record.requires.join("; ");
            e.appendChild(rr);
            const nc = document.createElement("details"), sm = document.createElement("summary");
            sm.textContent = "not checked (" + c.record.not_checked.length + ")";
            nc.appendChild(sm);
            for (const x of c.record.not_checked) { const li = document.createElement("div"); li.className = "dim"; li.textContent = "· " + x; nc.appendChild(li); }
            e.appendChild(nc);
          }
          if (c.still) {
            const sv = document.createElement("div");
            sv.className = c.still.flags.length ? "bad" : "dim";
            sv.textContent = "still " + c.still.sha256.slice(0, 12) + ": " + (c.still.flags.length ? c.still.flags.join("; ") : "the detectors flag nothing (they prove nothing either)");
            e.appendChild(sv);
          }
          const flagged = !!(c.still && c.still.flags.length);
          btn("Show", function () { pick(c.slot); }, c.slot !== null);
          btn("Admit", function () { admitWithStill(r.id, c); }, admissible(c));
          if (flagged) btn("Admit despite: " + c.still.flags.map(function (f) { return f.split(":")[0]; }).join(", "),
            function () { decide("admit", r.id, c.letter, { still: c.still.sha256, despite: true }); }, c.slot !== null && c.verdict === "CLEAN" && !c.decided);
          btn("Reject", function () { decide("reject", r.id, c.letter); }, !c.decided);
          box.appendChild(e);
        }
      }
      if (st.last && st.last.what) {
        const l = document.createElement("div"); l.className = "dim";
        l.textContent = "last: " + st.last.what + (st.last.candidate ? " " + st.last.candidate : "") + (st.last.of ? " of #" + st.last.of : "") + (st.last.ledger ? " (ledger #" + st.last.ledger.join(", #") + ")" : "");
        box.appendChild(l);
      }
      shell.candidates();
    };
    const admissible = function (c) { return c.slot !== null && c.verdict === "CLEAN" && !c.decided && (!c.record || c.record.rung === "A"); };

    // ---------------------------------------------------------------- STUDIO-2: the worlds, the queue, the toasts
    const go = function (wname, extra) { location.href = "/play.html?world=" + encodeURIComponent(wname) + (extra || ""); };
    let worldsKey = "", worlds = [];
    const worldsShow = function (ws) {
      if (!ws) return;
      const key = JSON.stringify(ws);
      if (key === worldsKey) return;
      worldsKey = key; worlds = ws;
      for (const id of ["st-world", "st-qworld", "cx-scene"]) {
        const sel = $(id), was = sel.value;
        sel.innerHTML = "";
        for (const w of ws) {
          const o = document.createElement("option");
          o.value = w.world; o.textContent = w.world + (id !== "st-qworld" && w.title ? " — " + w.title.slice(0, 40) : "");
          if (id !== "st-qworld" ? w.world === brief : (was ? w.world === was : w.world === brief)) o.selected = true;
          sel.appendChild(o);
        }
      }
    };
    $("st-world").onchange = function () { const v = $("st-world").value; if (v && v !== brief) go(v); };
    $("cx-scene").onchange = function () { const v = $("cx-scene").value; if (v && v !== brief) go(v); };
    $("st-dup").onclick = function () {
      const name = $("st-newname").value.trim();
      post("/studio/worlds/duplicate", { from: brief, name: name }).then(function (r) { note(r, "made world " + (r.world || "")); if (r.ok) go(r.world); });
    };
    let queueKey = "", seenNotice = performance.timeOrigin / 1000, optsKey = "";
    toast = function (text, bad) {
      const e = document.createElement("div");
      e.textContent = text; if (bad) e.className = "bad";
      $("toasts").appendChild(e);
      setTimeout(function () { e.remove(); }, 8000);
    };
    const queueOpts = function (qs) {
      const key = JSON.stringify([qs.providers, qs.models]);
      if (key === optsKey) return;
      optsKey = key;
      const ps = $("st-qprov"), ms = $("st-qmodel");
      ps.innerHTML = ""; ms.innerHTML = "";
      for (const p of qs.providers || []) { const o = document.createElement("option"); o.value = p.file; o.textContent = p.file.replace(/\.json$/, ""); o.title = p.label; ps.appendChild(o); }
      for (const m of qs.models || []) { const o = document.createElement("option"); o.value = m; o.textContent = m || "the configuration's model"; ms.appendChild(o); }
      const pv = (studio.provider || {}).config || "";
      for (const o of ps.options) if (pv && pv.endsWith(o.value)) o.selected = true;
    };
    const review = function (t) {
      if (t.world !== brief) { go(t.world, "&review=" + encodeURIComponent(t.id)); return; }
      post("/studio/queue/review", { id: t.id }).then(function (r) { note(r, "reviewing " + t.id + (r.drawn_again ? ": drawn again at the head as it is now" : "")); openPanel(); studio.last = ""; });
    };
    const queueShow = function (qs) {
      if (!qs) return;
      queueOpts(qs);
      for (const n of qs.notices || []) {
        if (n[0] > seenNotice) { seenNotice = n[0]; toast(n[1] + (n[4] === "ready" ? "  (review it in the queue)" : ""), n[4] !== "ready" && n[4] !== "answered"); }
      }
      const key = JSON.stringify(qs.tasks);
      if (key === queueKey) return;
      queueKey = key;
      const box = $("st-qlist");
      box.innerHTML = "";
      const c = qs.counts || {};
      const head = document.createElement("div"); head.className = "dim";
      head.textContent = (c.running || 0) + " running, " + (c.queued || 0) + " queued, " + (c.ready || 0) + " ready, " + (c.answered || 0) + " answered  ·  at most " + qs.concurrency + " at once, one per world";
      box.appendChild(head);
      for (const t of qs.tasks || []) {
        const e = document.createElement("div");
        e.className = "task " + t.status;
        const st = document.createElement("span"); st.className = "st"; st.textContent = t.status + (t.stale ? " (stale)" : "");
        e.appendChild(st);
        const u = t.usage || null;
        const cost = u ? (u.cost_usd !== null && u.cost_usd !== undefined ? "  $" + Number(u.cost_usd).toFixed(4) : "  " + (u.input_tokens || 0) + "+" + (u.output_tokens || 0) + " tokens") : "";
        e.appendChild(document.createTextNode(" " + t.world + " · " + t.prompt.slice(0, 48) + " · " + (t.model || t.provider.replace(/\.json$/, "")) + cost
          + (t.message && t.status !== "queued" ? " — " + (t.code ? t.code + ": " : "") + t.message.slice(0, 90) : "")));
        const btn = function (lab, fn) { const b = document.createElement("button"); b.textContent = lab; b.onclick = fn; e.appendChild(b); };
        if (t.status === "queued" || t.status === "running") btn("Cancel", function () { post("/studio/queue/cancel", { id: t.id }).then(function (r) { note(r, "cancelled " + t.id); }); });
        if (t.status === "ready") { btn("Review", function () { review(t); }); btn("Set aside", function () { post("/studio/queue/dismiss", { id: t.id }).then(function (r) { note(r, "set aside " + t.id); }); }); }
        if (t.status === "answered") btn("Set aside", function () { post("/studio/queue/dismiss", { id: t.id }).then(function (r) { note(r, "set aside " + t.id); }); });
        if (t.status === "answered" || t.status === "failed" || t.status === "cancelled" || t.status === "interrupted") btn("Queue again", function () { post("/studio/queue/requeue", { id: t.id }).then(function (r) { note(r, "queued again " + t.id); }); });
        box.appendChild(e);
      }
    };
    $("st-queue").onclick = function () {
      const w = $("st-qworld").value || brief;
      post("/studio/queue/add", { world: w, prompt: promptEl.value, provider: $("st-qprov").value, model: $("st-qmodel").value,
                                  camera: w === brief ? camNow() : null })
        .then(function (r) { note(r, "queued " + (r.id || "") + " for " + w + " (its target and pins as they stand there); play on, it runs in the background"); });
    };

    // ================================================================ the shell (STUDIO-3, 0230)
    const NOT_BUILT = {
      geometry: "Not built. The layout (walls, floors, cover) changes through the design tool (design/design.py), outside the studio; a geometry tool here comes later.",
      voxel: "Not built. The world is cells and boxes; there is no voxel representation to edit.",
      decals: "Not built. The art language has no decal statement yet.",
      audio: "Not built. The studio cannot make audio yet (the director's capabilities list it as unsupported).",
      ai: "Not built. There is no AI in the world yet; the spawns and targets are the map's (shown).",
      prefabs: "Not built. Every object is made by one statement of the brief; there is no prefab statement.",
      procedural: "Not built. World generation is a later slice of the roadmap.",
      templates: "Not built. A new world is a duplicate of one (the director's drawer, Duplicate).",
      compare: "Not built yet: a split view of the current scene and a candidate comes with Mark & Shape (the roadmap's next sprint).",
      move: "Not built. Nothing in the editor moves the world: it changes through a proposal the host checks and a person admits.",
      mark: "Not built yet: marking a surface and drawing a shape on it is the roadmap's next sprint (Mark & Shape).",
    };
    const nb = function (k) { toast(NOT_BUILT[k] || "Not built.", true); };
    const menus = {}, closeMenus = function () { document.querySelectorAll(".menu.open, .pillmenu.open").forEach(function (m) { m.classList.remove("open"); }); };
    document.addEventListener("mousedown", function (e) { if (!e.target.closest(".menu, .pillmenu")) closeMenus(); });
    // a drop-down: items are [label, fn, {key, on, disabled, nb}] or "-"
    const dropdown = function (items) {
      const d = el("div.drop");
      for (const it of (typeof items === "function" ? items() : items)) {
        if (it === "-") { d.appendChild(el("hr")); continue; }
        const o = it[2] || {};
        d.appendChild(el("button" + (o.on ? ".on" : ""), { disabled: !!o.disabled, title: o.title || "", onclick: function () { closeMenus(); it[1](); } },
          o.icon ? icon(o.icon) : null, it[0], o.key ? el("kbd", {}, o.key) : o.nb ? el("span.nb", {}, "not built") : null));
      }
      return d;
    };
    const menu = function (host, cls, labelNode, items) {
      const m = el("div." + cls), b = el("button" + (cls === "pillmenu" ? ".btn" : ""), {}, labelNode);
      m.appendChild(b);
      b.addEventListener("click", function () {
        const open = m.classList.contains("open");
        closeMenus();
        if (!open) { const old = m.querySelector(".drop"); if (old) old.remove(); m.appendChild(dropdown(items)); m.classList.add("open"); }
      });
      host.appendChild(m);
      return m;
    };
    const stillDownload = function () {
      const a = el("a", { download: brief + "-" + cur.sha.slice(0, 12) + ".png", href: canvas.toDataURL("image/png") });
      document.body.appendChild(a); a.click(); a.remove();
    };
    const copy = function (text, what) {
      const done = function () { toast("Copied " + what + ": " + text); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, function () { toast(text); });
      else toast(text);
    };
    const viewStatement = function (c, name) {
      // the art language's view statement: a cell, a yaw and a pitch (art/README.md); the eye is the player's
      return "view " + (name || "saved-" + (ui.saved.length + 1)) + " " + Math.floor(c.x / S.grid.cell) + "," + Math.floor(c.z / S.grid.cell) + " " + Math.round(((c.yaw / deg) % 360 + 360) % 360) + " " + Math.round(c.pitch / deg);
    };

    // ---- the editor's camera, the play mode
    const lockOK = function () { return document.pointerLockElement === canvas; };
    const enterPlay = function (full) {
      closeMenus();
      ui.mode = "play"; label = "play"; ui.measure = [];
      document.body.classList.toggle("playfull", !!full);
      $("overlay").style.display = "none";
      try { const p = canvas.requestPointerLock(); if (p && p.catch) p.catch(function () { if (ui.mode === "play") $("overlay").style.display = "flex"; }); } catch (e) { $("overlay").style.display = "flex"; }
      shell.chrome();
    };
    const leavePlay = function () {
      if (ui.mode !== "play") return;
      ui.mode = "edit"; label = "editor";
      ecam = Object.assign(eyeOf(s), { fov: ecam.fov || 66 });
      document.body.classList.remove("playfull");
      $("overlay").style.display = "none";
      if (lockOK()) document.exitPointerLock();
      shell.chrome();
    };
    const frameSelection = function () {
      const b = objectBox(ui.sel);
      if (!b) { toast("Nothing selected to frame", true); return; }
      if (ui.mode === "play") leavePlay();
      ecam = U.frameCam(b, 66); label = "framed " + nameOf(ui.sel);
    };
    const overviewCam = function () {
      const g = S.grid, cx = g.w * g.cell / 2, cz = g.h * g.cell / 2;
      return { x: cx, y: Math.max(g.w, g.h) * g.cell * 0.62, z: cz + g.h * g.cell * 0.62, yaw: 0, pitch: -46 * deg, fov: 66 };
    };
    const projection = function (kind) {
      // the renderer draws in perspective only: Top and Side are telephoto cameras, near-orthographic, and say so
      if (ui.mode === "play") leavePlay();
      const g = S.grid, cx = g.w * g.cell / 2, cz = g.h * g.cell / 2;
      const b = ui.sel && objectBox(ui.sel), tx = b ? (b[0] + b[3]) / 2 : cx, tz = b ? (b[2] + b[5]) / 2 : cz, ty = b ? (b[1] + b[4]) / 2 : 2;
      if (kind === "top") ecam = { x: tx, y: 420, z: tz + 0.001, yaw: 0, pitch: -89.6 * deg, fov: b ? 4 : 14 };
      else if (kind === "side") ecam = { x: tx + 420, y: ty, z: tz, yaw: -90 * deg, pitch: 0, fov: b ? 3 : 12 };
      else ecam = Object.assign({}, ecam, { fov: 66 }, ecam.y > 100 || Math.abs(ecam.x - tx) > 200 ? (b ? U.frameCam(b, 66) : overviewCam()) : {});
      ui.projection = kind; label = kind === "perspective" ? "editor" : kind + " (telephoto)";
    };
    ui.projection = "perspective";

    // ---- the menu bar
    const shell = {};
    const buildMenus = function () {
      const host = $("menus");
      host.innerHTML = "";
      $("brand").prepend(icon("logo"));
      const M = function (name, items) { menus[name] = menu(host, "menu", name, items); };
      M("File", function () { return [
        ["Open world…", function () { $("cx-scene").focus(); }, { icon: "globe" }],
        ["Duplicate world…", function () { openPanel(); $("st-newname").focus(); }, { icon: "template" }],
        "-",
        ["Launcher", function () { location.href = "/start.html"; }, { icon: "overview" }],
        ["History view", function () { location.href = "/history.html?world=" + W; }, { icon: "history" }],
        "-",
        ["Save a still of the viewport (PNG)", stillDownload, { icon: "camera" }],
        ["Reload the page", function () { location.reload(); }, { key: "F5", icon: "refresh" }],
      ]; });
      M("Edit", function () { return [
        ["Select none", function () { setSel(null); }, { key: "Esc" }],
        ["Make the selection the target", select, { key: "E", disabled: !subject() }],
        ["Pin the selection as a reference", pin, { key: "R", disabled: !subject() }],
        "-",
        ["Copy the selection's address", function () { copy(nameOf(ui.sel), "the address"); }, { disabled: !ui.sel }],
        ["Copy the camera as a view statement", function () { copy(viewStatement(eye()), "a view statement"); }],
      ]; });
      M("View", function () { return [
        ["Perspective", function () { projection("perspective"); }, { on: ui.projection === "perspective" }],
        ["Top (telephoto)", function () { projection("top"); }, { on: ui.projection === "top" }],
        ["Side (telephoto)", function () { projection("side"); }, { on: ui.projection === "side" }],
        "-",
        ["Frame the selection", frameSelection, { key: "F", disabled: !ui.sel }],
        ["Overview", function () { if (ui.mode === "play") leavePlay(); ecam = overviewCam(); label = "overview"; }],
        "-",
        ["Grid", function () { ui.show.grid = !ui.show.grid; }, { on: ui.show.grid }],
        ["Regions", function () { ui.show.regions = !ui.show.regions; }, { on: ui.show.regions }],
        ["Spawns and targets", function () { ui.show.spawns = !ui.show.spawns; }, { on: ui.show.spawns }],
        ["Tags", function () { ui.show.tags = !ui.show.tags; }, { on: ui.show.tags }],
        ["Statistics", function () { ui.show.stats = !ui.show.stats; $("stats").style.display = ui.show.stats ? "" : "none"; }, { on: ui.show.stats }],
      ]; });
      M("World", function () { return [
        ["Overview", function () { navGo("overview"); }, { icon: "overview" }],
        ["World settings", function () { setTab("world"); }, { icon: "globe" }],
        ["Layers", function () { setTab("layers"); }, { icon: "layers" }],
        "-",
      ].concat(views.map(function (v, i) { return ["View " + v, function () { goView(v); }, { key: String(i + 1), icon: "bookmark" }]; })).concat([
        "-", ["Save the camera as a view", saveView, { icon: "camera" }]]); });
      M("Tools", function () { return [
        ["Select", function () { setTool("select"); }, { key: "Q", on: ui.tool === "select", icon: "select" }],
        ["Measure", function () { setTool("measure"); }, { key: "T", on: ui.tool === "measure", icon: "ruler" }],
        ["Move, rotate, scale", function () { nb("move"); }, { nb: true, icon: "move", title: NOT_BUILT.move }],
        ["Mark & Shape", function () { nb("mark"); }, { nb: true, icon: "shape", title: NOT_BUILT.mark }],
        "-",
        ["Director…", openPanel, { key: "Enter", icon: "wand" }],
      ]; });
      M("Build", function () { return [
        ["Build now (every source of this world)", buildNow, { icon: "hammer" }],
        "-",
      ].concat(cur.slots.map(function (sl, k) { return ["[" + k + "] " + (sl.label || "").slice(0, 52), function () { if (sl.served) pick(k); }, { on: k === cur.k, disabled: !sl.served }]; })).concat([
        "-", ["Previous source", function () { step(-1); }, { key: "[" }], ["Next source", function () { step(1); }, { key: "]" }]]); });
      M("Play", function () { return [
        ["Play", function () { enterPlay(false); }, { key: "P", icon: "play" }],
        ["Play (1080p)", function () { enterPlay(true); }, { icon: "play" }],
        "-",
        ["Reset the game", function () { pending.reset = true; }, { key: "⌫" }],
        [paused ? "Resume the game" : "Pause the game", function () { paused = !paused; }],
      ]; });
      M("Validate", function () { return [
        ["Validate this source", validate, { icon: "shield" }],
        ["History and ledger", function () { location.href = "/history.html?world=" + W; }, { icon: "book" }],
      ]; });
      M("Help", function () { return [
        ["Keys", keysHelp, { key: "?" }],
        ["About this page", about],
      ]; });
      // the right of the bar: the source built and served, play at 1080p, validate
      const right = $("bar-right");
      right.innerHTML = "";
      const srcLabel = el("span.mono", { id: "mb-src" });
      menu(right, "pillmenu", el("span", {}, icon("hammer"), " Local Build ", srcLabel, " ", icon("chevron")), function () {
        return [["Build now", buildNow, { icon: "refresh" }], "-"].concat(cur.slots.map(function (sl, k) {
          return ["[" + k + "] " + (sl.ok ? "✓ " : "✗ ") + (sl.label || "").slice(0, 46), function () { if (sl.served) pick(k); }, { on: k === cur.k, disabled: !sl.served }];
        }));
      });
      right.appendChild(el("button.btn.primary#mb-play", { title: "Play at 1920 × 1080, the window filled (Esc returns to the editor)", onclick: function () { enterPlay(true); } }, icon("play"), "Play (1080p)"));
      right.appendChild(el("button.btn#mb-validate", { title: "The art checks as they were run for this source", onclick: validate }, icon("shield"), "Validate"));
    };

    // ---- the left navigator
    const NAV = [
      ["World", [["overview", "Overview", "overview"], ["layers", "Layers", "layers"], ["bookmarks", "Bookmarks", "bookmark"], ["saved", "Saved Views", "camera"]]],
      ["Create", [["geometry", "Geometry", "cube", true], ["voxel", "Voxel Tools", "voxel", true], ["paint", "Paint / Materials", "brush"], ["decals", "Decals", "decal", true],
                  ["lights", "Lights", "bulb"], ["audio", "Audio", "audio", true], ["gameplay", "Gameplay", "gamepad"], ["ai", "AI / Spawns", "agent"], ["volumes", "Volumes", "volume"]]],
      ["Content", [["assets", "Asset Browser", "folder"], ["materials", "Materials", "sphere"], ["prefabs", "Prefabs", "prefab", true], ["scenes", "Scenes", "map"],
                   ["procedural", "Procedural", "sparkle", true], ["templates", "Templates", "template", true]]],
      ["Review", [["candidates", "Candidates", "candidates"], ["compare", "Compare", "compare", true], ["history", "History / Ledger", "history"], ["validation", "Validation", "shield"]]],
    ];
    const buildNav = function () {
      const host = $("leftnav");
      host.innerHTML = "";
      for (const [title, items] of NAV) {
        const sec = el("div.navsec", {}, el("h4", {}, title));
        for (const [id, lab, ic, notBuilt] of items) {
          sec.appendChild(el("button.navit" + (notBuilt ? ".notbuilt" : ""), { dataset: { nav: id }, title: notBuilt ? NOT_BUILT[id] : "", onclick: function () { navGo(id); } },
            icon(ic), lab, notBuilt ? el("span.nb", {}, "not built") : el("span.count", { dataset: { count: id } })));
        }
        host.appendChild(sec);
      }
    };
    const navGo = function (id) {
      ui.nav = id;
      document.querySelectorAll(".navit").forEach(function (b) { b.classList.toggle("active", b.dataset.nav === id); });
      const flash = function (pid) { const p = $(pid); p.animate([{ boxShadow: "inset 0 0 0 2px #4d8dff" }, { boxShadow: "inset 0 0 0 0 transparent" }], 900); };
      if (NOT_BUILT[id]) { nb(id); return; }
      if (id === "overview") { setTab("world"); if (ui.mode === "play") leavePlay(); ecam = overviewCam(); label = "overview"; }
      else if (id === "layers") setTab("layers");
      else if (id === "bookmarks") { setFolder("views"); flash("assets"); }
      else if (id === "saved") { setFolder("saved"); flash("assets"); }
      else if (id === "paint" || id === "materials") { setFolder("materials"); flash("assets"); }
      else if (id === "lights") { setFolder("lights"); flash("assets"); }
      else if (id === "gameplay") { setFolder("movers"); flash("assets"); }
      else if (id === "ai") { ui.show.spawns = true; setFolder("spawns"); flash("assets"); }
      else if (id === "volumes") { ui.show.regions = true; setFolder("regions"); flash("assets"); }
      else if (id === "assets") flash("assets");
      else if (id === "scenes") worldsModal();
      else if (id === "candidates") { flash("cands"); if (!studio.req) openPanel(); }
      else if (id === "history") { flash("ledger"); ui.histKey = ""; }
      else if (id === "validation") validate();
    };

    // ---- the viewport's tools, pills and statistics
    const setTool = function (t) {
      ui.tool = t; ui.measure = [];
      document.querySelectorAll("#tools button").forEach(function (b) { b.classList.toggle("active", b.dataset.tool === t); });
      vp.classList.toggle("pick", t === "measure");
    };
    const buildTools = function () {
      const host = $("tools");
      host.innerHTML = "";
      const T = function (id, ic, title, fn, disabled) {
        host.appendChild(el("button", { dataset: { tool: id }, title: title, disabled: !!disabled, onclick: fn || function () { setTool(id); } }, icon(ic)));
      };
      T("select", "select", "Select (Q): click what to inspect");
      T("move", "move", NOT_BUILT.move, null, true);
      T("rotate", "rotate", NOT_BUILT.move, null, true);
      T("scale", "scale", NOT_BUILT.move, null, true);
      host.appendChild(el("hr"));
      T("measure", "ruler", "Measure (T): click two points; the distance between them, in metres");
      T("mark", "shape", NOT_BUILT.mark, null, true);
      host.appendChild(el("hr"));
      T("frame", "focus", "Frame the selection (F)", frameSelection);
      T("play", "play", "Play (P): the mouse is captured; Esc returns here", function () { enterPlay(false); });
      setTool(ui.tool);
    };
    const buildPills = function () {
      const host = $("pills");
      host.innerHTML = "";
      const pill = function (lab, items) {
        const m = el("div.pillmenu"), b = el("button.pill", {}, lab, icon("chevron"));
        m.appendChild(b);
        b.addEventListener("click", function () {
          const open = m.classList.contains("open");
          closeMenus();
          if (!open) { const old = m.querySelector(".drop"); if (old) old.remove(); m.appendChild(dropdown(items)); m.classList.add("open"); }
        });
        host.appendChild(m);
      };
      pill(el("span", { id: "pl-proj" }, "Perspective"), function () { return [
        ["Perspective", function () { projection("perspective"); }, { on: ui.projection === "perspective" }],
        ["Top (telephoto, not orthographic)", function () { projection("top"); }, { on: ui.projection === "top" }],
        ["Side (telephoto, not orthographic)", function () { projection("side"); }, { on: ui.projection === "side" }],
      ]; });
      pill(el("span", { id: "pl-lit" }, "Lit"), function () { return [
        ["Lit (as the renderer draws it)", function () { ui.show.wire = false; ui.show.collision = false; }, { on: !ui.show.wire && !ui.show.collision }],
        ["Lit + wireframe of the dressing", function () { ui.show.wire = !ui.show.wire; }, { on: ui.show.wire }],
        ["Lit + the play geometry (C)", function () { ui.show.collision = !ui.show.collision; }, { on: ui.show.collision }],
        ["Rain", function () { ui.show.rain = !ui.show.rain; R.load(viewScene(S)); }, { on: ui.show.rain }],
      ]; });
      pill("Show", function () { return [
        ["Grid (cells)", function () { ui.show.grid = !ui.show.grid; }, { on: ui.show.grid }],
        ["Regions", function () { ui.show.regions = !ui.show.regions; }, { on: ui.show.regions }],
        ["Spawns and targets", function () { ui.show.spawns = !ui.show.spawns; }, { on: ui.show.spawns }],
        ["Tags", function () { ui.show.tags = !ui.show.tags; }, { on: ui.show.tags }],
        ["Statistics", function () { ui.show.stats = !ui.show.stats; $("stats").style.display = ui.show.stats ? "" : "none"; }, { on: ui.show.stats }],
      ]; });
    };
    const statsShow = function (now) {
      if (now - ui.statsAt < 400) return;
      const dt = (now - ui.statsAt) / 1000;
      ui.fps = ui.frames / Math.max(dt, 1e-3); ui.frames = 0; ui.statsAt = now;
      const tris = (R.triangles || 0) + Math.round((R.nDyn || 0) / 3);
      const rows = [["FPS", ui.fps.toFixed(0)], ["Frame", ui.frameMs.toFixed(1) + " ms"], ["CPU submit", ui.cpuMs.toFixed(1) + " ms"], ["Draw calls", String(ui.callsShown)],
        ["Tris", tris.toLocaleString("en")], ["Boxes", (S.visuals.length + S.collision.length).toLocaleString("en")], ["Lights", String(R.nl || 0)],
        ["Res", canvas.width + "×" + canvas.height], ["VRAM", "n/a"]];
      const host = $("stats");
      host.innerHTML = "";
      for (const [k, v] of rows) host.append(el("span", { title: k === "VRAM" ? "not measured: WebGL does not report the memory it uses" : k === "CPU submit" ? "the time to issue the frame's work, measured; the GPU's time is not" : "" }, k), el("span", {}, v));
    };

    // ---- the context bar and the roadmap
    const chips = function () {
      const host = $("cx-chips");
      host.innerHTML = "";
      const insp = ui.history && ui.history.inspect;
      const sv = (cur.slots[cur.k] || {}).served || {};
      host.append(
        el("span.chip" + (ui.connected ? ".on" : ".off"), { title: ui.connected ? "play.py answers" : "play.py does not answer" }, icon("dot"), ui.connected ? "Connected" : "Disconnected"), " ",
        el("span.chip", {}, "World ", el("b", {}, brief)), " ",
        el("span.chip", { title: insp ? "the ledger's head " + (insp.head || "") + (insp.verified ? ", verified (integrity, not truth)" : "") : "the ledger is read with the history" },
          "Revision ", el("b", {}, insp ? "#" + insp.events + (insp.head ? " · " + insp.head.slice(0, 8) : "") : "—")), " ",
        el("span.chip", { title: "the source drawn and its scene's digest" }, "Source ", el("b", {}, "[" + cur.k + "] " + cur.sha.slice(0, 8)), sv.verdict ? " " + sv.verdict : ""), " ",
        el("span.chip", { title: "the simulation's rules (graybox/RULES-3.md)" }, "Rules ", el("b", {}, String(Sim.RULES))));
      $("mb-src").textContent = "[" + cur.k + "]";
    };
    const ROADMAP = [["done", "Sprint 1", "Core studio shell"], ["next", "Sprint 2", "Mark & Shape"], ["next", "Sprint 3", "Candidate loop"],
                     ["next", "Sprint 4", "World generation slice"], ["next", "Sprint 5", "Dynamic world"], ["next", "Sprint 6", "Scale"]];
    const buildRoadmap = function () {
      const host = $("roadmap");
      host.innerHTML = "";
      host.appendChild(el("span.sp", { title: "the product's road, as the owner's plan of 2026-10-14 lays it out" }, el("b", {}, "Roadmap")));
      for (const [st, n, t] of ROADMAP) host.appendChild(el("span.sp." + st, { title: st === "done" ? "built" : "not built yet" }, el("b", {}, n), t));
      host.appendChild(el("span.spacer"));
      host.appendChild(el("span", { id: "rm-note", class: "faint" }, "The director proposes, the host validates, a person admits."));
    };
    shell.chrome = function () {
      $("hint").style.display = ui.mode === "edit" ? "" : "none";
      $("cross").style.display = ui.mode === "play" ? "block" : "none";
      $("hud").style.display = ui.mode === "play" ? "" : "none";
    };

    // ---- the selection and the inspector
    let infoReq = 0;
    const setSel = function (piece) {
      ui.sel = piece; ui.info = null; ui.infoErr = "";
      $("cx-sel").textContent = piece ? nameOf(piece) : "none";
      if (piece) {
        const n = ++infoReq;
        getJSON("/object.json?world=" + W + "&slot=" + cur.k + "&piece=" + encodeURIComponent(piece)).then(function (d) {
          if (n !== infoReq) return;
          if (d.ok) ui.info = d; else ui.infoErr = (d.code || "") + ": " + (d.message || "");
          shell.inspector();
        }).catch(function (e) { if (n === infoReq) { ui.infoErr = String(e && e.message || e); shell.inspector(); } });
      }
      if (ui.rtab !== "inspector") setTab("inspector"); else shell.inspector();
      document.querySelectorAll(".tile").forEach(function (t) { t.classList.toggle("active", t.dataset.piece === piece); });
    };
    const setTab = function (t) {
      ui.rtab = t;
      document.querySelectorAll("#rtabs button").forEach(function (b) { b.classList.toggle("active", b.dataset.tab === t); });
      if (t === "inspector") shell.inspector(); else if (t === "layers") shell.layers(); else shell.worldSettings();
    };
    const buildTabs = function () {
      const host = $("rtabs");
      host.innerHTML = "";
      for (const [id, lab] of [["inspector", "Inspector"], ["layers", "Layers"], ["world", "World Settings"]]) {
        host.appendChild(el("button", { dataset: { tab: id }, onclick: function () { setTab(id); } }, lab));
      }
    };
    const sec = function (title, open, right, body) {
      const d = el("details.sec", { open: !!open }, el("summary", {}, icon("chevron", "chev"), title, right ? el("span.r", {}, right) : null), el("div.in", {}, body));
      return d;
    };
    const kv = function (rows) { const g = el("div.kv"); for (const [k, v] of rows) g.append(el("span", {}, k), v instanceof Node ? v : el("span", {}, v)); return g; };
    const xyz = function (a) { return el("div.xyz", {}, a.map(function (v) { return el("span", {}, (Math.round(v * 1000) / 1000).toFixed(3)); })); };
    const rgb = function (c) { return c ? c.join(", ") : "-"; };
    shell.inspector = function () {
      if (ui.rtab !== "inspector") return;
      const host = $("rbody");
      host.innerHTML = "";
      if (!ui.sel) {
        host.appendChild(el("div.empty", {}, el("p", {}, "Nothing selected."), el("p.dim", {}, "Click what you want to inspect in the viewport, or a tile of the asset browser. Right-drag looks around; with the right button held, W A S D fly (Q, E down and up); the wheel moves forward."),
          el("p.dim", {}, "P plays: the mouse is captured, the game's keys apply; Esc returns here, at the player's eye.")));
        return;
      }
      const d = ui.info;
      if (!d) { host.appendChild(el("div.empty", {}, ui.infoErr ? el("span.bad", {}, ui.infoErr) : "Reading " + nameOf(ui.sel) + "…")); return; }
      const g = d.geometry || {}, b = g.bounds_m || objectBox(ui.sel) || [0, 0, 0, 0, 0, 0];
      const tag = knownTag(d.object) || "", role = studio.refs.target && tagOf(d.object) === studio.refs.target ? "target" : tagOf(d.object) ? "pin" : "";
      host.appendChild(el("div.ihead", {}, el("div.t", {}, d.address),
        el("div.s", {}, el("span.badge.neutral", {}, d.kind), el("span", {}, "layer " + d.layer), d.region ? el("span", {}, "· region " + d.region) : null,
          tag ? el("span.badge." + (role ? "candidate" : "neutral"), { title: "the studio's tag for this object" }, tag + (role ? " " + role : "")) : null)));
      const art = !/^(play|mover|target)$/.test(d.layer) && d.kind !== "target";
      const acts = el("div.acts", { style: { padding: "8px 12px", borderBottom: "1px solid var(--line)" } },
        el("button.btn.small", { onclick: frameSelection, title: "F" }, icon("focus"), "Frame"),
        art ? el("button.btn.small", { onclick: select, title: "E: the director's target" }, icon("point"), role === "target" ? "Target ✓" : "Make target") : null,
        art ? el("button.btn.small", { onclick: pin, title: "R: a reference the director keeps as it is" }, icon("bookmark"), role === "pin" ? "Unpin" : "Pin") : null,
        art ? el("button.btn.small", { onclick: function () { (role === "target" ? Promise.resolve() : select()).then(openPanel); }, title: "Make it the target and open the director" }, icon("wand"), "Ask…") : null);
      host.appendChild(acts);
      // Transform: the boxes' extent; nothing in the scene is rotated
      host.appendChild(sec("Transform", true, "read-only", [
        kv([["Location", xyz(g.centre_m || [(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2])], ["Rotation", xyz([0, 0, 0])], ["Size", xyz(g.size_m || [b[3] - b[0], b[4] - b[1], b[5] - b[2]])],
            ["Bounds", el("span.mono", {}, "[" + b.map(function (v) { return Math.round(v * 1000) / 1000; }).join(", ") + "]")]].concat(d.cell ? [["Cell", el("span.mono", {}, d.cell.join(", "))]] : []).concat(d.cells ? [["Cells", el("span.mono", {}, d.cells.join(", "))]] : [])),
        el("div.lock", {}, icon("lock"), el("span", {}, "Metres; x east, z south, y up. " + (g.orientation || "axis-aligned boxes; no rotation") + ". The world changes through the director, not by dragging."))]));
      if (d.mesh) host.appendChild(sec("Static Mesh", true, null, [kv([["Asset", el("span.field", {}, (d.mesh.source && d.mesh.source.path) || d.mesh.asset)], ["Source", (d.mesh.source.source || "") + (d.mesh.source.licence ? " · " + d.mesh.source.licence : "")],
        ["Boxes", String(g.boxes || 1) + (d.parts && Object.keys(d.parts).length ? " (" + Object.keys(d.parts).map(function (k) { return k + " " + d.parts[k]; }).join(", ") + ")" : "")]])]));
      host.appendChild(sec("Materials (" + (d.materials || []).length + ")", true, null, (d.materials || []).map(function (m) {
        return el("div.mat", {}, U.swatch(m, 40), el("div", {}, el("div.nm", {}, m.name), el("div.pr", {}, "base " + rgb(m.base) + " · rough " + m.roughness + " · metal " + m.metallic),
          m.emissive_strength ? el("div.pr", {}, "emissive " + rgb(m.emissive) + " × " + m.emissive_strength) : null));
      }).concat([el("div.lock", {}, icon("info"), el("span", {}, "A swatch is a key to the material, drawn flat; the viewport is the renderer's picture."))])));
      host.appendChild(sec("Collision", true, d.collision && d.collision.blocks ? "blocks" : "none", [el("div", { class: d.collision && d.collision.blocks ? "" : "dim" }, d.collision ? d.collision.basis : "")]
        .concat(d.mover ? [kv([["Axis", d.mover.axis.join(", ")], ["Travel", (d.mover.len / 256) + " m"], ["Speed", (d.mover.speed / 2) + " m/s · " + d.mover.speed + " /256 m a tick"], ["Policy", d.mover.policy || "stop"]])] : [])));
      host.appendChild(sec("LOD", false, "one", [el("div.dim", {}, "One level: boxes, as the scene records them. The renderer draws every box at every distance.")]));
      host.appendChild(sec("Physics", false, d.layer === "movers" ? "mover" : "static", [el("div.dim", {}, d.layer === "movers" ? "A mover of rules " + d.rules + ": its pose each tick is the simulation's." : "Static. Nothing of the art moves; the simulation moves the player, the movers and the targets.")]));
      host.appendChild(sec("Gameplay Tags", false, tag || "none", [el("div", {}, tag ? tag + (role ? " · this request's " + role : " · known, not in this request") : "No tag. E or R gives the object a tag the director can name (@1, @2, …); a tag is never moved to another object.")]));
      const st = d.statement;
      const props = [["Statement", st ? el("span.field", {}, "line " + st.line + ": " + st.text) : el("span.dim", {}, d.statement_basis || "none")]];
      if (st) props.push(["Key", el("span.mono", {}, st.key)]);
      if (d.statement_basis && st) props.push(["Note", el("span.dim", {}, d.statement_basis)]);
      if (d.statement_makes) props.push(["Makes", d.statement_makes + " object" + (d.statement_makes === 1 ? "" : "s")]);
      if (d.changeable) props.push(["Changeable", el("span.dim", {}, d.changeable)]);
      if (d.nearest_wall) props.push(["Nearest wall", el("span", {}, d.nearest_wall.address + ", " + d.nearest_wall.side + ", " + d.nearest_wall.plan_gap_m + " m in plan")]);
      if (d.lights && d.lights.length) props.push(["Lights", d.lights.length + " · " + d.lights.map(function (L) { return L.type + " " + L.candela + " cd"; }).slice(0, 3).join(", ")]);
      props.push(["Scene", el("span.mono", {}, d.scene.slice(0, 16))]);
      host.appendChild(sec("Custom Properties", true, null, [kv(props)]));
    };
    shell.layers = function () {
      if (ui.rtab !== "layers") return;
      const host = $("rbody");
      host.innerHTML = "";
      const counts = {};
      for (const o of Object.values(objects())) counts[o.kind] = (counts[o.kind] || 0) + 1;
      const rows = [["play", "Play geometry (C)", S.collision.length]].concat(Object.keys(counts).sort().map(function (k) { return [k, "Dressing · " + k, counts[k]]; }))
        .concat([["movers", "Movers", (S.movers || []).length], ["targets", "Targets", Object.keys(S.targets || {}).length], ["lights", "Lights", S.lights.length]]);
      host.appendChild(el("div.ihead", {}, el("div.t", {}, "Layers"), el("div.s", {}, "The eye hides a layer from the view; the lock keeps it from being picked. Neither changes the world or the game.")));
      for (const [id, lab, n] of rows) {
        const hid = !!ui.hidden[id], lk = !!ui.locked[id];
        host.appendChild(el("div.lay", {},
          el("button" + (hid ? ".off" : ""), { title: hid ? "show" : "hide", onclick: function () { ui.hidden[id] = !hid; R.load(viewScene(S)); shell.layers(); } }, icon(hid ? "eyeoff" : "eye")),
          el("button" + (lk ? "" : ".off"), { title: lk ? "unlock: pick it again" : "lock: never pick it", onclick: function () { ui.locked[id] = !lk; shell.layers(); } }, icon("lock")),
          el("span", { style: { cursor: "pointer", color: ui.layer === id ? "#fff" : "" }, onclick: function () { setLayer(ui.layer === id ? "all" : id); } }, lab),
          el("span.n", {}, String(n))));
      }
    };
    shell.worldSettings = function () {
      if (ui.rtab !== "world") return;
      const host = $("rbody"), env = S.environment || {}, L = env.light || {}, fog = env.fog || {}, pl = S.player || {};
      host.innerHTML = "";
      host.appendChild(el("div.ihead", {}, el("div.t", {}, S.title || brief), el("div.s", {}, el("span.badge.neutral", {}, S.name || brief), "map " + S.map + " · rules " + (S.rules || 1))));
      host.appendChild(sec("Environment", true, env.time || "", [kv([["Light", (L.kind || "") + " az " + L.azimuth + "° el " + L.elevation + "° · " + L.lux + " lx"], ["Colour", rgb(L.color)],
        ["Fog", fog.density + " · " + rgb(fog.color)], ["Exposure", String(env.exposure)], ["Bloom", String(env.bloom)], ["Rain", String(env.rain)]])]));
      host.appendChild(sec("Grid", true, S.grid.w + " × " + S.grid.h, [kv([["Cell", S.grid.cell + " m"], ["Wall", S.grid.wall + " m"], ["Extent", S.grid.w * S.grid.cell + " × " + S.grid.h * S.grid.cell + " m"], ["Units", el("span.dim", {}, S.units)]])]));
      host.appendChild(sec("Player", false, "rules " + (S.rules || 1), [kv(Object.keys(pl).sort().map(function (k) { return [k, String(pl[k])]; }))]));
      host.appendChild(sec("Spawns", false, String(Object.keys(S.spawns || {}).length), [kv(Object.keys(S.spawns || {}).map(function (k) { const p = S.spawns[k]; return [k, p.x + ", " + p.z + " · yaw " + p.yaw + "°"]; }))]));
      host.appendChild(sec("Regions", false, String(Object.keys(S.regions || {}).length), [kv(Object.keys(S.regions || {}).sort().map(function (k) { return [k, el("span.mono", {}, S.regions[k].join(", "))]; }))]));
      host.appendChild(sec("Views", true, String(views.length), views.map(function (v, i) {
        return el("div.acts", { style: { margin: "2px 0" } }, el("button.btn.small", { onclick: function () { goView(v); } }, icon("bookmark"), (i + 1) + " " + v));
      })));
      const sv = (cur.slots[cur.k] || {}).served || {};
      host.appendChild(sec("Source", true, "[" + cur.k + "]", [kv([["Label", (cur.slots[cur.k] || {}).label || ""], ["Scene", el("span.mono", {}, cur.sha.slice(0, 24))], ["Map", el("span.mono", {}, (sv.map || "") + " " + cur.mapSha.slice(0, 12))],
        ["Counts", Object.keys(sv.counts || {}).map(function (k) { return k + " " + sv.counts[k]; }).join(", ")]]), el("div.lock", {}, icon("lock"), el("span", {}, "The brief's statements make all of this; it changes through the director or the art file, and a change is checked before it is drawn."))]));
    };
    const setLayer = function (id) {
      ui.layer = id;
      $("cx-layer").value = id;
      if (ui.rtab === "layers") shell.layers();
    };
    const fillLayers = function () {
      const sel = $("cx-layer"), counts = {};
      for (const o of Object.values(objects())) counts[o.kind] = 1;
      sel.innerHTML = "";
      for (const [v, t] of [["all", "All layers"], ["play", "Play geometry (C)"]].concat(Object.keys(counts).sort().map(function (k) { return [k, "Dressing · " + k]; })).concat([["movers", "Movers"], ["targets", "Targets"]])) {
        sel.appendChild(el("option", { value: v }, t));
      }
      sel.value = ui.layer;
    };
    $("cx-layer").onchange = function () { setLayer($("cx-layer").value); };

    // ---- the asset browser
    // a thumbnail is asked for once: the nodes waiting for it carry its key, and get it when it is drawn (a panel drawn
    // again in the meantime has new nodes with the same key)
    const thumbs = new U.Thumbs(192, 144), thumbCache = {}, thumbPending = {};
    const thumbPut = function (k) {
      document.querySelectorAll(".th").forEach(function (n) { if (n.dataset.thumb === k) n.style.backgroundImage = "url(" + thumbCache[k] + ")"; });
    };
    const thumbOf = function (key, cam, node) {
      const k = cur.sha + "|" + key;
      node.dataset.thumb = k;
      if (thumbCache[k]) { node.style.backgroundImage = "url(" + thumbCache[k] + ")"; return; }
      if (thumbPending[k]) return;
      thumbPending[k] = true;
      const sha = cur.sha, Sx = S;
      thumbs.later(function () {
        delete thumbPending[k];
        if (sha !== cur.sha) return;
        if (!thumbs.scene(Sx, sha)) { node.textContent = "no thumbnail"; return; }
        thumbCache[k] = thumbs.shot(cam, moverBoxes(s), targets(s));
        thumbPut(k);
      });
    };
    const folders = function () {
      const O = objects(), kinds = {};
      for (const o of Object.values(O)) (kinds[o.kind] = kinds[o.kind] || []).push(o);
      const playKinds = {};
      for (const c of S.collision) (playKinds[c.kind] = playKinds[c.kind] || []).push(c);
      const F = [["dressing", "Dressing", Object.values(O).length, null]];
      for (const k of Object.keys(kinds).sort()) F.push(["dressing/" + k, k, kinds[k].length, "dressing"]);
      F.push(["play", "Play geometry (C)", S.collision.length, null]);
      for (const k of Object.keys(playKinds).sort()) F.push(["play/" + k, k, playKinds[k].length, "play"]);
      F.push(["movers", "Movers", (S.movers || []).length, null], ["spawns", "Spawns & targets", Object.keys(S.spawns || {}).length + Object.keys(S.targets || {}).length, null],
        ["lights", "Lights", S.lights.length, null], ["materials", "Materials", Object.keys(S.materials).length, null], ["regions", "Regions", Object.keys(S.regions || {}).length, null],
        ["views", "Views", views.length, null], ["saved", "Saved views", ui.saved.length, null]);
      return { F: F, kinds: kinds, playKinds: playKinds };
    };
    const setFolder = function (f) { ui.folder = f; shell.assets(); };
    // a tile's thumbnail is drawn when the tile comes into view, not before
    const seen = typeof IntersectionObserver === "function" ? new IntersectionObserver(function (es) {
      for (const e of es) if (e.isIntersecting && e.target._thumb) { const f = e.target._thumb; e.target._thumb = null; seen.unobserve(e.target); f(e.target); }
    }, { root: null, rootMargin: "60px" }) : null;
    const tile = function (name, sub, piece, onclick, thumb) {
      const th = el("div.th"), t = el("div.tile" + (piece && piece === ui.sel ? ".active" : ""), { dataset: { piece: piece || "" }, title: name + (sub ? " · " + sub : ""), onclick: onclick }, th, el("div.nm", {}, name), sub ? el("div.sub", {}, sub) : null);
      if (thumb && seen) { th._thumb = thumb; seen.observe(th); } else if (thumb) thumb(th);
      return t;
    };
    const selectAndFrame = function (piece) { setSel(piece); frameSelection(); };
    shell.assets = function () {
      const fx = folders(), tree = $("a-tree"), grid = $("a-grid");
      $("a-head").innerHTML = "";
      $("a-head").append(icon("folderopen"), "Asset Browser", el("span.dim", {}, " · " + ui.folder.replace("/", " › ")), el("span.spacer"), el("span.dim", {}, "the scene's own pieces, drawn as they stand"));
      tree.innerHTML = "";
      for (const [id, lab, n, parent] of fx.F) {
        tree.appendChild(el("div.tf" + (parent ? ".sub" : "") + (ui.folder === id ? ".active" : ""), { onclick: function () { setFolder(id); } }, icon(ui.folder === id ? "folderopen" : "folder"), lab, el("span.n", {}, String(n))));
      }
      grid.innerHTML = "";
      const f = ui.folder, items = [];
      const objTile = function (o) {
        const b = union(o.boxes);
        return tile(o.id.slice(o.kind.length + 1), o.region + " · " + o.kind, o.id, function () { selectAndFrame(o.id); }, function (th) { thumbOf("obj:" + o.id, U.frameCam(b, 50), th); });
      };
      if (f === "dressing" || f.indexOf("dressing/") === 0) {
        const list = f === "dressing" ? Object.values(objects()) : fx.kinds[f.slice(9)] || [];
        for (const o of list.slice(0, 120)) items.push(objTile(o));
        if (list.length > 120) items.push(el("div.dim", {}, (list.length - 120) + " more: pick a kind"));
      } else if (f === "play" || f.indexOf("play/") === 0) {
        const list = f === "play" ? S.collision : fx.playKinds[f.slice(5)] || [];
        for (const c of list.slice(0, 120)) items.push(tile(c.id, c.kind + " · " + c.material, "play:" + c.id, function () { selectAndFrame("play:" + c.id); }, function (th) { thumbOf("play:" + c.id, U.frameCam(c.box, 50), th); }));
      } else if (f === "movers") {
        world.movers.forEach(function (m, i) { const b = moverBoxes(s)[i]; items.push(tile(m.id, (S.movers[i] || {}).policy || "stop", "mover:" + m.id, function () { selectAndFrame("mover:" + m.id); }, function (th) { thumbOf("mover:" + m.id, U.frameCam(b, 50), th); })); });
        if (!items.length) items.push(el("div.dim", {}, "This scene has no movers."));
      } else if (f === "spawns") {
        for (const k of Object.keys(S.spawns || {})) { const p = S.spawns[k]; items.push(tile("spawn " + k, p.x + ", " + p.z, null, function () { if (ui.mode === "play") leavePlay(); ecam = { x: p.x, y: p.y + P.eye, z: p.z, yaw: p.yaw * deg, pitch: 0, fov: 66 }; label = "spawn " + k; },
          function (th) { thumbOf("spawn:" + k, { x: p.x, y: p.y + P.eye, z: p.z, yaw: p.yaw * deg, pitch: 0, fov: 66 }, th); })); }
        for (const k of Object.keys(S.targets || {})) { const t = S.targets[k]; items.push(tile("target " + k, t.x + ", " + t.z, "target:" + k, function () { selectAndFrame("target:" + k); }, function (th) { thumbOf("target:" + k, U.frameCam([t.x - 0.4, t.y, t.z - 0.4, t.x + 0.4, t.y + 1.8, t.z + 0.4], 50), th); })); }
      } else if (f === "lights") {
        for (const L of S.lights.slice(0, 120)) {
          const owner = ids().has(L.id) ? rootOf(L.id) : null, p = L.pos;
          items.push(tile(L.id.split(":").slice(1).join(":") || L.id, L.type + " · " + L.candela + " cd", owner, function () { if (owner) selectAndFrame(owner); else { if (ui.mode === "play") leavePlay(); ecam = U.frameCam([p[0] - 1, p[1] - 1, p[2] - 1, p[0] + 1, p[1] + 1, p[2] + 1], 66); } },
            function (th) { th.style.background = "radial-gradient(circle at 50% 45%, rgb(" + L.color.join(",") + ") 0%, rgba(" + L.color.join(",") + ",0.35) 22%, #050a12 62%)"; }));
        }
      } else if (f === "materials") {
        const used = {};
        for (const v of S.visuals) used[v.material] = (used[v.material] || 0) + 1;
        for (const c of S.collision) used[c.material] = (used[c.material] || 0) + 1;
        for (const name of Object.keys(S.materials).sort()) {
          const m = S.materials[name];
          items.push(tile(name, (used[name] || 0) + " boxes · rough " + m.roughness, null, function () { toast(name + ": base " + rgb(m.base) + ", roughness " + m.roughness + ", metallic " + m.metallic + (m.emissive_strength ? ", emissive " + rgb(m.emissive) + " × " + m.emissive_strength : "") + " (" + (used[name] || 0) + " boxes)"); },
            function (th) { th.appendChild(U.swatch(m, 46)); }));
        }
      } else if (f === "regions") {
        for (const k of Object.keys(S.regions || {}).sort()) {
          const r = S.regions[k], c = S.grid.cell, b = [r[0] * c, 0, r[1] * c, (r[2] + 1) * c, 3, (r[3] + 1) * c];
          items.push(tile(k, r.join(", "), null, function () { ui.show.regions = true; if (ui.mode === "play") leavePlay(); ecam = U.frameCam(b, 66); label = "region " + k; }, function (th) { thumbOf("region:" + k, U.frameCam(b, 60), th); }));
        }
      } else if (f === "views") {
        views.forEach(function (v, i) { const w = S.views[v]; items.push(tile((i + 1) + " " + v, "yaw " + w.yaw + "° pitch " + w.pitch + "°", null, function () { goView(v); }, function (th) { thumbOf("view:" + v, { x: w.x, y: w.y, z: w.z, yaw: w.yaw * deg, pitch: w.pitch * deg, fov: 66 }, th); })); });
      } else if (f === "saved") {
        ui.saved.forEach(function (c, i) {
          items.push(tile("saved " + (i + 1), viewStatement(c, "saved-" + (i + 1)), null, function () { if (ui.mode === "play") leavePlay(); ecam = Object.assign({}, c); label = "saved " + (i + 1); }, function (th) { thumbOf("saved:" + i + ":" + JSON.stringify(c), c, th); }));
        });
        items.push(el("div.dim", { style: { gridColumn: "1 / -1" } }, "Saved views live in this page only. World ▸ Save the camera as a view; Edit ▸ Copy the camera as a view statement gives the art file's line for it."));
      }
      for (const it of items) grid.appendChild(it);
    };
    const saveView = function () { ui.saved.push(Object.assign({}, eye())); toast("Saved view " + ui.saved.length + ": " + viewStatement(eye(), "saved-" + ui.saved.length)); if (ui.folder === "saved") shell.assets(); };

    // ---- the candidates
    shell.candidates = function () {
      const r = studio.req, host = $("c-list"), head = $("c-head");
      const cands = (r && r.candidates) || [];
      head.innerHTML = "";
      head.append(icon("candidates"), "Candidates (" + cands.length + ")", el("span.dim", {}, r ? " · request " + r.state + (r.prompt ? ": " + r.prompt.slice(0, 40) : "") : " · no request"), el("span.spacer"),
        el("button.btn.small", { onclick: openPanel }, icon("wand"), "Director"));
      host.innerHTML = "";
      for (const c of cands) {
        const th = el("div.th", {}, el("span.letter", {}, c.letter));
        const st = c.decided ? el("span.badge." + (c.decided.indexOf("admit") === 0 ? "admitted" : "rejected"), {}, c.decided)
          : c.verdict === "CLEAN" ? el("span.badge.candidate", {}, "Ready") : el("span.badge.refused", {}, c.verdict || "?");
        const sv = c.slot !== null ? (cur.slots[c.slot] || {}).served : null;
        const card = el("div.card" + (c.slot !== null && c.slot === cur.k ? ".shown" : ""), { title: (c.message || c.title || ""), dataset: { sha: sv ? sv.sha : "", letter: c.letter } },
          th, el("div.tt", {}, c.title), el("div.st", {}, st, c.record ? el("span.faint", {}, "rung " + c.record.rung) : null),
          el("div.acts", {}, el("button.btn.small", { disabled: c.slot === null, onclick: function () { pick(c.slot); } }, "Show"),
            el("button.btn.small", { disabled: !admissible(c), onclick: function () { admitWithStill(r.id, c); } }, "Admit"),
            el("button.btn.small", { disabled: !!c.decided, onclick: function () { decide("reject", r.id, c.letter); } }, "Reject")));
        host.appendChild(card);
        if (c.slot !== null) candThumb(c, th);
      }
      host.appendChild(el("div.card.new", { onclick: openPanel, title: "Describe a change to the director" }, icon("plus"), "New"));
    };
    // a candidate drawn from where the target is framed (or where the eye is), in the thumbnailer: its scene fetched
    const candThumb = function (c, node) {
      const sv = (cur.slots[c.slot] || {}).served;
      if (!sv) return;
      const tb = studio.refs.target && (studio.refs.items || [])[0] ? objectBox((studio.refs.items || [])[0].piece) : null;
      const cam = tb ? U.frameCam(tb, 55) : Object.assign({}, eye());
      const key = "cand|" + sv.sha + "|" + [cam.x, cam.y, cam.z, cam.yaw, cam.pitch].map(function (v) { return v.toFixed(2); }).join(",");
      node.dataset.thumb = key;
      if (thumbCache[key]) { node.style.backgroundImage = "url(" + thumbCache[key] + ")"; return; }
      if (thumbPending[key]) return;
      thumbPending[key] = true;
      get("/scene/" + brief + ".json?slot=" + c.slot).then(json).then(function (Sc) {
        thumbs.later(function () {
          delete thumbPending[key];
          if (!thumbs.scene(Sc, sv.sha)) return;
          thumbCache[key] = thumbs.shot(cam, moverBoxes(s), targets(s));
          thumbPut(key);
        }, true);
      }).catch(function () { delete thumbPending[key]; });
    };

    // ---- the ledger
    const KIND = { admit: ["admitted", "ADMITTED"], evaluate: ["candidate", "CANDIDATE"], refuse: ["rejected", "REJECTED"], rebase: ["neutral", "REBASED"],
                   refuse_input: ["refused", "REFUSED INPUT"], genesis: ["neutral", "GENESIS"] };
    const ledgerShow = function () {
      const h = ui.history, host = $("l-list"), head = $("l-head");
      head.innerHTML = "";
      const insp = h && h.inspect;
      head.append(icon("history"), "History / Ledger", el("span.dim", {}, insp ? " · " + insp.events + " events" + (insp.verified ? " · verified" : "") : ""), el("span.spacer"),
        el("a.btn.small", { href: "/history.html?world=" + W, style: { textDecoration: "none" } }, "Open"));
      host.innerHTML = "";
      if (!h) { host.appendChild(el("div.empty", {}, "Reading the ledger…")); return; }
      if (!h.events.length) { host.appendChild(el("div.empty", {}, insp && insp.error ? insp.error : "No events yet.")); return; }
      for (const e of h.events.slice(0, 60)) {
        const k = KIND[e.kind] || ["neutral", e.kind.toUpperCase()];
        let cls = k[0], lab = k[1];
        if (e.kind === "evaluate" && e.verdict === "REFUSED") { cls = "refused"; lab = "REFUSED"; }
        const what = e.kind === "evaluate" ? (e.candidate ? e.candidate + " · " : "") + (e.prompt || "") + (e.codes && e.codes.length ? " · " + e.codes.join(",") : "")
          : e.kind === "admit" ? "evaluation #" + e.evaluation + (e.chooser ? " · by " + e.chooser : "") + (e.note ? " · " + e.note : "") + (e.head_after ? " → " + e.head_after : "")
          : e.kind === "refuse" || e.kind === "rebase" ? (e.evaluation ? "evaluation #" + e.evaluation + (e.note ? " · " : "") : "") + (e.note || (e.kind === "rebase" ? "rebased onto the head" : ""))
          : e.kind === "refuse_input" ? (e.code || "") + " " + (e.detail || "") : e.kind === "genesis" ? "head " + (e.head || "") : "";
        host.appendChild(el("div.lrow", { title: what }, el("span.mono.faint", {}, "#" + e.seq), el("span", {}, el("span.badge." + cls, {}, lab)), el("span.what", {}, what), el("span.when", {}, (e.at || "").replace("T", " ").slice(5, 16))));
      }
    };
    const historyPoll = function () {
      const key = cur.version + "|" + (studio.lastDecision || "");
      if (key === ui.histKey) return;
      ui.histKey = key;
      getJSON("/history.json?world=" + W).then(function (h) { ui.history = h; ledgerShow(); chips(); }).catch(function () { ui.histKey = ""; });
    };

    // ---- modals: validate, worlds, keys, about
    const modal = function (title, body) {
      $("m-title").innerHTML = ""; $("m-title").append(title, el("button.btn.small", { onclick: function () { $("modal").classList.remove("open"); } }, "Close"));
      $("m-body").innerHTML = ""; $("m-body").append(body);
      $("modal").classList.add("open");
    };
    $("modal").addEventListener("mousedown", function (e) { if (e.target === $("modal")) $("modal").classList.remove("open"); });
    const validate = function () {
      getJSON("/validate.json?world=" + W + "&slot=" + cur.k).then(function (v) {
        const body = el("div");
        body.appendChild(el("p.dim", {}, "Source [" + v.slot + "] " + (v.label || "") + " · scene " + (v.sha || "").slice(0, 16) + " · " + (v.basis || "")));
        if (v.refused) body.appendChild(el("div.vrow", {}, el("span.bad", {}, "✗"), el("div", {}, el("b", {}, "The latest compile of this source was refused; the scene before it is the one drawn"), el("div.d", {}, v.refused))));
        if (v.checks) {
          for (const [name, ok, detail] of v.checks) body.appendChild(el("div.vrow", {}, el("span", { class: ok ? "good" : "bad" }, ok ? "✓" : "✗"), el("div", {}, el("div", {}, name), el("div.d", {}, detail))));
          const n = v.checks.filter(function (r) { return r[1]; }).length;
          body.appendChild(el("p", { class: n === v.checks.length ? "good" : "bad" }, n + " of " + v.checks.length + " checks passed. Integrity, not truth: a check says what it checks and nothing more."));
        } else body.appendChild(el("p", {}, "A candidate's checks are the director's: verdict " + (v.verdict || "?") + (v.codes && v.codes.length ? " (" + v.codes.join(", ") + ")" : "") + (v.record ? "; rung " + v.record.rung + ", an admission needs: " + v.record.requires.join("; ") : "") + "."));
        modal(el("span", {}, icon("shield"), " Validation"), body);
      }).catch(function (e) { toast("Validate: " + (e && e.message || e), true); });
    };
    const buildNow = function () {
      toast("Building every source of " + brief + "…");
      post("/studio/build", {}).then(function (r) {
        if (!r.ok) { toast((r.code || "") + " " + (r.message || ""), true); return; }
        const bad = (r.slots || []).filter(function (x) { return !x.ok; });
        toast("Built in " + r.ms + " ms (v" + r.version + "): " + (bad.length ? bad.length + " source(s) refused; the scene before each stays" : "every source served") + (r.lines && r.lines.length ? " · " + r.lines.length + " change(s)" : " · nothing changed"), !!bad.length);
      });
    };
    const worldsModal = function () {
      const body = el("div");
      for (const w of worlds) body.appendChild(el("div.vrow", {}, icon("map"), el("div", {}, el("a", { href: "/play.html?world=" + encodeURIComponent(w.world), style: { color: "#cfe0ff" } }, w.world), el("div.d", {}, (w.title || "") + (w.open ? " · open" : "") + (w.default ? " · the default" : "")))));
      if (!worlds.length) body.appendChild(el("p.dim", {}, "Reading the worlds…"));
      modal(el("span", {}, icon("map"), " Scenes (worlds)"), body);
    };
    const keysHelp = function () {
      const K = [["Click", "select what the cursor is over (the editor)"], ["Right-drag", "look around"], ["Right button + W A S D, Q E", "fly; Shift faster"], ["Wheel", "move forward or back"],
        ["F", "frame the selection"], ["Q / T", "the select / measure tool"], ["1 – 9", "the registered views"], ["P", "play (the mouse captured); Esc back to the editor"],
        ["E / R", "the selection (in play, the crosshair) as the director's target / a pinned reference"], ["Enter", "the director"], ["[ ]", "step through the sources"], ["Backspace", "reset the game"], ["Esc", "select none; close a drawer"]];
      const body = el("div");
      for (const [k, v] of K) body.appendChild(el("div.vrow", {}, el("span"), el("div", {}, el("b", {}, k), el("div.d", {}, v))));
      modal(el("span", {}, "Keys"), body);
    };
    const about = function () {
      const body = el("div");
      body.appendChild(el("p", {}, "Verðandi Studio: the art scene of " + brief + ", drawn by scene_render.js, played by the graybox's simulation (rules " + Sim.RULES + "), served by art/play.py."));
      body.appendChild(el("p.dim", {}, "Code digests: " + Object.keys(cur.code).sort().map(function (k) { return k + " " + cur.code[k]; }).join(" · ")));
      body.appendChild(el("p.dim", {}, "The director proposes, the host validates, a person admits. Nothing in this page changes the world: it asks play.py, which checks."));
      modal(el("span", {}, "About"), body);
    };

    // ---- the overlay: the selection, the hover, the tags, the measure, the grid and the regions
    const og = ov.getContext("2d");
    const drawBox = function (b, c, W0, H0, style, width, dash) {
      const E = U.boxEdges(c, b, W0, H0);
      og.strokeStyle = style; og.lineWidth = width; og.setLineDash(dash || []);
      og.beginPath();
      for (const [a, z] of E) { og.moveTo(a[0], a[1]); og.lineTo(z[0], z[1]); }
      og.stroke(); og.setLineDash([]);
    };
    const drawLine = function (a, z, c, B, W0, H0) { const sgm = U.segment(c, B, a, z, W0, H0); if (sgm) { og.moveTo(sgm[0][0], sgm[0][1]); og.lineTo(sgm[1][0], sgm[1][1]); } };
    const label2 = function (x, y, text, bg, fg) {
      og.font = "600 11px system-ui, sans-serif";
      const w = og.measureText(text).width + 8;
      og.fillStyle = bg; og.fillRect(x, y - 15, w, 15); og.fillStyle = fg || "#0a111d"; og.fillText(text, x + 4, y - 4);
    };
    const drawOverlay = function () {
      const W0 = ov.clientWidth, H0 = ov.clientHeight, k = ov.width / Math.max(1, W0);
      og.setTransform(k, 0, 0, k, 0, 0);
      og.clearRect(0, 0, W0, H0);
      if (document.body.classList.contains("still")) return;
      const c = eye(), B = U.basis(c), g = S.grid;
      if (ui.show.grid) {
        og.strokeStyle = "rgba(120,170,255,0.22)"; og.lineWidth = 1; og.beginPath();
        const cx = Math.floor(c.x / g.cell), cz = Math.floor(c.z / g.cell), n = 16;
        for (let i = Math.max(0, cx - n); i <= Math.min(g.w, cx + n); i++) drawLine([i * g.cell, 0.02, Math.max(0, cz - n) * g.cell], [i * g.cell, 0.02, Math.min(g.h, cz + n) * g.cell], c, B, W0, H0);
        for (let j = Math.max(0, cz - n); j <= Math.min(g.h, cz + n); j++) drawLine([Math.max(0, cx - n) * g.cell, 0.02, j * g.cell], [Math.min(g.w, cx + n) * g.cell, 0.02, j * g.cell], c, B, W0, H0);
        og.stroke();
      }
      if (ui.show.regions) {
        for (const name of Object.keys(S.regions || {})) {
          const r = S.regions[name], b = [r[0] * g.cell, 0.03, r[1] * g.cell, (r[2] + 1) * g.cell, 0.03, (r[3] + 1) * g.cell];
          og.strokeStyle = "rgba(255,207,90,0.75)"; og.lineWidth = 1.5; og.setLineDash([6, 4]); og.beginPath();
          drawLine([b[0], b[1], b[2]], [b[3], b[1], b[2]], c, B, W0, H0); drawLine([b[3], b[1], b[2]], [b[3], b[1], b[5]], c, B, W0, H0);
          drawLine([b[3], b[1], b[5]], [b[0], b[1], b[5]], c, B, W0, H0); drawLine([b[0], b[1], b[5]], [b[0], b[1], b[2]], c, B, W0, H0);
          og.stroke(); og.setLineDash([]);
          const p = U.project(c, [(b[0] + b[3]) / 2, 0.05, (b[2] + b[5]) / 2], W0, H0);
          if (p) label2(p[0], p[1], name, "rgba(255,207,90,0.9)");
        }
      }
      if (ui.show.collision) for (const cb of S.collision) if (cb.kind !== "ground") drawBox(cb.box, c, W0, H0, "rgba(90,160,255,0.55)", 1);
      if (ui.show.wire) for (const v of S.visuals) if (!ui.hidden[v.id.split(":")[0]]) drawBox(v.box, c, W0, H0, "rgba(180,200,230,0.28)", 1);
      if (ui.show.spawns && ui.mode === "edit") {
        for (const sk of Object.keys(S.spawns || {})) {
          const sp = S.spawns[sk], p = U.project(c, [sp.x, sp.y + 0.05, sp.z], W0, H0);
          if (p) { og.fillStyle = "#3ccf91"; og.beginPath(); og.arc(p[0], p[1], 4, 0, Math.PI * 2); og.fill(); label2(p[0] + 6, p[1] - 2, "spawn " + sk, "rgba(60,207,145,0.9)"); }
        }
      }
      // the tags (STUDIO-1): each tagged object framed and labelled; the target amber, a pin cyan
      if (ui.show.tags) {
        for (const it of studio.refs.items || []) {
          if (it.status === "gone") continue;
          const b = objectBox(it.piece), fr = b && frameOf(b);
          if (!fr) continue;
          const col = it.role === "target" ? "#ffcf5a" : "#5fd3f3";
          og.strokeStyle = col; og.lineWidth = 1.2; og.setLineDash(it.role === "pin" ? [5, 3] : []); og.strokeRect(fr.L, fr.T, fr.W, fr.H); og.setLineDash([]);
          label2(fr.L, fr.T, it.tag + (it.role === "target" ? " target" : "") + (it.status === "changed" ? " (changed)" : ""), col);
        }
      }
      if (ui.mode === "edit" && ui.hover && ui.hover.piece !== ui.sel) for (const b of pieceBoxes(ui.hover.piece)) drawBox(b, c, W0, H0, ui.hover.selectable ? "rgba(140,190,255,0.75)" : "rgba(140,150,170,0.45)", 1, [4, 3]);
      if (ui.sel) {
        const bx = pieceBoxes(ui.sel), u = bx.length ? union(bx) : null;
        if (bx.length > 1) for (const b of bx) drawBox(b, c, W0, H0, "rgba(77,141,255,0.55)", 1);
        if (u) {
          og.shadowColor = "rgba(77,141,255,0.9)"; og.shadowBlur = 6;
          drawBox(u, c, W0, H0, "#4d8dff", 2);
          og.shadowBlur = 0;
          og.fillStyle = "#4d8dff";
          for (const p of U.corners(u)) { const sp = U.project(c, p, W0, H0); if (sp) og.fillRect(sp[0] - 3, sp[1] - 3, 6, 6); }
          const top = U.project(c, [(u[0] + u[3]) / 2, u[4], (u[2] + u[5]) / 2], W0, H0);
          if (top) label2(top[0] + 6, top[1] - 6, nameOf(ui.sel), "#4d8dff", "#fff");
        }
      }
      if (ui.measure.length) {
        og.strokeStyle = "#ffcf5a"; og.fillStyle = "#ffcf5a"; og.lineWidth = 2;
        const pts = ui.measure.map(function (p) { return U.project(c, p, W0, H0); });
        for (const p of pts) if (p) { og.beginPath(); og.arc(p[0], p[1], 4, 0, Math.PI * 2); og.fill(); }
        if (ui.measure.length === 2) {
          og.beginPath(); drawLine(ui.measure[0], ui.measure[1], c, B, W0, H0); og.stroke();
          const a = ui.measure[0], z = ui.measure[1], d = Math.hypot(z[0] - a[0], z[1] - a[1], z[2] - a[2]), m = U.project(c, [(a[0] + z[0]) / 2, (a[1] + z[1]) / 2, (a[2] + z[2]) / 2], W0, H0);
          if (m) label2(m[0] + 6, m[1] - 4, d.toFixed(3) + " m (plan " + Math.hypot(z[0] - a[0], z[2] - a[2]).toFixed(3) + ", rise " + (z[1] - a[1]).toFixed(3) + ")", "#ffcf5a");
        }
      }
    };

    // ---- assembling the shell
    buildMenus(); buildNav(); buildTools(); buildPills(); buildTabs(); buildRoadmap(); fillLayers();
    $("hint").textContent = "Click to select · right-drag to look · right button + WASD to fly · F frame · P play · Enter director";
    setTab("inspector"); shell.assets(); shell.candidates(); ledgerShow(); chips(); shell.chrome(); navGo("overview"); ecam = views.length ? ecam : overviewCam();
    if (views.length) { const v = S.views[views[0]]; ecam = { x: v.x, y: v.y, z: v.z, yaw: v.yaw * deg, pitch: v.pitch * deg, fov: 66 }; label = "view " + views[0]; }
    document.querySelectorAll(".navit").forEach(function (b) { b.classList.toggle("active", b.dataset.nav === "overview"); });
    shell.sceneChanged = function () {
      objIndex = null; fillLayers(); shell.assets(); shell.layers(); shell.worldSettings();
      if (ui.sel) { if (pieceBoxes(ui.sel).length) setSel(ui.sel); else setSel(null); }
      chips(); buildMenus();
    };
    shell.slotsChanged = function () { chips(); shell.candidates(); };

    // the hooks a still, a walk-through or a test uses
    window.PLAY = {
      get renderer() { return R; }, get scene() { return S; }, get state() { return s; }, get world() { return world; },
      live: cur, get sim() { return Sim; }, studio: studio, select: select, pin: pin, hover: function () { return studio.hover; },
      pause: function (on) { paused = !!on; },
      slot: pick,
      view: function (name, time) { goView(name); render(ecam, time || 0, s); },
      cam: function (x, y, z, yaw, pitch, time) { if (ui.mode === "play") leavePlay(); ecam = { x: x, y: y, z: z, yaw: yaw * deg, pitch: pitch * deg, fov: 66 }; label = "camera"; render(ecam, time || 0, s); },
      walkTo: function (tick) {
        // the self-test's walk is the map's, without movers: it is played in a world of the map alone
        if (!walk) walk = Sim.record(map)[0];
        const st = Sim.restore(walk.start), w0 = new Sim.World(map);
        for (let n = 0; n < Math.min(tick, walk.inputs.length); n++) Sim.step(w0, st, walk.inputs[n]);
        render(eyeOf(st), tick / 120, st);
        return { ticks: walk.inputs.length, x: st.x, z: st.z };
      },
      // STUDIO-3: the shell's state for a test (read-only copies), and its gestures
      shell: { get ui() { return ui; }, setSel: setSel, setTab: setTab, setFolder: setFolder, navGo: navGo, play: enterPlay, edit: leavePlay, validate: validate,
               hitAt: hitAt, get cam() { return Object.assign({}, eye()); }, setCam: function (c) { ecam = Object.assign({ fov: 66 }, c); } },
    };
    if (q.get("view") || q.get("cam") || q.get("still")) {
      document.body.classList.add("still");
      if (q.get("view")) window.PLAY.view(q.get("view"), parseFloat(q.get("t") || "0"));
      else if (q.get("cam")) { const c = q.get("cam").split(",").map(Number); window.PLAY.cam(c[0], c[1], c[2], c[3], c[4], parseFloat(q.get("t") || "0")); }
      window.PLAY_READY = true;
      return;
    }
    setInterval(poll, 500);
    setInterval(historyPoll, 2000); historyPoll();
    // B1: the page's heartbeat, which the supervisor reads in /healthz (the page has spoken; the window is alive)
    const alive = function () { post("/studio/alive", {}).catch(function () {}); };
    alive();
    setInterval(alive, 5000);
    // and its last word when the window goes (a reload says it too, then speaks again at once; the supervisor waits)
    window.addEventListener("pagehide", function () { try { navigator.sendBeacon("/studio/bye", token); } catch (e) { /* nothing to do */ } });
    if (q.get("review")) setTimeout(function () { review({ id: q.get("review"), world: brief }); }, 300);
    // 0220: the launcher's "Queue prompts" view: this world with the director's queue open
    if (q.get("panel") === "queue") setTimeout(function () { openPanel(); const ql = $("st-qlist"); if (ql && ql.scrollIntoView) ql.scrollIntoView(); }, 300);

    // ---------------------------------------------------------------- input: the editor and play
    const keys = {}, pending = { reset: false, jump: false }, refusals = {};
    let mdx = 0, mdy = 0, fire = false, acc = 0, last = performance.now();
    const t0 = last;
    const SENS = 0.0022;
    const overlay = $("overlay");
    overlay.addEventListener("click", function () { if (ui.mode === "play") enterPlay(document.body.classList.contains("playfull")); });
    document.addEventListener("pointerlockchange", function () {
      if (lockOK()) { overlay.style.display = "none"; return; }
      if (ui.mode === "play") leavePlay();       // Esc: back to the editor, at the player's eye; the game waits
    });
    const local = function (e) { const r = canvas.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    canvas.addEventListener("contextmenu", function (e) { e.preventDefault(); });
    canvas.addEventListener("mousedown", function (e) {
      if (ui.mode === "play") { if (lockOK() && e.button === 0) fire = true; return; }
      closeMenus();
      if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
      if (e.button === 2) { ui.rmb = true; vp.classList.add("fly"); e.preventDefault(); return; }
      if (e.button === 0) ui.drag = { at: local(e), moved: 0 };
    });
    document.addEventListener("mouseup", function (e) {
      if (e.button === 0) fire = false;
      if (e.button === 2 && ui.rmb) { ui.rmb = false; vp.classList.remove("fly"); }
      if (e.button === 0 && ui.drag && ui.mode === "edit") {
        const d = ui.drag; ui.drag = null;
        if (d.moved > 4) return;
        const h = hitAt(d.at[0], d.at[1]);
        if (ui.tool === "measure") {
          if (!h) { toast("Nothing there to measure to", true); return; }
          ui.measure = ui.measure.length >= 2 ? [h.point] : ui.measure.concat([h.point]);
          return;
        }
        if (!h) { setSel(null); return; }
        if (!h.selectable) { toast(ui.locked[h.layer] ? "The layer " + h.layer + " is locked" : "The layer is " + ui.layer + ": " + nameOf(h.piece) + " is not on it", true); return; }
        setSel(h.piece);
      }
    });
    document.addEventListener("mousemove", function (e) {
      if (ui.mode === "play") { if (lockOK()) { mdx += e.movementX; mdy += e.movementY; } return; }
      if (ui.rmb) { ecam.yaw += e.movementX * SENS; ecam.pitch = Math.max(-1.55, Math.min(1.55, ecam.pitch - e.movementY * SENS)); if (ui.projection !== "perspective") { ui.projection = "perspective"; ecam.fov = 66; } return; }
      if (ui.drag) ui.drag.moved += Math.abs(e.movementX) + Math.abs(e.movementY);
      if (e.target === canvas) ui.cursor = local(e); else ui.cursor = null;
    });
    canvas.addEventListener("wheel", function (e) {
      if (ui.mode !== "edit") return;
      e.preventDefault();
      const B = U.basis(ecam), d = (e.deltaY < 0 ? 1 : -1) * (e.shiftKey ? 6 : 1.5);
      ecam.x += B.f[0] * d; ecam.y += B.f[1] * d; ecam.z += B.f[2] * d;
    }, { passive: false });
    document.addEventListener("keydown", function (e) {
      // typing to the director is not playing: the panel's own keys, and nothing reaches the game
      if (e.target && /^(TEXTAREA|INPUT|SELECT)$/.test(e.target.tagName)) {
        if (e.code === "Escape") { closePanel(); e.target.blur(); }
        else if (e.code === "Enter" && (e.ctrlKey || e.metaKey) && e.target === promptEl) { e.preventDefault(); ask(); }
        return;
      }
      if (e.target && e.target.tagName === "BUTTON" && (e.code === "Enter" || e.code === "Space")) return;
      if (e.code === "Escape") {
        if ($("modal").classList.contains("open")) { $("modal").classList.remove("open"); return; }
        if (studio.open) { closePanel(); return; }
        if (document.querySelector(".menu.open, .pillmenu.open")) { closeMenus(); return; }
        if (ui.mode === "edit") { if (ui.measure.length) ui.measure = []; else setSel(null); }
        return;
      }
      if (e.code === "KeyE" && !ui.rmb) { select(); return; }
      if (e.code === "KeyR" && !ui.rmb) { pin(); return; }
      if (e.code === "Enter") { e.preventDefault(); openPanel(); return; }
      keys[e.code] = true;
      const n = parseInt(e.key, 10);
      if (n >= 1 && n <= views.length) goView(views[n - 1]);
      if (e.code === "Tab") { e.preventDefault(); if (ui.mode === "edit") enterPlay(false); }
      if (e.code === "Backspace") { pending.reset = true; e.preventDefault(); }
      if (e.code === "Space") { pending.jump = true; e.preventDefault(); }
      if (e.code === "BracketLeft") step(-1);
      if (e.code === "BracketRight") step(1);
      if (ui.mode === "edit" && !ui.rmb) {
        if (e.code === "KeyP") enterPlay(false);
        if (e.code === "KeyF") frameSelection();
        if (e.code === "KeyQ") setTool("select");
        if (e.code === "KeyT") setTool("measure");
        if (e.key === "?") keysHelp();
      }
    });
    document.addEventListener("keyup", function (e) { keys[e.code] = false; });
    window.addEventListener("blur", function () { for (const k in keys) keys[k] = false; fire = false; ui.rmb = false; vp.classList.remove("fly"); });
    // the editor's flight, while the right button is held (the camera is the view's; the game is not moved)
    const fly = function (dt) {
      if (!ui.rmb) return;
      const B = U.basis(ecam), v = (keys.ShiftLeft || keys.ShiftRight ? 24 : 8) * dt;
      const f = (keys.KeyW ? 1 : 0) - (keys.KeyS ? 1 : 0), r = (keys.KeyD ? 1 : 0) - (keys.KeyA ? 1 : 0), u = (keys.KeyE ? 1 : 0) - (keys.KeyQ ? 1 : 0);
      ecam.x += (B.f[0] * f + B.r[0] * r) * v; ecam.y += (B.f[1] * f) * v + u * v; ecam.z += (B.f[2] * f + B.r[2] * r) * v;
    };
    let hoverAt = 0, hudAt = 0;
    function frame(now) {
      const dt = Math.min(0.25, (now - last) / 1000);
      ui.frameMs = ui.frameMs * 0.9 + (now - last) * 0.1; last = now; ui.frames++;
      if (ui.mode === "play" && !paused) {
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
      } else { acc = 0; fly(dt); }
      ui.calls = 0;
      const c0 = performance.now();
      render(eye(), (now - t0) / 1000, s);
      ui.cpuMs = ui.cpuMs * 0.9 + (performance.now() - c0) * 0.1; ui.callsShown = ui.calls;
      if (now - hoverAt > 60) {
        hoverAt = now;
        if (ui.mode === "play") {
          const hv = pickPiece(), hroot = hv ? rootOf(hv.id) : null;
          studio.hover = hv ? { piece: hroot, address: addressOf({ id: hroot, region: hv.region }), tag: tagOf(hroot) } : null;
        } else ui.hover = ui.cursor && !ui.rmb ? hitAt(ui.cursor[0], ui.cursor[1]) : null;
      }
      drawOverlay();
      if (ui.show.stats) statsShow(now);
      if (now - hudAt > 120) {
        hudAt = now;
        const info = cur.slots[cur.k] || {}, sv = info.served || {};
        if (ui.mode === "play") {
          $("hud").textContent = "world " + brief + "  ·  " + (S.title || brief) + "  ·  " + label + "  ·  cell " + Math.floor(s.x / S.grid.cell) + "," + Math.floor(s.z / S.grid.cell)
            + "  ·  hits " + s.score + "\n" + views.map(function (v, i) { return (i + 1) + " " + v; }).join("  ") + "  ·  WASD, mouse, Space, Backspace reset  ·  E target, R pin, Enter director  ·  Esc editor"
            + "\nunder the crosshair: " + (studio.hover ? studio.hover.address + (studio.hover.tag ? "  " + studio.hover.tag : "") : "nothing of the art")
            + (studio.refs.target ? "  ·  target " + studio.refs.target : "") + ((studio.refs.pins || []).length ? "  ·  pins " + studio.refs.pins.join(" ") : "")
            + "\nsource [" + cur.k + "] " + (info.label || "") + (sv.verdict ? "  ·  " + sv.verdict : "")
            + "  ·  scene " + cur.sha.slice(0, 12) + (cur.slots.length > 1 ? "  ·  [ ] steps through the " + cur.slots.length + " sources" : "")
            + "\nmovement and collision: the graybox's simulation, rules " + Sim.RULES + ", against C" + (world.movers.length ? " and " + world.movers.length + " mover(s)" : "") + "  ·  live: play.py v" + cur.version
            + (cur.note && now - cur.noteAt < 8000 ? "\n" + cur.note : "");
        } else {
          const hv = ui.hover;
          $("hint").textContent = (cur.note && now - cur.noteAt < 6000 ? cur.note : (hv ? nameOf(hv.piece) + (hv.selectable ? "" : " (not selectable here)") + " · " + hv.face + " face · " + hv.point.map(function (v) { return v.toFixed(2); }).join(", ") + " m"
            : label + " · click to select · right-drag to look · right button + WASD to fly · P play · Enter director"));
        }
        $("pl-proj").textContent = ui.projection === "perspective" ? "Perspective" : ui.projection === "top" ? "Top" : "Side";
        $("pl-lit").textContent = ui.show.collision ? "Lit + C" : ui.show.wire ? "Lit + wire" : "Lit";
      }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
})();
