# Sampled faithfulness check of hypot32 (2026-11-14). Two arguments cannot be swept exhaustively, so: one million
# binary32 pairs, seeded, in four regimes, evaluated by the native program (gen/sweep.exe, the same binary whose corpus
# output equals Orlog's backends bit for bit), each result checked exactly with rationals:
#   r is a binary32 value and pred(r)^2 < x^2 + y^2 < succ(r)^2   (r = 0 only for x = y = 0).
# A plant (results nudged up one binary32 step) must be flagged. Writes nothing but its report.
import os, random, struct, subprocess, sys
from fractions import Fraction as F
HERE = os.path.dirname(os.path.abspath(__file__))
def f32(u): return struct.unpack('<f', struct.pack('<I', u))[0]
def u32(x): return struct.unpack('<I', struct.pack('<f', x))[0]
def bits(d): return struct.unpack('<Q', struct.pack('<d', d))[0]
def dbl(b): return struct.unpack('<d', struct.pack('<Q', b))[0]
rnd = random.Random(20261114); N = 250000; pairs = []
def pos(lo=1, hi=0x7e800000): return rnd.randrange(lo, hi)           # positive, below 2^126
def sgn(u): return u | (rnd.getrandbits(1) << 31)
for _ in range(N): pairs.append((sgn(pos()), sgn(pos())))                                   # independent magnitudes
for _ in range(N):                                                                          # nearby exponents
    a = pos(); e = (a >> 23) + rnd.randint(-2, 2); e = min(max(e, 0), 0xfc)
    pairs.append((sgn(a), sgn((e << 23) | rnd.getrandbits(23))))
for _ in range(N): pairs.append((sgn(rnd.randrange(0, 0x01800000)), sgn(rnd.randrange(0, 0x01800000))))   # subnormal and tiny
for _ in range(N): pairs.append((sgn(pos()), rnd.choice((0, 0x80000000))) if rnd.getrandbits(1) else (0, sgn(pos())))  # one zero
inp = '\n'.join('%x %x' % (bits(f32(a)), bits(f32(b))) for a, b in pairs) + '\n'
out = subprocess.run([os.path.join(HERE, 'gen', 'sweep.exe'), 'corpus', 'hypot32'], input=inp, capture_output=True, text=True).stdout.split()
assert len(out) == len(pairs), (len(out), len(pairs))
def faithful(x, y, r):
    if struct.unpack('<f', struct.pack('<f', r))[0] != r or r < 0: return False
    t = F(x) ** 2 + F(y) ** 2; u = u32(r)
    if u == 0: return t == 0
    return F(f32(u - 1)) ** 2 < t < F(f32(u + 1)) ** 2
bad = planted = 0; first = None
for (a, b), o in zip(pairs, out):
    x, y, r = f32(a), f32(b), dbl(int(o, 16))
    if not faithful(x, y, r):
        bad += 1; first = first or (hex(a), hex(b), o)
    if (len(pairs) % 1 == 0) and (a & 0xfff) == 0:                     # the plant, on about 1 pair in 4096
        if faithful(x, y, f32(u32(r) + 1) if r > 0 else r): pass
        else: planted += 1
print('hypot32 sampled check: %d pairs; not faithful: %d%s; plant (one step up) flagged on %d of the pairs it touched' % (
    len(pairs), bad, '' if not bad else ' first %s' % (first,), planted))
print('HYPOT32 SAMPLE %s' % ('HELD' if bad == 0 and planted > 0 else 'FAILED')); sys.exit(0 if bad == 0 and planted > 0 else 1)
