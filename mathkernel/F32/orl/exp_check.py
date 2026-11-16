# Exact sampled check of exp32 (2026-11-14), independent of the C runtime's exp that the exhaustive sweep leans on:
# one million binary32 inputs, seeded, in four regimes, evaluated by the native program (gen/sweep2.exe, the binary whose
# corpus output equals Orlog's backends bit for bit), each result checked against Python's decimal exp at 60 digits
# (libmpdec, correctly rounded):   r is a binary32 value, r >= 0, and pred(r) < exp(x) < succ(r).
# A margin of 1e-50 (relative) around each neighbour counts as ambiguous, not as a pass. The plant moves every 4096th
# result two binary32 steps up and must be flagged every time. Writes nothing but its report.
import decimal, os, random, struct, subprocess, sys
from decimal import Decimal as D
HERE = os.path.dirname(os.path.abspath(__file__))
decimal.getcontext().prec = 60
XMAX_U = 0x42B17217
def f32(u): return struct.unpack('<f', struct.pack('<I', u))[0]
def u32(x): return struct.unpack('<I', struct.pack('<f', x))[0]
def r32(x): return struct.unpack('<f', struct.pack('<f', x))[0]
def bits(d): return struct.unpack('<Q', struct.pack('<d', d))[0]
def dbl(b): return struct.unpack('<d', struct.pack('<Q', b))[0]
rnd = random.Random(20261114); N = 250000; xs = []
xs += [r32(rnd.uniform(-104.5, 88.72)) for _ in range(N)]                       # uniform in value over the live range
xs += [f32(rnd.randrange(0, XMAX_U + 1)) for _ in range(N)]                     # uniform in bits, positive
xs += [-f32(rnd.randrange(0, 0x7f800000)) for _ in range(N)]                    # uniform in bits, negative, every magnitude
xs += [r32(rnd.uniform(-104.2, -102.9)) for _ in range(N // 2)]                 # the underflow band
xs += [r32(rnd.uniform(88.0, 88.7228317)) for _ in range(N // 2)]               # the top
xs = [x for x in xs if x <= f32(XMAX_U)]
out = subprocess.run([os.path.join(HERE, 'gen', 'sweep2.exe'), 'corpus', 'exp32'], input='\n'.join('%x' % bits(x) for x in xs) + '\n',
                     capture_output=True, text=True).stdout.split()
assert len(out) == len(xs), (len(out), len(xs))
EPS = D(10) ** -50
def verdict(f, r):
    """1 faithful, 0 not, -1 ambiguous. f = exp(x) to 60 digits; r the result as a float."""
    if r < 0 or r32(r) != r: return 0
    u = u32(r); hi = D(f32(u + 1)); lo = D(f32(u - 1)) if u else D(-1)
    if lo * (1 + EPS) < f and f < hi * (1 - EPS): return 1
    if f <= lo * (1 - EPS) or f >= hi * (1 + EPS): return 0
    return -1
bad = amb = touched = flagged = 0; first = None
for i, (x, o) in enumerate(zip(xs, out)):
    r = dbl(int(o, 16)); f = D(x).exp(); v = verdict(f, r)
    if v == 0: bad += 1; first = first or (x.hex(), o)
    if v < 0: amb += 1
    if i % 4096 == 0 and r32(r) == r and 0 < r < 1e38:
        touched += 1; flagged += verdict(f, f32(u32(r) + 2)) == 0
ok = bad == 0 and amb == 0 and touched > 0 and flagged == touched
print('exp32 sampled check: %d inputs; not faithful: %d%s; ambiguous: %d; plant (two steps up) flagged on %d of the %d results it touched' % (
    len(xs), bad, '' if not bad else ' first %s' % (first,), amb, flagged, touched))
print('EXP32 SAMPLE %s' % ('HELD' if ok else 'FAILED')); sys.exit(0 if ok else 1)
