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
  let win = null, doc = null, toasts = [], observer = null, left = 0;
  const sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  const say = function (s) { logEl.textContent = (logEl.textContent + "\n" + s).split("\n").slice(-14).join("\n"); };
  const text = function (el) { return el ? (el.textContent || "").replace(/\s+/g, " ").trim() : ""; };
  let stepEnd = Infinity;
  const until = async function (fn, ms, what) {
    const t0 = performance.now();
    ms = Math.min(ms, Math.max(0, stepEnd - t0));      // never past the step's own deadline
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
    // DASHBOARD-0 (0249): what the card says of the host's account (its badge, why Admit cannot be pressed, its names)
    const a = function (k) { return card.getAttribute(k) || ""; };
    return { letter: a("data-letter"), title: text(card.querySelector(".tt")), badge: text(card.querySelector(".st .badge")),
             chips: Array.prototype.slice.call(card.querySelectorAll(".hv")).map(function (h) { return { text: text(h), cls: h.className, title: h.getAttribute("title") || "" }; }),
             buttons: bs, acc: a("data-acc"), admit: a("data-admit"), why: text(card.querySelector(".why")), ev: text(card.querySelector(".ev")), drawn: text(card.querySelector(".drawn")),
             world: a("data-world"), head: a("data-head"), request: a("data-request"), scene: a("data-scene"), rev: ((win.PLAY.dash && win.PLAY.dash.rev) || {}).id || "" };
  };
  // DASHBOARD-0: the dock's Candidates tab shown (a hidden tab's controls measure 0 x 0 and are not pressed)
  const cardTab = function () {
    const list = $("c-list");
    if (list && list.hidden) press(doc.querySelector('#d-tabs button[data-dtab="candidates"]'), "the Candidates tab");
  };
  // a card once the host's account of it is of the revision the page last read (Admit is enabled by nothing else)
  const accounted = function (title, ms, rev) {
    return until(function () { const c = cardOf(title); return c && c.getAttribute("data-acc") === "current" && atRev(rev) ? c : null; }, ms,
                 "the host's account of " + title + " at the page's revision" + (rev ? " " + rev.slice(0, 8) : ""));
  };
  // the page has read the host's revision `rev` (when one is named): what it shows is then of that revision, whatever it says
  const atRev = function (rev) { return !rev || ((win.PLAY.dash && win.PLAY.dash.rev) || {}).id === rev; };
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
      // DASHBOARD-0 (0249): opened again, the page is the new document's (the old one stands until the frame navigates)
      const old = frame.contentDocument;
      frame.src = st.url;
      // DASHBOARD-0: a page that does not build its shell says what it showed (its state, its overlay's words), never only "waited"
      // what the frame's document was answered, from its resource timing (a request still waiting is not listed)
      const fetched = function (w) {
        try {
          return w.performance.getEntriesByType("resource").map(function (e) {
            const u = new URL(e.name);
            return u.pathname + ":" + (e.responseStatus === undefined ? "?" : e.responseStatus) + "@" + Math.round(e.startTime) + "+" + Math.round(e.duration);
          }).join(" ") || "nothing";
        } catch (e) { return "not read (" + e + ")"; }
      };
      const seen = function () {
        const d = frame.contentDocument, w = frame.contentWindow, o = d && d.getElementById("overlay");
        return "the document " + (d === old ? "not yet replaced" : (d ? d.readyState : "none")) + "; the shell " + (w && w.PLAY ? "built" : "not built") +
          "; its overlay " + (o && o.style.display !== "none" && text(o) ? JSON.stringify(text(o).slice(0, 200)) : "not shown") +
          "; its director " + (w && w.PLAY && w.PLAY.studio && w.PLAY.studio.provider && w.PLAY.studio.provider.configured ? "read" : "not read") +
          "; its scripts' globals " + ["GrayboxSim", "VerdandiScene", "StudioUI"].map(function (g) { return g + (w && w[g] ? "" : " MISSING"); }).join(", ") +
          "; what it fetched and was answered (path:status@start+ms) " + fetched(w);
      };
      try {
        await until(function () { win = frame.contentWindow; doc = frame.contentDocument; return doc !== old && win && win.PLAY && doc.getElementById("toasts"); }, st.timeout_ms, "the studio page to build its shell");
      } catch (e) { throw new Error(e.message + " (" + seen() + ")"); }
      // DASHBOARD-0 (0250): a navigation the page itself begins away from the document opened here is counted
      left = 0;
      win.addEventListener("beforeunload", function () { left++; });
      win.addEventListener("pagehide", function () { left++; });
      for (const k in held) delete held[k];
      toasts = [];
      if (observer) observer.disconnect();
      observer = new MutationObserver(function (ms) {
        ms.forEach(function (m) { Array.prototype.forEach.call(m.addedNodes, function (n) { if (n.nodeType === 1) toasts.push({ text: text(n), bad: n.classList.contains("bad") }); }); });
      });
      observer.observe(doc.getElementById("toasts"), { childList: true });
      try {
        await until(function () { return win.PLAY.studio.provider && win.PLAY.studio.provider.configured; }, st.timeout_ms, "the page to read its director");
      } catch (e) { throw new Error(e.message + " (" + seen() + ")"); }
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
      cardTab();
      await until(function () { return cardOf(st.title); }, st.timeout_ms, "the card " + st.title);
      return cardSaid(await accounted(st.title, st.timeout_ms, st.rev));
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
      cardTab();
      await until(function () { return cardOf(st.title); }, 10000, "the card " + st.title);
      // DASHBOARD-0: Admit is pressed once the card's account is of the page's revision (it is enabled by nothing else); the
      // card is found again after that wait, in the step that presses it
      if (/^Admit/.test(st.button)) await accounted(st.title, Math.min(st.timeout_ms, 120000), st.rev);
      const c = cardOf(st.title);
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
      cardTab();
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

    // ---------------------------------------------------------------- DASHBOARD-0 (0249): PAGE-CARDS (art/page_dash.py)
    // every panel as a person reads it: its state, the words of its badge (or why, for a panel with none), the revision
    // the page holds; when `wait` names a state, until every panel named in `panels` says it (or one of them, bounded)
    panels: async function (st) {
      const read = function () {
        const out = {};
        Array.prototype.slice.call(doc.querySelectorAll("[data-panel]")).forEach(function (n) {
          const b = n.querySelector(":scope > .pstate");
          out[n.getAttribute("data-panel")] = { state: n.getAttribute("data-state") || "", why: n.getAttribute("data-state-why") || "", badge: text(b), shown: !n.hidden && n.getBoundingClientRect().width > 0,
                                               revless: n.getAttribute("data-revless") === "1" };
        });
        return out;
      };
      if (st.wait) await until(function () { const p = read(); return (st.panels || []).every(function (k) { return p[k] && st.wait.indexOf(p[k].state) >= 0; }) ? p : null; }, st.timeout_ms, "the panels " + (st.panels || []).join(", ") + " to say " + st.wait.join(" or "));
      const d = win.PLAY.dash;
      return { panels: read(), rev: (d.rev || {}).id || "", settled: (d.rev || {}).settled, chips: text($("cx-chips")), undo_chip: text($("cx-undo")), source: text(Array.prototype.slice.call(doc.querySelectorAll("#cx-chips .chip")).filter(function (c) { return /^Source/.test(text(c)); })[0]),
               revision: text(Array.prototype.slice.call(doc.querySelectorAll("#cx-chips .chip")).filter(function (c) { return /^Revision/.test(text(c)); })[0]),
               worlds: Array.prototype.slice.call(doc.querySelectorAll("[data-world]")).map(function (n) { return n.getAttribute("data-world"); }),
               html_has: st.marker ? doc.body.innerHTML.indexOf(st.marker) >= 0 : null };
    },
    // a tab of the dock pressed (as a person does), and its body once the host's answer is drawn in it
    tab: async function (st) {
      const b = doc.querySelector('#d-tabs button[data-dtab="' + st.tab + '"]');
      const body = { candidates: "c-list", queue: "q-list", validation: "v-body", evidence: "e-body" }[st.tab];
      const a0 = ($(body) || {}).dataset ? $(body).dataset.answers || "0" : "0";
      const pressed = press(b, "the " + st.tab + " tab");
      // a tab that reads the host (Validation, Evidence) is read once its new answer is drawn, never the one before it
      if (st.tab === "validation" || (st.tab === "evidence" && $(body).dataset.answers !== undefined)) await until(function () { return ($(body).dataset.answers || "0") !== a0; }, st.timeout_ms, "the " + st.tab + " tab's new answer");
      await until(function () { const n = $(body); return n && !n.hidden && (st.tab === "candidates" || n.children.length > 1 || n.getAttribute("data-refused")) ? n : null; }, st.timeout_ms, "the " + st.tab + " tab's body");
      // Validation read at a version the host names: whatever it then says is of that version (a row reads it)
      if (st.live !== undefined) await until(function () { const v = win.PLAY.dash.ui.vAnswer; return v && v.version === st.live && $(body).getAttribute("data-state") === "current"; }, st.timeout_ms, "the Validation tab's answer of v" + st.live + ", current");
      if (st.want) await until(function () { return text($(body)).indexOf(st.want) >= 0; }, st.timeout_ms, "the " + st.tab + " tab to say " + st.want);
      if (st.state) await until(function () { return st.state.indexOf($(body).getAttribute("data-state")) >= 0; }, st.timeout_ms, "the " + st.tab + " tab to be " + st.state.join(" or "));
      const n = $(body);
      return { pressed: pressed, state: n.getAttribute("data-state") || "", why: n.getAttribute("data-state-why") || "", refused: n.getAttribute("data-refused") || "", text: text(n).slice(0, 4000),
               first: text(n.querySelector(".vrow")), refusedRow: text(n.querySelector(".vrow.refused")), sum: text(n.querySelector(".vsum")),
               rows: n.querySelectorAll(".vrow").length, adm: text(n.querySelector(".vrow.adm")), next: text(n.querySelector(".chknext")),
               items: Array.prototype.slice.call(n.querySelectorAll(".vrow.chk")).map(function (r) { return { item: r.getAttribute("data-item"), status: r.getAttribute("data-status") }; }),
               tasks: Array.prototype.slice.call(n.querySelectorAll(".task")).map(text) };
    },
    // a queued task's Cancel, pressed in the Queue tab
    queue_cancel: async function (st) {
      const t = await until(function () { return Array.prototype.slice.call(doc.querySelectorAll("#q-list .task")).filter(function (x) { return text(x).indexOf(st.words) >= 0; })[0]; }, st.timeout_ms, "the task in the Queue tab");
      const b = Array.prototype.slice.call(t.querySelectorAll("button")).filter(function (x) { return text(x) === "Cancel"; })[0];
      return { pressed: press(b, "the task's Cancel") };
    },
    // a card's Evidence pressed (the Candidates tab first), and the Evidence tab once it shows the host's answer
    evidence: async function (st) {
      cardTab();
      await until(function () { return cardOf(st.title); }, st.timeout_ms, "the card " + st.title);
      const c = cardOf(st.title);
      const a0 = $("e-body").dataset.answers || "0";
      const pressed = press(buttonOf(c, "Evidence"), "Evidence on " + st.title);
      await until(function () { const n = $("e-body"); return !n.hidden && (n.dataset.answers || "0") !== a0 && (n.querySelector(".vrow.adm") || n.getAttribute("data-refused")) ? n : null; }, st.timeout_ms, "the Evidence tab to show the host's new answer");
      const n = $("e-body");
      return { pressed: pressed, state: n.getAttribute("data-state") || "", refused: n.getAttribute("data-refused") || "", adm: text(n.querySelector(".vrow.adm")), next: text(n.querySelector(".chknext")),
               items: Array.prototype.slice.call(n.querySelectorAll(".vrow.chk")).map(function (r) { return { item: r.getAttribute("data-item"), status: r.getAttribute("data-status") }; }), text: text(n).slice(0, 3000) };
    },
    // the statistics box as a person reads it, its titles too
    stats: async function (st) {
      const s = $("stats");
      await until(function () { return s.querySelector(".stitle"); }, st.timeout_ms, "the statistics");
      const spans = Array.prototype.slice.call(s.querySelectorAll("span"));
      const rows = {};
      for (let i = 0; i + 1 < spans.length; i += 2) rows[text(spans[i])] = { value: text(spans[i + 1]), title: spans[i].getAttribute("title") || "" };
      return { stitle: text(s.querySelector(".stitle")), rows: rows };
    },
    // the face frames the page's script holds (studio_ui.js), for the host to hold against MARK-0's (art/studio_marks.py)
    frames: async function (st) {
      const U = win.StudioUI, out = {};
      for (const f of Object.keys(U.FRAMES)) { const F = U.FRAMES[f](st.box); out[f] = { o: F.o, u: F.u, v: F.v, W: F.W, H: F.H, n: U.NORMALS[f] }; }
      return { frames: out };
    },
    // the strip's controls held, a redraw forced (the world's slot chosen again: a scene applied, the menus built again),
    // and whether they are the same elements; a card held beside them is the positive control (the cards are built again)
    strip: async function (st) {
      cardTab();
      const u0 = $("mb-undo"), x0 = $("cx-undo"), n0 = doc.querySelector("#c-list div.card.new"), sw = win.PLAY.live.swaps, m0 = doc.querySelector("#menus .menu");
      win.PLAY.slot(0);
      await until(function () { return win.PLAY.live.swaps > sw && doc.querySelector("#menus .menu") !== m0; }, st.timeout_ms, "a scene applied and the menus built again");
      const n1 = doc.querySelector("#c-list div.card.new");
      return { undo_same: u0 === $("mb-undo") && u0.isConnected, chip_same: x0 === $("cx-undo") && x0.isConnected, menus_rebuilt: doc.querySelector("#menus .menu") !== m0,
               card_replaced: !!n0 && (!n0.isConnected || n0 !== n1) };
    },
    // a card element kept, and later reported: whether it is still in the page, the same element, and what it says
    hold: async function (st) {
      cardTab();
      held[st.title] = await until(function () { return cardOf(st.title); }, st.timeout_ms, "the card " + st.title);
      return cardSaid(held[st.title]);
    },
    held: async function (st) {
      const h = held[st.title];
      if (st.rev) await until(function () { return h && h.getAttribute("data-acc") === "current" && atRev(st.rev) ? h : null; }, st.timeout_ms, "the held card's account at the host's revision " + st.rev.slice(0, 8));
      if (st.wait) await until(function () { return h && h.getAttribute("data-acc") === "current" && st.wait.indexOf(h.getAttribute("data-admit")) >= 0 ? h : null; }, st.timeout_ms, "the held card's account to say " + st.wait.join(" or "));
      return { same: !!h && h.isConnected && h === cardOf(st.title), card: h ? cardSaid(h) : null, cards_state: $("c-list").getAttribute("data-state") || "" };
    },
    // a card read without waiting for its account (what it says now), or once its account says one of `wait`
    card_now: async function (st) {
      cardTab();
      const c = await until(function () {
        const x = cardOf(st.title);
        return x && (!st.wait || (x.getAttribute("data-acc") === "current" && st.wait.indexOf(x.getAttribute("data-admit")) >= 0))
          && (!st.rev || (x.getAttribute("data-acc") === "current" && atRev(st.rev)))
          && (!st.state || st.state.indexOf($("c-list").getAttribute("data-state")) >= 0) ? x : null;
      }, st.timeout_ms, "the card " + st.title + (st.wait ? " to say " + st.wait.join(" or ") : "") + (st.state ? ", the cards " + st.state.join(" or ") : ""));
      return Object.assign(cardSaid(c), { cards_state: $("c-list").getAttribute("data-state") || "" });
    },
    // the strip's Undo pressed (or the Edit menu's): what the page says of what came back
    undo_strip: async function (st) {
      await closeDrawer();
      const t0 = toasts.length, s0 = status().text;
      let label = "", outcome;
      // what Undo undoes read at the host's revision (when named), in the strip and the menu alike
      if (st.rev) await until(function () { const x = $("mb-undo"); return x && x.getAttribute("data-state") === "current" && atRev(st.rev) ? x : null; }, st.timeout_ms, "Undo's account read at the host's revision");
      if (st.menu) {
        const mb = Array.prototype.slice.call(doc.querySelectorAll("#menus .menu > button")).filter(function (b) { return text(b) === "Edit"; })[0];
        press(mb, "the Edit menu");
        const it = await until(function () { return Array.prototype.slice.call(doc.querySelectorAll("#menus .menu.open .drop button")).filter(function (b) { return /^Undo admission/.test(text(b)); })[0]; }, 5000, "the Edit menu's Undo");
        label = text(it);
        if (!st.press) { press(mb, "the Edit menu"); return { label: label, disabled: !!it.disabled }; }
        outcome = press(it, "the Edit menu's Undo");
        if (outcome === "disabled") throw new Error("the Edit menu's Undo is disabled: " + label);
      } else {
        const b = await until(function () { const x = $("mb-undo"); return x && !x.disabled ? x : null; }, st.timeout_ms, "the strip's Undo to be enabled");
        label = text(b);
        outcome = press(b, "the strip's Undo");
      }
      await until(function () { const s = status(); return s.text !== s0 && (s.good || s.bad) ? s : null; }, st.timeout_ms, "the page's word on the undo");
      await sleep(300);
      return { label: label, pressed: outcome, status: status(), toasts: toasts.slice(t0), chip: text($("cx-undo")) };
    },
    // DASHBOARD-0 (0250): the left panel as the page shows it — the worlds' rows, the outline's objects, import's briefs, its
    // staged record and its last word, the collapse, the three panels' marks, every data-world in the page — once the
    // named conditions hold (each a fact of the page, never a host's value: a plant fails its row, not a wait)
    lp: async function (st) {
      const attr = function (n, a) { return n ? n.getAttribute(a) || "" : ""; };
      const read = function () {
        const panel = function (id) { const n = $(id); return n ? { state: attr(n, "data-state"), why: attr(n, "data-state-why"), refused: attr(n, "data-refused"), answers: +(attr(n, "data-answers") || 0),
                                                           forced: +(attr(n, "data-forced") || 0), text: text(n).slice(0, 3000) } : null; };
        const said = doc.querySelector("#lp-import .lpsaid"), stg = doc.querySelector("#lp-import .lpstaged"), u = win.PLAY.shell.ui;
        return { worlds: Array.prototype.slice.call(doc.querySelectorAll("#lp-worlds .lpw")).map(function (r) {
                   return { name: attr(r, "data-wname"), state: attr(r, "data-wstate"), code: attr(r, "data-wcode"), events: +attr(r, "data-wevents"), head: attr(r, "data-whead"), text: text(r) }; }),
                 outline: Array.prototype.slice.call(doc.querySelectorAll("#lp-outline .lpo")).map(function (b) { return attr(b, "data-oid"); }),
                 outline_head: text(doc.querySelector("#lp-outline > p.dim")), outline_shown: attr(doc.querySelector("#lp-outline .lpcount"), "data-shown"),
                 importable: Array.prototype.slice.call(doc.querySelectorAll("#lp-import .lpi")).map(function (b) { return attr(b, "data-iname"); }),
                 staged: stg ? { staging: attr(stg, "data-staging"), sha: attr(stg, "data-sha"), text: text(stg) } : null,
                 said: said ? text(said) : "", said_code: attr(said, "data-code"), committed: attr(said, "data-committed"),
                 open_offered: !!doc.querySelector("#lp-import button[data-act=open]"),
                 panels: { worlds: panel("lp-worlds"), outline: panel("lp-outline"), import: panel("lp-import"), validation: panel("v-body") },
                 collapsed: doc.body.classList.contains("leftcollapsed"), columns: win.getComputedStyle($("work")).gridTemplateColumns,
                 data_worlds: Array.prototype.slice.call(doc.querySelectorAll("[data-world]")).map(function (n) { return attr(n, "data-world"); }),
                 html_has: st.marker ? doc.body.innerHTML.indexOf(st.marker) >= 0 : null, brief: attr(doc.body, "data-brief"),
                 left: left, same_doc: frame.contentDocument === doc, href: String((frame.contentWindow || {}).location && frame.contentWindow.location.search || ""),
                 sel: (u && u.sel) || "", info: u && u.info ? { piece: u.info.piece || u.info.id || "", world: u.info.world || "" } : null };
      };
      // the worlds' periodic read, set for a row that must see what the mark alone asks for (PLAY.shell.ui, a hook)
      if (st.set_every !== undefined) win.PLAY.shell.ui.worldsEvery = st.set_every;
      const c = st.until || {};
      const holds = function (x) {
        if (c.worlds_any && !x.worlds.length) return false;
        if (c.forced_gt !== undefined && !((x.panels.worlds || {}).forced > c.forced_gt)) return false;
        if (c.rev_refused && !((((win.PLAY.dash || {}).rev || {}).slots || [])[0] || {}).refused_sha256) return false;
        if (c.world_state && !x.worlds.some(function (w) { return w.name === c.world_state[0] && w.state === c.world_state[1]; })) return false;
        if (c.outline_any && !x.outline.length) return false;
        if (c.outline_answers_gt !== undefined && !((x.panels.outline || {}).answers > c.outline_answers_gt)) return false;
        if (c.importable_any && !x.importable.length) return false;
        if (c.staged && !x.staged) return false;
        if (c.said_code && !x.said_code) return false;
        if (c.committed && !x.committed) return false;
        if (c.sel && x.sel !== c.sel) return false;
        if (c.info && !(x.info && x.info.piece)) return false;
        if (c.panel_state && !c.panel_state[1].some(function (s) { return ((x.panels[c.panel_state[0]] || {}).state || "") === s; })) return false;
        return true;
      };
      if (Object.keys(c).length) await until(function () { const x = read(); return holds(x) ? x : null; }, st.timeout_ms, "the left panel: " + JSON.stringify(c));
      return read();
    },
    // a control of the left panel pressed as a person does (its centre hit-tested first: collapsed, it is not shown)
    lp_press: async function (st) {
      const q = { toggle: "#lp-toggle", wrefresh: "#lp-wrefresh", irefresh: "#lp-irefresh", commit: "#lp-import button[data-act=commit]",
                  discard: "#lp-import button[data-act=discard]" }[st.what];
      const b = q ? doc.querySelector(q) : st.what === "stage" ? doc.querySelector('#lp-import .lpi[data-iname="' + st.name + '"] button[data-act=stage]')
        : st.what === "object" ? Array.prototype.slice.call(doc.querySelectorAll("#lp-outline .lpo")).filter(function (x) { return x.getAttribute("data-oid") === st.name; })[0] : null;
      return { pressed: press(b, "the left panel's " + st.what + (st.name ? " " + st.name : "")) };
    },
    // the outline's search, typed
    lp_search: async function (st) {
      const i = $("lp-search");
      i.value = st.text;
      i.dispatchEvent(new win.Event("input", { bubbles: true }));
      return { shown: Array.prototype.slice.call(doc.querySelectorAll("#lp-outline .lpo")).map(function (b) { return b.getAttribute("data-oid"); }) };
    },
    // the restoration chip, once it says (or no longer says) a phrase
    chip: async function (st) {
      if (st.has !== undefined) await until(function () { return (text($("cx-undo")).indexOf(st.phrase) >= 0) === st.has; }, st.timeout_ms, "the restoration chip " + (st.has ? "to say " : "to stop saying ") + st.phrase);
      return { chip: text($("cx-undo")), bad: $("cx-undo").classList.contains("bad") };
    },
    // Compare, from the bar (outside Mark mode): what its window says Current is
    compare: async function (st) {
      await closeDrawer();
      const pressed = press($("mb-compare"), "Compare");
      await until(function () { return $("modal").classList.contains("open") && $("m-body").querySelector(".cmpbase"); }, st.timeout_ms, "the Compare window");
      const split = $("m-body").querySelector(".split");
      const out = { pressed: pressed, title: text($("m-title")), said: text($("m-body").querySelector(".cmpbase")), state: split ? split.getAttribute("data-state") : "",
                    base: split ? split.getAttribute("data-base") : "" };
      press(Array.prototype.slice.call($("m-title").querySelectorAll("button")).filter(function (x) { return text(x) === "Close"; })[0], "the Compare window's Close");
      return out;
    },
  };
  const held = {};

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
        stepEnd = performance.now() + (step.timeout_ms || 60000);
        result = Object.assign({ n: step.n, ok: true }, await fn(step));
      } catch (e) {
        result = { n: step.n, ok: false, error: String((e && e.message) || e), status: doc ? status() : null, toasts: toasts.slice(-6) };
      }
      result.ms = Math.round(performance.now() - t0);
      say("  " + (result.ok ? "done" : "FAILED: " + result.error) + " (" + result.ms + " ms)");
    }
  })();
})();
