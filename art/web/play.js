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
//
// The studio (STUDIO-0, art/studio.py): Enter opens the director's panel. The prompt and the camera go to play.py, whose
// gateway asks the configured provider for at most three candidates and has the director evaluate each; those it
// draws are sources this page switches to in place, the game untouched, exactly as [ and ] do. Nothing here admits,
// rejects or undoes: the panel's buttons ask play.py, which does it through the director's ledger. A failure of the
// provider is shown, and the world goes on.
//
// The references (STUDIO-1): what is under the crosshair is named on screen (its kind and address, and its tag if it
// has one). E makes it the target, R pins it as a reference (or unpins it), up to four; play.py gives each a tag
// (@1, @2, ...) that names that object for as long as it runs, and says whether it is as tagged, changed, or gone. Each
// tagged object is framed and labelled; the panel lists them. The game's reset is Backspace here (R pins).

(function () {
  "use strict";
  const Sim = window.GrayboxSim, q = new URLSearchParams(location.search), $ = function (id) { return document.getElementById(id); };
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
  const fail = function (e) { $("overlay").textContent = String(e && e.message || e); $("overlay").style.display = "flex"; };

  get(live_url).then(json).then(function (live) {
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
      get(live_url).then(json).then(function (live) {
        busy = false;
        studioShow(live.studio);
        worldsShow(live.worlds);
        queueShow(live.queue);
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

    // ---------------------------------------------------------------- the studio
    const token = document.body.getAttribute("data-studio") || "";
    const studio = { open: false, refs: { target: null, pins: [], items: [] }, last: "", req: null, hover: null };
    const panel = $("studio"), promptEl = $("st-prompt");
    const post = function (path, body) {
      body = Object.assign({ world: brief }, body || {});
      return fetch(path, { method: "POST", headers: { "Content-Type": "application/json", "X-Studio-Token": token }, body: JSON.stringify(body) })
        .then(function (r) { return r.json().catch(function () { return { ok: false, message: "HTTP " + r.status }; }); })
        .catch(function (e) { return { ok: false, message: "play.py does not answer (" + (e && e.message || e) + ")" }; });
    };
    const eye = function () { return mode === "play" ? eyeOf(s) : vcam; };
    // the distance along the ray at which it enters the box, or Infinity (the view's own arithmetic: nothing here is state)
    const enter = function (o, d, b) {
      let near = -Infinity, far = Infinity;
      for (let a = 0; a < 3; a++) {
        const lo = b[a], hi = b[a + 3];
        if (d[a] === 0) { if (o[a] < lo || o[a] > hi) return Infinity; continue; }
        let t1 = (lo - o[a]) / d[a], t2 = (hi - o[a]) / d[a];
        if (t1 > t2) { const t = t1; t1 = t2; t2 = t; }
        if (t1 > near) near = t1;
        if (t2 < far) far = t2;
        if (near > far) return Infinity;
      }
      return far < 0 ? Infinity : Math.max(near, 0);
    };
    // the piece under the crosshair: the nearest box the ray meets, of the scene's dressing or its play world (a wall in
    // front hides what is behind it, and is the map's, not the art's)
    const pickPiece = function () {
      const c = eye(), cp = Math.cos(c.pitch), o = [c.x, c.y, c.z], d = [cp * Math.sin(c.yaw), Math.sin(c.pitch), -cp * Math.cos(c.yaw)];
      let best = null, bt = Infinity;
      for (const v of S.visuals) { if (v.box) { const t = enter(o, d, v.box); if (t < bt) { bt = t; best = v; } } }
      for (const b of S.collision || []) { const t = enter(o, d, b.box); if (t < bt) { bt = t; best = null; } }
      return best;
    };
    // the object a box belongs to (art/studio_refs.py's rule): its own id, or the id of the object it extends
    const ids = function () { if (!S._ids) S._ids = new Set(S.visuals.map(function (v) { return v.id; })); return S._ids; };
    const rootOf = function (id) {
      let r = id;
      while (r.split(":").length >= 3 && ids().has(r.slice(0, r.lastIndexOf(":")))) r = r.slice(0, r.lastIndexOf(":"));
      return r;
    };
    const addressOf = function (v) { const i = v.id.indexOf(":"); return (v.region === "*" ? "city" : v.region) + "/" + v.id.slice(0, i) + "/" + v.id.slice(i + 1); };
    const objectBox = function (piece) {
      let b = null;
      for (const v of S.visuals) {
        if (v.id !== piece && v.id.indexOf(piece + ":") !== 0) continue;
        b = b ? [Math.min(b[0], v.box[0]), Math.min(b[1], v.box[1]), Math.min(b[2], v.box[2]), Math.max(b[3], v.box[3]), Math.max(b[4], v.box[4]), Math.max(b[5], v.box[5])] : v.box.slice();
      }
      return b;
    };
    // a box's frame on screen, or null when it is behind the eye (the view's own arithmetic; nothing here is state)
    const frameOf = function (b) {
      const c = eye(), cp = Math.cos(c.pitch), f = [cp * Math.sin(c.yaw), Math.sin(c.pitch), -cp * Math.cos(c.yaw)], r = [Math.cos(c.yaw), 0, Math.sin(c.yaw)];
      const u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
      const th = Math.tan(33 * deg), asp = canvas.clientWidth / canvas.clientHeight;
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, seen = 0;
      for (let i = 0; i < 8; i++) {
        const p = [b[i & 1 ? 3 : 0] - c.x, b[i & 2 ? 4 : 1] - c.y, b[i & 4 ? 5 : 2] - c.z];
        const z = p[0] * f[0] + p[1] * f[1] + p[2] * f[2];
        if (z < 0.1) continue;
        seen++;
        const sx = (p[0] * r[0] + p[1] * r[1] + p[2] * r[2]) / (z * th * asp), sy = (p[0] * u[0] + p[1] * u[1] + p[2] * u[2]) / (z * th);
        x0 = Math.min(x0, sx); x1 = Math.max(x1, sx); y0 = Math.min(y0, sy); y1 = Math.max(y1, sy);
      }
      if (!seen) return null;
      const W = canvas.clientWidth, H = canvas.clientHeight, cl = function (v, a, b2) { return Math.max(a, Math.min(b2, v)); };
      const L = cl((x0 + 1) / 2 * W, -2, W + 2), R = cl((x1 + 1) / 2 * W, -2, W + 2), T = cl((1 - y1) / 2 * H, -2, H + 2), B = cl((1 - y0) / 2 * H, -2, H + 2);
      return R - L > 1 && B - T > 1 ? { L: L, T: T, W: R - L, H: B - T } : null;
    };
    const marks = {};
    const markRefs = function () {
      const want = {};
      for (const it of studio.refs.items || []) {
        if (it.status === "gone") continue;
        const b = objectBox(it.piece), fr = b && frameOf(b);
        if (!fr) continue;
        want[it.tag] = true;
        let el = marks[it.tag];
        if (!el) { el = document.createElement("div"); el.className = "mark"; el.appendChild(document.createElement("span")); document.body.appendChild(el); marks[it.tag] = el; }
        el.classList.toggle("pin", it.role === "pin");
        el.firstChild.textContent = it.tag + (it.role === "target" ? " target" : "") + (it.status === "changed" ? " (changed)" : "");
        el.style.display = "block"; el.style.left = fr.L + "px"; el.style.top = fr.T + "px"; el.style.width = fr.W + "px"; el.style.height = fr.H + "px";
      }
      for (const t in marks) if (!want[t]) marks[t].style.display = "none";
    };
    const tagOf = function (piece) { const it = (studio.refs.items || []).find(function (x) { return x.piece === piece; }); return it ? it.tag : ""; };
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
      if (!items.length) { const e = document.createElement("div"); e.textContent = "No target: the prompt is for the whole world. E makes what is under the crosshair the target; R pins a reference."; box.appendChild(e); return; }
      for (const it of items) {
        const el = document.createElement("div");
        el.className = "ref " + it.status;
        const st = it.statement;
        el.textContent = it.tag + " " + it.role + " · " + it.address + " · " + it.size_m.join(" × ") + " m" + (st ? " · line " + st.line : "")
          + (it.status === "changed" ? " · changed since tagged" : it.status === "gone" ? " · gone: no such object in this scene" : "");
        if (it.role === "pin") {
          const b = document.createElement("button"); b.textContent = "unpin";
          b.onclick = function () { post("/studio/unpin", { tag: it.tag }).then(function (r) { if (r.ok) { studio.refs = r.refs; showRefs(); } note(r, "unpinned " + it.tag); }); };
          el.appendChild(b);
        }
        box.appendChild(el);
      }
    };
    const setRefs = function (refs) { if (refs) { studio.refs = refs; showRefs(); } };
    const select = function () {
      const v = pickPiece();
      return post("/studio/select", { piece: v ? v.id : null }).then(function (r) {
        setRefs(r.refs);
        const t = studio.refs.target;
        say(r.ok ? (v ? "target " + t + ": " + addressOf({ id: rootOf(v.id), region: v.region }) : "nothing of the art under the crosshair; no target") : (r.code || "") + " " + (r.message || ""));
        return r;
      });
    };
    const pin = function () {
      const v = pickPiece();
      if (!v) { say("nothing of the art under the crosshair to pin"); return Promise.resolve({ ok: false }); }
      const before = tagOf(rootOf(v.id)), was = (studio.refs.pins || []).indexOf(before) >= 0;
      return post("/studio/pin", { piece: v.id }).then(function (r) {
        setRefs(r.refs);
        const t = tagOf(rootOf(v.id));
        say(r.ok ? (was ? "unpinned " + before : "pinned " + t + ": " + addressOf({ id: rootOf(v.id), region: v.region })) : (r.code || "") + ": " + (r.message || ""));
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
    const note = function (r, what) { $("st-status").innerHTML = ""; const el = document.createElement("span"); el.className = r.ok ? "good" : "bad"; el.textContent = r.ok ? what : (r.code ? r.code + ": " : "") + (r.message || "failed"); $("st-status").appendChild(el); };
    const ask = function () {
      const c = eye();
      post("/studio/ask", { prompt: promptEl.value, camera: { x: c.x, y: c.y, z: c.z, yaw_deg: c.yaw / deg, pitch_deg: c.pitch / deg } })
        .then(function (r) { note(r, "asked: request " + (r.id || "")); studio.last = ""; });
    };
    const decide = function (what, rid, letter) {
      post("/studio/" + what, { id: rid, candidate: letter }).then(function (r) {
        note(r, what === "admit" ? "admitted: ledger #" + (r.ledger || []).join(", #") : "rejected: ledger #" + (r.ledger || []).join(", #"));
        if (r.ok && what === "admit") pick(0);
        studio.last = "";
      });
    };
    $("st-ask").onclick = ask;
    $("st-cancel").onclick = function () { if (studio.req) post("/studio/cancel", { id: studio.req.id }).then(function (r) { note({ ok: true }, r.ok ? "cancelled" : "nothing to cancel"); }); };
    $("st-original").onclick = function () { pick(0); };
    $("st-undo").onclick = function () { post("/studio/undo", {}).then(function (r) { note(r, "undone: ledger #" + (r.ledger || []).join(", #")); if (r.ok) pick(0); }); };
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
          const el = document.createElement("div");
          el.className = "disp " + (d.kind === "FAILED" ? "bad" : "dim");
          const k = document.createElement("div");
          k.textContent = d.kind + " · decided by " + (d.decided_by === "host" ? "the studio" : "the provider (its own account)");
          el.appendChild(k);
          if (d.unmet && d.unmet.length) { const u = document.createElement("div"); u.textContent = "not made yet: " + d.unmet.join(", "); el.appendChild(u); }
          if (d.questions && d.questions.length) {
            for (const q of d.questions) { const qq = document.createElement("div"); qq.className = "q"; qq.textContent = "? " + q; el.appendChild(qq); }
          }
          if (d.note) { const n = document.createElement("div"); n.className = "dim"; n.textContent = d.note; el.appendChild(n); }
          box.appendChild(el);
        }
        for (const c of r.candidates || []) {
          const el = document.createElement("div");
          el.className = "cand" + (c.slot !== null && c.slot === cur.k ? " shown" : "");
          const t = document.createElement("div");
          t.textContent = c.letter + " · " + c.title + " · " + (c.verdict || "?") + (c.codes && c.codes.length ? " " + c.codes.join(",") : "") + (c.decided ? " · " + c.decided : "");
          t.className = c.verdict === "CLEAN" ? "good" : c.verdict === "REFUSED" ? "bad" : "";
          el.appendChild(t);
          if (c.message) { const m = document.createElement("div"); m.className = "dim"; m.textContent = c.message.slice(0, 300); el.appendChild(m); }
          if (c.touches) {
            const tt = c.touches, m = document.createElement("div"), parts = [];
            for (const tag of Object.keys(tt.tags).sort()) parts.push(tag + " " + tt.tags[tag]);
            parts.push(tt.others_count ? tt.others_count + " other object" + (tt.others_count === 1 ? "" : "s") + " changed (" + tt.others.slice(0, 3).join(", ") + (tt.others_count > 3 ? ", …" : "") + ")" : "no other object changed");
            if (tt.added_count) parts.push(tt.added_count + " new (" + tt.added.slice(0, 3).join(", ") + (tt.added_count > 3 ? ", …" : "") + ")");
            m.className = tt.others_count ? "bad" : "dim"; m.textContent = "touches: " + parts.join(" · "); el.appendChild(m);
          }
          const btn = function (label, fn, on) { const b = document.createElement("button"); b.textContent = label; b.disabled = !on; b.onclick = fn; el.appendChild(b); };
          btn("Show", function () { pick(c.slot); }, c.slot !== null);
          btn("Admit", function () { decide("admit", r.id, c.letter); }, c.slot !== null && c.verdict === "CLEAN" && !c.decided);
          btn("Reject", function () { decide("reject", r.id, c.letter); }, !c.decided);
          box.appendChild(el);
        }
      }
      if (st.last && st.last.what) {
        const l = document.createElement("div"); l.className = "dim";
        l.textContent = "last: " + st.last.what + (st.last.candidate ? " " + st.last.candidate : "") + (st.last.of ? " of #" + st.last.of : "") + (st.last.ledger ? " (ledger #" + st.last.ledger.join(", #") + ")" : "");
        box.appendChild(l);
      }
    };

    // ---------------------------------------------------------------- STUDIO-2: the worlds, the queue, the toasts
    const go = function (world, extra) { location.href = "/play.html?world=" + encodeURIComponent(world) + (extra || ""); };
    let worldsKey = "";
    const worldsShow = function (ws) {
      if (!ws) return;
      const key = JSON.stringify(ws);
      if (key === worldsKey) return;
      worldsKey = key;
      for (const id of ["st-world", "st-qworld"]) {
        const sel = $(id), was = sel.value;
        sel.innerHTML = "";
        for (const w of ws) {
          const o = document.createElement("option");
          o.value = w.world; o.textContent = w.world + (id === "st-world" && w.title ? " — " + w.title.slice(0, 40) : "");
          if (id === "st-world" ? w.world === brief : (was ? w.world === was : w.world === brief)) o.selected = true;
          sel.appendChild(o);
        }
      }
    };
    $("st-world").onchange = function () { const v = $("st-world").value; if (v && v !== brief) go(v); };
    $("st-dup").onclick = function () {
      const name = $("st-newname").value.trim();
      post("/studio/worlds/duplicate", { from: brief, name: name }).then(function (r) { note(r, "made world " + (r.world || "")); if (r.ok) go(r.world); });
    };
    let queueKey = "", seenNotice = performance.timeOrigin / 1000, optsKey = "";
    const toast = function (text, bad) {
      const el = document.createElement("div");
      el.textContent = text; if (bad) el.className = "bad";
      $("toasts").appendChild(el);
      setTimeout(function () { el.remove(); }, 8000);
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
        const el = document.createElement("div");
        el.className = "task " + t.status;
        const st = document.createElement("span"); st.className = "st"; st.textContent = t.status + (t.stale ? " (stale)" : "");
        el.appendChild(st);
        const u = t.usage || null;
        const cost = u ? (u.cost_usd !== null && u.cost_usd !== undefined ? "  $" + Number(u.cost_usd).toFixed(4) : "  " + (u.input_tokens || 0) + "+" + (u.output_tokens || 0) + " tokens") : "";
        el.appendChild(document.createTextNode(" " + t.world + " · " + t.prompt.slice(0, 48) + " · " + (t.model || t.provider.replace(/\.json$/, "")) + cost
          + (t.message && t.status !== "queued" ? " — " + (t.code ? t.code + ": " : "") + t.message.slice(0, 90) : "")));
        const btn = function (label, fn) { const b = document.createElement("button"); b.textContent = label; b.onclick = fn; el.appendChild(b); };
        if (t.status === "queued" || t.status === "running") btn("Cancel", function () { post("/studio/queue/cancel", { id: t.id }).then(function (r) { note(r, "cancelled " + t.id); }); });
        if (t.status === "ready") { btn("Review", function () { review(t); }); btn("Set aside", function () { post("/studio/queue/dismiss", { id: t.id }).then(function (r) { note(r, "set aside " + t.id); }); }); }
        if (t.status === "answered") btn("Set aside", function () { post("/studio/queue/dismiss", { id: t.id }).then(function (r) { note(r, "set aside " + t.id); }); });
        if (t.status === "answered" || t.status === "failed" || t.status === "cancelled" || t.status === "interrupted") btn("Queue again", function () { post("/studio/queue/requeue", { id: t.id }).then(function (r) { note(r, "queued again " + t.id); }); });
        box.appendChild(el);
      }
    };
    $("st-queue").onclick = function () {
      const c = eye();
      const w = $("st-qworld").value || brief;
      post("/studio/queue/add", { world: w, prompt: promptEl.value, provider: $("st-qprov").value, model: $("st-qmodel").value,
                                  camera: w === brief ? { x: c.x, y: c.y, z: c.z, yaw_deg: c.yaw / deg, pitch_deg: c.pitch / deg } : null })
        .then(function (r) { note(r, "queued " + (r.id || "") + " for " + w + " (its target and pins as they stand there); play on, it runs in the background"); });
    };
    if (q.get("review")) setTimeout(function () { review({ id: q.get("review"), world: brief }); }, 300);
    // 0220: the launcher's "Queue prompts" view: this world with the director's queue open
    if (q.get("panel") === "queue") setTimeout(function () { openPanel(); const ql = $("st-qlist"); if (ql && ql.scrollIntoView) ql.scrollIntoView(); }, 300);

    // the hooks a still, a walk-through or a test uses
    window.PLAY = {
      get renderer() { return R; }, get scene() { return S; }, get state() { return s; }, get world() { return world; },
      live: cur, sim: Sim, studio: studio, select: select, pin: pin, hover: function () { return studio.hover; },
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
    // B1: the page's heartbeat, which the supervisor reads in /healthz (the page has spoken; the window is alive)
    const alive = function () { post("/studio/alive", {}).catch(function () {}); };
    alive();
    setInterval(alive, 5000);
    // and its last word when the window goes (a reload says it too, then speaks again at once; the supervisor waits)
    window.addEventListener("pagehide", function () { try { navigator.sendBeacon("/studio/bye", token); } catch (e) { /* nothing to do */ } });

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
      // typing to the director is not playing: the panel's own keys, and nothing reaches the game
      if (e.target && /^(TEXTAREA|INPUT|BUTTON|SELECT)$/.test(e.target.tagName)) {
        if (e.code === "Escape") closePanel();
        else if (e.code === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); ask(); }
        return;
      }
      if (e.code === "KeyE" && mode === "play") select();
      if (e.code === "KeyR" && mode === "play") { pin(); return; }
      if (e.code === "Enter") { e.preventDefault(); openPanel(); return; }
      keys[e.code] = true;
      const n = parseInt(e.key, 10);
      if (n >= 1 && n <= views.length) { goView(views[n - 1]); overlay.style.display = "none"; }
      if (e.code === "Tab") { mode = "play"; label = "play"; e.preventDefault(); }
      if (e.code === "Backspace") { pending.reset = true; e.preventDefault(); }
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
      markRefs();
      const hv = pickPiece(), hroot = hv ? rootOf(hv.id) : null;
      studio.hover = hv ? { piece: hroot, address: addressOf({ id: hroot, region: hv.region }), tag: tagOf(hroot) } : null;
      const info = cur.slots[cur.k] || {}, sv = info.served || {};
      $("hud").textContent = "world " + brief + "  ·  " + (S.title || brief) + "  ·  " + label + "  ·  cell " + Math.floor(s.x / S.grid.cell) + "," + Math.floor(s.z / S.grid.cell)
        + "  ·  hits " + s.score + "\n" + views.map(function (v, i) { return (i + 1) + " " + v; }).join("  ") + "  ·  Tab play  ·  WASD, mouse, Space, Backspace reset  ·  E target, R pin, Enter director"
        + "\nunder the crosshair: " + (studio.hover ? studio.hover.address + (studio.hover.tag ? "  " + studio.hover.tag : "") : "nothing of the art")
        + (studio.refs.target ? "  ·  target " + studio.refs.target : "") + ((studio.refs.pins || []).length ? "  ·  pins " + studio.refs.pins.join(" ") : "")
        + "\nsource [" + cur.k + "] " + (info.label || "") + (sv.verdict ? "  ·  " + sv.verdict : "")
        + "  ·  scene " + cur.sha.slice(0, 12) + (cur.slots.length > 1 ? "  ·  [ ] steps through the " + cur.slots.length + " sources" : "")
        + "\nmovement and collision: the graybox's simulation against C  ·  live: play.py v" + cur.version
        + (cur.note && now - cur.noteAt < 8000 ? "\n" + cur.note : "");
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
})();
