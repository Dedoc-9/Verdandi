# Build the SEPARATELY-IDENTIFIED adversarial characterization corpus (not the frozen 90-vector corpus).
# Domain (declared, per the frozen S5 spec): kernel argument x in [-1.45, 2*pi)  (pitch in [-1.45,1.45], yaw in [0,2pi)).
# Categories (owner's list): reduction-boundary neighbors; adjacent doubles at critical points; near k*pi/2;
# small-normal/subnormal; domain endpoints; hard-to-round (SEARCHED); different reduction paths.
import struct, math, csv, sys
import gmpy2
from gmpy2 import mpfr

def fbits(x): return struct.pack('>d', x).hex()
PREC = 400
def true_val(xf, which):
    with gmpy2.local_context(gmpy2.context(precision=PREC)):
        x = mpfr(xf, 53)
        return gmpy2.sin(x) if which=='sin' else gmpy2.cos(x)

DOM_LO = -1.45
TWO_PI = 2.0*math.pi
DOM_HI = math.nextafter(TWO_PI, 0.0)   # largest double strictly below 2*pi (yaw is [0,2pi))

# high-precision special points
with gmpy2.local_context(gmpy2.context(precision=PREC)):
    PI = gmpy2.const_pi()
    specials = {
        '0': mpfr(0), 'pi/4': PI/4, 'pi/2': PI/2, '3pi/4': 3*PI/4, 'pi': PI,
        '5pi/4': 5*PI/4, '3pi/2': 3*PI/2, '7pi/4': 7*PI/4, '2pi': 2*PI,
        '-pi/4': -PI/4, '-1.45(pitch-)': mpfr('-1.45'), '1.45(pitch+)': mpfr('1.45'),
    }

rows = []   # (input_bits, input_repr, category, op_scope, note)
seen = set()
def add(xf, category, note, op='both'):
    if not (DOM_LO <= xf <= DOM_HI):   # keep strictly inside the declared domain
        return
    b = fbits(xf)
    if (b, op) in seen: return
    seen.add((b, op))
    rows.append((b, repr(xf), category, op, note))

# (a,b,c,e) neighbors of each special point: the nearest double and +-3 adjacent doubles
for name, sp in specials.items():
    base = float(sp)
    xs = [base]
    u, d = base, base
    for _ in range(3):
        u = math.nextafter(u, math.inf); xs.append(u)
        d = math.nextafter(d, -math.inf); xs.append(d)
    cat = 'near-k*pi/2' if name in ('pi/2','pi','3pi/2','2pi') else \
          'reduction-boundary' if 'pi/4' in name else 'domain-endpoint'
    for xf in xs:
        add(xf, cat, 'neighbor of '+name)

# (d) very small normal and subnormal, and the 2^-27 reduction cutoff (fdlibm |x|<2^-27 returns x for sin)
smalls = [5e-324, 1e-320, 2.2250738585072014e-308, math.ldexp(1,-1022),
          math.ldexp(1,-28), math.ldexp(1,-27), math.nextafter(math.ldexp(1,-27),0),
          math.ldexp(1,-26), 1e-10, 1e-5]
for xf in smalls:
    add(xf, 'small/subnormal', 'small or subnormal')
    add(-xf, 'small/subnormal', 'small or subnormal (neg)')

# (g) one representative inside the no-reduction path (|x|<=pi/4) and one in the medium-reduction path
add(0.4, 'reduction-path', 'no-reduction path |x|<=pi/4')
add(2.0, 'reduction-path', 'medium-reduction path pi/4<|x|')
add(5.0, 'reduction-path', 'medium-reduction path pi/4<|x|')
add(-1.0, 'reduction-path', 'medium-reduction path (neg)')

# (f) HARD-TO-ROUND SEARCH: sample in-domain, score by closeness of true result to a binary64 midpoint
def hardness(xf, which):
    # distance of true to nearest midpoint, in ulp; smaller = harder. Returns (dist_ulp, cr_point_bits)
    t = true_val(xf, which)
    with gmpy2.local_context(gmpy2.context(precision=53, round=gmpy2.RoundToNearest)):
        m = +mpfr(t)
    mf = float(m)
    if mf == 0.0 or not math.isfinite(mf):
        return (1.0, fbits(mf))
    u = mpfr(math.ulp(mf))
    mid_hi = mpfr(mf) + u/2
    mid_lo = mpfr(mf) - u/2
    dist = min(abs(t-mid_hi), abs(t-mid_lo)) / u
    return (float(dist), fbits(mf))

import random
random.seed(0)
samples = []
# random doubles uniform in-domain
for _ in range(60000):
    xf = random.uniform(DOM_LO, DOM_HI)
    samples.append(xf)
# dense grid near each special (where hard cases cluster)
for name, sp in specials.items():
    base = float(sp); x = base
    for _ in range(400):
        x = math.nextafter(x, math.inf)
        if DOM_LO <= x <= DOM_HI: samples.append(x)
    x = base
    for _ in range(400):
        x = math.nextafter(x, -math.inf)
        if DOM_LO <= x <= DOM_HI: samples.append(x)

for which in ('sin','cos'):
    scored = []
    for xf in samples:
        d, _ = hardness(xf, which)
        scored.append((d, xf))
    scored.sort(key=lambda t: t[0])
    for d, xf in scored[:15]:
        add(xf, 'hard-to-round', 'hardest-%s dist_to_midpoint=%.3e ulp'%(which, d), op=which)

out = r"<SCRATCH>\MATH-KERNEL-CHAR-CORPUS-2026-11-10.csv"
with open(out, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['input_bits','input_repr','category','op_scope','note'])
    for r in rows:
        w.writerow(r)
print('wrote', len(rows), 'corpus rows ->', out)
from collections import Counter
c = Counter(r[2] for r in rows)
for k in sorted(c): print('  %-20s %d' % (k, c[k]))
