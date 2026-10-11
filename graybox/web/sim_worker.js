// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/sim_worker.js — the simulation in a realm of its own, for the self-test and the trace experiment.
//
// The page sends a snapshot of the authoritative state, a map and a run of inputs; this steps them in a separate
// JavaScript realm (its own globals, its own Math, its own copy of sim.js) and sends back every tick's snapshot, under
// the rules the message names (1, the default, or 0). With `offByOne`, it first replaces the named Math functions here,
// and only here, by ones whose every result has its last bit flipped: a counterfactual engine, to measure what a
// browser whose Math differs in the last bit would do to a run. With `kind: "trace"` (graybox/trace.py), it plays the
// runs under rules 0 and under rules 1 — the runs it records itself, or the runs the message gives, so that two
// browsers play the same inputs — logging, in call order, every call of Math.sin, Math.cos, Math.hypot, Math.atan2 and
// Math.sqrt with its arguments' and its result's bits (under rules 1 there should be none), and every tick's input and
// snapshot. The wrappers return what the engine returns; the page's realm is never touched. With `kind: "cases"`
// (trace.py run --cases), it plays the input contract's table under rules 1 and sends back each step's outcome and
// state.

importScripts("sim.js");

const TRACED = ["sin", "cos", "hypot", "atan2", "sqrt"];

// an input as the trace writes it (its keys in order, each number as "f" and the 16 hex digits of its bits), and back
function encodeInput(Sim, inp) {
  return JSON.stringify(Object.keys(inp).sort().map(function (k) { return [k, typeof inp[k] === "number" ? "f" + Sim.bits(inp[k]) : inp[k]]; }));
}
function decodeInput(Sim, text) {
  const o = {};   // each field an own property, "__proto__" too (an assignment would set the prototype and lose the field)
  for (const [k, v] of JSON.parse(text)) {
    Object.defineProperty(o, k, { value: typeof v === "string" && v.length === 17 && v[0] === "f" ? Sim.fromBits(v.slice(1)) : v,
                                  enumerable: true, writable: true, configurable: true });
  }
  return o;
}

function trace(Sim, map, given) {
  const calls = [], saved = {};
  let phase = "record", tick = -1;
  for (const fn of TRACED) {
    const f = saved[fn] = Math[fn];
    Math[fn] = function () {
      const r = f.apply(Math, arguments), a = [];
      for (let i = 0; i < arguments.length; i++) a.push(Sim.bits(arguments[i]));
      calls.push([phase, tick, fn, a.join(","), Sim.bits(r)]);
      return r;
    };
  }
  try {
    const runs = given ? given.map(function (r) { return { name: r.name, start: r.start, inputs: r.inputs.map(function (t) { return decodeInput(Sim, t); }) }; })
                       : Sim.record(map);
    const out = [];
    for (const run of runs) {
      phase = "play " + run.name;
      const world = new Sim.World(map), s = Sim.restore(run.start), inputs = [], snaps = [];
      for (let n = 0; n < run.inputs.length; n++) {
        inputs.push(encodeInput(Sim, run.inputs[n]));
        tick = n + 1;
        Sim.step(world, s, run.inputs[n]);
        snaps.push(Sim.snapshot(s));
      }
      tick = -1;
      out.push({ name: run.name, start: run.start, inputs: inputs, snaps: snaps });
    }
    return { calls: calls, runs: out };
  } finally {
    for (const fn in saved) Math[fn] = saved[fn];
  }
}

self.onmessage = function (e) {
  const d = e.data, Sim = d.rules === 0 ? self.GrayboxSim.withRules(0) : self.GrayboxSim, saved = {};
  try {
    if (d.kind === "cases") {   // the input contract's table (web/input_cases.json), under rules 1
      self.postMessage({ id: d.id, cases: { contract: self.GrayboxSim.INPUT, results: self.GrayboxSim.inputCases(d.map, d.table) } });
      return;
    }
    if (d.kind === "trace") {
      self.postMessage({ id: d.id, trace: { rules: { "0": trace(self.GrayboxSim.withRules(0), d.map, d.runs), "1": trace(self.GrayboxSim, d.map, d.runs) } } });
      return;
    }
    for (const fn of d.offByOne || []) {
      const f = saved[fn] = Math[fn];
      Math[fn] = function () { return Sim.nudge(f.apply(Math, arguments)); };
    }
    const world = new Sim.World(d.map), s = Sim.restore(d.snap), snaps = [];
    for (const inp of d.inputs) { Sim.step(world, s, inp); snaps.push(Sim.snapshot(s)); }
    self.postMessage({ id: d.id, snaps: snaps });
  } catch (err) {
    self.postMessage({ id: d.id, error: String(err && err.stack || err) });
  } finally {
    for (const fn in saved) Math[fn] = saved[fn];
  }
};
