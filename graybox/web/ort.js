// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/ort.js — ORT-1 (graybox/ORT-1.md, 0227): a rules-2 world's origin moved between two ticks, as a
// transition bound to the exact state it was prepared from. The JavaScript side of three answers: the values worked by
// hand (web/ort_cases.json), graybox/ort_ref.py (Python, written apart) and this file; the two programs are held to the
// hand-worked values and then to each other, byte for byte.
//
//   GrayboxORT.owner(Sim, world, state)          the tick owner: its world, its state, its receipts; step(input)
//   GrayboxORT.prepare(Sim, owner, event)        a candidate transition, or a refusal with its code; writes nothing
//   GrayboxORT.commit(Sim, owner, prepared)      the candidate made the owner's world and state together, or refused
//   GrayboxORT.bytes(Sim, world, state)          the canonical bytes of a basis (a world and a state)
//   GrayboxORT.ortCases(Sim, map, table)         the table played, for graybox/ort_ref.py to hold
//
// Sim is GrayboxSim.withRules(2). No DOM: it runs in a worker and under node. It reads the simulation only through its
// API (World, step, snapshot, restore, hash), and moves nothing but what the frame table names.

(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.GrayboxORT = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const FORMAT = "VERDANDI-ORT 1", EVENT = "VERDANDI-ORT-EVENT 1", RECEIPT = "VERDANDI-ORT-RECEIPT 1";
  const ORIGIN_MAX = 1048576, TICK_MAX = 9007199254740991, NONE = "0000000000000000000000000000000000000000000000000000000000000000";

  // ---------------------------------------------------------------- SHA-256 (FIPS 180-4), over bytes; lower-case hex
  const K256 = new Uint32Array([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01,
    0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08,
    0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]);
  function sha256(bytes) {
    const n = bytes.length, total = Math.ceil((n + 9) / 64) * 64, m = new Uint8Array(total);
    m.set(bytes); m[n] = 0x80;
    const bits = n * 8, dv = new DataView(m.buffer);
    dv.setUint32(total - 8, Math.floor(bits / 4294967296)); dv.setUint32(total - 4, bits >>> 0);
    const H = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
    const w = new Uint32Array(64);
    const rot = function (x, r) { return (x >>> r) | (x << (32 - r)); };
    for (let off = 0; off < total; off += 64) {
      for (let i = 0; i < 16; i++) w[i] = dv.getUint32(off + i * 4);
      for (let i = 16; i < 64; i++) {
        const s0 = rot(w[i - 15], 7) ^ rot(w[i - 15], 18) ^ (w[i - 15] >>> 3), s1 = rot(w[i - 2], 17) ^ rot(w[i - 2], 19) ^ (w[i - 2] >>> 10);
        w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0;
      }
      let a = H[0], b = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
      for (let i = 0; i < 64; i++) {
        const t1 = (h + (rot(e, 6) ^ rot(e, 11) ^ rot(e, 25)) + ((e & f) ^ (~e & g)) + K256[i] + w[i]) >>> 0;
        const t2 = ((rot(a, 2) ^ rot(a, 13) ^ rot(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) >>> 0;
        h = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
      }
      H[0] += a; H[1] += b; H[2] += c; H[3] += d; H[4] += e; H[5] += f; H[6] += g; H[7] += h;
    }
    let out = "";
    for (let i = 0; i < 8; i++) out += ("00000000" + H[i].toString(16)).slice(-8);
    return out;
  }
  const utf8 = function (t) { return new TextEncoder().encode(t); };
  const dec = function (v) { return String(v + 0); };   // a whole number in decimal; -0 is 0

  // ---------------------------------------------------------------- canonical bytes of a basis
  // "VERDANDI-ORT 1", then the world's identity and the state's snapshot, each framed by its byte count
  function bytes(Sim, world, s) {
    const id = utf8(world.identity), snap = utf8(Sim.snapshot(s));
    const head = utf8(FORMAT + "\nidentity " + id.length + "\n"), mid = utf8("\nstate " + snap.length + "\n"), tail = utf8("\n");
    const out = new Uint8Array(head.length + id.length + mid.length + snap.length + tail.length);
    let k = 0;
    for (const part of [head, id, mid, snap, tail]) { out.set(part, k); k += part.length; }
    return out;
  }
  function digest(Sim, world, s) { return sha256(bytes(Sim, world, s)); }

  // ---------------------------------------------------------------- the frame table
  // Every leaf of the snapshot, by its path ('*' an index): moved by the rebase along x ("x"), along z ("z"), or not
  // ("-": the leaf does not depend on where the origin is). A leaf the table does not name refuses (ORT-UNDECLARED).
  const FRAME = [
    ["x", "x"], ["z", "z"], ["targets.*.x", "x"], ["targets.*.z", "z"],
    ["cooldown", "-"], ["feet", "-"], ["movers.*.phase", "-"], ["movers.*.stopped", "-"], ["onGround", "-"],
    ["onObjective", "-"], ["pitch", "-"], ["score", "-"], ["shots", "-"], ["side", "-"], ["targets.*.downFor", "-"],
    ["targets.*.id", "-"], ["targets.*.up", "-"], ["targets.*.y", "-"], ["tick", "-"], ["vy", "-"], ["yaw", "-"]];
  function leaves(v, path, out) {
    if (v === null || typeof v !== "object") { out.push(path); return out; }
    const keys = Array.isArray(v) ? v.map(function (_, i) { return i; }) : Object.keys(v).sort();
    for (const k of keys) leaves(v[k], path.concat([k]), out);
    return out;
  }
  // the world's own fields, each declared: read through the origin ("global"), the origin itself, the movers (local,
  // moved), or made from the rest (the identity); a field not named here refuses (ORT-UNDECLARED)
  const WORLD = { cell: "global", h: "global", identity: "made", identityState: "made", map: "global", movers: "moved", objective: "global",
                  oi: "origin", oj: "origin", probes: "global", routes: "global", spawns: "global", targetDefs: "global", tops: "global",
                  w: "global", wall: "global" };
  function frameOf(path) {
    const pat = path.map(function (k) { return typeof k === "number" ? "*" : k; }).join(".");
    for (const f of FRAME) if (f[0] === pat) return f[1];
    return null;
  }

  // p - d, and whether it is exact: the rounding error of the subtraction (Knuth's TwoSum), 0 when exact
  function sub(p, d) {
    const r = p - d, bb = r - p, err = (p - (r - bb)) + (-d - bb);
    return { r: r, exact: err === 0 && isFinite(r) };
  }

  // ---------------------------------------------------------------- the event
  function isWhole(v, lo, hi) { return typeof v === "number" && v === Math.floor(v) && v >= lo && v <= hi; }
  function eventBytes(e) { return EVENT + "\ntick " + dec(e.tick) + "\ndi " + dec(e.di) + "\ndj " + dec(e.dj) + "\n"; }
  function eventFault(e) {
    if (e === null || typeof e !== "object" || Array.isArray(e)) return "the event is not a record";
    const keys = Object.keys(e).sort();
    if (keys.join(",") !== "di,dj,tick") return "the event's fields are " + JSON.stringify(keys) + ", not di, dj and tick";
    if (!isWhole(e.tick, 0, TICK_MAX)) return "its tick is not a whole number from 0";
    if (!isWhole(e.di, -ORIGIN_MAX, ORIGIN_MAX) || !isWhole(e.dj, -ORIGIN_MAX, ORIGIN_MAX)) return "di and dj are not whole numbers of cells, each at most 2^20";
    return null;
  }

  // ---------------------------------------------------------------- the owner, prepare and commit
  // the owner publishes one record, its world and its state together, and replaces it whole; `last` is the id of its
  // last committed receipt (the history a transition must have been prepared at, not only the bytes)
  function owner(Sim, world, s) {
    const o = { cur: Object.freeze({ world: world, state: s }), seq: 0, last: NONE, receipts: [], committed: {} };
    Object.defineProperty(o, "world", { get: function () { return o.cur.world; } });
    Object.defineProperty(o, "state", { get: function () { return o.cur.state; } });
    o.step = function (inp) { return Sim.step(o.cur.world, o.cur.state, inp); };
    return o;
  }
  function no(code, why) { return { ok: false, code: code, why: why }; }

  function prepare(Sim, ow, event) {
    const world = ow.world, s = ow.state;
    if (Sim.RULES !== 2) return no("ORT-RULES", "the simulation is rules " + Sim.RULES + "; ORT-1 moves the origin of rules 2's worlds");
    if (!(world.cell === Math.floor(world.cell) && world.cell >= 1 && world.cell <= 64)) return no("ORT-CELL", "the cell is " + world.cell + " m, not a whole number of metres from 1 to 64");
    const ef = eventFault(event);
    if (ef) return no("ORT-EVENT", ef);
    if (event.tick !== s.tick) return no("ORT-STALE-TICK", "the event is for tick " + event.tick + "; the state is at tick " + s.tick);
    const oi = world.oi + event.di, oj = world.oj + event.dj;
    if (Math.abs(oi) > ORIGIN_MAX || Math.abs(oj) > ORIGIN_MAX) return no("ORT-ORIGIN", "the origin would be " + oi + ", " + oj + ": beyond 2^20 cells");
    const snap = JSON.parse(Sim.snapshot(s)), paths = leaves(snap, [], []);
    for (const p of paths) if (frameOf(p) === null) return no("ORT-UNDECLARED", "the state's leaf " + p.join(".") + " is not in the frame table");
    for (const k of Object.keys(world).sort()) if (!Object.prototype.hasOwnProperty.call(WORLD, k)) return no("ORT-UNDECLARED", "the world's field " + k + " is not in the frame table");
    const dx = event.di * world.cell, dz = event.dj * world.cell;
    // every number the rebase moves, moved exactly, or nothing moves: the state's, then the movers'
    const moved = [];
    for (const p of paths) {
      const f = frameOf(p);
      if (f === "-") continue;
      let v = s;
      for (const k of p) v = v[k];
      const r = sub(v, f === "x" ? dx : dz);
      if (!r.exact) return no("ORT-INEXACT", "the state's " + p.join(".") + " = " + v + " less " + (f === "x" ? dx : dz) + " m is not a double");
      moved.push([p, r.r]);
    }
    const movers = [];
    for (const m of world.map.movers || []) {
      const b = m.box.slice();
      for (const [i, d] of [[0, dx], [3, dx], [2, dz], [5, dz]]) {
        const r = sub(b[i], d);
        if (!r.exact) return no("ORT-INEXACT", "the mover " + m.id + "'s box[" + i + "] = " + b[i] + " less " + d + " m is not a double");
        b[i] = r.r;
      }
      movers.push(Object.assign({}, m, { box: b }));
    }
    let world2;
    try {
      world2 = new Sim.World(Object.assign({}, world.map, { origin: [oi, oj], movers: movers }));
    } catch (e) {
      const t = String(e && e.message || e);
      return no(t.indexOf("RULES2-MOVER") === 0 ? "ORT-MOVER" : "ORT-WORLD", t);
    }
    const s2 = Sim.restore(Sim.snapshot(s));
    for (const [p, v] of moved) {
      let o = s2;
      for (let i = 0; i < p.length - 1; i++) o = o[p[i]];
      o[p[p.length - 1]] = v;
    }
    // the candidate held to what it should be: every leaf the old one's, but the moved ones, each moved as computed
    const want = {};
    for (const [p, v] of moved) want[p.join(".")] = v;
    const snap2 = JSON.parse(Sim.snapshot(s2)), paths2 = leaves(snap2, [], []);
    if (paths2.length !== paths.length) return no("ORT-SELF", "the candidate's leaves are not the state's");
    for (let i = 0; i < paths.length; i++) {
      const p = paths[i], key = p.join(".");
      if (paths2[i].join(".") !== key) return no("ORT-SELF", "the candidate's leaves are not the state's");
      let a = snap, b = snap2;
      for (const k of p) { a = a[k]; b = b[k]; }
      const ok = Object.prototype.hasOwnProperty.call(want, key) ? b === JSON.parse(Sim.snapshot({ v: want[key] })).v : a === b;
      if (!ok) return no("ORT-SELF", "the candidate's " + key + " is not what the rebase computed");
    }
    const pre = digest(Sim, world, s), post = digest(Sim, world2, s2), ev = eventBytes(event);
    const receipt = RECEIPT + "\nseq " + (ow.seq + 1) + "\nprev " + ow.last + "\ntick " + dec(event.tick) + "\npre " + pre + "\nevent " + sha256(utf8(ev)) + "\npost " + post + "\n";
    return { ok: true, prepared: { tick: event.tick, prev: ow.last, pre: pre, post: post, event: ev, receipt: receipt, id: sha256(utf8(receipt)), world: world2, state: s2 } };
  }

  function commit(Sim, ow, P) {
    if (ow.committed[P.id]) return no("ORT-REPLAY", "this transition was committed already (receipt " + P.id.slice(0, 12) + ")");
    if (ow.state.tick !== P.tick) return no("ORT-STALE-TICK", "prepared at tick " + P.tick + "; the owner is at tick " + ow.state.tick);
    const now = digest(Sim, ow.world, ow.state);
    if (now !== P.pre) return no("ORT-STALE-BASIS", "prepared from basis " + P.pre.slice(0, 12) + "; the owner's is " + now.slice(0, 12));
    // the same bytes are not the same basis: a world moved there and back has its old bytes and a longer history (ABA)
    if (ow.last !== P.prev) return no("ORT-STALE-BASIS", "prepared after receipt " + P.prev.slice(0, 12) + "; the owner's last is " + ow.last.slice(0, 12));
    // the candidate and its receipt as prepared: nothing changed in them since
    const lines = P.receipt.split("\n");
    if (sha256(utf8(P.receipt)) !== P.id || digest(Sim, P.world, P.state) !== P.post || lines[2] !== "prev " + P.prev || lines[4] !== "pre " + P.pre
        || lines[6] !== "post " + P.post) return no("ORT-TAMPERED", "the candidate or its receipt is not what was prepared");
    ow.cur = Object.freeze({ world: P.world, state: P.state });   // one assignment: the world and the state together
    ow.seq += 1; ow.last = P.id; ow.receipts.push(P.receipt); ow.committed[P.id] = true;
    return { ok: true, receipt: P.receipt };
  }

  // ---------------------------------------------------------------- the independent check of conservation
  // A double as an integer count of 2^-1074 (every finite double is one), in BigInt: exact
  function units(x) {
    const dv = new DataView(new ArrayBuffer(8));
    dv.setFloat64(0, x);
    const hi = dv.getUint32(0), lo = dv.getUint32(4), sign = hi >>> 31, e = (hi >>> 20) & 0x7ff;
    let m = (BigInt(hi & 0xfffff) << 32n) | BigInt(lo);
    if (e !== 0) m = (m | (1n << 52n)) << BigInt(e - 1);
    return sign ? -m : m;
  }
  // every moved leaf's global position before and after, origin * cell + local, compared exactly
  function conserved(world, s, world2, s2) {
    const U = 1n << 1074n, cell = BigInt(world.cell);
    const pairs = [["x", world.oi, world2.oi, s.x, s2.x], ["z", world.oj, world2.oj, s.z, s2.z]];
    s.targets.forEach(function (t, k) {
      pairs.push(["targets." + k + ".x", world.oi, world2.oi, t.x, s2.targets[k].x], ["targets." + k + ".z", world.oj, world2.oj, t.z, s2.targets[k].z]);
    });
    world.movers.forEach(function (m, k) {
      const b = m.box, b2 = world2.movers[k].box;
      pairs.push(["movers." + k + ".x0", world.oi, world2.oi, b.x0, b2.x0], ["movers." + k + ".x1", world.oi, world2.oi, b.x1, b2.x1],
                 ["movers." + k + ".z0", world.oj, world2.oj, b.z0, b2.z0], ["movers." + k + ".z1", world.oj, world2.oj, b.z1, b2.z1]);
    });
    for (const [what, o, o2, p, p2] of pairs) {
      if (BigInt(o) * cell * U + units(p) !== BigInt(o2) * cell * U + units(p2)) return what;
    }
    return null;
  }

  // ---------------------------------------------------------------- the table (web/ort_cases.json)
  const SETTABLE = ["feet", "onGround", "pitch", "vy", "x", "yaw", "z"];
  function ortCases(Sim, map, table) {
    if (Sim.RULES !== 2) throw new Error("ortCases runs under rules 2");
    const self = sha256(utf8("abc"));
    const out = [{ name: "sha256", abc: self, empty: sha256(new Uint8Array(0)), two: sha256(utf8("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq")) }];
    for (const c of table.cases) {
      const r = { name: c.name, snaps: [], hashes: [], events: [] };
      try {
        const world = new Sim.World(Object.assign({}, map, { movers: c.movers || [] }));
        const s = Sim.newState(world, (c.start && c.start.side) || "A");
        const set = (c.start && c.start.set) || {};
        for (const k of Object.keys(set).sort()) { if (SETTABLE.indexOf(k) < 0) throw new Error("a start cannot set " + k); s[k] = set[k]; }
        const ow = owner(Sim, world, s), held = {};
        r.start = new TextDecoder().decode(bytes(Sim, ow.world, ow.state));
        let inside = 0;
        const tick = function (inp) {
          const e = ow.step(inp);
          if (e) throw new Error("an input was refused: " + e);
          r.snaps.push(Sim.snapshot(ow.state)); r.hashes.push(Sim.hash(ow.state, ow.world));
          for (let k = 0; k < ow.world.movers.length; k++) {
            const b = Sim.poseOf(ow.world.movers[k], ow.state.movers[k].phase), st = ow.state;
            const px = Math.max(b.x0, Math.min(st.x, b.x1)), pz = Math.max(b.z0, Math.min(st.z, b.z1));
            if ((st.x - px) * (st.x - px) + (st.z - pz) * (st.z - pz) < Sim.P.radius * Sim.P.radius && b.y1 > st.feet && b.y0 < st.feet + Sim.BODY) { inside += 1; break; }
          }
        };
        // a rebase tried: the outcome, and on a refusal whether the owner's basis is what it was (nothing written)
        const attempt = function (label, fn) {
          const before = digest(Sim, ow.world, ow.state), w0 = ow.world, s0 = ow.state, n0 = ow.receipts.length, q0 = ow.seq, l0 = ow.last;
          const res = fn();
          const ev = { label: label, at: ow.state.tick, ok: res.ok };
          if (res.ok) {
            ev.receipt = res.receipt; ev.bytes = new TextDecoder().decode(bytes(Sim, ow.world, ow.state));
            ev.conserved = conserved(w0, s0, ow.world, ow.state) || "every moved leaf";
          } else {
            ev.code = res.code; ev.why = res.why;
            ev.unchanged = digest(Sim, ow.world, ow.state) === before && ow.world === w0 && ow.state === s0 && ow.receipts.length === n0 && ow.seq === q0 && ow.last === l0;
          }
          r.events.push(ev);
        };
        for (const seg of c.inputs || []) {
          if (seg.rebase) {
            attempt("rebase " + seg.rebase.join(","), function () {
              const p = prepare(Sim, ow, { tick: ow.state.tick, di: seg.rebase[0], dj: seg.rebase[1] });
              return p.ok ? commit(Sim, ow, p.prepared) : p;
            });
          } else if (seg.event !== undefined) {
            attempt("event", function () { const p = prepare(Sim, ow, seg.event); return p.ok ? commit(Sim, ow, p.prepared) : p; });
          } else if (seg.prepare) {
            const p = prepare(Sim, ow, { tick: ow.state.tick, di: seg.prepare[0], dj: seg.prepare[1] });
            r.events.push({ label: "prepare " + seg.as, at: ow.state.tick, ok: p.ok, code: p.code, receipt: p.ok ? p.prepared.receipt : undefined });
            if (p.ok) held[seg.as] = p.prepared;
          } else if (seg.world_field) {   // a field the frame table does not name (the hand-worked case O14)
            ow.world[seg.world_field] = [7, 31];
          } else if (seg.poke !== undefined) {   // the live state written outside a tick and a commit (the hand-worked case O13)
            ow.state.x = ow.state.x + seg.poke;
          } else if (seg.tamper) {   // a candidate changed after it was prepared (the hand-worked case O12)
            held[seg.tamper].state.x = held[seg.tamper].state.x + 1;
          } else if (seg.commit) {
            attempt("commit " + seg.commit, function () { return commit(Sim, ow, held[seg.commit]); });
          } else {
            const made = seg.stress ? Sim.stressInputs(seg.stress) : null;
            for (let i = 0; i < (made ? made.length : seg.n); i++) tick(made ? made[i] : Object.assign({}, seg.in || {}));
          }
        }
        r.inside = inside;
        r.end = new TextDecoder().decode(bytes(Sim, ow.world, ow.state));
        r.receipts = ow.receipts.slice();
      } catch (e) {
        r.error = String(e && e.message || e);
      }
      out.push(r);
    }
    return out;
  }

  return { FORMAT: FORMAT, FRAME: FRAME, sha256: sha256, bytes: bytes, digest: digest, owner: owner, prepare: prepare, commit: commit,
           conserved: conserved, eventBytes: eventBytes, ortCases: ortCases };
});
