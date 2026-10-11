// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// graybox/web/sim.js — FPS-GRAYBOX-0's simulation: the player, collision, gravity, the weapon and the targets.
//
// It reads the collision world C (each cell's solid top, in metres) for movement and the canonical world's gameplay
// marks (spawns, targets, the objective, probes, routes) and nothing of the render mesh. Fixed tick, 120 per second;
// inputs are given per tick. The renderer reads the state and writes none of it. No DOM here: the same file runs in
// the page, in a worker and under node.
//
// The rules are versioned. Rules 1 (the default, since 2026-10-11, by the owner's ruling: "investigate and implement
// the deterministic math layer now") compute a tick with operations ECMA-262 fixes to the last bit, so that the same
// state and input give the same next state, bit for bit, in every conforming engine (the contract: graybox/README.md).
// Rules 0 are the rules as first built, calling the engine's Math.sin, Math.cos, Math.hypot and Math.atan2, whose last
// bits the language leaves to the engine; they are kept to measure the old baseline against, and nothing else uses
// them.

(function (root, factory) {
  // make(rules) builds one instance of the simulation under those rules; its fresh() builds another, under the same
  // rules, that shares no variable with the first (the self-test resumes snapshots in fresh instances, to show that the
  // state holds everything a tick reads). source is the factory's text, for the self-test's reading of its own code.
  const make = function (rules) {
    const m = factory(rules === 0 ? 0 : 1);
    m.fresh = function () { return make(m.RULES); };
    m.withRules = make;
    m.source = String(factory);
    return m;
  };
  if (typeof module === "object" && module.exports) module.exports = make(1);
  else root.GrayboxSim = make(1);
})(typeof self !== "undefined" ? self : this, function (RULES) {
  "use strict";

  const TICK = 1 / 120;
  const P = {
    radius: 0.35, eye: 1.62, step: 0.55, speed: 6.0, gravity: 20.0, jump: 7.0,
    fireCooldown: 0.12, targetRadius: 0.4, targetHeight: 1.9, targetDown: 2.5, range: 200,
  };
  // The rules, frozen, so that no tick and no page can change them in the middle of a run. (Frozen here rather than
  // in the declaration: art/check.py reads the player's numbers from the declaration's text.)
  Object.freeze(P);

  // ---------------------------------------------------------------- the rules' arithmetic (rules 1)
  // A tick's numbers come from operations ECMA-262 fixes to the last bit: + - * / % (IEEE 754 binary64, round to
  // nearest, ties to even), comparisons, Math.floor, Math.ceil, Math.min, Math.max, Math.abs, Math.imul, the bit
  // operators, DataView's reading and writing of a double's bits, and BigInt, which is exact. Math.sin, Math.cos,
  // Math.atan2, Math.hypot and Math.sqrt are not among them: the language leaves their last bits to the engine, and two
  // engines were measured to differ (R-6). The rules use these instead:
  //   xsin, xcos    fdlibm 5.3's algorithm (k_sin.c, k_cos.c, the medium range of e_rem_pio2.c): a Cody-Waite
  //                 reduction by pi/2 in three parts of 33 bits, with a second and third step when the first cancels,
  //                 then the kernels' polynomials. Defined for |x| <= 2^20 * pi/2 (about 1.65e6); beyond it they refuse
  //                 (RangeError).
  //   xatan2        fdlibm 5.3's e_atan2.c and s_atan.c, with FreeBSD's later correction (when |y/x| > 2^60 the
  //                 result is +-pi/2 whatever the sign of x): the quadrant by the signs, |y/x| reduced to one of four
  //                 intervals around 0.5, 1, 1.5 and infinity, an odd polynomial in two halves.
  //   xsqrt         correctly rounded, by an integer square root in BigInt: no Math.sqrt.
  //   xhypot        correctly rounded: the sum of the squares formed exactly in BigInt, then its square root as xsqrt
  //                 takes one, so no step overflows or underflows; Infinity only when the result does.
  // Every constant is written as the bits of its double, not as a decimal: ECMA-262 lets an engine round a literal of
  // more than 20 significant digits either way, and fdlibm's decimals have 21. graybox/rules_ref.py is a second
  // implementation of the same algorithms, in Python, and holds these to it and to a high-precision reference.
  const XV = new DataView(new ArrayBuffer(8));
  function hiw(x) { XV.setFloat64(0, x); return XV.getInt32(0); }          // the high word, signed, as fdlibm's __HI
  function low(x) { XV.setFloat64(0, x); return XV.getUint32(4); }         // the low word, as __LO
  function dbl(hi, lo) { XV.setUint32(0, hi >>> 0); XV.setUint32(4, lo >>> 0); return XV.getFloat64(0); }

  // k_sin.c, k_cos.c
  const S1 = dbl(0xBFC55555, 0x55555549), S2 = dbl(0x3F811111, 0x1110F8A6), S3 = dbl(0xBF2A01A0, 0x19C161D5),
        S4 = dbl(0x3EC71DE3, 0x57B1FE7D), S5 = dbl(0xBE5AE5E6, 0x8A2B9CEB), S6 = dbl(0x3DE5D93A, 0x5ACFD57C);
  const C1 = dbl(0x3FA55555, 0x5555554C), C2 = dbl(0xBF56C16C, 0x16C15177), C3 = dbl(0x3EFA01A0, 0x19CB1590),
        C4 = dbl(0xBE927E4F, 0x809C52AD), C5 = dbl(0x3E21EE9E, 0xBDB4B1C4), C6 = dbl(0xBDA8FAE9, 0xBE8838D4);
  function kSin(x, y, iy) {
    const ix = hiw(x) & 0x7fffffff;
    if (ix < 0x3e400000) return x;                          // |x| < 2^-27
    const z = x * x, v = z * x, r = S2 + z * (S3 + z * (S4 + z * (S5 + z * S6)));
    if (iy === 0) return x + v * (S1 + z * r);
    return x - ((z * (0.5 * y - v * r) - y) - v * S1);
  }
  function kCos(x, y) {
    const ix = hiw(x) & 0x7fffffff;
    if (ix < 0x3e400000) return 1;                          // |x| < 2^-27
    const z = x * x, r = z * (C1 + z * (C2 + z * (C3 + z * (C4 + z * (C5 + z * C6)))));
    if (ix < 0x3FD33333) return 1 - (0.5 * z - (z * r - x * y));   // |x| < 0.3
    const qx = ix > 0x3fe90000 ? 0.28125 : dbl(ix - 0x00200000, 0);  // x/4, cut to its high word
    const hz = 0.5 * z - qx, a = 1 - qx;
    return a - (hz - (z * r - x * y));
  }
  // e_rem_pio2.c, its small and medium ranges: x = n * pi/2 + (y0 + y1), |y0 + y1| <= pi/4. (fdlibm skips the test for
  // cancellation, by a table of n * pi/2's high words, when n < 32 and x is not near one; here the test is always
  // made. V8 12.4's fdlibm, which keeps the table, gave the same bits on every argument tried.)
  const INVPIO2 = dbl(0x3FE45F30, 0x6DC9C883), PIO2_1 = dbl(0x3FF921FB, 0x54400000), PIO2_1T = dbl(0x3DD0B461, 0x1A626331),
        PIO2_2 = dbl(0x3DD0B461, 0x1A600000), PIO2_2T = dbl(0x3BA3198A, 0x2E037073), PIO2_3 = dbl(0x3BA3198A, 0x2E000000),
        PIO2_3T = dbl(0x397B839A, 0x252049C1);
  function remPio2(x, y) {
    const hx = hiw(x), ix = hx & 0x7fffffff;
    if (ix <= 0x3fe921fb) { y[0] = x; y[1] = 0; return 0; }
    if (ix < 0x4002d97c) {                                  // |x| < 3pi/4: n is 1 or -1
      let z;
      if (hx > 0) {
        z = x - PIO2_1;
        if (ix !== 0x3ff921fb) { y[0] = z - PIO2_1T; y[1] = (z - y[0]) - PIO2_1T; }
        else { z -= PIO2_2; y[0] = z - PIO2_2T; y[1] = (z - y[0]) - PIO2_2T; }
        return 1;
      }
      z = x + PIO2_1;
      if (ix !== 0x3ff921fb) { y[0] = z + PIO2_1T; y[1] = (z - y[0]) + PIO2_1T; }
      else { z += PIO2_2; y[0] = z + PIO2_2T; y[1] = (z - y[0]) + PIO2_2T; }
      return -1;
    }
    if (ix > 0x413921fb) throw new RangeError("the rules' sine and cosine are defined for |x| <= 2^20 * pi/2, not " + x);
    const t = Math.abs(x), n = Math.floor(t * INVPIO2 + 0.5), fn = n;
    let r = t - fn * PIO2_1, w = fn * PIO2_1T;
    const j = ix >> 20;
    y[0] = r - w;
    let i = j - ((hiw(y[0]) >> 20) & 0x7ff);
    if (i > 16) {                                           // the first step cancelled: a second, good to 118 bits
      let u = r; w = fn * PIO2_2; r = u - w; w = fn * PIO2_2T - ((u - r) - w); y[0] = r - w;
      i = j - ((hiw(y[0]) >> 20) & 0x7ff);
      if (i > 49) {                                         // and a third, to 151
        u = r; w = fn * PIO2_3; r = u - w; w = fn * PIO2_3T - ((u - r) - w); y[0] = r - w;
      }
    }
    y[1] = (r - y[0]) - w;
    if (hx < 0) { y[0] = -y[0]; y[1] = -y[1]; return -n; }
    return n;
  }
  const RY = [0, 0];
  function xsin(x) {
    const ix = hiw(x) & 0x7fffffff;
    if (ix <= 0x3fe921fb) return kSin(x, 0, 0);
    if (ix >= 0x7ff00000) return x - x;                    // NaN, or an infinity: NaN
    const n = remPio2(x, RY);
    switch (n & 3) {
      case 0: return kSin(RY[0], RY[1], 1);
      case 1: return kCos(RY[0], RY[1]);
      case 2: return -kSin(RY[0], RY[1], 1);
      default: return -kCos(RY[0], RY[1]);
    }
  }
  function xcos(x) {
    const ix = hiw(x) & 0x7fffffff;
    if (ix <= 0x3fe921fb) return kCos(x, 0);
    if (ix >= 0x7ff00000) return x - x;
    const n = remPio2(x, RY);
    switch (n & 3) {
      case 0: return kCos(RY[0], RY[1]);
      case 1: return -kSin(RY[0], RY[1], 1);
      case 2: return -kCos(RY[0], RY[1]);
      default: return kSin(RY[0], RY[1], 1);
    }
  }
  // s_atan.c, e_atan2.c
  const ATANHI = [dbl(0x3FDDAC67, 0x0561BB4F), dbl(0x3FE921FB, 0x54442D18), dbl(0x3FEF730B, 0xD281F69B), dbl(0x3FF921FB, 0x54442D18)];
  const ATANLO = [dbl(0x3C7A2B7F, 0x222F65E2), dbl(0x3C81A626, 0x33145C07), dbl(0x3C700788, 0x7AF0CBBD), dbl(0x3C91A626, 0x33145C07)];
  const AT = [dbl(0x3FD55555, 0x5555550D), dbl(0xBFC99999, 0x9998EBC4), dbl(0x3FC24924, 0x920083FF), dbl(0xBFBC71C6, 0xFE231671),
              dbl(0x3FB745CD, 0xC54C206E), dbl(0xBFB3B0F2, 0xAF749A6D), dbl(0x3FB10D66, 0xA0D03D51), dbl(0xBFADDE2D, 0x52DEFD9A),
              dbl(0x3FA97B4B, 0x24760DEB), dbl(0xBFA2B444, 0x2C6A6C2F), dbl(0x3F90AD3A, 0xE322DA11)];
  function xatan(x) {
    const hx = hiw(x), ix = hx & 0x7fffffff;
    let id;
    if (ix >= 0x44100000) {                                 // |x| >= 2^66, or not a number
      if (ix > 0x7ff00000 || (ix === 0x7ff00000 && low(x) !== 0)) return x + x;
      return hx > 0 ? ATANHI[3] + ATANLO[3] : -ATANHI[3] - ATANLO[3];
    }
    if (ix < 0x3fdc0000) {                                  // |x| < 0.4375
      if (ix < 0x3e200000) return x;                        // |x| < 2^-29
      id = -1;
    } else {
      x = Math.abs(x);
      if (ix < 0x3ff30000) {                                // |x| < 1.1875
        if (ix < 0x3fe60000) { id = 0; x = (2 * x - 1) / (2 + x); }        // 7/16 <= |x| < 11/16
        else { id = 1; x = (x - 1) / (x + 1); }                             // 11/16 <= |x| < 19/16
      } else if (ix < 0x40038000) { id = 2; x = (x - 1.5) / (1 + 1.5 * x); } // |x| < 2.4375
      else { id = 3; x = -1 / x; }                                          // 2.4375 <= |x| < 2^66
    }
    const z = x * x, w = z * z;
    const s1 = z * (AT[0] + w * (AT[2] + w * (AT[4] + w * (AT[6] + w * (AT[8] + w * AT[10])))));
    const s2 = w * (AT[1] + w * (AT[3] + w * (AT[5] + w * (AT[7] + w * AT[9]))));
    if (id < 0) return x - x * (s1 + s2);
    const r = ATANHI[id] - ((x * (s1 + s2) - ATANLO[id]) - x);
    return hx < 0 ? -r : r;
  }
  const TINY = dbl(0x01a56e1f, 0xc2f8f359);                 // 1e-300
  const PI_O_4 = dbl(0x3FE921FB, 0x54442D18), PI_O_2 = dbl(0x3FF921FB, 0x54442D18), PI = dbl(0x400921FB, 0x54442D18),
        PI_LO = dbl(0x3CA1A626, 0x33145C07);
  function xatan2(y, x) {
    if (x !== x || y !== y) return x + y;
    const hx = hiw(x), ix = hx & 0x7fffffff, lx = low(x), hy = hiw(y), iy = hy & 0x7fffffff, ly = low(y);
    if (((hx - 0x3ff00000) | lx) === 0) return xatan(y);   // x is 1
    const m = ((hy >> 31) & 1) | ((hx >> 30) & 2);          // 2 * sign(x) + sign(y)
    if ((iy | ly) === 0) {                                  // y is 0
      if (m < 2) return y;
      return m === 2 ? PI + TINY : -PI - TINY;
    }
    if ((ix | lx) === 0) return hy < 0 ? -PI_O_2 - TINY : PI_O_2 + TINY;
    if (ix === 0x7ff00000) {                                // x is infinite
      if (iy === 0x7ff00000) return [PI_O_4 + TINY, -PI_O_4 - TINY, 3 * PI_O_4 + TINY, -3 * PI_O_4 - TINY][m];
      return [0, -0, PI + TINY, -PI - TINY][m];
    }
    if (iy === 0x7ff00000) return hy < 0 ? -PI_O_2 - TINY : PI_O_2 + TINY;
    const k = (iy - ix) >> 20;
    let z, q = m;
    if (k > 60) { z = PI_O_2 + 0.5 * PI_LO; q = m & 1; }    // |y/x| > 2^60: +-pi/2, whatever the sign of x
    else if (hx < 0 && k < -60) z = 0;                      // |y|/x < -2^60
    else z = xatan(Math.abs(y / x));
    switch (q) {
      case 0: return z;
      case 1: return -z;
      case 2: return PI - (z - PI_LO);
      default: return (z - PI_LO) - PI;
    }
  }
  // square roots, correctly rounded, in BigInt
  const B52 = 1n << 52n, B53 = 1n << 53n;
  function bitlen(n) { return n === 0n ? 0 : n.toString(2).length; }
  function parts(x) {                                       // |x| = m * 2^e, x finite and not 0
    XV.setFloat64(0, x);
    const b = XV.getBigUint64(0) & 0x7fffffffffffffffn, e = Number(b >> 52n), f = b & (B52 - 1n);
    return e === 0 ? [f, -1074] : [f | B52, e - 1075];
  }
  function isqrt(n) {                                       // the integer part of the square root of n >= 0
    if (n < 2n) return n;
    let x = 1n << BigInt((bitlen(n) + 1) >> 1);
    for (;;) { const y = (x + n / x) >> 1n; if (y >= x) return x; x = y; }
  }
  // the double nearest to (q + d) * 2^ex, d in [0, 1), sticky when d > 0: ties to even, subnormals and overflow
  function nearest(q, ex, sticky) {
    const top = ex + bitlen(q) - 1;
    let u = top >= -1022 ? top - 52 : -1074;
    const sh = u - ex;
    if (sh < 2) throw new Error("the rules' rounding was given too few bits");
    const S = BigInt(sh), rest = q & ((1n << S) - 1n), half = 1n << (S - 1n);
    let r = q >> S;
    if (rest > half || (rest === half && (sticky || (r & 1n) === 1n))) r += 1n;
    if (r === B53) { r = B52; u += 1; }
    if (u + 1075 > 2046) return Infinity;
    XV.setBigUint64(0, r < B52 ? r : (BigInt(u + 1075) << 52n) | (r - B52));
    return XV.getFloat64(0);
  }
  function rootOf(S, e) {                                   // the double nearest to sqrt(S) * 2^e, S > 0n, e an integer
    let k = Math.max(0, 112 - bitlen(S));
    if (k & 1) k += 1;
    const N = S << BigInt(k), q = isqrt(N);
    return nearest(q, e - k / 2, q * q !== N);
  }
  function xsqrt(x) {
    if (x !== x || x < 0) return NaN;
    if (x === 0 || x === Infinity) return x;
    const [m, e] = parts(x);
    return (e & 1) ? rootOf(m << 1n, (e - 1) / 2) : rootOf(m, e / 2);
  }
  function xhypot() {
    let inf = false, nan = false;
    for (let i = 0; i < arguments.length; i++) { const v = arguments[i]; if (v === Infinity || v === -Infinity) inf = true; else if (v !== v) nan = true; }
    if (inf) return Infinity;
    if (nan) return NaN;
    const ps = [];
    let lo = Infinity;
    for (let i = 0; i < arguments.length; i++) if (arguments[i] !== 0) { const p = parts(arguments[i]); ps.push(p); if (p[1] < lo) lo = p[1]; }
    if (!ps.length) return 0;
    let S = 0n;
    for (const [m, e] of ps) S += (m * m) << BigInt(2 * (e - lo));
    return rootOf(S, lo);
  }

  // rules 0: the engine's own functions, read when called (the self-test's counterfactual engines replace them)
  const ENGINE = { sin: function (x) { return Math.sin(x); }, cos: function (x) { return Math.cos(x); },
                   atan2: function (y, x) { return Math.atan2(y, x); }, hypot: function () { return Math.hypot.apply(Math, arguments); } };
  // end of rules 0
  const EXACT = { sin: xsin, cos: xcos, atan2: xatan2, hypot: xhypot, sqrt: xsqrt };
  const M = RULES === 0 ? ENGINE : EXACT;
  Object.freeze(ENGINE); Object.freeze(EXACT);

  // ---------------------------------------------------------------- the world
  function World(map) {
    const C = map.collision, W = map.canonical;
    if (C.w !== W.w || C.h !== W.h || C.tops.length !== C.w * C.h) throw new Error("the collision world is not the canonical world's size");
    this.w = C.w; this.h = C.h; this.cell = C.cell; this.tops = C.tops; this.wall = W.wall;
    this.spawns = W.spawns; this.objective = W.objective; this.targetDefs = W.targets;
    this.probes = W.probes; this.routes = W.routes;
  }
  World.prototype.top = function (i, j) {
    if (i < 0 || j < 0 || i >= this.w || j >= this.h) return Infinity;
    return this.tops[j * this.w + i];
  };

  // the cells a circle of radius r at (x, z) overlaps, strictly
  function touching(world, x, z, r, fn) {
    const c = world.cell;
    const i0 = Math.floor((x - r) / c), i1 = Math.floor((x + r) / c);
    const j0 = Math.floor((z - r) / c), j1 = Math.floor((z + r) / c);
    for (let j = j0; j <= j1; j++) {
      for (let i = i0; i <= i1; i++) {
        const px = Math.max(i * c, Math.min(x, (i + 1) * c)), pz = Math.max(j * c, Math.min(z, (j + 1) * c));
        const dx = x - px, dz = z - pz;
        if (dx * dx + dz * dz < r * r) fn(i, j);
      }
    }
  }

  function blocked(world, s, x, z, feet) {
    let b = false;
    touching(world, x, z, P.radius, function (i, j) { if (world.top(i, j) > feet + P.step) b = true; });
    if (b) return true;
    for (const t of s.targets) {
      if (!t.up) continue;
      const dx = x - t.x, dz = z - t.z, rr = P.radius + P.targetRadius;
      if (dx * dx + dz * dz < rr * rr && feet < t.y + P.targetHeight) return true;
    }
    return false;
  }

  function groundAt(world, x, z) {
    let g = 0;
    touching(world, x, z, P.radius, function (i, j) { const t = world.top(i, j); if (t > g) g = t; });
    return g;
  }

  // ---------------------------------------------------------------- the state
  function newState(world, side) {
    const s = {
      tick: 0, side: side || "A", x: 0, z: 0, feet: 0, vy: 0, yaw: 0, pitch: 0, onGround: true,
      cooldown: 0, score: 0, shots: 0, onObjective: false,
      targets: world.targetDefs.map(function (t) {
        const c = world.cell;
        return { id: t.id, x: (t.x + 0.5) * c, z: (t.z + 0.5) * c, y: world.top(t.x, t.z), up: true, downFor: 0 };
      }),
      fx: { hitMarker: 0, flash: {}, lastShot: null },   // feedback for the view: not part of the authoritative state
    };
    spawn(world, s, s.side);
    return s;
  }

  function spawn(world, s, side) {
    const sp = world.spawns[side];
    const c = world.cell;
    s.side = side; s.x = (sp.x + 0.5) * c; s.z = (sp.z + 0.5) * c;
    s.feet = groundAt(world, s.x, s.z); s.vy = 0; s.onGround = true;
    s.yaw = sp.yaw * Math.PI / 180; s.pitch = 0;
  }

  function wrap(a) { const t = 2 * Math.PI; return ((a % t) + t) % t; }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

  // ---------------------------------------------------------------- the input (contract 1, graybox/RULES-1.md)
  // Before a tick its input is admitted or refused, whole: a record whose own fields, in the order of their names, are
  // flags (true or false), a side ("A" or "B") or a finite turn (dyaw, dpitch); every field optional. A refused input
  // changes nothing, and step returns its category; an admitted one is copied, read once, and the tick reads the copy.
  // `lax` exists for the self-test's plants alone (a validator that lets NaN through, or ignores an unknown field).
  const INPUT = 1, FLAGS = ["b", "f", "fire", "jump", "l", "r", "reset"], TURNS = ["dpitch", "dyaw"];
  function admit(inp, lax) {
    if (inp === null || typeof inp !== "object") return "INPUT-NOT-RECORD";
    const proto = Object.getPrototypeOf(inp);   // a plain object, of this realm or another: its prototype is a root
    if (proto !== null && Object.getPrototypeOf(proto) !== null) return "INPUT-NOT-RECORD";
    const keys = Object.keys(inp).sort(), a = {};
    for (const k of keys) {
      const v = inp[k];
      if (FLAGS.indexOf(k) >= 0) { if (v !== true && v !== false) return "INPUT-FLAG"; }
      else if (k === "side") { if (v !== "A" && v !== "B") return "INPUT-SIDE"; }
      else if (TURNS.indexOf(k) >= 0) {
        if (typeof v !== "number") return "INPUT-NUMBER";
        if (!Number.isFinite(v) && !(lax && lax.nan && v !== v)) return "INPUT-NOT-FINITE";
      } else if (lax && lax.unknown) continue;
      else return "INPUT-UNKNOWN-FIELD";
      a[k] = v;
    }
    return a;
  }

  // ---------------------------------------------------------------- one tick
  // inp: a record of {f, b, l, r, jump, fire, reset, side, dyaw, dpitch}, every field optional. Returns null when the
  // tick ran, or the category of the refused input, the state untouched.
  function step(world, s, inp) {
    const a = admit(inp);
    if (typeof a === "string") return a;
    advance(world, s, a);
    return null;
  }

  // the tick itself, on an admitted input (RULES-1.md, One tick)
  function advance(world, s, inp) {
    s.tick += 1;
    if (inp.side) spawn(world, s, inp.side);
    else if (inp.reset) spawn(world, s, s.side);
    s.yaw = wrap(s.yaw + (inp.dyaw || 0));
    s.pitch = clamp(s.pitch + (inp.dpitch || 0), -1.45, 1.45);
    // walking: forward is -z at yaw 0 and +x at yaw 90 degrees; right is +x at yaw 0
    const fwd = (inp.f ? 1 : 0) - (inp.b ? 1 : 0), side = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
    const sy = M.sin(s.yaw), cy = M.cos(s.yaw);
    let mx = fwd * sy + side * cy, mz = -fwd * cy + side * sy;
    const len = M.hypot(mx, mz);
    if (len > 0) {
      mx = mx / len * P.speed * TICK; mz = mz / len * P.speed * TICK;
      moveAxis(world, s, mx, 0);
      moveAxis(world, s, 0, mz);
    }
    // gravity, the jump, the ground
    const wasOnGround = s.onGround;
    if (inp.jump && s.onGround) { s.vy = P.jump; s.onGround = false; }
    s.vy -= P.gravity * TICK;
    s.feet += s.vy * TICK;
    const g = groundAt(world, s.x, s.z);
    if (s.feet <= g || (wasOnGround && s.vy <= 0 && s.feet - g <= P.step)) {
      s.feet = g; s.vy = 0; s.onGround = true;
    } else {
      s.onGround = false;
    }
    // the weapon and the targets
    s.cooldown = Math.max(0, s.cooldown - TICK);
    if (inp.fire && s.cooldown === 0) { s.cooldown = P.fireCooldown; fire(world, s); }
    for (const t of s.targets) {
      if (!t.up) { t.downFor -= TICK; if (t.downFor <= 1e-9) { t.up = true; t.downFor = 0; } }
    }
    s.onObjective = inObjective(world, s);
    s.fx.hitMarker = Math.max(0, s.fx.hitMarker - TICK);
    for (const k in s.fx.flash) s.fx.flash[k] = Math.max(0, s.fx.flash[k] - TICK);
  }

  // ---------------------------------------------------------------- the input contract's cases (web/input_cases.json)
  // A case's values are written as the table says: true, false and null; "f" and a number's 16 hex digits; "s" and a
  // string; {list: [...]}; {record: [[field, value], ...]}, each field made an own property (so that "__proto__" is a
  // field like any other, as it is in Python's dict).
  function caseValue(v) {
    if (v === null || typeof v === "boolean") return v;
    if (typeof v === "string") {
      if (v.length === 17 && v[0] === "f") return ofBits(v.slice(1));
      if (v[0] === "s") return v.slice(1);
      throw new Error("not a value of the table: " + v);
    }
    if (Array.isArray(v.list)) return v.list.map(caseValue);
    if (Array.isArray(v.record)) {
      const o = {};
      for (const [k, x] of v.record) Object.defineProperty(o, k, { value: caseValue(x), enumerable: true, writable: true, configurable: true });
      return o;
    }
    throw new Error("not a value of the table: " + JSON.stringify(v));
  }
  // each case from a new state at spawn A: every step's outcome ("tick" or a category) and the snapshot after it
  function inputCases(map, table, stepFn) {
    stepFn = stepFn || step;
    const world = new World(map), out = [];
    for (const c of table.cases) {
      const s = newState(world, "A"), start = snapshot(s), steps = [];
      for (const st of c.steps) {
        let got;
        try { const r = stepFn(world, s, caseValue(st.input)); got = r == null ? "tick" : String(r); } catch (e) { got = "THREW " + String(e && e.message || e); }
        steps.push({ got: got, snap: snapshot(s) });
      }
      out.push({ name: c.name, start: start, steps: steps });
    }
    return out;
  }
  // what the table requires of a run of it: each step's outcome, a refused step's state unchanged, and a case named in
  // same_as ending where that case ends
  function inputFaults(table, results) {
    const faults = [], last = {};
    if (results.length !== table.cases.length) return ["the results hold " + results.length + " cases, the table " + table.cases.length];
    table.cases.forEach(function (c, i) {
      const r = results[i];
      if (r.name !== c.name || r.steps.length !== c.steps.length) { faults.push(c.name + ": not the table's case"); return; }
      c.steps.forEach(function (st, k) {
        const got = r.steps[k], before = k ? r.steps[k - 1].snap : r.start;
        if (got.got !== st.expect) faults.push(c.name + ", step " + (k + 1) + ": " + got.got + ", not " + st.expect);
        else if (st.expect !== "tick" && got.snap !== before) faults.push(c.name + ", step " + (k + 1) + ": refused, and the state changed");
      });
      last[c.name] = r.steps[r.steps.length - 1].snap;
    });
    for (const c of table.cases) if (c.same_as && last[c.name] !== last[c.same_as]) faults.push(c.name + ": does not end where " + c.same_as + " ends");
    return faults;
  }

  // move along one axis; when blocked, close the gap by halving
  function moveAxis(world, s, dx, dz) {
    if (!blocked(world, s, s.x + dx, s.z + dz, s.feet)) { s.x += dx; s.z += dz; return; }
    for (let k = 0; k < 6; k++) {
      dx /= 2; dz /= 2;
      if (!blocked(world, s, s.x + dx, s.z + dz, s.feet)) { s.x += dx; s.z += dz; }
    }
  }

  function inObjective(world, s) {
    const o = world.objective;
    if (!o) return false;
    const i = Math.floor(s.x / world.cell), j = Math.floor(s.z / world.cell);
    return i >= o.rect[0] && i <= o.rect[2] && j >= o.rect[1] && j <= o.rect[3];
  }

  // ---------------------------------------------------------------- rays
  // The first solid the ray meets: a 2D walk of the cells it crosses in x-z; in each cell the column [0, top] is solid.
  function rayWorld(world, ox, oy, oz, dx, dy, dz, maxT) {
    const c = world.cell;
    let i = Math.floor(ox / c), j = Math.floor(oz / c);
    const si = dx > 0 ? 1 : -1, sj = dz > 0 ? 1 : -1;
    const tdx = dx !== 0 ? Math.abs(c / dx) : Infinity, tdz = dz !== 0 ? Math.abs(c / dz) : Infinity;
    let tmx = dx !== 0 ? (dx > 0 ? (i + 1) * c - ox : ox - i * c) / Math.abs(dx) : Infinity;
    let tmz = dz !== 0 ? (dz > 0 ? (j + 1) * c - oz : oz - j * c) / Math.abs(dz) : Infinity;
    let t0 = 0;
    for (let guard = 0; guard < 10000 && t0 < maxT; guard++) {
      const t1 = Math.min(tmx, tmz, maxT);
      const top = world.top(i, j);
      if (top === Infinity) return { t: t0, i: i, j: j, what: "edge" };
      const y0 = oy + dy * t0, y1 = oy + dy * t1;
      if (y0 <= top) return { t: t0, i: i, j: j, what: "side" };
      if (y1 <= top) return { t: (top - oy) / dy, i: i, j: j, what: "top" };
      if (tmx < tmz) { i += si; t0 = tmx; tmx += tdx; } else { j += sj; t0 = tmz; tmz += tdz; }
    }
    return { t: maxT, i: i, j: j, what: "range" };
  }

  // a ray against an upright box; the entry distance, or Infinity
  function rayBox(ox, oy, oz, dx, dy, dz, x0, y0, z0, x1, y1, z1) {
    let tn = -Infinity, tf = Infinity;
    const o = [ox, oy, oz], d = [dx, dy, dz], lo = [x0, y0, z0], hi = [x1, y1, z1];
    for (let a = 0; a < 3; a++) {
      if (d[a] === 0) { if (o[a] < lo[a] || o[a] > hi[a]) return Infinity; continue; }
      let ta = (lo[a] - o[a]) / d[a], tb = (hi[a] - o[a]) / d[a];
      if (ta > tb) { const q = ta; ta = tb; tb = q; }
      if (ta > tn) tn = ta;
      if (tb < tf) tf = tb;
      if (tn > tf) return Infinity;
    }
    return tf < 0 ? Infinity : Math.max(tn, 0);
  }

  function aim(s) {
    const cp = M.cos(s.pitch);
    return [cp * M.sin(s.yaw), M.sin(s.pitch), -cp * M.cos(s.yaw)];
  }

  function fire(world, s) {
    s.shots += 1;
    const d = aim(s), ox = s.x, oy = s.feet + P.eye, oz = s.z;
    const wall = rayWorld(world, ox, oy, oz, d[0], d[1], d[2], P.range);
    let best = null, bt = wall.t;
    for (const t of s.targets) {
      if (!t.up) continue;
      const r = P.targetRadius;
      const tt = rayBox(ox, oy, oz, d[0], d[1], d[2], t.x - r, t.y, t.z - r, t.x + r, t.y + P.targetHeight, t.z + r);
      if (tt < bt) { bt = tt; best = t; }
    }
    if (best) {
      best.up = false; best.downFor = P.targetDown; s.score += 1;
      s.fx.hitMarker = 0.2; s.fx.flash[best.id] = 0.25;
    }
    s.fx.lastShot = { o: [ox, oy, oz], h: [ox + d[0] * bt, oy + d[1] * bt, oz + d[2] * bt], hit: best ? best.id : null, age: 0 };
    return best ? best.id : null;
  }

  // ---------------------------------------------------------------- the authoritative state's hash
  // FNV-1a over each number's 8 bytes, little-endian (as a Float64Array lays them on every platform a browser runs on;
  // written with a DataView so that the order is the hash's, not the platform's)
  const HV = new DataView(new ArrayBuffer(8));
  function hash(s) {
    const nums = [s.tick, s.x, s.z, s.feet, s.vy, s.yaw, s.pitch, s.onGround ? 1 : 0, s.cooldown, s.score, s.shots, s.onObjective ? 1 : 0];
    for (const t of s.targets) nums.push(t.up ? 1 : 0, t.downFor);
    let h = 0x811c9dc5;
    for (const v of nums) {
      HV.setFloat64(0, v, true);
      for (let k = 0; k < 8; k++) { h ^= HV.getUint8(k); h = Math.imul(h, 0x01000193) >>> 0; }
    }
    return ("00000000" + h.toString(16)).slice(-8) + s.side;
  }

  // ---------------------------------------------------------------- the authoritative state, bit for bit
  // The authoritative state is the whole of s but s.fx, the view's feedback. A snapshot writes it with every number as
  // the 16 hex digits of its IEEE 754 bits, so the last bit, -0 and a NaN's payload survive, and every string marked
  // as one; restore reads it back into a new state with an empty fx. A snapshot is the state's identity for the checks
  // below; the hash above is the cheap one the replay compares, and the checks hold it to the snapshot.
  const DV = new DataView(new ArrayBuffer(8));
  function bitsOf(v) {
    DV.setFloat64(0, v, false);
    let h = "";
    for (let k = 0; k < 8; k++) h += ("0" + DV.getUint8(k).toString(16)).slice(-2);
    return h;
  }
  function ofBits(h) {
    for (let k = 0; k < 8; k++) DV.setUint8(k, parseInt(h.substr(2 * k, 2), 16));
    return DV.getFloat64(0, false);
  }
  function snapshot(s) {
    const enc = function (v, top) {
      if (typeof v === "number") return "f" + bitsOf(v);
      if (typeof v === "string") return "s" + v;
      if (v === null || typeof v === "boolean") return v;
      if (Array.isArray(v)) return v.map(function (x) { return enc(x, false); });
      if (typeof v !== "object") throw new Error("the state holds a " + typeof v);
      const o = {};
      for (const k of Object.keys(v).sort()) if (!(top && k === "fx")) o[k] = enc(v[k], false);
      return o;
    };
    return JSON.stringify(enc(s, true));
  }
  function restore(text) {
    const dec = function (v) {
      if (typeof v === "string") return v[0] === "f" ? ofBits(v.slice(1)) : v.slice(1);
      if (v === null || typeof v === "boolean") return v;
      if (Array.isArray(v)) return v.map(dec);
      const o = {};
      for (const k of Object.keys(v)) o[k] = dec(v[k]);
      return o;
    };
    const s = dec(JSON.parse(text));
    s.fx = { hitMarker: 0, flash: {}, lastShot: null };
    return s;
  }

  // every leaf of the authoritative state (a number, a boolean, a string or null), as its path of keys
  function leaves(s) {
    const out = [];
    const walk = function (v, path) {
      if (v === null || typeof v !== "object") { out.push(path); return; }
      const keys = Array.isArray(v) ? v.map(function (_, i) { return i; }) : Object.keys(v).sort();
      for (const k of keys) if (!(path.length === 0 && k === "fx")) walk(v[k], path.concat([k]));
    };
    walk(s, []);
    return out;
  }
  function getAt(o, p) { for (const k of p) { if (o === null || typeof o !== "object") return undefined; o = o[k]; } return o; }
  function setAt(o, p, v) { for (let i = 0; i < p.length - 1; i++) o = o[p[i]]; o[p[p.length - 1]] = v; }
  function leafKind(p) { return p.map(function (k, i) { return typeof k === "number" ? "[]" : (i ? "." : "") + k; }).join(""); }
  function leafBits(v) { return typeof v === "number" ? "f" + bitsOf(v) : JSON.stringify(v); }
  // the smallest change to a leaf: a number's last significand bit, which is one byte of the hash's input; a boolean
  // flipped; the other side; any other string with a mark added
  function nudge(v) {
    if (typeof v === "number") { DV.setFloat64(0, v, true); DV.setUint8(0, DV.getUint8(0) ^ 1); return DV.getFloat64(0, true); }
    if (typeof v === "boolean") return !v;
    if (typeof v === "string") return v === "A" ? "B" : v === "B" ? "A" : v + "'";
    return v === null ? 0 : v;
  }

  // ---------------------------------------------------------------- the runtime's conformance checks
  // Run against the runtime's own collision and movement, not a copy of them: probes, spawns, routes walked by a bot,
  // gravity, mounting cover, the weapon, occlusion, reset, and replay of recorded inputs, every tick hashed.
  function walkGraph(world) {
    const standing = new Set(world.targetDefs.map(function (t) { return t.z * world.w + t.x; }));
    const ok = function (i, j) { return world.top(i, j) < world.wall && !standing.has(j * world.w + i); };
    return function (a, b) {   // a breadth-first path of cells from a to b, each step up at most the step height
      const key = function (p) { return p[1] * world.w + p[0]; };
      const prev = new Map([[key(a), null]]), q = [a];
      while (q.length) {
        const p = q.shift();
        if (p[0] === b[0] && p[1] === b[1]) break;
        for (const d of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const n = [p[0] + d[0], p[1] + d[1]];
          if (!ok(n[0], n[1]) || prev.has(key(n))) continue;
          if (world.top(n[0], n[1]) - world.top(p[0], p[1]) > P.step) continue;
          prev.set(key(n), p); q.push(n);
        }
      }
      if (!prev.has(key(b))) return null;
      const path = [];
      for (let p = b; p; p = prev.get(key(p))) path.unshift(p);
      return path;
    };
  }

  // a bot that walks a path of cell centres through the real movement; returns its inputs and the outcome
  function walk(world, s, path, limitTicks) {
    const c = world.cell, inputs = [];
    let k = 1, best = Infinity, still = 0;
    for (let n = 0; n < limitTicks; n++) {
      if (k >= path.length) return { ok: true, inputs: inputs, ticks: n };
      const tx = (path[k][0] + 0.5) * c, tz = (path[k][1] + 0.5) * c;
      const dx = tx - s.x, dz = tz - s.z, dist = M.hypot(dx, dz);
      if (dist < 0.3) { k += 1; best = Infinity; still = 0; continue; }
      const want = M.atan2(dx, -dz);
      let dyaw = wrap(want - s.yaw); if (dyaw > Math.PI) dyaw -= 2 * Math.PI;
      const inp = { f: true, dyaw: dyaw };
      inputs.push(inp); step(world, s, inp);
      if (dist < best - 1e-6) { best = dist; still = 0; } else if (++still > 180) return { ok: false, inputs: inputs, ticks: n, at: path[k] };
    }
    return { ok: false, inputs: inputs, ticks: limitTicks, at: path[k] };
  }

  // a route's waypoints joined by the walk graph into one path of cells, or the waypoint no path reaches
  function routePath(graph, pts) {
    let path = [pts[0]], broken = null;
    for (let k = 1; k < pts.length && !broken; k++) {
      const seg = graph(pts[k - 1], pts[k]);
      if (!seg) broken = pts[k]; else path = path.concat(seg.slice(1));
    }
    return { path: path, broken: broken };
  }

  // the first open line to a target (from 4 to 30 m) and the first that a wall stops, searching floor cells in order
  function lines(world) {
    const c = world.cell;
    let shot = null, hidden = null;
    const s0 = newState(world, "A");
    for (const t of s0.targets) {
      for (let j = 0; j < world.h; j++) for (let i = 0; i < world.w; i++) {
        if (world.top(i, j) !== 0) continue;
        const x = (i + 0.5) * c, z = (j + 0.5) * c, dist = M.hypot(t.x - x, t.z - z);
        if (dist < 4 || dist > 30) continue;
        const oy = P.eye, ty = t.y + 1.2, dx = t.x - x, dz = t.z - z, dy = ty - oy, L = M.hypot(dx, dy, dz);
        const w = rayWorld(world, x, oy, z, dx / L, dy / L, dz / L, P.range);
        if (!shot && w.t > L) shot = { t: t, x: x, z: z };
        if (!hidden && w.t < L - 1 && w.what === "side") hidden = { t: t, x: x, z: z };
      }
      if (shot && hidden) break;
    }
    return { shot: shot, hidden: hidden };
  }

  // A run made from integers alone, so that every engine makes the same inputs: from spawn A, held moves of every kind
  // (forward, back, strafes and diagonals) for 10 to 59 ticks each, a turn and a look up or down at every tick (whole
  // multiples of 2^-13 and 2^-14 rad), jumps, shots, and a change of side half way. It walks into walls and slides
  // along them, which is where a last bit can decide a halving.
  function stressInputs(n) {
    let st = 0x9e3779b9 >>> 0, hold = 0, cur = null;
    const next = function () { st = (Math.imul(st, 1664525) + 1013904223) >>> 0; return st; };
    const inputs = [];
    for (let k = 0; k < n; k++) {
      if (hold === 0) { const a = next(); cur = { f: (a & 1) === 1, b: (a & 3) === 2, l: (a & 4) === 4, r: (a & 12) === 8 }; hold = 10 + next() % 50; }
      hold -= 1;
      const a = next(), inp = { f: cur.f, b: cur.b, l: cur.l, r: cur.r, dyaw: (a % 2049 - 1024) / 8192, dpitch: ((a >>> 11) % 257 - 128) / 16384 };
      if ((a >>> 20) % 97 === 0) inp.jump = true;
      if ((a >>> 24) % 23 === 0) inp.fire = true;
      if (k === (n >> 1)) inp.side = "B";
      inputs.push(inp);
    }
    return inputs;
  }

  // The three runs the state checks use, made by playing: the first route (in name order) the bot walked end to end,
  // as recorded; a fight from the first open line to a target (shots, a jump, a walk, the targets standing again, a
  // change of side); and the stress run above. Each starts from a snapshot.
  function makeRuns(world, recorded, shotSpot) {
    const c = world.cell, runs = [];
    if (recorded) {
      const s = newState(world, "A");
      s.x = (recorded.start[0] + 0.5) * c; s.z = (recorded.start[1] + 0.5) * c; s.feet = groundAt(world, s.x, s.z);
      runs.push({ name: "the walk", start: snapshot(s), inputs: recorded.inputs, every: 30, resumeEvery: 120 });
    }
    if (shotSpot) {
      const s = newState(world, "A");
      s.x = shotSpot.x; s.z = shotSpot.z; s.feet = groundAt(world, s.x, s.z);
      const tgt = s.targets.find(function (q) { return q.id === shotSpot.t.id; });
      const dx = tgt.x - s.x, dz = tgt.z - s.z;
      s.yaw = wrap(M.atan2(dx, -dz)); s.pitch = M.atan2(tgt.y + 1.2 - (s.feet + P.eye), M.hypot(dx, dz));
      const inputs = [];
      const add = function (n, inp) { for (let k = 0; k < n; k++) inputs.push(typeof inp === "function" ? inp(k) : inp); };
      add(1, { fire: true }); add(20, {}); add(1, { fire: true }); add(1, { jump: true }); add(8, {});
      add(1, { fire: true, dyaw: 0.02 });
      add(60, function (k) { return { f: true, dyaw: 0.01, dpitch: -0.002, fire: k % 25 === 0 }; });
      add(Math.ceil(P.targetDown / TICK) + 10, {});
      add(1, { side: "B" }); add(30, { f: true, r: true }); add(1, { fire: true }); add(1, { reset: true }); add(1, { side: "A" });
      add(40, function (k) { return { b: true, l: true, jump: k % 15 === 0 }; });
      runs.push({ name: "the fight", start: snapshot(s), inputs: inputs, every: 5, resumeEvery: 40 });
    }
    runs.push({ name: "the stress", start: snapshot(newState(world, "A")), inputs: stressInputs(3600), every: 120, resumeEvery: 600 });
    return runs;
  }

  // the same three runs without the self-test around them, for the trace experiment (graybox/trace.py)
  function record(map) {
    const world = new World(map), c = world.cell, graph = walkGraph(world);
    let recorded = null;
    for (const name of Object.keys(world.routes).sort()) {
      const pts = world.routes[name].cells, rp = routePath(graph, pts);
      if (rp.broken) continue;
      const s = newState(world, "A");
      s.x = (pts[0][0] + 0.5) * c; s.z = (pts[0][1] + 0.5) * c; s.feet = groundAt(world, s.x, s.z);
      const r = walk(world, s, rp.path, rp.path.length * 120 + 600);
      if (r.ok) { recorded = { start: pts[0], inputs: r.inputs }; break; }
    }
    return makeRuns(world, recorded, lines(world).shot);
  }

  // ---------------------------------------------------------------- the rules' arithmetic, checked
  // Fixed sets of arguments for each function, made from integers by one generator and exact operations, so that every
  // engine makes the same ones (graybox/rules_ref.py makes them too): ordinary angles and ratios, sums near multiples
  // of pi/2, the tiny and the large, unit vectors, every binade from the subnormals to the largest doubles, and special
  // values. A function's digest folds the bits of all its results (FNV-1a, big-endian).
  const PIO2D = dbl(0x3FF921FB, 0x54442D18), TWOPI = dbl(0x401921FB, 0x54442D18);
  // the edges of the reduction's and the kernels' branches: 2^-27, 0.3, 0.78125, pi/4, 3pi/4 (as doubles)
  const EDGES = [dbl(0x3E400000, 0), dbl(0x3FD33333, 0x33333333), 0.78125, dbl(0x3FE921FB, 0x54442D18), dbl(0x4002D97C, 0x7F3321D2)];
  const SPECIAL = [0, -0, 1, -1, Infinity, -Infinity, 0.5, -0.5, 2.4375, 1.1875, 0.4375, 0.6875, 0.75, dbl(0x01a56e1f, 0xc2f8f359), -dbl(0x7e37e43c, 0x8800759c)];
  function pow2(e) {
    if (e >= -1022) return dbl((e + 1023) << 20, 0);
    const b = e + 1074;
    return b >= 32 ? dbl((1 << (b - 32)) >>> 0, 0) : dbl(0, (1 << b) >>> 0);
  }
  function ruleArgs(fn, n) {
    let st = { sin: 1, cos: 2, atan2: 3, hypot: 4, sqrt: 5 }[fn];
    const next = function () { st = (Math.imul(st, 1664525) + 1013904223) >>> 0; return st; };
    const u = function () { return next() / 4294967296; }, sg = function () { return u() * 2 - 1; };
    const out = [];
    for (let i = 0; i < n; i++) {
      if (fn === "sin" || fn === "cos") {
        const k = i % 7;
        if (k === 0) out.push([sg() * 8]);
        else if (k === 1) out.push([sg() * 1024]);
        else if (k === 2) { const m = next() % 2001 - 1000; out.push([m * PIO2D + (u() - 0.5) * pow2(-20 - next() % 30)]); }
        else if (k === 3) out.push([sg() * pow2(-26 - next() % 40)]);
        else if (k === 4) out.push([sg() * 800000]);
        else if (k === 5) out.push([u() * TWOPI + (next() % 3 === 0 ? -0.25 : 0)]);
        else { const e = EDGES[next() % EDGES.length]; out.push([(next() % 9 - 4) * PIO2D + e * (1 + (next() % 2001 - 1000) * pow2(-24))]); }
      } else if (fn === "atan2") {
        const k = i % 4;
        if (k === 0) out.push([sg() * 10, sg() * 10]);
        else if (k === 1) out.push([sg() * pow2(next() % 200 - 100), sg() * pow2(next() % 200 - 100)]);
        else if (k === 2) out.push([SPECIAL[next() % SPECIAL.length], SPECIAL[next() % SPECIAL.length]]);
        else out.push([sg() * 60, -(sg() * 60)]);
      } else if (fn === "hypot") {
        const k = i % 4;
        if (k === 0) out.push([sg() * 60, sg() * 60]);
        else if (k === 1) { const t = u() * TWOPI; out.push([xsin(t), xcos(t)]); }
        else if (k === 2) out.push([sg() * pow2(next() % 2098 - 1074), sg() * pow2(next() % 2098 - 1074)]);
        else out.push([sg() * 60, sg() * 3, sg() * 60]);
      } else {
        const k = i % 3;
        if (k === 0) out.push([u() * pow2(next() % 2098 - 1074)]);
        else if (k === 1) { const a = sg() * 1000; out.push([a * a]); }
        else out.push([u() * 4]);
      }
    }
    return out;
  }
  const DG = new DataView(new ArrayBuffer(8));
  function ruleDigest(fn, f, n) {
    let h = 0x811c9dc5;
    for (const a of ruleArgs(fn, n)) {
      DG.setFloat64(0, f.apply(null, a));
      for (let k = 0; k < 8; k++) { h ^= DG.getUint8(k); h = Math.imul(h, 0x01000193) >>> 0; }
    }
    return ("00000000" + h.toString(16)).slice(-8);
  }
  // the constants of the algorithms, in order, folded into one digest: each must be fdlibm's to the last bit
  function constantsDigest() {
    let h = 0x811c9dc5;
    for (const v of [S1, S2, S3, S4, S5, S6, C1, C2, C3, C4, C5, C6, INVPIO2, PIO2_1, PIO2_1T, PIO2_2, PIO2_2T, PIO2_3, PIO2_3T]
                    .concat(ATANHI, ATANLO, AT, [TINY, PI_O_4, PI_O_2, PI, PI_LO])) {
      DG.setFloat64(0, v);
      for (let k = 0; k < 8; k++) { h ^= DG.getUint8(k); h = Math.imul(h, 0x01000193) >>> 0; }
    }
    return ("00000000" + h.toString(16)).slice(-8);
  }
  const RULE_CONSTANTS = "b258b096";
  // the digests graybox/rules_ref.py gives for 4,000 arguments a function
  const RULE_N = 4000;
  const RULE_DIGESTS = { sin: "9d99eeb3", cos: "f46aa452", atan2: "2034de36", hypot: "015dd106", sqrt: "e78d20f8" };
  // special values, as IEEE 754 and fdlibm define them: [function, arguments, the result's bits]
  const RULE_SPECIALS = [
    ["sin", [0], "0000000000000000"], ["sin", [-0], "8000000000000000"], ["sin", [Infinity], "nan"], ["sin", [NaN], "nan"],
    ["cos", [0], "3ff0000000000000"], ["cos", [-Infinity], "nan"],
    ["atan2", [0, -1], "400921fb54442d18"], ["atan2", [-0, -1], "c00921fb54442d18"], ["atan2", [0, 0], "0000000000000000"],
    ["atan2", [-0, 0], "8000000000000000"], ["atan2", [0, -0], "400921fb54442d18"], ["atan2", [1, 0], "3ff921fb54442d18"],
    ["atan2", [Infinity, Infinity], "3fe921fb54442d18"], ["atan2", [-Infinity, -Infinity], "c002d97c7f3321d2"],
    ["atan2", [1, Infinity], "0000000000000000"], ["atan2", [-1, -Infinity], "c00921fb54442d18"], ["atan2", [1e300, -1e-300], "3ff921fb54442d18"],
    ["hypot", [Infinity, NaN], "7ff0000000000000"], ["hypot", [NaN, 1], "nan"], ["hypot", [-0, -0], "0000000000000000"], ["hypot", [], "0000000000000000"],
    ["hypot", [3, 4], "4014000000000000"], ["hypot", [dbl(0x7fefffff, 0xffffffff), dbl(0x7fefffff, 0xffffffff)], "7ff0000000000000"],
    ["hypot", [dbl(0, 1), 0], "0000000000000001"], ["hypot", [dbl(0, 3), dbl(0, 4)], "0000000000000005"],
    ["sqrt", [-0], "8000000000000000"], ["sqrt", [-1], "nan"], ["sqrt", [Infinity], "7ff0000000000000"], ["sqrt", [2], "3ff6a09e667f3bcd"],
    ["sqrt", [dbl(0, 1)], "1e60000000000000"], ["sqrt", [dbl(0x7fefffff, 0xffffffff)], "5fefffffffffffff"],
  ];
  function bitsHex(v) { if (v !== v) return "nan"; DG.setFloat64(0, v); let h = ""; for (let k = 0; k < 8; k++) h += ("0" + DG.getUint8(k).toString(16)).slice(-2); return h; }
  // the source's own text up to the self-test (the rules, the runs and the bot), its comments taken out and the rules-0
  // block set aside: the approximated Math functions it names (none, in rules 1's code)
  const APPROX = ["sin", "cos", "tan", "asin", "acos", "atan", "atan2", "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
                  "exp", "expm1", "log", "log1p", "log2", "log10", "pow", "cbrt", "hypot", "sqrt"];
  function approxNamed(src) {
    const end = src.indexOf("function selftest(map, ctx)"), a = src.indexOf("// rules 0: the engine's own functions"), b = src.indexOf("// end of rules 0");
    let t = src.slice(0, end > 0 ? end : src.length);
    t = a >= 0 && b > a && b < t.length ? t.slice(0, a) + t.slice(b) : t;
    t = t.replace(/\/\*[\s\S]*?\*\//g, " ").replace(/\/\/[^\n]*/g, " ");
    const found = [];
    const re = /\bMath\s*\.\s*([A-Za-z0-9_]+)|\*\*/g;
    let m;
    while ((m = re.exec(t))) if (!m[1] || APPROX.indexOf(m[1]) >= 0) found.push(m[1] ? "Math." + m[1] : "**");
    return found;
  }

  function overlaps(world, x, z, i, j) {
    let hit = false;
    touching(world, x, z, P.radius, function (a, b) { if (a === i && b === j) hit = true; });
    return hit;
  }

  // ctx, if given, receives the runs the state checks use (ctx.runs), for the page's own checks after these
  function selftest(map, ctx) {
    const out = [];
    const check = function (name, ok, detail) { out.push({ name: name, ok: !!ok, detail: detail || "" }); };
    let world;
    try { world = new World(map); } catch (e) { check("load", false, String(e)); return out; }
    check("load", world.tops.length === world.w * world.h, world.w + " x " + world.h + " cells of " + world.cell + " m");
    const c = world.cell;
    // spawns
    for (const side of ["A", "B"]) {
      const s = newState(world, side); step(world, s, {});
      const sp = world.spawns[side];
      check("spawn " + side, s.onGround && Math.abs(s.x - (sp.x + 0.5) * c) < 1e-9 && Math.abs(s.z - (sp.z + 0.5) * c) < 1e-9
            && s.feet === world.top(sp.x, sp.z) && !blocked(world, s, s.x, s.z, s.feet),
            "cell " + sp.x + "," + sp.z + ", feet " + s.feet + " m, on the ground");
    }
    // probes, through the runtime's movement
    for (const p of world.probes) {
      const s = newState(world, "A");
      if (p.expect === "open") {
        s.x = (p.x + 0.5) * c; s.z = (p.z + 0.5) * c; s.feet = groundAt(world, s.x, s.z);
        const free = !blocked(world, s, s.x, s.z, s.feet);
        let moved = false;
        for (const yaw of [0, Math.PI / 2, Math.PI, 3 * Math.PI / 2]) {
          const t = newState(world, "A"); t.x = s.x; t.z = s.z; t.feet = s.feet; t.yaw = yaw;
          for (let n = 0; n < 30; n++) step(world, t, { f: true });
          if (M.hypot(t.x - s.x, t.z - s.z) > 1.0) moved = true;
        }
        check("probe open " + p.x + "," + p.z, free && moved, free ? (moved ? "the player stands in it and walks out of it" : "the player cannot walk out of it") : "the player cannot stand in it");
      } else {
        let tried = 0, held = true;
        for (const d of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const ni = p.x + d[0], nj = p.z + d[1];
          if (world.top(ni, nj) > P.step) continue;
          tried += 1;
          const s2 = newState(world, "A");
          s2.x = (ni + 0.5) * c; s2.z = (nj + 0.5) * c; s2.feet = groundAt(world, s2.x, s2.z); s2.yaw = M.atan2(-d[0], d[1]);
          for (let n = 0; n < 180; n++) {
            step(world, s2, { f: true, jump: n % 30 === 0 });
            if (overlaps(world, s2.x, s2.z, p.x, p.z)) { held = false; break; }
          }
        }
        check("probe wall " + p.x + "," + p.z, held, tried ? "walked and jumped at from " + tried + " side(s), never entered" : "no open side to walk at it from; held by its top alone");
      }
    }
    // routes, walked by a bot through the runtime's movement; the first one's inputs kept for the replay
    const graph = walkGraph(world);
    let recorded = null;
    for (const name of Object.keys(world.routes).sort()) {
      const pts = world.routes[name].cells;
      const { path, broken } = routePath(graph, pts);
      if (broken) { check("route " + name, false, "no path to " + broken); continue; }
      const s = newState(world, "A");
      s.x = (pts[0][0] + 0.5) * c; s.z = (pts[0][1] + 0.5) * c; s.feet = groundAt(world, s.x, s.z);
      const r = walk(world, s, path, path.length * 120 + 600);
      const end = pts[pts.length - 1];
      const there = Math.floor(s.x / c) === end[0] && Math.floor(s.z / c) === end[1];
      check("route " + name, r.ok && there, r.ok ? path.length + " cells walked in " + (r.ticks / 120).toFixed(1) + " s" : "stuck before " + r.at);
      if (r.ok && !recorded) recorded = { start: pts[0], inputs: r.inputs };
    }
    // gravity and the jump
    {
      const s = newState(world, "A"); const g0 = s.feet; let top = g0, landed = -1;
      step(world, s, { jump: true });
      for (let n = 1; n < 240; n++) { step(world, s, {}); if (s.feet > top) top = s.feet; if (s.feet < g0 - 1e-9) break; if (s.onGround && landed < 0) landed = n; }
      check("gravity and jump", top - g0 > 1.1 && top - g0 < 1.4 && landed > 0 && s.feet === g0,
            "rose " + (top - g0).toFixed(3) + " m, landed after " + (landed / 120).toFixed(2) + " s, never below the floor");
    }
    // cover: blocked on foot, mounted with a jump
    {
      let found = null;
      for (let j = 0; j < world.h && !found; j++) for (let i = 0; i < world.w && !found; i++) {
        const t = world.top(i, j);
        if (t > P.step && t <= 1.0 + 1e-9) for (const d of [[1, 0], [-1, 0], [0, 1], [0, -1]]) if (!found && world.top(i - d[0], j - d[1]) === 0) found = [i, j, d];
      }
      if (!found) check("cover", true, "not applicable: the map has no cover of 1 m beside the floor");
      else {
        const [ci, cj, d] = found, yaw = M.atan2(d[0], -d[1]);
        const a = newState(world, "A"); a.x = (ci - d[0] + 0.5) * c; a.z = (cj - d[1] + 0.5) * c; a.feet = 0; a.yaw = yaw;
        let entered = false;
        for (let n = 0; n < 120; n++) { step(world, a, { f: true }); if (overlaps(world, a.x, a.z, ci, cj)) entered = true; }
        const b = newState(world, "A"); b.x = (ci - d[0] + 0.5) * c; b.z = (cj - d[1] + 0.5) * c; b.feet = 0; b.yaw = yaw;
        for (let n = 0; n < 240; n++) {
          const dist = M.hypot((ci + 0.5) * c - b.x, (cj + 0.5) * c - b.z);
          step(world, b, { f: dist > 0.2, jump: n === 0 });
        }
        check("cover", !entered && a.feet === 0 && b.feet === world.top(ci, cj) && b.onGround,
              "cover at " + ci + "," + cj + " (" + world.top(ci, cj) + " m): on foot never entered; with a jump stood on it at " + b.feet + " m");
      }
    }
    // the weapon: a hit in the open, a miss behind a wall, the target back up
    let shotSpot = null;
    {
      const { shot, hidden } = lines(world);
      shotSpot = shot;
      const fireAt = function (spot) {
        const s = newState(world, "A");
        s.x = spot.x; s.z = spot.z; s.feet = 0;
        const tgt = s.targets.find(function (q) { return q.id === spot.t.id; });
        const dx = tgt.x - s.x, dz = tgt.z - s.z, dy = tgt.y + 1.2 - (s.feet + P.eye);
        s.yaw = wrap(M.atan2(dx, -dz)); s.pitch = M.atan2(dy, M.hypot(dx, dz));
        step(world, s, { fire: true });
        return { s: s, tgt: tgt };
      };
      if (!shot) check("weapon hit", false, "no open line to any target");
      else {
        const r = fireAt(shot);
        const down = !r.tgt.up && r.s.score === 1;
        for (let n = 0; n < Math.ceil(P.targetDown / TICK) + 2; n++) step(world, r.s, {});
        check("weapon hit", down && r.tgt.up, "target " + r.tgt.id + " hit from " + (M.hypot(r.tgt.x - shot.x, r.tgt.z - shot.z)).toFixed(1) + " m, down, and up again after " + P.targetDown + " s");
      }
      if (!hidden) check("weapon occlusion", false, "no target behind a wall to try");
      else {
        const r = fireAt(hidden);
        check("weapon occlusion", r.tgt.up && r.s.score === 0, "target " + r.tgt.id + " behind a wall: the shot stopped at the wall");
      }
    }
    // reset
    {
      const s = newState(world, "A"); const h0 = [s.x, s.z, s.feet, s.yaw];
      for (let n = 0; n < 60; n++) step(world, s, { f: true, r: true, dyaw: 0.01 });
      step(world, s, { reset: true });
      check("reset", s.x === h0[0] && s.z === h0[1] && s.feet === h0[2] && s.yaw === h0[3], "back at spawn A");
    }
    // replay: the recorded inputs from the same start reach the same state at every tick
    if (!recorded) check("replay", false, "no route was walked to record");
    else {
      const run = function () {
        const s = newState(world, "A");
        s.x = (recorded.start[0] + 0.5) * c; s.z = (recorded.start[1] + 0.5) * c; s.feet = groundAt(world, s.x, s.z);
        const hs = [];
        for (const inp of recorded.inputs) { step(world, s, inp); hs.push(hash(s)); }
        return hs;
      };
      const h1 = run(), h2 = run();
      let same = h1.length === h2.length;
      for (let k = 0; same && k < h1.length; k++) if (h1[k] !== h2[k]) same = false;
      check("replay", same && h1.length > 0, h1.length + " ticks, every tick's state hash the same in both runs (last " + h1[h1.length - 1] + ")");
    }

    // ---- the state checks. The replay above compares hashes; these say what an equal hash is worth. Each runs on
    // two runs made by playing (the first route's recorded walk, and a fight), and each has a planted defect it must
    // refuse, so that a check that cannot fail does not pass for one.
    const runs = makeRuns(world, recorded, shotSpot);
    if (ctx) ctx.runs = runs;
    const kinds = function (ps) { return Array.from(new Set(ps.map(leafKind))).join(", "); };

    // hash-coverage: every leaf of the authoritative state is seen by the hash at its last bit, or is one the world
    // declares (a target's name and place, which the map's own digest covers), equal to the world's value and of a
    // kind no tick of the runs writes. Without it an equal hash would say nothing about the leaves it does not read.
    // The leaves are found by walking the state, not listed by hand, so a leaf added later is checked without anyone
    // remembering to; one the world does not declare must be hashed. The state it is tried on is taken mid-fight: a
    // target down, the weapon cooling, the player in the air.
    const WORLD_LEAVES = ["targets[].id", "targets[].x", "targets[].y", "targets[].z"];
    const coverage = function (hashFn, stepFn, prep) {
      const written = new Set();   // kinds of leaf, so that one target's write counts for all of them
      let base = null, lastSnap = null;
      for (const run of runs) {
        const s = restore(run.start);
        if (prep) prep(s);
        let last = new Map(leaves(s).map(function (p) { return [p.join("/"), leafBits(getAt(s, p))]; }));
        for (const inp of run.inputs) {
          stepFn(world, s, inp);
          const now = new Map(leaves(s).map(function (p) { return [p.join("/"), leafBits(getAt(s, p))]; }));
          for (const [k, v] of now) if (last.get(k) !== v) written.add(leafKind(k.split("/").map(function (x) { return /^[0-9]+$/.test(x) ? +x : x; })));
          last = now;
          if (!base && s.score >= 1 && !s.onGround && s.cooldown > 0 && s.targets.some(function (t) { return !t.up; })) base = snapshot(s);
          lastSnap = snapshot(s);
        }
      }
      const b = restore(base || lastSnap), h0 = hashFn(b), fresh = newState(world, b.side);
      if (prep) prep(fresh);
      const res = { hashed: [], fixed: [], open: [] };
      for (const p of leaves(b)) {
        const t = restore(snapshot(b));
        setAt(t, p, nudge(getAt(t, p)));
        const k = leafKind(p);
        if (hashFn(t) !== h0) res.hashed.push(p);
        else if (WORLD_LEAVES.indexOf(k) >= 0 && !written.has(k) && leafBits(getAt(fresh, p)) === leafBits(getAt(b, p))) res.fixed.push(p);
        else res.open.push(p);
      }
      return res;
    };
    if (!runs.length) check("hash-coverage", false, "no run to take a state from");
    else {
      const real = coverage(hash, step);
      const caught = function (r, name) { return r.open.some(function (p) { return leafKind(p) === name; }); };
      const plants = [
        ["a hash blind to vy", caught(coverage(function (s) { const t = restore(snapshot(s)); t.vy = 0; return hash(t); }, step), "vy")],
        ["a hash blind to the targets' downFor", caught(coverage(function (s) { const t = restore(snapshot(s)); for (const q of t.targets) q.downFor = 0; return hash(t); }, step), "targets[].downFor")],
        ["an unhashed leaf written every tick", caught(coverage(hash, function (w, s, inp) { step(w, s, inp); s.stamina = (s.stamina || 0) + TICK; }), "stamina")],
        ["an unhashed leaf no tick writes, not the world's", caught(coverage(hash, step, function (s) { s.mode = "solo"; }), "mode")],
      ];
      const refused = plants.every(function (p) { return p[1]; });
      check("hash-coverage", real.open.length === 0 && real.hashed.length > 0 && refused,
        (real.open.length ? "NOT SEEN by the hash: " + kinds(real.open) + "; " : "")
        + (real.hashed.length + real.fixed.length + real.open.length) + " leaves of the authoritative state, found by walking it: " + real.hashed.length
        + " seen by the hash at their last bit, " + real.fixed.length + " the world's, unchanged by every tick (" + kinds(real.fixed) + "); "
        + plants.length + " plants " + (refused ? "refused" : "NOT all refused: " + plants.filter(function (p) { return !p[1]; }).map(function (p) { return p[0]; }).join(", ")));
    }

    // fx-noninterference: the view's feedback never reaches the authoritative state, which is why the hash may leave
    // it out. At reachable states a twin with the feedback swapped (the hit marker, the flashes, the last shot) is
    // stepped beside the original, and the two must stay the same bit for bit at every tick that follows: the lockstep
    // form of noninterference, tested from states the game reaches rather than from made-up ones.
    const swapFx = function (fx, ids) {
      const flash = {};
      if (!Object.keys(fx.flash).length) { for (const id of ids) flash[id] = 0.25; flash.zz = 1; }
      return { hitMarker: fx.hitMarker > 0 ? 0 : 0.2, flash: flash,
               lastShot: fx.lastShot ? null : { o: [0, 0, 0], h: [1, 1, 1], hit: ids.length ? ids[0] : null, age: 3 } };
    };
    const quiet = function (stepFn) {
      let pairs = 0, ticks = 0, bad = null;
      for (const run of runs) {
        const s = restore(run.start);
        for (let n = 0; n < run.inputs.length && !bad; n++) {
          stepFn(world, s, run.inputs[n]);
          if (n % run.every) continue;
          const a = restore(snapshot(s)), b = restore(snapshot(s));
          a.fx = JSON.parse(JSON.stringify(s.fx));
          b.fx = swapFx(s.fx, s.targets.map(function (t) { return t.id; }));
          pairs++;
          for (let m = n + 1; m < Math.min(run.inputs.length, n + 121); m++) {
            stepFn(world, a, run.inputs[m]); stepFn(world, b, run.inputs[m]); ticks++;
            if (snapshot(a) !== snapshot(b)) { bad = run.name + ", swapped at tick " + (n + 1) + ", apart at tick " + (m + 1); break; }
          }
        }
      }
      return { pairs: pairs, ticks: ticks, bad: bad };
    };
    if (runs.length) {
      const real = quiet(step);
      const peek = quiet(function (w, s, inp) { step(w, s, inp); s.x += Object.keys(s.fx.flash).length * 1e-9; });
      check("fx-noninterference", !real.bad && real.pairs > 0 && !!peek.bad,
        (real.bad ? "the authoritative state DIVERGED (" + real.bad + "); " : "")
        + "the view's feedback (hit marker, flashes, last shot) swapped at " + real.pairs + " reachable states: the authoritative state the same bit for bit at each of the "
        + real.ticks + " ticks that followed; plant: a tick that reads the flashes " + (peek.bad ? "refused (" + peek.bad + ")" : "NOT refused"));
    }

    // snapshot-resume: the authoritative state is everything a tick reads. Snapshots taken along each run are read back
    // exactly and resumed in fresh instances of the simulation, which share no variable with the one that took them,
    // and every later tick must reach the same state bit for bit (Factorio's "heavy mode" saves and loads every tick
    // for the same reason). A fresh instance is still this realm: the page also resumes one in a worker (resume-realm).
    const resume = function (make) {
      let resumed = 0, ticks = 0, bad = null;
      for (const run of runs) {
        if (bad) break;
        const A = make(), wA = new A.World(map), s = A.restore(run.start), trail = [];
        for (const inp of run.inputs) { A.step(wA, s, inp); trail.push(A.snapshot(s)); }
        for (let k = 7; k < run.inputs.length - 1 && !bad; k += run.resumeEvery) {
          const B = make(), wB = new B.World(map), t = B.restore(trail[k]);
          if (B.snapshot(t) !== trail[k]) { bad = "the snapshot at tick " + (k + 1) + " of " + run.name + " did not read back exactly"; break; }
          resumed++;
          for (let m = k + 1; m < run.inputs.length; m++) {
            B.step(wB, t, run.inputs[m]); ticks++;
            if (B.snapshot(t) !== trail[m]) { bad = run.name + ", resumed after tick " + (k + 1) + ", apart at tick " + (m + 1); break; }
          }
        }
      }
      return { resumed: resumed, ticks: ticks, bad: bad };
    };
    if (runs.length) {
      const real = resume(function () { return api.fresh(); });
      const hidden = resume(function () {
        let n = 0;   // a count kept outside the state: a resumed instance starts it again from 0
        return { World: World, restore: restore, snapshot: snapshot,
                 step: function (w, s, inp) { n++; step(w, s, inp); if (n % 100 === 0) s.x += 1e-9; } };
      });
      const frozen = Object.isFrozen(P);
      check("snapshot-resume", !real.bad && real.resumed > 0 && !!hidden.bad && frozen,
        (real.bad ? "DIVERGED (" + real.bad + "); " : "") + (frozen ? "" : "the rules are NOT frozen; ")
        + real.resumed + " snapshots of the authoritative state read back bit for bit and resumed in fresh instances: the same state at each of the "
        + real.ticks + " later ticks; the rules frozen; plant: a tick count kept outside the state " + (hidden.bad ? "refused (" + hidden.bad + ")" : "NOT refused"));
    }

    // ---- the rules' arithmetic: why a tick is the same in every engine. These hold rules 1; rules 0 are measured.
    // rules-arithmetic: each function over its fixed set of arguments, every result's bits folded into a digest that
    // must be the one graybox/rules_ref.py (the same algorithms, in Python) gives; equal digests in two engines mean
    // every result is equal. Then the special values, and the domain the sine and cosine refuse to leave. Plant: a sine
    // whose result at one argument of the set is one bit off.
    {
      const bad = [];
      const cd = constantsDigest();
      if (cd !== RULE_CONSTANTS) bad.push("the constants " + cd + ", not " + RULE_CONSTANTS);
      for (const f of Object.keys(RULE_DIGESTS)) { const d = ruleDigest(f, EXACT[f], RULE_N); if (d !== RULE_DIGESTS[f]) bad.push(f + " " + d + ", not " + RULE_DIGESTS[f]); }
      for (const [f, a, want] of RULE_SPECIALS) { const got = bitsHex(EXACT[f].apply(null, a)); if (got !== want) bad.push(f + "(" + a.join(", ") + ") = " + got + ", not " + want); }
      let refusesRange = false;
      try { xsin(1700000); } catch (e) { refusesRange = e instanceof RangeError; }
      const one = ruleArgs("sin", 101)[100][0];
      const planted = ruleDigest("sin", function (x) { const r = xsin(x); return x === one ? nudge(r) : r; }, RULE_N) !== RULE_DIGESTS.sin;
      check("rules-arithmetic", !bad.length && refusesRange && planted,
        (bad.length ? "DIFFERENT: " + bad.slice(0, 4).join("; ") + "; " : "") + "the algorithms' 43 constants, fdlibm's to the last bit (digest " + RULE_CONSTANTS + "); the rules' sine, cosine, atan2, hypot and square root over " + RULE_N
        + " arguments each: every result as graybox/rules_ref.py gives it (digests " + Object.keys(RULE_DIGESTS).map(function (f) { return f + " " + RULE_DIGESTS[f]; }).join(", ")
        + "); " + RULE_SPECIALS.length + " special values as IEEE 754 and fdlibm define them; the sine " + (refusesRange ? "refuses" : "does NOT refuse") + " an angle past 2^20 pi/2"
        + "; plant: one sine one bit off " + (planted ? "refused" : "NOT refused"));
    }

    // math-fence: no function whose last bits the language leaves to the engine reaches the state. Every one of Math's
    // approximated functions is replaced by one that throws, and the runs are recorded (the bot's walk, the lines, the
    // fight, the stress) and played: the same states at every tick as without the fence. The source, read back, names
    // none of them outside the rules-0 block. Plants: rules 0 under the fence; a source that calls Math.cos in a tick.
    {
      const fenced = function (fn) {
        const saved = {};
        for (const f of APPROX) { saved[f] = Math[f]; Math[f] = function () { throw new Error("the fence: Math." + f + " was called"); }; }
        try { return fn(); } catch (e) { return { error: String(e && e.message || e) }; } finally { for (const f of APPROX) Math[f] = saved[f]; }
      };
      const playAll = function (S) {
        const w = new S.World(map), out = [];
        for (const r of S.record(map)) { const st = S.restore(r.start); for (const inp of r.inputs) { S.step(w, st, inp); out.push(S.snapshot(st)); } }
        return out;
      };
      const plain = playAll(api), inside = fenced(function () { return playAll(api); });
      const same = Array.isArray(inside) && inside.length === plain.length && inside.every(function (x, k) { return x === plain[k]; });
      const r0 = fenced(function () { return playAll(api.withRules(0)); });
      const named = approxNamed(api.source);
      const plantSrc = approxNamed(api.source.replace("function step(world, s, inp) {", "function step(world, s, inp) { Math.cos(0);"));
      check("math-fence", same && named.length === 0 && !!r0.error && plantSrc.length > 0,
        (inside.error ? "a fenced function was called: " + inside.error + "; " : same ? "" : "the states DIFFER under the fence; ")
        + (named.length ? "the source NAMES " + named.join(", ") + "; " : "")
        + "with Math's " + APPROX.length + " approximated functions made to throw, the runs recorded and played, " + plain.length
        + " ticks, the same state at each as without the fence; the source names none of them; plants: rules 0 under the fence "
        + (r0.error ? "refused (" + r0.error + ")" : "NOT refused") + ", a tick that calls Math.cos " + (plantSrc.length ? "found in the source" : "NOT found"));
    }

    // input-contract: the shared table (web/input_cases.json, which the page passes as ctx.inputCases): every admitted
    // step ticks, every refused step is refused with its category and leaves the state as it was, and a run with
    // refusals among its ticks ends where the run without them ends. Then four records only JavaScript can make. Plants:
    // the check made after the tick has begun, NaN admitted, an unknown field ignored, a side applied before the rest of
    // the record is checked; each must break the table.
    {
      const table = ctx && ctx.inputCases;
      if (!table || table.format !== "VERDANDI-INPUT-CASES" || table.contract !== String(INPUT)) {
        check("input-contract", false, "the table of cases (web/input_cases.json, contract " + INPUT + ") was not given to the self-test");
      } else {
        const faults = inputFaults(table, inputCases(map, table));
        let reads = 0;
        const getter = {};
        Object.defineProperty(getter, "f", { get: function () { reads++; return true; }, enumerable: true });
        const bare = Object.create(null); bare.f = true;
        const own = [["a flag left undefined", { f: undefined }, "INPUT-FLAG"], ["a Date", new Date(0), "INPUT-NOT-RECORD"],
                     ["a record without a prototype", bare, "tick"], ["a getter", getter, "tick"]];
        for (const [what, inp, want] of own) {
          const st = newState(new World(map), "A"), r = step(new World(map), st, inp), got = r == null ? "tick" : r;
          if (got !== want) faults.push(what + ": " + got + ", not " + want);
        }
        if (reads !== 1) faults.push("a getter read " + reads + " times, not once");
        const plants = [
          ["the check made after the tick has begun", function (w, s, inp) { s.tick += 1; const a = admit(inp); if (typeof a === "string") return a; s.tick -= 1; advance(w, s, a); return null; }],
          ["NaN admitted", function (w, s, inp) { const a = admit(inp, { nan: true }); if (typeof a === "string") return a; advance(w, s, a); return null; }],
          ["an unknown field ignored", function (w, s, inp) { const a = admit(inp, { unknown: true }); if (typeof a === "string") return a; advance(w, s, a); return null; }],
          ["a side applied before the rest is checked", function (w, s, inp) { if (inp && (inp.side === "A" || inp.side === "B")) spawn(w, s, inp.side); return step(w, s, inp); }],
        ];
        const caught = plants.map(function (p) { const f = inputFaults(table, inputCases(map, table, p[1])); return [p[0], f.length, f[0] || ""]; });
        const steps = table.cases.reduce(function (n, c) { return n + c.steps.length; }, 0);
        check("input-contract", !faults.length && caught.every(function (c) { return c[1] > 0; }),
          (faults.length ? "FAULTS: " + faults.slice(0, 3).join("; ") + "; " : "") + table.cases.length + " cases, " + steps
          + " steps (web/input_cases.json, contract " + INPUT + "): every admitted step ticked, every refused one refused with its category and the state as it was, the runs with refusals among their ticks ending where the runs without them end"
          + "; this engine's own records: a flag left undefined, a Date, a record without a prototype, a getter (read once)"
          + "; plants: " + caught.map(function (c) { return c[0] + " " + (c[1] ? "refused (" + c[1] + " faults)" : "NOT refused"); }).join(", "));
      }
    }

    // measured, not checked: rules 0 against their recorded baseline, and this engine's Math against the rules'
    if (ctx) {
      ctx.measurements = [];
      const S0 = api.withRules(0), w0 = new S0.World(map), walk0 = S0.record(map)[0];
      if (walk0) {
        const st = S0.restore(walk0.start);
        let last = "";
        for (const inp of walk0.inputs) { S0.step(w0, st, inp); last = S0.hash(st); }
        const base = RULES0_BASELINE[(map.canonical && map.canonical.name) || ""];
        ctx.measurements.push({ name: "rules 0 (the engine's Math)", detail: "the first route's walk, recorded and replayed under rules 0: " + walk0.inputs.length
          + " ticks, the last state's hash " + last + (base ? "; the baseline recorded on 2026-10-10 in the build container and on the owner's machine: " + base : "") + " (this browser)" });
      }
      const nat = { sin: Math.sin, cos: Math.cos, atan2: Math.atan2, hypot: Math.hypot, sqrt: Math.sqrt };
      ctx.measurements.push({ name: "this engine's Math against the rules'", detail: Object.keys(nat).map(function (f) {
        let n = 0;
        for (const a of ruleArgs(f, RULE_N)) if (bitsHex(nat[f].apply(Math, a)) !== bitsHex(EXACT[f].apply(null, a))) n++;
        return "Math." + f + " different on " + n;
      }).join(", ") + " of " + RULE_N + " arguments each (this browser)" });
    }
    return out;
  }

  const RULES0_BASELINE = { tactical: "91350c39A", witness: "ce819a52A" };

  const api = { RULES: RULES, INPUT: INPUT, admit: function (inp) { return admit(inp); }, inputCases: function (map, table) { return inputCases(map, table); },
                inputFaults: inputFaults, math: M, TICK: TICK, P: P, World: World, newState: newState, step: step, spawn: spawn, fire: fire, aim: aim,
                rayWorld: rayWorld, blocked: blocked, groundAt: groundAt, hash: hash, snapshot: snapshot, restore: restore,
                nudge: nudge, bits: bitsOf, fromBits: ofBits, record: record, selftest: selftest };
  return api;
});
