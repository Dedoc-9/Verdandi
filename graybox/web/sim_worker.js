// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/sim_worker.js — the simulation in a realm of its own, for the self-test only.
//
// The page sends a snapshot of the authoritative state, a map and a run of inputs; this steps them in a separate
// JavaScript realm (its own globals, its own Math, its own copy of sim.js) and sends back every tick's snapshot.
// With `offByOne`, it first replaces the named Math functions here, and only here, by ones whose every result has its
// last bit flipped: a counterfactual engine, to measure what a browser whose Math differs in the last bit would do to a
// run. The page's realm is never touched.

importScripts("sim.js");

self.onmessage = function (e) {
  const d = e.data, Sim = self.GrayboxSim, saved = {};
  try {
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
