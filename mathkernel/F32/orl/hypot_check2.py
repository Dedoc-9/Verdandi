# Sampled faithfulness check of hypot32, version 2 (2026-11-14, review findings F1 and F5). A new file beside
# hypot_check.py, which stays as it is. What was wrong with version 1:
#   F1  it sampled magnitudes below 2^126 only, so it never saw a pair whose hypotenuse leaves binary32;
#   F5  its plant touched almost only pairs with a zero input, and passed if at least one touched pair was flagged.
# Here: seeded; more than a million binary32 pairs in seven regimes and the three known pairs; results from the native
# program gen/sweep.exe in corpus mode for hypot32 (f_hypot32, the generated function); an exact reference.
#   regimes  whole range        both inputs anywhere in the finite binary32 range (uniform in bit pattern)
#            top two binades    both in [2^126, 2^128)
#            nearby exponents   exponents within 2 of each other, any exponent up to the top
#            subnormal and tiny both below 2^-124
#            one zero           one input +0 or -0, the other anywhere in the finite range
#            domain edge        x in [2^126, 2^128), y chosen so that the hypotenuse is within a few binary32 steps of FLT_MAX
#            top and small      one input in the top binade, the other anywhere below it
#            known              (FLT_MAX, FLT_MAX), (2^127, 0x1.bb67aep127), (FLT_MAX, 2^116), at indices 0, 1024, 2048
# Reference: every finite binary32 number is a whole multiple of 2^-149, so with X = x * 2^149, Y = y * 2^149 (integers)
# the exact square of the hypotenuse is the integer T = X^2 + Y^2 (in units of 2^-298), and every comparison below is
# between integers: exact, no rounding anywhere. Every 997th pair is checked a second time with Fractions built from
# the floats themselves, which shares nothing with the integer decoding.
#   in the domain of the theorem HYPOT32_FINITE (exact hypotenuse <= FMAX32, i.e. T <= FMAX^2):
#       the result must be a finite binary32 number r >= 0 with pred(r)^2 < T < succ(r)^2 (succ(FMAX32) = 2^128;
#       r = 0 only for T = 0): one of the two binary32 numbers bracketing the exact result, or the result itself.
#   outside it: the result is not judged. Counted: such pairs, and how many results are finite binary32 numbers.
#       What the function returned for the three known pairs is printed.
# Plant: every pair whose index is a multiple of 1024 has its result moved two binary32 steps up before the check
# (a result that is not a finite binary32 number is left alone). Caught only if EVERY touched pair inside the domain
# is flagged; and the touched pairs must come from every regime, with at least one inside the domain in every regime
# that has pairs inside it (the count per regime is printed).
#   python -B hypot_check2.py      prints HYPOT32 SAMPLE 2 HELD or FAILED, exit status 0 or 1. Writes nothing.
# What it does not show: anything about pairs not sampled (a sample is not a proof); infinities and NaN; that the Orlog
# law or the Coq graph agree with the native program (emit.py corpus, evidence/graph_agree.py).
import os, random, struct, subprocess, sys
from fractions import Fraction as F
HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, 'gen', 'sweep.exe')
SEED = 2026111402
FMAX_U = 0x7f7fffff
def f32(u): return struct.unpack('<f', struct.pack('<I', u))[0]
def u32(x): return struct.unpack('<I', struct.pack('<f', x))[0]
def bits(d): return struct.unpack('<Q', struct.pack('<d', d))[0]
def dbl(b): return struct.unpack('<d', struct.pack('<Q', b))[0]
def scaled(u):
    """the magnitude of the finite binary32 number with pattern u, as an integer multiple of 2^-149"""
    e = (u >> 23) & 0xff; m = u & 0x7fffff
    assert e != 0xff
    return m if e == 0 else (m | 0x800000) << (e - 1)
FMAXI = scaled(FMAX_U); TOPI = 1 << 277                       # FMAX32 and 2^128, in units of 2^-149
assert F(FMAXI, 2 ** 149) == F(f32(FMAX_U)) == F(2) ** 128 - F(2) ** 104 and F(TOPI, 2 ** 149) == F(2) ** 128
def as32(r):
    """the pattern of r if r (a float) is a finite binary32 number, otherwise None"""
    if r != r or r in (float('inf'), float('-inf')): return None
    try: back = struct.unpack('<f', struct.pack('<f', r))[0]
    except OverflowError: return None
    return u32(r) if back == r else None
def faithful(T, r):
    """T = X^2 + Y^2; r the result as a float. Exact."""
    u = as32(r)
    if u is None or u >> 31: return False                      # not a finite binary32 number, or negative (or -0)
    if u == 0: return T == 0
    lo = scaled(u - 1); hi = TOPI if u == FMAX_U else scaled(u + 1)
    return lo * lo < T < hi * hi
def faithful_fraction(x, y, r):
    """the same verdict from the floats themselves, with Fractions (the cross-check)"""
    u = as32(r)
    if u is None or r < 0 or (r == 0 and bits(r) >> 63): return False
    t = F(x) ** 2 + F(y) ** 2
    if r == 0: return t == 0
    hi = F(2) ** 128 if u == FMAX_U else F(f32(u + 1))
    return F(f32(u - 1)) ** 2 < t < hi ** 2
def two_up(r):
    u = as32(r)
    if u is None: return r
    return f32(u + 2)                                          # past FLT_MAX this is infinity or a NaN: refused by the check

def sample():
    rnd = random.Random(SEED); regs = []
    def sgn(u): return u | (rnd.getrandbits(1) << 31)
    def anyu(): return rnd.randrange(1, FMAX_U + 1)
    def top(): return rnd.randrange(0x7e800000, FMAX_U + 1)    # [2^126, 2^128)
    regs.append(('whole range', [(sgn(anyu()), sgn(anyu())) for _ in range(200000)]))
    regs.append(('top two binades', [(sgn(top()), sgn(top())) for _ in range(200000)]))
    L = []
    for _ in range(200000):
        a = anyu(); e = min(max((a >> 23) + rnd.randint(-2, 2), 0), 0xfe)
        L.append((sgn(a), sgn((e << 23) | rnd.getrandbits(23))))
    regs.append(('nearby exponents', L))
    regs.append(('subnormal and tiny', [(sgn(rnd.randrange(0, 0x01800000)), sgn(rnd.randrange(0, 0x01800000))) for _ in range(150000)]))
    L = []
    for _ in range(150000):
        z = rnd.choice((0, 0x80000000)); a = sgn(anyu())
        L.append((a, z) if rnd.getrandbits(1) else (z, a))
    regs.append(('one zero', L))
    L = []
    while len(L) < 150000:                                     # y near sqrt(FMAX^2 - x^2), then moved by up to 3 binary32 steps
        a = top(); x = f32(a); t = F(f32(FMAX_U)) ** 2 - F(x) ** 2
        y0 = float(t) ** 0.5
        b = u32(y0) + rnd.randint(-3, 3)
        if not 0 < b <= FMAX_U: continue
        p = (sgn(a), sgn(b)); L.append(p if rnd.getrandbits(1) else (p[1], p[0]))
    regs.append(('domain edge', L))
    L = []
    for _ in range(100000):
        p = (sgn(rnd.randrange(0x7f000000, FMAX_U + 1)), sgn(rnd.randrange(0, 0x7f000000))); L.append(p if rnd.getrandbits(1) else (p[1], p[0]))
    regs.append(('top and small', L))
    pairs = [p for _, L in regs for p in L]; reg = [i for i, (_, L) in enumerate(regs) for _ in L]
    known = [('(FLT_MAX, FLT_MAX)', (FMAX_U, FMAX_U)), ('(2^127, 0x1.bb67aep127)', (u32(2.0 ** 127), u32(float.fromhex('0x1.bb67aep127')))),
             ('(FLT_MAX, 2^116)', (FMAX_U, u32(2.0 ** 116)))]
    names = [n for n, _ in regs] + ['known']
    for k, (_, p) in enumerate(known):                         # at indices 0, 1024, 2048: the plant touches all three
        pairs.insert(k * 1024, p); reg.insert(k * 1024, len(names) - 1)
    return names, pairs, reg, known

def main():
    names, pairs, reg, known = sample(); R = len(names)
    inp = '\n'.join('%x %x' % (bits(f32(a)), bits(f32(b))) for a, b in pairs) + '\n'
    q = subprocess.run([EXE, 'corpus', 'hypot32'], input=inp, capture_output=True, text=True)
    out = q.stdout.split()
    if q.returncode != 0 or len(out) != len(pairs):
        print('HYPOT32 SAMPLE 2 FAILED (gen/sweep.exe returned %d lines for %d pairs, exit %d)' % (len(out), len(pairs), q.returncode)); return 1
    Z = lambda: [0] * R
    n, indom, bad, outdom, out_finite32, out_notb32, touched, touched_in, flagged, top_in = Z(), Z(), Z(), Z(), Z(), Z(), Z(), Z(), Z(), Z()
    first = None; missed = None; cross = cross_bad = 0; biggest = 0
    for i, ((a, b), o) in enumerate(zip(pairs, out)):
        g = reg[i]; r = dbl(int(o, 16)); X, Y = scaled(a & 0x7fffffff), scaled(b & 0x7fffffff); T = X * X + Y * Y
        n[g] += 1; inside = T <= FMAXI * FMAXI; biggest = max(biggest, X, Y)
        if inside:
            indom[g] += 1; ok = faithful(T, r)
            if a & 0x7fffffff >= 0x7e800000 or b & 0x7fffffff >= 0x7e800000: top_in[g] += 1
            if not ok:
                bad[g] += 1; first = first or (names[g], f32(a).hex(), f32(b).hex(), o)
            if i % 997 == 0:
                cross += 1; cross_bad += faithful_fraction(f32(a), f32(b), r) != ok
        else:
            outdom[g] += 1
            if as32(r) is not None: out_finite32[g] += 1
            else: out_notb32[g] += 1
        if i % 1024 == 0:                                      # the plant
            touched[g] += 1
            if inside:
                touched_in[g] += 1
                if not faithful(T, two_up(r)): flagged[g] += 1
                elif missed is None: missed = (names[g], f32(a).hex(), f32(b).hex(), o)
    print('hypot32 sampled check 2: %d pairs, seed %d, program gen/sweep.exe; largest input magnitude sampled %s' % (
        len(pairs), SEED, (biggest / 2.0 ** 149).hex()))
    print('%-19s %8s %9s %9s %12s | %8s %14s %14s | %8s %9s %8s' % ('regime', 'pairs', 'in domain', '(an input', 'not faithful', 'outside', 'result finite', 'result not a',
                                                                   'plant', 'touched', 'flagged'))
    print('%-19s %8s %9s %9s %12s | %8s %14s %14s | %8s %9s %8s' % ('', '', '', '>= 2^126)', '', 'domain', 'binary32', 'binary32 number', 'touched', 'in domain', ''))
    for g in range(R):
        print('%-19s %8d %9d %9d %12d | %8d %14d %14d | %8d %9d %8d' % (names[g], n[g], indom[g], top_in[g], bad[g], outdom[g], out_finite32[g], out_notb32[g],
                                                                       touched[g], touched_in[g], flagged[g]))
    print('%-19s %8d %9d %9d %12d | %8d %14d %14d | %8d %9d %8d' % ('all', sum(n), sum(indom), sum(top_in), sum(bad), sum(outdom), sum(out_finite32), sum(out_notb32),
                                                                   sum(touched), sum(touched_in), sum(flagged)))
    print('the three known pairs (all outside the domain: not judged):')
    known_out = True
    for k, (name, (a, b)) in enumerate(known):
        i = k * 1024; r = dbl(int(out[i], 16)); T = scaled(a) ** 2 + scaled(b) ** 2; known_out &= pairs[i] == (a, b) and T > FMAXI * FMAXI
        rel = 'above 2^128' if T > TOPI * TOPI else 'exactly 2^128' if T == TOPI * TOPI else 'between FMAX32 and 2^128'
        print('  %-24s x=%s y=%s -> %s (bits %s); a finite binary32 number: %s; exact hypotenuse %s, %s 2^128 - 2^103' % (
            name, f32(a).hex(), f32(b).hex(), 'nan' if r != r else r.hex(), out[i], 'yes' if as32(r) is not None else 'no', rel,
            'at or above' if 4 * T >= (2 * TOPI - (1 << 253)) ** 2 else 'below'))
    if first: print('first pair in the domain that is not faithful: regime %s, x=%s y=%s -> bits %s' % first)
    if missed: print('first touched pair the plant was not flagged on: regime %s, x=%s y=%s -> bits %s' % missed)
    req = [('at least 1,000,000 pairs', len(pairs) >= 1000000),
           ('inputs at or above 2^126 were sampled inside the domain (what version 1 left out)', sum(top_in) > 0 and biggest == FMAXI),
           ('every pair in the domain: the result is a finite binary32 number and faithful', sum(bad) == 0),
           ('the Fraction cross-check agrees with the integer verdict on each of its %d pairs' % cross, cross > 1000 and cross_bad == 0),
           ('the three known pairs sit at indices 0, 1024, 2048 and are outside the domain', known_out),
           ('plant: touched pairs come from every regime', all(t > 0 for t in touched)),
           ('plant: in every regime with pairs in the domain, touched pairs in the domain', all(touched_in[g] > 0 for g in range(R) if indom[g] > 0)),
           ('plant: every touched pair in the domain is flagged (%d of %d)' % (sum(flagged), sum(touched_in)), sum(touched_in) > 0 and flagged == touched_in)]
    ok = True
    for text, good in req:
        print('  %-4s %s' % ('ok' if good else 'FAIL', text)); ok &= bool(good)
    print('HYPOT32 SAMPLE 2 %s: %d pairs; in the domain of HYPOT32_FINITE %d, not faithful %d; outside it %d (not judged), of which the result is a finite '
          'binary32 number on %d and not on %d; plant (two steps up) flagged on %d of the %d in-domain pairs it touched, %d touched in all, from %d of %d regimes' % (
              'HELD' if ok else 'FAILED', len(pairs), sum(indom), sum(bad), sum(outdom), sum(out_finite32), sum(out_notb32), sum(flagged), sum(touched_in),
              sum(touched), sum(1 for t in touched if t), R))
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
