// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// art/web/history.js — the History view (0220): a world's ledger read back (replayed to its files, under its lock),
// its events newest first, and its request record with each request's disposition, the record's chain, and what was
// asked for that the studio cannot make yet (telemetry, never a gate). Read-only: it holds only the window's
// heartbeat token. Everything a model wrote is shown as text.
(function () {
  "use strict";
  const $ = function (id) { return document.getElementById(id); };
  const presence = document.body.getAttribute("data-presence") || "";
  const world = new URLSearchParams(location.search).get("world") || "";
  const text = function (tag, cls, t) { const el = document.createElement(tag); if (cls) el.className = cls; el.textContent = t; return el; };
  const row = function (table, cells, head) {
    const tr = document.createElement("tr");
    for (const c of cells) { const td = document.createElement(head ? "th" : "td"); if (c && c.nodeType) td.appendChild(c); else td.textContent = c === undefined || c === null ? "" : String(c); tr.appendChild(td); }
    table.appendChild(tr);
  };

  fetch("/history.json?world=" + encodeURIComponent(world), { cache: "no-store" }).then(function (r) {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }).then(function (h) {
    document.title = "History of " + h.world + " — Verðandi Studio";
    $("title").textContent = "History of " + h.world + (h.inspect.title ? " — " + h.inspect.title : "");
    const v = $("verify"), i = h.inspect;
    v.textContent = "";
    if (i.verified) {
      v.appendChild(text("div", "ok", "Verified: the files are the bytes this ledger records (" + i.events + " events)."));
      v.appendChild(text("div", "dim", "That is integrity, not truth: it says what was admitted and in what order, not that the world is right."));
      const head = document.createElement("div");
      head.appendChild(document.createTextNode("head "));
      head.appendChild(text("code", "", i.head));
      v.appendChild(head);
      const last = document.createElement("div");
      last.appendChild(document.createTextNode("the ledger's last line, sha256 "));
      last.appendChild(text("code", "", i.last_line_sha256));
      v.appendChild(last);
      v.appendChild(text("div", "warn", "Not anchored: these two values live only in this world's folder, so a rewrite of the whole folder would not be noticed. Keep a copy of them elsewhere to make it noticeable."));
      const b = document.createElement("button");
      b.textContent = "Copy them";
      b.onclick = function () {
        const t = "Verðandi world " + h.world + ": " + i.events + " events; head " + i.head + "; ledger last line sha256 " + i.last_line_sha256;
        try { navigator.clipboard.writeText(t).then(function () { b.textContent = "Copied"; }, function () { b.textContent = "Select and copy the text above"; }); } catch (e) { b.textContent = "Select and copy the text above"; }
      };
      v.appendChild(b);
    } else {
      v.appendChild(text("div", "no", "Not verified: " + i.error));
    }
    const rec = h.records, rbox = $("records");
    rbox.textContent = "";
    rbox.appendChild(text("div", rec.breaks.length ? "no" : "ok", rec.lines + (rec.lines === 1 ? " line" : " lines") + " in the request record; " +
      (rec.breaks.length ? "the chain is broken at line " + rec.breaks.join(", ") : "its chain whole") +
      (rec.legacy ? " (" + rec.legacy + " lines from before the chain began)" : "") + (rec.unreadable.length ? "; " + rec.unreadable.length + " unreadable" : "")));
    const ds = Object.keys(rec.dispositions).sort().map(function (k) { return k + " " + rec.dispositions[k]; });
    rbox.appendChild(text("div", "", "dispositions: " + (ds.join(", ") || "none recorded yet")));
    const um = Object.keys(rec.unmet).sort(function (a, b) { return rec.unmet[b] - rec.unmet[a] || (a < b ? -1 : 1); }).map(function (k) { return k + " " + rec.unmet[k]; });
    if (um.length) rbox.appendChild(text("div", "warn", "asked for and not made yet: " + um.join(", ")));
    rbox.appendChild(text("div", "dim", "A line cut from the end of the record is not found here; that needs the last line's hash kept elsewhere."));
    const rq = $("requests");
    row(rq, ["when", "prompt", "came to", "why", "model"], true);
    for (const r of h.requests) row(rq, [r.at, r.prompt, r.disposition || r.outcome, r.detail, r.model]);
    const ev = $("events");
    row(ev, ["#", "kind", "when", "what"], true);
    for (const e of h.events) {
      let what = "";
      if (e.kind === "evaluate") what = "candidate " + e.candidate + " " + e.verdict + (e.codes && e.codes.length ? " " + e.codes.join(",") : "") + (e.again !== "" ? " (again, of #" + e.again + ")" : "") + " · " + e.prompt;
      else if (e.kind === "admit") what = "evaluation #" + e.evaluation + " admitted by " + e.chooser + " → head " + e.head_after + (e.note ? " · " + e.note : "");
      else if (e.kind === "refuse") what = "evaluation #" + e.evaluation + " refused by " + e.chooser + (e.note ? " · " + e.note : "");
      else if (e.kind === "rebase") what = "recorded a change made outside the loop" + (e.note ? " · " + e.note : "");
      else if (e.kind === "refuse_input") what = e.code + " · " + e.detail;
      else if (e.kind === "genesis") what = "the ledger began at head " + e.head;
      row(ev, [e.seq, e.kind, e.at, what]);
    }
  }).catch(function (e) { $("verify").textContent = ""; $("verify").appendChild(text("div", "no", "This view cannot open: " + e)); });

  const alive = function () {
    fetch("/studio/alive", { method: "POST", headers: { "Content-Type": "application/json", "X-Studio-Token": presence }, body: "{}" }).catch(function () {});
  };
  alive();
  setInterval(alive, 5000);
  window.addEventListener("pagehide", function () { try { navigator.sendBeacon("/studio/bye", presence); } catch (e) { /* nothing to do */ } });
})();
