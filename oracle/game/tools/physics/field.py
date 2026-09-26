# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""urdr-field -- deterministic scalar-field transport (advection-diffusion).

A reactive-environment substrate: a scalar grid (heat / chemical concentration)
that evolves under diffusion + first-order upwind advection. The pipeline's
`exact vs scale` tradeoff is exposed as an explicit, user-selectable BACKEND, and
made honest by the four rules:

  1. The backend is part of STATE IDENTITY. The frame carries a backend tag, so a
     fixed-point field and an exact field are never conflated:
         [MAGIC "URDRFLD1"][BACKEND 8B "FIELDFP " | "FIELDQ  "]
         [W u32][H u32][per-cell canonical payload]
  2. The `FixedPoint` parameters are FROZEN SPEC: radix 2^32, round-to-nearest
     ties-away-from-zero — so every compiler/CPU truncates identically.
  3. Both backends are DETERMINISTIC and CROSS-PLACEABLE (bit-identical across
     placements). The choice only trades exactness vs scale, never determinism.
  4. `FixedPoint` is the load-bearing real-time path (BOUNDED, ROUNDS); `Exact`
     (reusing the physics rational `Q`) is EXACT but its denominators grow, so it
     REFUSES on any sizable/long field — a scoped, small, high-stakes option.

The step is a CONSERVATIVE FLUX FORM: each edge flux is computed once and applied
`+` to one cell and `-` to its neighbor, so total mass (Σ cells) is conserved
EXACTLY even in fixed-point (integer add/sub cancel the rounded flux). The
boundary is zero-flux (adiabatic): out-of-domain neighbors clamp to the edge cell,
so no mass leaves the grid. No float, no clock, no RNG. Consumes rational; touches
no core; no new glyph."""
import hashlib

from rational import Q as RQ, RationalError

ONE = 1 << 32                     # FixedPoint radix (Q32.32), FROZEN
IMAX = (1 << 63) - 1
MAGIC = b"URDRFLD1"


class FieldError(Exception):
    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _int(name, v):
    """THE SUBSTRATE'S DOMAIN, ENFORCED — and it was reachable.

    This module's headline is "No float, no clock, no RNG", and the whole
    determinism argument above rests on it: every placement rounds identically
    because the arithmetic is exact integer. Nothing checked. `FixedPoint.unit`
    accepted a float, `_rdiv`'s `//` returns a float for a float operand, and the
    float rode into the Q32.32 state — 232 float words in the worldstep witness on
    the pinned highway scene, from ONE malformed impulse.

    It was invisible because `ser` did `int(a).to_bytes(...)`: the serializer
    truncated at witness time, so every digest looked well-formed while the running
    state sat off-lattice, and the divergence only surfaced later when `mul_k`
    rounded a float differently from the exact integer path at a wall bounce.

    And it was a DESYNC VECTOR rather than an audit hole, which is the part that
    made this the first move. `lockstep._u` is `FP.unit(int(v), 1)` and truncates;
    `worldstep.step_tick` is `FP.unit(dvx, 1)` and does not. So one malformed
    transcript produced TWO DIFFERENT WITNESS CHAINS with no refusal from either —
    8a0dfd44… through N4 against 9a636787… through N5 — which is exactly the
    composed sentence D12 states for worldpeer ("the identical witness chain OR the
    same typed refusal") failing on both arms at once. Every pinned log is integer,
    so the corpus sat entirely inside the admitted domain and never saw it (L20).

    `bool` is excluded on purpose: `True == 1` reaches a frozen integer parameter as
    a value nobody wrote, which is the `boolport` rung's law applied one layer down."""
    if not isinstance(v, int) or isinstance(v, bool):
        raise FieldError("FIELD-REFUSE",
                         "%s must be an exact integer, got %r (%s) — the Q32.32 "
                         "substrate has no float anywhere, and a silent conversion "
                         "here is an authority act with no record"
                         % (name, v, type(v).__name__))
    return v


def _rdiv(p, d):
    """Round p/d to nearest, ties away from zero (d > 0). The FROZEN rounding
    rule — every placement must evaluate this identically."""
    if p >= 0:
        return (2 * p + d) // (2 * d)
    return -((2 * (-p) + d) // (2 * d))


class FixedPoint:
    """Q32.32 fixed-point backend: bounded, deterministic, round-to-nearest.
    Reproducible across placements, but it ROUNDS — not exact."""
    tag = b"FIELDFP "
    ONE = ONE

    @staticmethod
    def _g(v):
        if v > IMAX or v < -IMAX:
            raise FieldError("FIELD-REFUSE", f"i64 overflow ({v})")
        return v

    @staticmethod
    def zero():
        return 0

    @staticmethod
    def unit(num, den):
        # THE DOOR. Every caller-supplied quantity enters the substrate here, and
        # `add`/`sub`/`mul_k` are closed over the integers, so guarding this point
        # closes entry for all of them — asserted nowhere and MEASURED by
        # `arithmetic_is_int_closed`, because "the middle cannot produce a float" is
        # exactly the kind of claim this module already got wrong once.
        return FixedPoint._g(_rdiv(_int("num", num) * ONE, _int("den", den)))

    @staticmethod
    def add(a, b):
        return FixedPoint._g(a + b)

    @staticmethod
    def sub(a, b):
        return FixedPoint._g(a - b)

    @staticmethod
    def mul_k(a, kn, kd):
        # A SECOND DOOR, and I had it wrong one edit ago. `unit` looked like the only
        # entry because `add`/`sub` are closed over the substrate's own values — but
        # `kn`/`kd` are a CALLER-SUPPLIED rational coefficient, so they enter here and
        # nowhere else. `FixedPoint.mul_k(x, 1.5, 2)` was admitted and returned a
        # float. `lockstep` reaches this with `w["e"]`, the restitution, so a world
        # authored with a float bounce coefficient walked straight in past a guarded
        # `unit`. Caught by `arithmetic_is_int_closed` rather than by review, which is
        # the argument for measuring the closure instead of asserting it.
        # `a` is deliberately NOT guarded: it is a value already inside the substrate,
        # it is on the hot path of every tick, and a float reaching it by some other
        # route is caught at the witness by `ser`.
        return FixedPoint._g(_rdiv(a * _int("kn", kn), _int("kd", kd)))

    @staticmethod
    def is_zero(a):
        return a == 0

    @staticmethod
    def ser(a):
        # THE WITNESS, and it is a SECOND guard rather than a redundant one. The
        # door stops a float ENTERING; this stops a float that got in by another
        # route from minting a well-formed digest. `int(a)` was doing the truncation
        # silently, which is precisely why the contamination was invisible to every
        # conformance digest in the tree. Their independence is measured, not argued:
        # a word injected directly into a state list never passes through `unit`.
        return _int("word", a).to_bytes(8, "big", signed=True)


class Exact:
    """Exact rational backend (reuses the physics `Q`): EXACT, but denominators
    grow — it REFUSES (PHYS-REFUSE) on any sizable/long field. Scoped-tiny."""
    tag = b"FIELDQ  "

    @staticmethod
    def zero():
        return RQ(0, 1)

    @staticmethod
    def unit(num, den):
        # THE SAME DOOR, because the hole was in BOTH backends and fixing one would
        # have broken rule 3 above — the two differ in exactness and scale, "never
        # determinism". `Exact` was the worse of the pair: it did not truncate, it
        # built RQ(5.5, 1) and carried a RATIONAL WHOSE PARTS ARE FLOATS, printing
        # `11.0/2.0`, after which `ser` raises an untyped AttributeError reaching for
        # `.to_bytes` on a float. A rational with a float numerator is not a slower
        # exact number, it is the exactness claim inverted.
        return RQ(_int("num", num), _int("den", den))

    @staticmethod
    def add(a, b):
        return a + b

    @staticmethod
    def sub(a, b):
        return a - b

    @staticmethod
    def mul_k(a, kn, kd):
        return a * RQ(_int("kn", kn), _int("kd", kd))

    @staticmethod
    def is_zero(a):
        return a.is_zero()

    @staticmethod
    def ser(a):
        return _int("num", a.n).to_bytes(8, "big", signed=True) \
            + _int("den", a.d).to_bytes(8, "big", signed=True)


def _clamp(i, n):
    return 0 if i < 0 else (n - 1 if i >= n else i)


def step(B, grid, w, h, k, vx, vy):
    """One conservative flux-form step over backend B. `grid` is a length-w*h
    list of B values (row-major). `k=(kn,kd)` diffusion coeff, `vx,vy` velocity
    (rational (num,den)). Diffusion flux `k·(c_b − c_a)`; first-order UPWIND
    advection flux `v·c_upwind`; each flux applied +to one cell, −to the neighbor
    (mass conserved exactly). Zero-flux boundary via edge clamping."""
    kn, kd = k
    vxn, vxd = vx
    vyn, vyd = vy
    new = list(grid)

    def ix(x, y):
        return _clamp(y, h) * w + _clamp(x, w)

    for y in range(h):
        for x in range(w - 1):
            a = ix(x, y)
            b = ix(x + 1, y)
            fd = B.mul_k(B.sub(grid[b], grid[a]), kn, kd)   # diffusion
            new[a] = B.add(new[a], fd)
            new[b] = B.sub(new[b], fd)
            if vxn > 0:                                     # upwind = left cell
                fu = B.mul_k(grid[a], vxn, vxd)
                new[a] = B.sub(new[a], fu)
                new[b] = B.add(new[b], fu)
            elif vxn < 0:                                   # upwind = right cell
                fu = B.mul_k(grid[b], -vxn, vxd)
                new[b] = B.sub(new[b], fu)
                new[a] = B.add(new[a], fu)
    for y in range(h - 1):
        for x in range(w):
            a = ix(x, y)
            b = ix(x, y + 1)
            fd = B.mul_k(B.sub(grid[b], grid[a]), kn, kd)
            new[a] = B.add(new[a], fd)
            new[b] = B.sub(new[b], fd)
            if vyn > 0:
                fu = B.mul_k(grid[a], vyn, vyd)
                new[a] = B.sub(new[a], fu)
                new[b] = B.add(new[b], fu)
            elif vyn < 0:
                fu = B.mul_k(grid[b], -vyn, vyd)
                new[b] = B.sub(new[b], fu)
                new[a] = B.add(new[a], fu)
    return new


def mass(B, grid):
    """Total scalar mass Σ cells (the exactly-conserved flux-form invariant)."""
    m = B.zero()
    for v in grid:
        m = B.add(m, v)
    return m


#: Every caller-supplied scalar, per backend, as (label, call). The domain law is
#: enforced at the DOORS (`unit`, `mul_k`'s coefficient) and at the WITNESS (`ser`);
#: `add`/`sub` take only values the doors already admitted.
def _doors(B):
    one = B.unit(1, 1)
    return (("unit.num", lambda v: B.unit(v, 1)),
            ("unit.den", lambda v: B.unit(1, v)),
            ("mul_k.kn", lambda v: B.mul_k(one, v, 1)),
            ("mul_k.kd", lambda v: B.mul_k(one, 1, v)))


def every_door_refuses(B):
    """RED-FIRST: each caller-supplied scalar refuses a float and a bool, and admits
    the honest int — a door that refused everything would not be a door."""
    for _label, call in _doors(B):
        for bad in (5.5, True, "5"):
            try:
                call(bad)
                return False
            except FieldError as exc:
                if exc.code != "FIELD-REFUSE":
                    return False
            except Exception:
                return False                      # untyped is not a refusal
        try:
            call(2)
        except Exception:
            return False
    return True


def the_witness_refuses(B):
    """The SECOND guard, and the one that makes the contamination visible. A float
    injected straight into a state list never passes a door; `ser` used to truncate
    it with `int(a)` so the digest looked well-formed while the state was off-lattice.
    Independence is the claim: this must refuse a value no door ever saw."""
    class _OffLattice:                            # a rational whose parts are floats
        n, d = 11.0, 2.0
    try:
        B.ser(5.5 if B is FixedPoint else _OffLattice())
    except FieldError as exc:
        return exc.code == "FIELD-REFUSE"
    except Exception:
        return False
    return False


def arithmetic_is_int_closed(B, rounds=64):
    """MEASURED, never asserted: given values the doors admitted, `add`/`sub`/`mul_k`
    return values still in the domain. This is the claim that lets the guards sit at
    the doors instead of in the hot inner loop — and its first draft was WRONG, which
    is why it is a census. It named `unit` as the only door and missed `mul_k`'s
    caller-supplied coefficient, so a float coefficient produced a float word from
    two integer inputs."""
    vals = [B.unit(n, 1) for n in (-3, 0, 1, 7)]
    ok = True
    for i in range(rounds):
        a, b = vals[i % len(vals)], vals[(i // len(vals)) % len(vals)]
        for out in (B.add(a, b), B.sub(a, b), B.mul_k(a, (i % 5) - 2, (i % 3) + 1)):
            try:
                B.ser(out)                        # the domain, asked at the witness
            except FieldError:
                ok = False
    return ok


def digest(B, grid, w, h):
    """Digest(Field) = SHA-256(MAGIC | backend tag | W | H | per-cell payload).
    The backend tag is part of identity — FixedPoint and Exact never collide."""
    out = bytearray(MAGIC) + B.tag + w.to_bytes(4, "big") + h.to_bytes(4, "big")
    for v in grid:
        out += B.ser(v)
    return hashlib.sha256(bytes(out)).hexdigest()
