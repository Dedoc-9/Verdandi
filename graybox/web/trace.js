// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/trace.js — the page of the trace experiment (graybox/trace.py). A diagnostic, not a check: it decides
// nothing and is not part of the self-test.
//
// It asks a worker (sim_worker.js) to play the self-test's three runs under rules 0 and under rules 1, with Math.sin,
// Math.cos, Math.hypot, Math.atan2 and Math.sqrt logged call by call, and sends the log and every tick's state back with
// this browser's own description of itself. The runs are the ones the worker records, or, when trace.py was given a
// trace to take them from (`run --inputs`), that trace's: then every browser plays the same inputs. trace.py writes it
// to graybox/build/trace/ and compares two such traces, from two engines or two machines. With ?cases=1 it plays the
// input contract's table instead (web/input_cases.json), and sends back each step's outcome and state.

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
  const given = q.get("inputs") === "1", cases = q.get("cases") === "1", rules2 = q.get("rules2") === "1", ort = q.get("ort") === "1";
  if (ort) {   // ORT-1's table (web/ort_cases.json, graybox/ORT-1.md), played in a worker under rules 2 through ort.js
    Promise.all([
      fetch("/map/" + encodeURIComponent(name) + ".json").then(function (r) { if (!r.ok) throw new Error("the map " + name + " could not be loaded: " + r.status); return r.json(); }),
      fetch("/ort_cases.json").then(function (r) { if (!r.ok) throw new Error("ORT-1's table could not be loaded: " + r.status); return r.json(); }),
    ]).then(function (got) {
      return new Promise(function (resolve, reject) {
        const w = new Worker("sim_worker.js");
        w.onmessage = function (e) { w.terminate(); if (e.data.error) reject(new Error(e.data.error)); else resolve({ map: got[0], results: e.data.ort }); };
        w.onerror = function (e) { w.terminate(); reject(new Error(e.message || "the worker failed")); };
        w.postMessage({ kind: "ort", map: got[0], table: got[1] });
      });
    }).then(function (r) {
      out.textContent = "played " + (r.results.length - 1) + " cases of ORT-1; sending them to trace.py…";
      return post({ format: "VERDANDI-ORT-RESULTS", version: "1", map: name, manifest: r.map.manifest, runtime: runtime(), rules: 2, results: r.results });
    }).then(function () {
      out.textContent += "\ndone";
    }).catch(function (e) {
      out.textContent = String(e && e.stack || e);
      post({ format: "VERDANDI-ORT-RESULTS", version: "1", map: name, error: String(e && e.stack || e) });
    });
    return;
  }
  if (rules2) {   // rules 2's table (web/rules2_cases.json, graybox/RULES-2.md), played in a worker under rules 2
    Promise.all([
      fetch("/map/" + encodeURIComponent(name) + ".json").then(function (r) { if (!r.ok) throw new Error("the map " + name + " could not be loaded: " + r.status); return r.json(); }),
      fetch("/rules2_cases.json").then(function (r) { if (!r.ok) throw new Error("rules 2's table could not be loaded: " + r.status); return r.json(); }),
    ]).then(function (got) {
      return new Promise(function (resolve, reject) {
        const w = new Worker("sim_worker.js");
        w.onmessage = function (e) { w.terminate(); if (e.data.error) reject(new Error(e.data.error)); else resolve({ map: got[0], results: e.data.rules2 }); };
        w.onerror = function (e) { w.terminate(); reject(new Error(e.message || "the worker failed")); };
        w.postMessage({ kind: "rules2", map: got[0], table: got[1] });
      });
    }).then(function (r) {
      out.textContent = "played " + r.results.length + " cases of rules 2; sending them to trace.py…";
      return post({ format: "VERDANDI-RULES2-RESULTS", version: "1", map: name, manifest: r.map.manifest, runtime: runtime(), rules: 2, results: r.results });
    }).then(function () {
      out.textContent += "\ndone";
    }).catch(function (e) {
      out.textContent = String(e && e.stack || e);
      post({ format: "VERDANDI-RULES2-RESULTS", version: "1", map: name, error: String(e && e.stack || e) });
    });
    return;
  }
  if (cases) {   // the input contract's table (web/input_cases.json), played in a worker under rules 1
    Promise.all([
      fetch("/map/" + encodeURIComponent(name) + ".json").then(function (r) { if (!r.ok) throw new Error("the map " + name + " could not be loaded: " + r.status); return r.json(); }),
      fetch("/input_cases.json").then(function (r) { if (!r.ok) throw new Error("the table of cases could not be loaded: " + r.status); return r.json(); }),
    ]).then(function (got) {
      return new Promise(function (resolve, reject) {
        const w = new Worker("sim_worker.js");
        w.onmessage = function (e) { w.terminate(); if (e.data.error) reject(new Error(e.data.error)); else resolve({ map: got[0], table: got[1], cases: e.data.cases }); };
        w.onerror = function (e) { w.terminate(); reject(new Error(e.message || "the worker failed")); };
        w.postMessage({ kind: "cases", map: got[0], table: got[1] });
      });
    }).then(function (r) {
      out.textContent = "played " + r.cases.results.length + " cases of the input contract; sending them to trace.py…";
      return post({ format: "VERDANDI-INPUT-RESULTS", version: "1", map: name, manifest: r.map.manifest, runtime: runtime(),
                    contract: String(r.cases.contract), table: r.table.contract, results: r.cases.results });
    }).then(function () {
      out.textContent += "\ndone";
    }).catch(function (e) {
      out.textContent = String(e && e.stack || e);
      post({ format: "VERDANDI-INPUT-RESULTS", version: "1", map: name, error: String(e && e.stack || e) });
    });
    return;
  }
  Promise.all([
    fetch("/map/" + encodeURIComponent(name) + ".json").then(function (r) { if (!r.ok) throw new Error("the map " + name + " could not be loaded: " + r.status); return r.json(); }),
    given ? fetch("/inputs.json").then(function (r) { if (!r.ok) throw new Error("the given runs could not be loaded: " + r.status); return r.json(); }) : Promise.resolve(null),
  ]).then(function (got) {
    const map = got[0], inputs = got[1];
    return new Promise(function (resolve, reject) {
      const w = new Worker("sim_worker.js");
      w.onmessage = function (e) { w.terminate(); if (e.data.error) reject(new Error(e.data.error)); else resolve({ map: map, inputs: inputs, trace: e.data.trace }); };
      w.onerror = function (e) { w.terminate(); reject(new Error(e.message || "the worker failed")); };
      w.postMessage({ kind: "trace", map: map, runs: inputs ? inputs.runs : null });
    });
  }).then(function (r) {
    const body = { format: "VERDANDI-TRACE", version: "1", map: name, manifest: r.map.manifest, runtime: runtime(),
                   inputs_from: r.inputs ? r.inputs.from : null, rules: r.trace.rules };
    out.textContent = "traced, under rules 0, " + body.rules["0"].calls.length + " calls of the engine's Math, and under rules 1, "
      + body.rules["1"].calls.length + "; " + body.rules["1"].runs.length + " runs each; sending them to trace.py…";
    return post(body);
  }).then(function () {
    out.textContent += "\ndone";
  }).catch(function (e) {
    out.textContent = String(e && e.stack || e);
    post({ format: "VERDANDI-TRACE", version: "1", map: name, error: String(e && e.stack || e) });
  });
})();
