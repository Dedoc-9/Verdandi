// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/trace.js — the page of the trace experiment (graybox/trace.py). A diagnostic, not a check: it decides
// nothing and is not part of the self-test.
//
// It asks a worker (sim_worker.js) to record and play the self-test's two runs with Math.sin, Math.cos, Math.hypot and
// Math.atan2 logged, call by call, and sends the log back with this browser's own description of itself. trace.py
// writes it to graybox/build/trace/ and compares two such traces, from two engines or two machines.

(function () {
  "use strict";
  const q = new URLSearchParams(location.search), name = q.get("map") || "tactical";
  const out = document.getElementById("out");
  const post = function (body) {
    return fetch("/trace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  };
  const runtime = function () {
    const n = navigator, d = n.userAgentData;
    return { userAgent: n.userAgent, brands: d ? d.brands.map(function (b) { return b.brand + " " + b.version; }) : null,
             platform: d ? d.platform : null, crossOriginIsolated: !!self.crossOriginIsolated };
  };
  fetch("/map/" + encodeURIComponent(name) + ".json").then(function (r) {
    if (!r.ok) throw new Error("the map " + name + " could not be loaded: " + r.status);
    return r.json();
  }).then(function (map) {
    return new Promise(function (resolve, reject) {
      const w = new Worker("sim_worker.js");
      w.onmessage = function (e) { w.terminate(); if (e.data.error) reject(new Error(e.data.error)); else resolve({ map: map, trace: e.data.trace }); };
      w.onerror = function (e) { w.terminate(); reject(new Error(e.message || "the worker failed")); };
      w.postMessage({ kind: "trace", map: map });
    });
  }).then(function (r) {
    const body = { format: "VERDANDI-TRACE", version: "0", map: name, manifest: r.map.manifest, runtime: runtime(),
                   calls: r.trace.calls, runs: r.trace.runs };
    out.textContent = "traced " + body.calls.length + " calls and " + body.runs.length + " runs; sending them to trace.py…";
    return post(body);
  }).then(function () {
    out.textContent += "\ndone";
  }).catch(function (e) {
    out.textContent = String(e && e.stack || e);
    post({ format: "VERDANDI-TRACE", version: "0", map: name, error: String(e && e.stack || e) });
  });
})();
