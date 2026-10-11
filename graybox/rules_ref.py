# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/rules_ref.py — the reference for the rules' arithmetic (rules 1 of graybox/web/sim.js): a second implementation,
# in Python, of the same algorithms, and what holds sim.js to it.
#
#   python graybox/rules_ref.py
#
# By the owner's ruling of 2026-10-11 ("investigate and implement the deterministic math layer now"). sim.js's sine,
# cosine, atan2, hypot and square root are built from operations whose results ECMA-262 fixes to the last bit. Python's
# float is the same IEEE 754 binary64 with the same rounding, and its int is exact, so the same algorithms written here
# must give the same bits. This prints PASS or FAIL for each of:
#   - the digests: each function over the argument sets sim.js makes (the same generator, here) gives the digest
#     sim.js's RULE_DIGESTS holds, so the JavaScript in any engine that passes rules-arithmetic agrees with this file
#     on every one of those results;
#   - the special values (zeros, infinities, NaN, the subnormals, the largest double);
#   - the square root and hypot correctly rounded: each result checked exactly, in fractions, against the midpoints to
#     its neighbours;
#   - sim.js's source, up to its self-test, naming no function whose last bits the language leaves to the engine
#     (outside the rules-0 block, which keeps the engine's functions for comparison);
#   - plants: a result one bit off, a square root one place off, a source that calls Math.cos in a tick: each refused.
# And it measures, against a reference computed in decimal to 70 digits, the largest error of the sine, cosine and
# atan2 in units in the last place (a measurement: the rules need the same bits everywhere, not the nearest ones).
# Standard library only; it writes nothing.

import json
import math
import os
import re
import struct
import sys
from decimal import Decimal as Dec, getcontext
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HERE, "web", "sim.js")


# ------------------------------------------------------------------------------------------------ the algorithms
def hiw(x):
    return struct.unpack(">i", struct.pack(">d", x)[:4])[0]


def low(x):
    return struct.unpack(">I", struct.pack(">d", x)[4:])[0]


def dbl(hi, lo):
    return struct.unpack(">d", struct.pack(">II", hi & 0xffffffff, lo & 0xffffffff))[0]


S1, S2, S3 = dbl(0xBFC55555, 0x55555549), dbl(0x3F811111, 0x1110F8A6), dbl(0xBF2A01A0, 0x19C161D5)
S4, S5, S6 = dbl(0x3EC71DE3, 0x57B1FE7D), dbl(0xBE5AE5E6, 0x8A2B9CEB), dbl(0x3DE5D93A, 0x5ACFD57C)
C1, C2, C3 = dbl(0x3FA55555, 0x5555554C), dbl(0xBF56C16C, 0x16C15177), dbl(0x3EFA01A0, 0x19CB1590)
C4, C5, C6 = dbl(0xBE927E4F, 0x809C52AD), dbl(0x3E21EE9E, 0xBDB4B1C4), dbl(0xBDA8FAE9, 0xBE8838D4)


def k_sin(x, y, iy):
    ix = hiw(x) & 0x7fffffff
    if ix < 0x3e400000:
        return x
    z = x * x
    v = z * x
    r = S2 + z * (S3 + z * (S4 + z * (S5 + z * S6)))
    if iy == 0:
        return x + v * (S1 + z * r)
    return x - ((z * (0.5 * y - v * r) - y) - v * S1)


def k_cos(x, y):
    ix = hiw(x) & 0x7fffffff
    if ix < 0x3e400000:
        return 1.0
    z = x * x
    r = z * (C1 + z * (C2 + z * (C3 + z * (C4 + z * (C5 + z * C6)))))
    if ix < 0x3FD33333:
        return 1.0 - (0.5 * z - (z * r - x * y))
    qx = 0.28125 if ix > 0x3fe90000 else dbl(ix - 0x00200000, 0)
    hz = 0.5 * z - qx
    a = 1.0 - qx
    return a - (hz - (z * r - x * y))


INVPIO2 = dbl(0x3FE45F30, 0x6DC9C883)
PIO2_1, PIO2_1T = dbl(0x3FF921FB, 0x54400000), dbl(0x3DD0B461, 0x1A626331)
PIO2_2, PIO2_2T = dbl(0x3DD0B461, 0x1A600000), dbl(0x3BA3198A, 0x2E037073)
PIO2_3, PIO2_3T = dbl(0x3BA3198A, 0x2E000000), dbl(0x397B839A, 0x252049C1)


def rem_pio2(x):
    hx = hiw(x)
    ix = hx & 0x7fffffff
    if ix <= 0x3fe921fb:
        return 0, x, 0.0
    if ix < 0x4002d97c:
        if hx > 0:
            z = x - PIO2_1
            if ix != 0x3ff921fb:
                y0 = z - PIO2_1T
                return 1, y0, (z - y0) - PIO2_1T
            z -= PIO2_2
            y0 = z - PIO2_2T
            return 1, y0, (z - y0) - PIO2_2T
        z = x + PIO2_1
        if ix != 0x3ff921fb:
            y0 = z + PIO2_1T
            return -1, y0, (z - y0) + PIO2_1T
        z += PIO2_2
        y0 = z + PIO2_2T
        return -1, y0, (z - y0) + PIO2_2T
    if ix > 0x413921fb:
        raise ValueError("out of the rules' domain: %r" % x)
    t = abs(x)
    n = math.floor(t * INVPIO2 + 0.5)
    fn = float(n)
    r = t - fn * PIO2_1
    w = fn * PIO2_1T
    j = ix >> 20
    y0 = r - w
    i = j - ((hiw(y0) >> 20) & 0x7ff)
    if i > 16:
        u = r
        w = fn * PIO2_2
        r = u - w
        w = fn * PIO2_2T - ((u - r) - w)
        y0 = r - w
        i = j - ((hiw(y0) >> 20) & 0x7ff)
        if i > 49:
            u = r
            w = fn * PIO2_3
            r = u - w
            w = fn * PIO2_3T - ((u - r) - w)
            y0 = r - w
    y1 = (r - y0) - w
    if hx < 0:
        return -n, -y0, -y1
    return n, y0, y1


def xsin(x):
    ix = hiw(x) & 0x7fffffff
    if ix <= 0x3fe921fb:
        return k_sin(x, 0.0, 0)
    if ix >= 0x7ff00000:
        return x - x
    n, a, b = rem_pio2(x)
    q = n & 3
    if q == 0:
        return k_sin(a, b, 1)
    if q == 1:
        return k_cos(a, b)
    if q == 2:
        return -k_sin(a, b, 1)
    return -k_cos(a, b)


def xcos(x):
    ix = hiw(x) & 0x7fffffff
    if ix <= 0x3fe921fb:
        return k_cos(x, 0.0)
    if ix >= 0x7ff00000:
        return x - x
    n, a, b = rem_pio2(x)
    q = n & 3
    if q == 0:
        return k_cos(a, b)
    if q == 1:
        return -k_sin(a, b, 1)
    if q == 2:
        return -k_cos(a, b)
    return k_sin(a, b, 1)


ATANHI = [dbl(0x3FDDAC67, 0x0561BB4F), dbl(0x3FE921FB, 0x54442D18), dbl(0x3FEF730B, 0xD281F69B), dbl(0x3FF921FB, 0x54442D18)]
ATANLO = [dbl(0x3C7A2B7F, 0x222F65E2), dbl(0x3C81A626, 0x33145C07), dbl(0x3C700788, 0x7AF0CBBD), dbl(0x3C91A626, 0x33145C07)]
AT = [dbl(0x3FD55555, 0x5555550D), dbl(0xBFC99999, 0x9998EBC4), dbl(0x3FC24924, 0x920083FF), dbl(0xBFBC71C6, 0xFE231671),
      dbl(0x3FB745CD, 0xC54C206E), dbl(0xBFB3B0F2, 0xAF749A6D), dbl(0x3FB10D66, 0xA0D03D51), dbl(0xBFADDE2D, 0x52DEFD9A),
      dbl(0x3FA97B4B, 0x24760DEB), dbl(0xBFA2B444, 0x2C6A6C2F), dbl(0x3F90AD3A, 0xE322DA11)]


def xatan(x):
    hx = hiw(x)
    ix = hx & 0x7fffffff
    if ix >= 0x44100000:
        if ix > 0x7ff00000 or (ix == 0x7ff00000 and low(x) != 0):
            return x + x
        return ATANHI[3] + ATANLO[3] if hx > 0 else -ATANHI[3] - ATANLO[3]
    if ix < 0x3fdc0000:
        if ix < 0x3e200000:
            return x
        idx = -1
    else:
        x = abs(x)
        if ix < 0x3ff30000:
            if ix < 0x3fe60000:
                idx = 0
                x = (2.0 * x - 1.0) / (2.0 + x)
            else:
                idx = 1
                x = (x - 1.0) / (x + 1.0)
        elif ix < 0x40038000:
            idx = 2
            x = (x - 1.5) / (1.0 + 1.5 * x)
        else:
            idx = 3
            x = -1.0 / x
    z = x * x
    w = z * z
    s1 = z * (AT[0] + w * (AT[2] + w * (AT[4] + w * (AT[6] + w * (AT[8] + w * AT[10])))))
    s2 = w * (AT[1] + w * (AT[3] + w * (AT[5] + w * (AT[7] + w * AT[9]))))
    if idx < 0:
        return x - x * (s1 + s2)
    r = ATANHI[idx] - ((x * (s1 + s2) - ATANLO[idx]) - x)
    return -r if hx < 0 else r


TINY = dbl(0x01a56e1f, 0xc2f8f359)
PI_O_4, PI_O_2, PI, PI_LO = dbl(0x3FE921FB, 0x54442D18), dbl(0x3FF921FB, 0x54442D18), dbl(0x400921FB, 0x54442D18), dbl(0x3CA1A626, 0x33145C07)


def xatan2(y, x):
    if x != x or y != y:
        return x + y
    hx, lx, hy, ly = hiw(x), low(x), hiw(y), low(y)
    ix, iy = hx & 0x7fffffff, hy & 0x7fffffff
    if ((hx - 0x3ff00000) | lx) == 0:
        return xatan(y)
    m = ((hy >> 31) & 1) | ((hx >> 30) & 2)
    if (iy | ly) == 0:
        if m < 2:
            return y
        return PI + TINY if m == 2 else -PI - TINY
    if (ix | lx) == 0:
        return -PI_O_2 - TINY if hy < 0 else PI_O_2 + TINY
    if ix == 0x7ff00000:
        if iy == 0x7ff00000:
            return [PI_O_4 + TINY, -PI_O_4 - TINY, 3.0 * PI_O_4 + TINY, -3.0 * PI_O_4 - TINY][m]
        return [0.0, -0.0, PI + TINY, -PI - TINY][m]
    if iy == 0x7ff00000:
        return -PI_O_2 - TINY if hy < 0 else PI_O_2 + TINY
    k = (iy - ix) >> 20
    if k > 60:
        z = PI_O_2 + 0.5 * PI_LO
        m &= 1
    elif hx < 0 and k < -60:
        z = 0.0
    else:
        z = xatan(abs(y / x))
    if m == 0:
        return z
    if m == 1:
        return -z
    if m == 2:
        return PI - (z - PI_LO)
    return (z - PI_LO) - PI


B52, B53 = 1 << 52, 1 << 53


def parts(x):
    b = struct.unpack(">Q", struct.pack(">d", x))[0] & 0x7fffffffffffffff
    e, f = b >> 52, b & (B52 - 1)
    return (f, -1074) if e == 0 else (f | B52, e - 1075)


def nearest(q, ex, sticky):
    top = ex + q.bit_length() - 1
    u = top - 52 if top >= -1022 else -1074
    sh = u - ex
    assert sh >= 2
    rest, half = q & ((1 << sh) - 1), 1 << (sh - 1)
    r = q >> sh
    if rest > half or (rest == half and (sticky or (r & 1) == 1)):
        r += 1
    if r == B53:
        r, u = B52, u + 1
    if u + 1075 > 2046:
        return math.inf
    bits = r if r < B52 else ((u + 1075) << 52) | (r - B52)
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def root_of(S, e):
    k = max(0, 112 - S.bit_length())
    if k & 1:
        k += 1
    N = S << k
    q = math.isqrt(N)
    return nearest(q, e - k // 2, q * q != N)


def xsqrt(x):
    if x != x or x < 0:
        return math.nan
    if x == 0 or x == math.inf:
        return x
    m, e = parts(x)
    return root_of(m << 1, (e - 1) // 2) if e & 1 else root_of(m, e // 2)


def xhypot(*args):
    if any(a in (math.inf, -math.inf) for a in args):
        return math.inf
    if any(a != a for a in args):
        return math.nan
    ps = [parts(a) for a in args if a != 0]
    if not ps:
        return 0.0
    lo = min(e for _m, e in ps)
    S = sum((m * m) << (2 * (e - lo)) for m, e in ps)
    return root_of(S, lo)


# ------------------------------------------------------------------------------------------------ the argument sets
PIO2D, TWOPI = dbl(0x3FF921FB, 0x54442D18), dbl(0x401921FB, 0x54442D18)
EDGES = [dbl(0x3E400000, 0), dbl(0x3FD33333, 0x33333333), 0.78125, dbl(0x3FE921FB, 0x54442D18), dbl(0x4002D97C, 0x7F3321D2)]
SPECIAL = [0.0, -0.0, 1.0, -1.0, math.inf, -math.inf, 0.5, -0.5, 2.4375, 1.1875, 0.4375, 0.6875, 0.75,
           dbl(0x01a56e1f, 0xc2f8f359), -dbl(0x7e37e43c, 0x8800759c)]
SEEDS = {"sin": 1, "cos": 2, "atan2": 3, "hypot": 4, "sqrt": 5}
FUNCS = {"sin": xsin, "cos": xcos, "atan2": xatan2, "hypot": xhypot, "sqrt": xsqrt}


def pow2(e):
    if e >= -1022:
        return dbl((e + 1023) << 20, 0)
    b = e + 1074
    return dbl(1 << (b - 32), 0) if b >= 32 else dbl(0, 1 << b)


def rule_args(fn, n):
    """sim.js's ruleArgs, step for step."""
    st = [SEEDS[fn]]

    def nxt():
        st[0] = (st[0] * 1664525 + 1013904223) & 0xffffffff
        return st[0]

    u = lambda: nxt() / 4294967296.0
    sg = lambda: u() * 2.0 - 1.0
    out = []
    for i in range(n):
        if fn in ("sin", "cos"):
            k = i % 7
            if k == 0:
                out.append((sg() * 8,))
            elif k == 1:
                out.append((sg() * 1024,))
            elif k == 2:
                m = nxt() % 2001 - 1000
                out.append((m * PIO2D + (u() - 0.5) * pow2(-20 - nxt() % 30),))
            elif k == 3:
                out.append((sg() * pow2(-26 - nxt() % 40),))
            elif k == 4:
                out.append((sg() * 800000,))
            elif k == 5:
                out.append((u() * TWOPI + (-0.25 if nxt() % 3 == 0 else 0),))
            else:
                e = EDGES[nxt() % len(EDGES)]
                out.append(((nxt() % 9 - 4) * PIO2D + e * (1 + (nxt() % 2001 - 1000) * pow2(-24)),))
        elif fn == "atan2":
            k = i % 4
            if k == 0:
                out.append((sg() * 10, sg() * 10))
            elif k == 1:
                out.append((sg() * pow2(nxt() % 200 - 100), sg() * pow2(nxt() % 200 - 100)))
            elif k == 2:
                out.append((SPECIAL[nxt() % len(SPECIAL)], SPECIAL[nxt() % len(SPECIAL)]))
            else:
                out.append((sg() * 60, -(sg() * 60)))
        elif fn == "hypot":
            k = i % 4
            if k == 0:
                out.append((sg() * 60, sg() * 60))
            elif k == 1:
                t = u() * TWOPI
                out.append((xsin(t), xcos(t)))
            elif k == 2:
                out.append((sg() * pow2(nxt() % 2098 - 1074), sg() * pow2(nxt() % 2098 - 1074)))
            else:
                out.append((sg() * 60, sg() * 3, sg() * 60))
        else:
            k = i % 3
            if k == 0:
                out.append((u() * pow2(nxt() % 2098 - 1074),))
            elif k == 1:
                a = sg() * 1000
                out.append((a * a,))
            else:
                out.append((u() * 4,))
    return out


def constants_digest():
    h = 0x811c9dc5
    for v in [S1, S2, S3, S4, S5, S6, C1, C2, C3, C4, C5, C6, INVPIO2, PIO2_1, PIO2_1T, PIO2_2, PIO2_2T, PIO2_3, PIO2_3T] + \
            ATANHI + ATANLO + AT + [TINY, PI_O_4, PI_O_2, PI, PI_LO]:
        for byte in struct.pack(">d", v):
            h = ((h ^ byte) * 0x01000193) & 0xffffffff
    return "%08x" % h


def bits(v):
    return "nan" if v != v else struct.pack(">d", v).hex()


def digest(fn, f, n):
    h = 0x811c9dc5
    for a in rule_args(fn, n):
        for byte in struct.pack(">d", f(*a)):
            h = ((h ^ byte) * 0x01000193) & 0xffffffff
    return "%08x" % h


SPECIALS = [  # the same as sim.js's RULE_SPECIALS
    ("sin", (0.0,), "0000000000000000"), ("sin", (-0.0,), "8000000000000000"), ("sin", (math.inf,), "nan"), ("sin", (math.nan,), "nan"),
    ("cos", (0.0,), "3ff0000000000000"), ("cos", (-math.inf,), "nan"),
    ("atan2", (0.0, -1.0), "400921fb54442d18"), ("atan2", (-0.0, -1.0), "c00921fb54442d18"), ("atan2", (0.0, 0.0), "0000000000000000"),
    ("atan2", (-0.0, 0.0), "8000000000000000"), ("atan2", (0.0, -0.0), "400921fb54442d18"), ("atan2", (1.0, 0.0), "3ff921fb54442d18"),
    ("atan2", (math.inf, math.inf), "3fe921fb54442d18"), ("atan2", (-math.inf, -math.inf), "c002d97c7f3321d2"),
    ("atan2", (1.0, math.inf), "0000000000000000"), ("atan2", (-1.0, -math.inf), "c00921fb54442d18"), ("atan2", (1e300, -1e-300), "3ff921fb54442d18"),
    ("hypot", (math.inf, math.nan), "7ff0000000000000"), ("hypot", (math.nan, 1.0), "nan"), ("hypot", (-0.0, -0.0), "0000000000000000"), ("hypot", (), "0000000000000000"),
    ("hypot", (3.0, 4.0), "4014000000000000"), ("hypot", (dbl(0x7fefffff, 0xffffffff), dbl(0x7fefffff, 0xffffffff)), "7ff0000000000000"),
    ("hypot", (dbl(0, 1), 0.0), "0000000000000001"), ("hypot", (dbl(0, 3), dbl(0, 4)), "0000000000000005"),
    ("sqrt", (-0.0,), "8000000000000000"), ("sqrt", (-1.0,), "nan"), ("sqrt", (math.inf,), "7ff0000000000000"), ("sqrt", (2.0,), "3ff6a09e667f3bcd"),
    ("sqrt", (dbl(0, 1),), "1e60000000000000"), ("sqrt", (dbl(0x7fefffff, 0xffffffff),), "5fefffffffffffff"),
]


# ------------------------------------------------------------------------------------------------ exactness and accuracy
def correctly_rounded_root(r, S):
    """Is r the double nearest to the square root of the fraction S >= 0?"""
    if r == 0:
        return S == 0
    if math.isinf(r):
        big = Fr(*math.nextafter(math.inf, 0).as_integer_ratio())
        return S >= (big + Fr(2) ** 970) ** 2
    lo, hi, R = (Fr(*v.as_integer_ratio()) for v in (math.nextafter(r, 0), math.nextafter(r, math.inf), r))
    return ((lo + R) / 2) ** 2 <= S <= ((R + hi) / 2) ** 2


getcontext().prec = 70


def _atan_small(t):
    s, term, k, t2 = Dec(0), t, 0, t * t
    while True:
        add = term / (2 * k + 1)
        if k > 0 and abs(add) <= abs(s) * Dec(10) ** -66:
            return s
        s += add if k % 2 == 0 else -add
        term *= t2
        k += 1


def d_atan(t):
    n = 0
    while abs(t) > Dec("0.1"):
        t = t / (1 + (1 + t * t).sqrt())
        n += 1
    return _atan_small(t) * (2 ** n)


D_PI = 4 * (4 * d_atan(Dec(1) / 5) - d_atan(Dec(1) / 239))


def d_sin(x):
    x = Dec(x)
    x -= (x / (2 * D_PI)).to_integral_value() * 2 * D_PI
    s, term, n = Dec(0), x, 1
    while term != 0 and (s == 0 or abs(term) > abs(s) * Dec(10) ** -66):
        s += term
        term = -term * x * x / ((n + 1) * (n + 2))
        n += 2
    return s


def d_cos(x):
    return d_sin(Dec(x) + D_PI / 2)


def d_atan2(y, x):
    y, x = Dec(y), Dec(x)
    if x > 0:
        return d_atan(y / x) if abs(y) <= abs(x) else (D_PI / 2 if y > 0 else -D_PI / 2) - d_atan(x / y)
    if x < 0:
        if abs(y) <= abs(x):
            b = d_atan(y / x)
            return b + D_PI if y >= 0 else b - D_PI
        return (D_PI / 2 if y > 0 else -D_PI / 2) - d_atan(x / y)
    return D_PI / 2 if y > 0 else -D_PI / 2


def ulp_error(r, true):
    a = abs(true)
    if a == 0:
        return 0.0 if r == 0 else math.inf
    e = math.frexp(float(a))[1] - 1
    while Dec(2) ** e > a:
        e -= 1
    while Dec(2) ** (e + 1) <= a:
        e += 1
    return float(abs(Dec(r) - true) / (Dec(2) ** max(e - 52, -1074)))


# ------------------------------------------------------------------------------------------------ sim.js
def approx_named(src):
    """sim.js's approxNamed: the approximated Math functions the source names, up to its self-test, comments out, the
    rules-0 block set aside."""
    end = src.find("function selftest(map, ctx)")
    t = src[:end if end > 0 else len(src)]
    a, b = t.find("// rules 0: the engine's own functions"), t.find("// end of rules 0")
    if 0 <= a < b:
        t = t[:a] + t[b:]
    t = re.sub(r"/\*[\s\S]*?\*/", " ", t)
    t = re.sub(r"//[^\n]*", " ", t)
    approx = {"sin", "cos", "tan", "asin", "acos", "atan", "atan2", "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
              "exp", "expm1", "log", "log1p", "log2", "log10", "pow", "cbrt", "hypot", "sqrt"}
    out = []
    for m in re.finditer(r"\bMath\s*\.\s*([A-Za-z0-9_]+)|\*\*", t):
        if m.group(1) is None or m.group(1) in approx:
            out.append("Math." + m.group(1) if m.group(1) else "**")
    return out


def main(argv):
    src = open(SIM, encoding="utf-8").read().replace("\r\n", "\n")
    rows = []

    def row(name, ok, detail):
        rows.append(ok)
        print("%s %s — %s" % ("PASS" if ok else "FAIL", name, detail))

    m = re.search(r"const RULE_N = (\d+);", src)
    d = re.search(r'const RULE_DIGESTS = \{ sin: "([0-9a-f]{8})", cos: "([0-9a-f]{8})", atan2: "([0-9a-f]{8})", hypot: "([0-9a-f]{8})", sqrt: "([0-9a-f]{8})" \};', src)
    if not m or not d:
        row("sim.js's digests", False, "RULE_N or RULE_DIGESTS not found in sim.js")
        return 1
    n = int(m.group(1))
    held = dict(zip(("sin", "cos", "atan2", "hypot", "sqrt"), d.groups()))
    c = re.search(r'const RULE_CONSTANTS = "([0-9a-f]{8})";', src)
    row("the constants", bool(c) and c.group(1) == constants_digest(), "the algorithms' 43 constants, each written in sim.js as its bits: digest %s%s" % (
        constants_digest(), "" if c and c.group(1) == constants_digest() else ", sim.js holds %s" % (c.group(1) if c else "none")))
    mine = {f: digest(f, FUNCS[f], n) for f in FUNCS}
    row("the digests", mine == held, "each function over its %d arguments: %s%s" % (n, ", ".join("%s %s" % kv for kv in mine.items()),
        "" if mine == held else "; sim.js holds " + ", ".join("%s %s" % kv for kv in held.items())))
    bad = [(f, a, bits(FUNCS[f](*a)), want) for f, a, want in SPECIALS if bits(FUNCS[f](*a)) != want]
    row("the special values", not bad, "%d, as IEEE 754 and fdlibm define them%s" % (len(SPECIALS), "; DIFFERENT: %r" % bad[:3] if bad else ""))
    try:
        xsin(1700000.0)
        refused = False
    except ValueError:
        refused = True
    row("the sine's domain", refused, "an angle past 2^20 pi/2 refused, as sim.js's RangeError")
    roots = [(a, xsqrt(*a)) for a in rule_args("sqrt", n)]
    hyps = [(a, xhypot(*a)) for a in rule_args("hypot", n)]
    wrong = sum(1 for a, r in roots if not correctly_rounded_root(r, Fr(*a[0].as_integer_ratio()))) +         sum(1 for a, r in hyps if not correctly_rounded_root(r, sum(Fr(*v.as_integer_ratio()) ** 2 for v in a)))
    row("correctly rounded", wrong == 0, "the square root over %d arguments and hypot over %d, each result checked exactly against the midpoints to its neighbours: %d not the nearest" % (n, n, wrong))
    named = approx_named(src)
    row("the source", not named, "sim.js up to its self-test, comments out, the rules-0 block set aside, names %s" % (", ".join(named) if named else "no approximated Math function"))
    # plants
    one = rule_args("sin", 101)[100][0]
    flip = lambda v: struct.unpack(">d", (int.from_bytes(struct.pack(">d", v), "big") ^ 1).to_bytes(8, "big"))[0]
    p1 = digest("sin", lambda x: flip(xsin(x)) if x == one else xsin(x), n) != held["sin"]
    a0 = roots[1][0][0]
    p2 = not correctly_rounded_root(math.nextafter(xsqrt(a0), math.inf), Fr(*a0.as_integer_ratio()))
    p3 = bool(approx_named(src.replace("function step(world, s, inp) {", "function step(world, s, inp) { Math.cos(0);")))
    row("plants", p1 and p2 and p3, "a sine one bit off at one argument %s; a square root one place up %s; a tick that calls Math.cos %s" % (
        "refused" if p1 else "NOT refused", "refused" if p2 else "NOT refused", "found" if p3 else "NOT found"))
    # measured
    k = min(n, int(argv[argv.index("--accuracy") + 1]) if "--accuracy" in argv else 1000)
    worst = {}
    for f, ref in (("sin", d_sin), ("cos", d_cos)):
        worst[f] = max(ulp_error(FUNCS[f](*a), ref(a[0])) for a in rule_args(f, k))
    worst["atan2"] = max(ulp_error(xatan2(*a), d_atan2(*a)) for a in rule_args("atan2", k) if all(math.isfinite(v) for v in a) and a[0] != 0)
    print("MEASURED accuracy — the largest error over the first %d arguments of each set, against 70 decimal digits, in units in the last place: %s" % (
        k, ", ".join("%s %.3f" % kv for kv in worst.items())))
    print("RULES REFERENCE %s" % ("PASSED" if all(rows) else "FAILED"))
    return 0 if all(rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
