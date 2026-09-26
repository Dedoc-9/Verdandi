# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Exact rational over Z -- the physics substrate. num/den, gcd-reduced, den>0,
i64-bounded; any overflow or division by zero is a REFUSAL ('PHYS-REFUSE'),
never a wrap or an approximation. No floating point: momentum and energy stay
EXACT so conservation is decidable by integer equality."""
IMAX = (1 << 63) - 1


class RationalError(Exception):
    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _g(v):
    if v > IMAX or v < -IMAX:
        raise RationalError("PHYS-REFUSE", f"i64 overflow ({v})")
    return v


def _gcd(a, b):
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


class Q:
    """Reduced rational n/d, d>0. The constructor is the canonical form."""
    __slots__ = ("n", "d")

    def __init__(self, n, d=1):
        if d == 0:
            raise RationalError("PHYS-REFUSE", "rational with zero denominator")
        if d < 0:
            n, d = -n, -d
        g = _gcd(n, d) or 1
        self.n = _g(n // g)
        self.d = _g(d // g)

    def __add__(s, o): return Q(_g(s.n * o.d) + _g(o.n * s.d), _g(s.d * o.d))
    def __sub__(s, o): return Q(_g(s.n * o.d) - _g(o.n * s.d), _g(s.d * o.d))
    def __mul__(s, o): return Q(_g(s.n * o.n), _g(s.d * o.d))

    def __truediv__(s, o):
        if o.n == 0:
            raise RationalError("PHYS-REFUSE", "division by zero rational")
        return Q(_g(s.n * o.d), _g(s.d * o.n))

    def __neg__(s): return Q(-s.n, s.d)
    def __eq__(s, o): return s.n == o.n and s.d == o.d
    def __lt__(s, o): return _g(s.n * o.d) < _g(o.n * s.d)
    def __le__(s, o): return _g(s.n * o.d) <= _g(o.n * s.d)
    def __hash__(s): return hash((s.n, s.d))
    def is_zero(s): return s.n == 0
    def pair(s): return (s.n, s.d)
    def __repr__(s): return f"{s.n}/{s.d}"


def Z(i):
    return Q(i, 1)
