// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// art/web/start.js — the studio's first window (0220, the owner's direction of 2026-10-13: "when i click the desktop
// icon a window should open asking what part of the studio should open first; different abstractions can be added as
// be design"). It lists the worlds, each read back (its ledger replayed to its files, under its lock), and the views,
// one manifest each (art/web/views/); a view is added by adding a manifest. It holds no authority: it is served with a
// token good only for the window's heartbeat, so it cannot ask, admit, reject or undo. A view that cannot open says
// why. The remembered first view is a preference of this window's browser profile, never part of a world.
(function () {
  "use strict";
  const $ = function (id) { return document.getElementById(id); };
  const presence = document.body.getAttribute("data-presence") || "";
  const KEY = "verdandi.studio.first";
  let chosen = null, data = null, autoTimer = null;

  const remembered = function () {
    try { const v = JSON.parse(localStorage.getItem(KEY) || "null"); return v && typeof v.view === "string" ? v : null; } catch (e) { return null; }
  };
  const remember = function (v) {
    try { if (v) localStorage.setItem(KEY, JSON.stringify(v)); else localStorage.removeItem(KEY); } catch (e) { /* a preference only */ }
  };
  const text = function (tag, cls, t) { const el = document.createElement(tag); if (cls) el.className = cls; el.textContent = t; return el; };
  const urlOf = function (v, world) { return "/" + v.open.split("{world}").join(encodeURIComponent(world || "")); };

  const open = function (v) {
    if (!v || v.status !== "ready") return;
    if (v.needs_world && !chosen) return;
    if ($("remember").checked) remember({ view: v.id, world: chosen }); else remember(null);
    location.href = urlOf(v, chosen);
  };

  const showWorlds = function () {
    const box = $("worlds");
    box.innerHTML = "";
    if (!data.worlds.length) { box.appendChild(text("div", "err", "No world is here yet.")); return; }
    for (const w of data.worlds) {
      const lab = document.createElement("label");
      lab.className = "world" + (w.world === chosen ? " on" : "");
      const r = document.createElement("input");
      r.type = "radio"; r.name = "world"; r.checked = w.world === chosen;
      r.onchange = function () { chosen = w.world; showWorlds(); showViews(); };
      lab.appendChild(r);
      lab.appendChild(text("span", "t", w.world));
      lab.appendChild(text("div", "s", w.title || ""));
      const st = document.createElement("div");
      st.className = "s";
      if (w.verified) {
        st.appendChild(text("span", "ok", "verified "));
        st.appendChild(document.createTextNode(w.events + " events, head " + w.head.slice(0, 12) + (w.anchored ? "" : " · not anchored outside the world folder")));
      } else if (w.fresh) {
        st.appendChild(document.createTextNode("new: its ledger starts when it is first opened"));
      } else {
        st.appendChild(text("span", "no", "not verified: "));
        st.appendChild(document.createTextNode(w.error));
      }
      lab.appendChild(st);
      box.appendChild(lab);
    }
  };

  const card = function (v) {
    const el = document.createElement("div");
    const ready = v.status === "ready";
    el.className = "view" + (ready ? "" : " off");
    el.appendChild(text("div", "t", v.title));
    el.appendChild(text("div", "s", v.summary));
    el.appendChild(text("div", "badge", (v.capability === "inspect" ? "reads only" : "proposes; you admit") + (ready ? "" : " · " + v.status)));
    if (!ready) el.appendChild(text("div", "why", v.why));
    const b = document.createElement("button");
    b.textContent = ready ? "Open" : "Not available";
    b.disabled = !ready || (v.needs_world && !chosen);
    b.onclick = function () { open(v); };
    el.appendChild(b);
    return el;
  };

  const showViews = function () {
    $("paint").innerHTML = ""; $("deep").innerHTML = "";
    for (const v of data.views) $(v.level === "paint" ? "paint" : "deep").appendChild(card(v));
  };

  const auto = function () {
    const r = remembered();
    if (!r) return;
    const v = data.views.find(function (x) { return x.id === r.view; });
    const worldOk = !v || !v.needs_world || data.worlds.some(function (w) { return w.world === r.world; });
    if (!v || v.status !== "ready" || !worldOk) {
      $("auto").style.display = "block";
      $("auto").textContent = "The view you chose to open first is not available now" + (v ? " (" + (v.status !== "ready" ? v.why : "no world " + r.world) + ")" : "") + "; choose again.";
      remember(null);
      return;
    }
    chosen = v.needs_world ? r.world : chosen;
    $("remember").checked = true;
    let n = 3;
    const box = $("auto");
    box.style.display = "block";
    const say = function () {
      box.textContent = "";
      box.appendChild(document.createTextNode("Opening " + v.title + (v.needs_world ? " in " + r.world : "") + " in " + n + " s  "));
      const stay = document.createElement("button");
      stay.textContent = "Stay here";
      stay.onclick = function () { clearInterval(autoTimer); box.textContent = "Staying here."; };
      box.appendChild(stay);
    };
    say();
    autoTimer = setInterval(function () { n -= 1; if (n <= 0) { clearInterval(autoTimer); open(v); } else say(); }, 1000);
  };

  fetch("/launcher.json", { cache: "no-store" }).then(function (r) { return r.json(); }).then(function (d) {
    data = d;
    const def = d.worlds.find(function (w) { return w.default; }) || d.worlds[0];
    chosen = def ? def.world : null;
    showWorlds();
    showViews();
    $("foot").textContent = "Each world is checked when this window opens: its ledger replayed to its files. Verified means the files are the bytes the ledger records; it does not mean the world is right. " +
      (d.mode === "worlds" ? "The worlds live in your per-user folder." : "Serving one tree.");
    auto();
  }).catch(function (e) { $("worlds").textContent = ""; $("worlds").appendChild(text("div", "err", "The studio did not answer: " + e)); });

  // the window's heartbeat and goodbye, as the play page's (the supervisor reads them); this token is good for nothing else
  const alive = function () {
    fetch("/studio/alive", { method: "POST", headers: { "Content-Type": "application/json", "X-Studio-Token": presence }, body: "{}" }).catch(function () {});
  };
  alive();
  setInterval(alive, 5000);
  window.addEventListener("pagehide", function () { try { navigator.sendBeacon("/studio/bye", presence); } catch (e) { /* nothing to do */ } });
})();
