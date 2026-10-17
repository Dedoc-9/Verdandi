// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// art/web/page_test.js — PAGE-0 (0246): the studio page driven through its own controls, in a real browser.
//
// The host (art/page_test.py) lays the steps; this script takes them one at a time (POST /studio/page-test, which
// answers the next step), does each to the page in the frame as a person would — a key, a click on a control where the
// control is (lesson 75: the point is hit-tested first, and a control something covers is said, never clicked through;
// the key and the click themselves are synthetic events) —
// waits for what the page shows, and gives back what it saw. It decides nothing: whether a step held is the host's,
// read from the host's own state (the ledger, the request, the stills the page gave it). What a step reports is the
// page's words and states as a person would read them (its status line, its toasts, a card's buttons and chips, the
// preview's badge), so that the host can say the page showed what happened.
"use strict";
(function () {
  const token = document.body.getAttribute("data-studio") || "";
  const frame = document.getElementById("app"), logEl = document.getElementById("log");
  let win = null, doc = null, toasts = [], observer = null;
  const sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  const say = function (s) { logEl.textContent = (logEl.textContent + "\n" + s).split("\n").slice(-14).join("\n"); };
  const text = function (el) { return el ? (el.textContent || "").replace(/\s+/g, " ").trim() : ""; };
  const until = async function (fn, ms, what) {
    const t0 = performance.now();
    for (;;) {
      let v = null;
      try { v = fn(); } catch (e) { v = null; }
      if (v) return v;
      if (performance.now() - t0 > ms) throw new Error("waited " + Math.round(ms / 1000) + " s for " + what);
      await sleep(100);
    }
  };
  const $ = function (id) { return doc.getElementById(id); };
  const describe = function (n) {
    if (!n) return "nothing";
    return n.tagName.toLowerCase() + (n.id ? "#" + n.id : "") + (n.className && typeof n.className === "string" ? "." + n.className.trim().split(/\s+/).join(".") : "");
  };
  // a click where a person clicks (a synthetic one): the control must be the element at its own centre; a disabled control
  // is not pressed (a click on it does nothing, which is what a person meets too)
  const press = function (el, what) {
    if (!el) throw new Error("no " + what + " in the page");
    // 0248: a control found before the page redrew it is no longer in the page; it is said, never pressed
    if (!el.isConnected) throw new Error(what + " was replaced as the page redrew it, and is not pressed");
    if (el.scrollIntoView) el.scrollIntoView({ block: "nearest", inline: "nearest" });
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) throw new Error(what + " is not shown (" + Math.round(r.width) + " x " + Math.round(r.height) + ")");
    const hit = doc.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    if (!hit || !(hit === el || el.contains(hit))) throw new Error(what + " is covered by " + describe(hit));
    if (el.disabled) return "disabled";
    el.click();
    return "pressed";
  };
  const keydown = function (code, key, target, extra) {
    (target || doc.body).dispatchEvent(new win.KeyboardEvent("keydown", Object.assign({ code: code, key: key, bubbles: true, cancelable: true }, extra || {})));
  };
  const status = function () {
    const s = $("st-status");
    return { text: text(s), bad: !!(s && s.querySelector("span.bad")), good: !!(s && s.querySelector("span.good")) };
  };
  const req = function () { return win.PLAY && win.PLAY.studio && win.PLAY.studio.req; };
  const cards = function () { return Array.prototype.slice.call(doc.querySelectorAll("#c-list div.card[data-letter]")); };
  const cardOf = function (title) { return cards().filter(function (c) { return text(c.querySelector(".tt")) === title; })[0] || null; };
  const buttonOf = function (card, label) { return Array.prototype.slice.call(card.querySelectorAll(".acts button")).filter(function (b) { return text(b) === label; })[0] || null; };
  const cardSaid = function (card) {
    const bs = {};
    Array.prototype.slice.call(card.querySelectorAll(".acts button")).forEach(function (b) { bs[text(b)] = { disabled: !!b.disabled }; });
    return { letter: card.getAttribute("data-letter"), title: text(card.querySelector(".tt")), badge: text(card.querySelector(".st .badge")),
             chips: Array.prototype.slice.call(card.querySelectorAll(".hv")).map(function (h) { return { text: text(h), cls: h.className, title: h.getAttribute("title") || "" }; }),
             buttons: bs };
  };
  const openDrawer = async function () {
    if ($("studio").classList.contains("open")) return;
    keydown("Enter", "Enter");                                       // the key a person presses in the world (play.js)
    await until(function () { return $("studio").classList.contains("open"); }, 5000, "the director's drawer to open on Enter");
  };
  const closeDrawer = async function () {
    if (!$("studio").classList.contains("open")) return;
    press($("st-close"), "the drawer's close button");
    await until(function () { return !$("studio").classList.contains("open"); }, 5000, "the drawer to close");
  };
  const gpu = function () {
    try {
      const gl = document.createElement("canvas").getContext("webgl2");
      if (!gl) return "no webgl2";
      const x = gl.getExtension("WEBGL_debug_renderer_info");
      return x ? String(gl.getParameter(x.UNMASKED_RENDERER_WEBGL)) : String(gl.getParameter(gl.RENDERER));
    } catch (e) { return "unknown: " + e; }
  };

  const STEPS = {
    // the studio page opened in the frame, as the launcher opens it; ready when its shell is built and its director known
    open: async function (st) {
      frame.src = st.url;
      await until(function () { win = frame.contentWindow; doc = frame.contentDocument; return win && win.PLAY && doc.getElementById("toasts"); }, st.timeout_ms, "the studio page to build its shell");
      toasts = [];
      if (observer) observer.disconnect();
      observer = new MutationObserver(function (ms) {
        ms.forEach(function (m) { Array.prototype.forEach.call(m.addedNodes, function (n) { if (n.nodeType === 1) toasts.push({ text: text(n), bad: n.classList.contains("bad") }); }); });
      });
      observer.observe(doc.getElementById("toasts"), { childList: true });
      await until(function () { return win.PLAY.studio.provider && win.PLAY.studio.provider.configured; }, st.timeout_ms, "the page to read its director");
      const cv = doc.getElementById("view");
      return { title: doc.title, provider: text($("st-provider")), canvas: cv ? [cv.width, cv.height] : null, ua: navigator.userAgent, gpu: gpu(),
               slot: win.PLAY.live.k };
    },
    // the shape the host saved, as the page lists it in the drawer (it is read at the next poll)
    shapes: async function (st) {
      const b = await until(function () { return Array.prototype.slice.call(doc.querySelectorAll("#st-shapes button.tag")).filter(function (x) { return text(x) === "#" + st.name; })[0]; },
                            st.timeout_ms, "#" + st.name + " in the drawer's shapes");
      return { tag: text(b), gone: b.classList.contains("gone"), title: b.getAttribute("title") || "" };
    },
    // the director summoned with Enter, the shape put into the prompt by its tag, Strict ticked, Ask pressed; the request
    // followed to its end, as the drawer shows it
    ask: async function (st) {
      await openDrawer();
      const before = (req() || {}).id || "";
      const prompt = $("st-prompt");
      prompt.value = st.words;
      prompt.selectionStart = prompt.selectionEnd = prompt.value.length;
      const tag = Array.prototype.slice.call(doc.querySelectorAll("#st-shapes button.tag")).filter(function (x) { return text(x) === "#" + st.shape; })[0];
      const pressedTag = press(tag, "the shape's tag #" + st.shape);
      const strict = $("st-strict");
      if (!!strict.checked !== !!st.strict) press(strict, "the Strict box");
      const asked = press($("st-ask"), "Ask");
      const r = await until(function () { const q = req(); return q && q.id && q.id !== before && q.state !== "running" ? q : null; }, st.timeout_ms, "the request to end");
      await until(function () { return cards().length >= ((r.candidates || []).filter(function (c) { return c.slot !== null; }).length ? 1 : 0); }, 10000, "the candidates' cards");
      const said = { prompt: prompt.value, tag: pressedTag, strict: strict.checked, ask: asked, status: status(), drawer: text($("st-cands").firstChild),
                     request: { id: r.id, state: r.state, strict: r.strict, head: r.head, candidates: (r.candidates || []).map(function (c) { return { letter: c.letter, title: c.title, verdict: c.verdict, slot: c.slot }; }) } };
      await closeDrawer();
      return said;
    },
    // a candidate's card as the dock shows it: its buttons and whether each can be pressed, its chips and its badge
    card: async function (st) {
      const c = await until(function () { return cardOf(st.title); }, st.timeout_ms, "the card " + st.title);
      return cardSaid(c);
    },
    // the editor's camera put where the host says (the request's own framed path) through PLAY.cam, a hook: a person moves the
    // view there with the mouse and keys, which pointer lock keeps from a test
    camera: async function (st) {
      win.PLAY.cam(st.x, st.y, st.z, st.yaw_deg, st.pitch_deg);
      return { cam: win.PLAY.shell.cam };
    },
    // a card's button pressed; then what the page shows of it: the preview's window, or the status line and the toasts
    press: async function (st) {
      await closeDrawer();
      const c = await until(function () { return cardOf(st.title); }, 10000, "the card " + st.title);
      const t0 = toasts.length, s0 = status().text, cam0 = win.PLAY.shell.cam;
      const outcome = press(buttonOf(c, st.button), st.button + " on " + st.title);
      const out = { pressed: outcome, card: cardSaid(c), cam_before: cam0 };
      if (outcome === "disabled") { await sleep(1500); out.status = status(); out.toasts = toasts.slice(t0); return out; }
      if (st.button === "Preview") {
        await until(function () { return $("modal").classList.contains("open") || toasts.slice(t0).some(function (t) { return t.bad; }); }, st.timeout_ms, "the preview's window or a refusal");
        out.modal = $("modal").classList.contains("open");
        if (out.modal) {
          const b = $("m-title").querySelector(".hv");
          out.badge = { text: text(b), cls: b ? b.className : "", title: b ? b.getAttribute("title") || "" : "" };
          out.title = text($("m-title"));
          out.lines = Array.prototype.slice.call($("m-body").querySelectorAll("p.dim, div.dim")).map(text).slice(0, 8);
          press(Array.prototype.slice.call($("m-title").querySelectorAll("button")).filter(function (x) { return text(x) === "Close"; })[0], "the preview's Close");
        }
      } else {
        // an admission: the page takes its still, gives it to the host, then admits; its last word is the status line
        await until(function () { const s = status(); return s.text !== s0 && (s.good || s.bad) ? s : null; }, st.timeout_ms, "the page's word on " + st.button);
        out.cam_after = win.PLAY.shell.cam;          // the view the still was taken in is the view before and after it
      }
      await sleep(300);
      out.status = status();
      out.toasts = toasts.slice(t0);
      return out;
    },
    // Undo last admission, from the drawer
    undo: async function (st) {
      await openDrawer();
      const t0 = toasts.length, s0 = status().text;
      const outcome = press($("st-undo"), "Undo last admission");
      await until(function () { const s = status(); return s.text !== s0 && (s.good || s.bad) ? s : null; }, st.timeout_ms, "the page's word on the undo");
      const out = { pressed: outcome, status: status(), toasts: toasts.slice(t0) };
      await closeDrawer();
      return out;
    },
    // a card's Show, then the drawer's Original: what the view drew each time (its slot, and the scene it applied, which the
    // host holds against the scenes it serves in those slots). A slot counts as drawn when the scene served in it is the
    // one applied, not when it is chosen (pick sets the slot at once, and draws later)
    original: async function (st) {
      await closeDrawer();
      const live = win.PLAY.live;
      // drawn: the slot chosen and the scene served in it applied; and, when the host names the scene it serves there
      // (0247), that scene: the page's own list of slots is as old as its last read of /live, and may lag the host's
      const drawn = function (k, want) { const s = live.slots && live.slots[k]; return live.k === k && s && s.served && live.sha === s.served.sha && (!want || live.sha === want); };
      const held = await until(function () { return cardOf(st.title); }, 10000, "the card " + st.title);
      // 0247: when the host names them, the world it serves drawn first (the page's own may be older), so that Show must
      // draw a scene other than the one standing; and each press must make the view apply a scene (its count of swaps
      // grows), never only choose a slot whose scene happens to be the one already drawn
      if (st.want_world) await until(function () { return drawn(0, st.want_world); }, st.timeout_ms, "the world the host serves to be drawn first");
      // 0248: the page builds its cards again on every sync of its slots (shell.candidates empties the list). His run of
      // 0247 failed at this press, its error cut to "Show on Pane"; a Show found before such a sync (detached, 0 x 0) is
      // INFERRED, and a forced sync reproduced it. The cards are now drawn again on purpose here, after every wait, by a
      // hook (PLAY.slot(0), the function Original's button calls), so that the redraw is met in every run; the card is
      // found after it, in the same step as the press, where nothing can redraw between
      const first0 = doc.querySelector("#c-list div.card[data-letter]"), swr = live.swaps;
      win.PLAY.slot(0);
      await until(function () { const f = doc.querySelector("#c-list div.card[data-letter]"); return f && f !== first0 && live.swaps > swr && drawn(0, st.want_world); }, 10000, "the cards to be drawn again");
      const c = st.plant_card_held ? held : cardOf(st.title);     // the plant presses the card found before the redraw
      const k = ((req() || {}).candidates || []).filter(function (x) { return x.letter === (c && c.getAttribute("data-letter")); }).map(function (x) { return x.slot; })[0];
      if (k === undefined || k === null || k === 0) throw new Error("the card " + st.title + " has no slot of its own");
      const sw0 = live.swaps;
      const show = press(buttonOf(c, "Show"), "Show on " + st.title);
      await until(function () { return drawn(k, st.want_cand) && (!st.want_cand || live.swaps > sw0); }, st.timeout_ms, "the candidate's scene to be drawn");
      const shown = { k: live.k, sha: live.sha, swapped: live.swaps > sw0 };
      await openDrawer();
      const sw1 = live.swaps;
      const original = press($("st-original"), "Original");
      await until(function () { return drawn(0, st.want_world) && (!st.want_world || live.swaps > sw1); }, st.timeout_ms, "the world's own scene to be drawn again");
      const back = { k: live.k, sha: live.sha, swapped: live.swaps > sw1 };
      await closeDrawer();
      return { show: show, shown: shown, original: original, back: back };
    },
  };

  const post = function (body) {
    return fetch("/studio/page-test", { method: "POST", headers: { "Content-Type": "application/json", "X-Studio-Token": token }, body: JSON.stringify(body) })
      .then(function (r) { return r.json(); });
  };
  (async function loop() {
    let result = null, lost = 0;
    for (;;) {
      let step;
      try { step = await post({ result: result }); lost = 0; } catch (e) {
        // the host gone for a minute (its process ended without ending the test): the page under test is let go, so that a
        // browser left standing draws nothing
        if (++lost >= 120) { frame.src = "about:blank"; say("the host is gone: the test ends"); document.title = "PAGE TEST LOST ITS HOST"; return; }
        await sleep(500); continue;
      }
      result = null;
      if (!step || !step.ok || step.do === "wait") { if (!step || !step.ok) await sleep(500); continue; }
      if (step.do === "end") { say("the host ended the test"); document.title = "PAGE TEST ENDED"; return; }
      say("step " + step.n + ": " + step.do + (step.title ? " " + step.title : "") + (step.button ? " · " + step.button : ""));
      const t0 = performance.now();
      try {
        const fn = STEPS[step.do];
        if (!fn) throw new Error("no step " + step.do);
        result = Object.assign({ n: step.n, ok: true }, await fn(step));
      } catch (e) {
        result = { n: step.n, ok: false, error: String((e && e.message) || e), status: doc ? status() : null, toasts: toasts.slice(-6) };
      }
      result.ms = Math.round(performance.now() - t0);
      say("  " + (result.ok ? "done" : "FAILED: " + result.error) + " (" + result.ms + " ms)");
    }
  })();
})();
