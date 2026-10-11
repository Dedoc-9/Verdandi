// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/sim_worker.js — the simulation in a realm of its own, for the self-test and the trace experiment.
//
// The page sends a snapshot of the authoritative state, a map and a run of inputs; this steps them in a separate
// JavaScript realm (its own globals, its own Math, its own copy of sim.js) and sends back every tick's snapshot.
// With `offByOne`, it first replaces the named Math functions here, and only here, by ones whose every result has its
// last bit flipped: a counterfactual engine, to measure what a browser whose Math differs in the last bit would do to a
// run. With `kind: "trace"` (graybox/trace.py), it records the two runs the self-test uses and plays them, logging, in
// call order, every call of Math.sin, Math.cos, Math.hypot and Math.atan2 with its arguments' and its result's bits,
// and every tick's input and snapshot. The wrappers return what the engine returns; the page's realm is never touched.

importScripts("sim.js");

const TRACED = ["sin", "cos", "hypot", "atan2"];

function trace(Sim, map) {
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
    const runs = Sim.record(map), out = [];
    for (const run of runs) {
      phase = "play " + run.name;
      const world = new Sim.World(map), s = Sim.restore(run.start), inputs = [], snaps = [];
      for (let n = 0; n < run.inputs.length; n++) {
        const inp = run.inputs[n];
        inputs.push(JSON.stringify(Object.keys(inp).sort().map(function (k) {
          return [k, typeof inp[k] === "number" ? "f" + Sim.bits(inp[k]) : inp[k]];
        })));
        tick = n + 1;
        Sim.step(world, s, inp);
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
  const d = e.data, Sim = self.GrayboxSim, saved = {};
  try {
    if (d.kind === "trace") { self.postMessage({ id: d.id, trace: trace(Sim, d.map) }); return; }
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
