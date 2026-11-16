# NARROW TOP (2026-11-14, review finding F2).
# The exhaustive narrow sweep of orl/gen/sweep.c leaves out every value of magnitude at or above FLT_MAX
# (its line "if (!(fabs(y) < 0x1.fffffep127)) continue;"). This test covers the top, with the narrow of gen/sweep.c
# itself: the test program includes sweep.c as it is (main renamed by a #define) and has no narrow of its own.
#   FLT_MAX = 0x1.fffffep127, the largest finite binary32 number
#   OVF     = 0x1.ffffffp127 = 2^128 - 2^103, the least binary64 value the IEEE conversion rounds to infinity
# A step is one binary64 step (2^75 here). Three parts, both signs in each:
#   A  the 2^24 binary64 values just below OVF                 required: narrow(v) = (double)(float)v, bit for bit
#   B  the 2^25 + 1 values within 2^24 steps of FLT_MAX        required: narrow(v) = (double)(float)v, bit for bit
#      (OVF is 2^28 steps above FLT_MAX, so all of B is below OVF)
#   C  OVF and the 2^24 values above it                        recorded; required only that what the review documented
#      is what is seen: narrow returns the finite value 2^128 (with v's sign), which is not a binary32 number, where
#      the conversion returns infinity. So narrow is NOT the conversion at or above OVF, and this test says so.
# Named values far above (2^200, 1e300, DBL_MAX, infinity, NaN) are printed as seen and required of nothing.
# Plant (compile time, -DPLANT_TOP): one result of A is moved one binary64 step and one result of C is replaced by
# infinity; the plant program must report exactly one difference in A and exactly one result of C that is not 2^128.
#   python -B narrow_top.py        prints NARROW TOP HELD or FAILED, exit status 0 or 1
# What it does not show: values between FLT_MAX + 2^24 steps and OVF - 2^24 steps (about 2^28 values a sign, not
# visited); anything above OVF + 2^24 steps beyond the named values; the Orlog, Python or Coq renderings of narrow.
import hashlib, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(os.path.dirname(HERE), 'gen')
SWEEP_C = os.path.join(GEN, 'sweep.c')
SRC = os.path.join(HERE, 'narrow_top.c')
CFLAGS = ['-O2', '-ffp-contract=off', '-fno-math-errno', '-D_CRT_SECURE_NO_WARNINGS']
W = 1 << 24
OVF_BITS = 0x47EFFFFFF0000000        # the bits of 0x1.ffffffp127 (run 1 of this test had FLT_MAX's bits here, and failed its two plant rows)
# ---- copied from orl/gen/sweep.c (held to the live file below): the narrow under test, and the sweep's exclusion
NARROW = 'static double narrow(double v) { if (fabs(v) <= HH) return v * 0.0; if (fabs(v) < TT) return (v + MM) - MM; double c = KK * v; return c - (c - v); }'
EXCL = '      for (int i = 0; i < 5; i++) { double y = ys[i]; if (!(fabs(y) < 0x1.fffffep127)) continue; n++;'

C_SRC = r'''// Written by narrow_top.py. The narrow of gen/sweep.c (included as it is) at the top of the binary32 range.
#define main sweep_main
#include "../gen/sweep.c"
#undef main
#include <float.h>
#include <inttypes.h>
#define W ((int64_t)1 << 24)
static double (*volatile nar)(double) = narrow;
static void named(const char *name, double v) { volatile double w = v; double r = nar(w), c = (double)(float)w;
  printf("named %-28s v=%016" PRIx64 " narrow=%016" PRIx64 " cast=%016" PRIx64 "\n", name, bits(w), bits(r), bits(c)); }
int main(void) {
  const uint64_t o = bits(0x1.ffffffp127), f = bits(0x1.fffffep127), INFB = bits(INFINITY), P128 = bits(0x1p128), SIGN = 0x8000000000000000ull;
  double (*g)(double) = nar;
  { uint64_t n = 0, differ = 0, first = 0;                                   // A: below OVF
    for (int64_t d = 1; d <= W; d++) for (int s = 0; s < 2; s++) { double v = frombits((o - (uint64_t)d) | (s ? SIGN : 0));
      double r = g(v), c = (double)(float)v;
#ifdef PLANT_TOP
      if (d == 4097 && s == 0) r = nextafter(r, 0.0);
#endif
      n++; if (bits(r) != bits(c)) { if (!differ) first = bits(v); differ++; } }
    printf("A n=%" PRIu64 " differ=%" PRIu64 " first=%016" PRIx64 "\n", n, differ, first); }
  { uint64_t n = 0, differ = 0, first = 0, above = 0;                        // B: around FLT_MAX
    for (int64_t d = -W; d <= W; d++) for (int s = 0; s < 2; s++) { double v = frombits((f + (uint64_t)d) | (s ? SIGN : 0));
      double r = g(v), c = (double)(float)v; above += !(fabs(v) < 0x1.fffffep127);
      n++; if (bits(r) != bits(c)) { if (!differ) first = bits(v); differ++; } }
    printf("B n=%" PRIu64 " differ=%" PRIu64 " first=%016" PRIx64 " left_out_by_the_sweep=%" PRIu64 "\n", n, differ, first, above); }
  for (int s = 0; s < 2; s++) {                                              // C: OVF and above
    uint64_t n = 0, is128 = 0, finite = 0, b32 = 0, castinf = 0, same = 0, lo = ~0ull, hi = 0, firstother = 0;
    for (int64_t d = 0; d <= W; d++) { double v = frombits((o + (uint64_t)d) | (s ? SIGN : 0));
      double r = g(v), c = (double)(float)v;
#ifdef PLANT_TOP
      if (d == 4097 && s == 0) r = INFINITY;
#endif
      uint64_t rb = bits(r); n++;
      if (rb == (P128 | (s ? SIGN : 0))) is128++; else if (!firstother) firstother = bits(v);
      finite += isfinite(r) ? 1 : 0; b32 += (isfinite(r) && (double)(float)r == r) ? 1 : 0;
      castinf += bits(c) == (INFB | (s ? SIGN : 0)); same += rb == bits(c);
      if (rb < lo) lo = rb; if (rb > hi) hi = rb; }
    printf("C sign=%c n=%" PRIu64 " is_2p128=%" PRIu64 " finite=%" PRIu64 " binary32=%" PRIu64 " cast_is_inf=%" PRIu64 " same_as_cast=%" PRIu64
           " lowest=%016" PRIx64 " highest=%016" PRIx64 " first_other=%016" PRIx64 "\n", s ? '-' : '+', n, is128, finite, b32, castinf, same, lo, hi, firstother); }
  named("FLT_MAX", 0x1.fffffep127); named("OVF-1step", frombits(o - 1)); named("OVF", 0x1.ffffffp127); named("OVF+1step", frombits(o + 1));
  named("2^128", 0x1p128); named("3*2^127", 0x1.8p128); named("2^200", 0x1p200); named("2^994", 0x1p994); named("2^995-1step", 0x1.fffffffffffffp994);
  named("2^995", 0x1p995); named("1e300", 1e300); named("DBL_MAX", DBL_MAX); named("infinity", INFINITY); named("-infinity", -INFINITY); named("NaN", NAN);
  return 0; }
'''

def sha(path):
    with open(path, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()

def parse(text):
    d = {}; named = []
    for l in text.splitlines():
        f = l.split()
        if not f: continue
        if f[0] == 'named': named.append(l); continue
        kv = dict(x.split('=', 1) for x in f[1:])
        d[f[0] + kv.pop('sign', '')] = kv
    return d, named

def live_rows():
    t = open(SWEEP_C, encoding='utf-8').read().splitlines(); c = C_SRC.splitlines()
    return [('gen/sweep.c holds the narrow tested here exactly once and no other definition of narrow',
             t.count(NARROW) == 1 and sum(l.startswith('static double narrow(') for l in t) == 1),
            ('gen/sweep.c still leaves out |y| >= FLT_MAX in its narrow sweep (the line this test stands beside)', t.count(EXCL) == 1),
            ('the test program includes gen/sweep.c itself and defines no narrow of its own',
             c.count('#include "../gen/sweep.c"') == 1 and not any('double narrow(' in l for l in c))]

def run(exe, extra):
    q = subprocess.run(['clang'] + CFLAGS + extra + [SRC, '-o', exe], capture_output=True, text=True, cwd=HERE)
    print('build: clang %s narrow_top.c -o %s -> exit %d' % (' '.join(CFLAGS + extra), os.path.basename(exe), q.returncode))
    if q.returncode != 0: print(q.stdout + q.stderr); return None
    p = subprocess.run([exe], capture_output=True, text=True)
    if p.returncode != 0: print('%s: exit %d' % (os.path.basename(exe), p.returncode)); return None
    return p.stdout

def main():
    ok = True
    open(SRC, 'w', encoding='utf-8', newline='\n').write(C_SRC)
    ver = subprocess.run(['clang', '--version'], capture_output=True, text=True).stdout.splitlines()[0]
    print('gen/sweep.c sha256 %s; narrow_top.c sha256 %s; %s' % (sha(SWEEP_C), sha(SRC), ver))
    out = run(os.path.join(HERE, 'narrow_top.exe'), []); pout = run(os.path.join(HERE, 'narrow_top_plant.exe'), ['-DPLANT_TOP'])
    if out is None or pout is None:
        print('NARROW TOP FAILED (the test program did not build or run)'); return 1
    d, named = parse(out); p, _ = parse(pout)
    for l in out.splitlines():
        if not l.startswith('named'): print('  ' + l)
    print('named values, as seen (required of nothing):')
    for l in named: print('  ' + l)
    print('plant program:')
    for l in pout.splitlines():
        if not l.startswith('named'): print('  ' + l)
    I = lambda k, f, dd=None: int((dd or d)[k][f])
    P128, NEG = '47f0000000000000', 'c7f0000000000000'
    req = live_rows() + [
        ('A: all %d values below OVF were visited' % (2 * W), I('A', 'n') == 2 * W),
        ('A: narrow equals the conversion on every one', I('A', 'differ') == 0),
        ('B: all %d values within 2^24 steps of FLT_MAX were visited, %d of them left out by the sweep' % (2 * (2 * W + 1), 2 * (W + 1)),
         I('B', 'n') == 2 * (2 * W + 1) and I('B', 'left_out_by_the_sweep') == 2 * (W + 1)),
        ('B: narrow equals the conversion on every one', I('B', 'differ') == 0),
        ('C: OVF and the 2^24 values above it were visited, each sign (%d a sign)' % (W + 1), I('C+', 'n') == W + 1 and I('C-', 'n') == W + 1),
        ('C, as documented: narrow returns exactly +2^128 on every positive value and -2^128 on every negative one',
         I('C+', 'is_2p128') == W + 1 and I('C-', 'is_2p128') == W + 1 and d['C+']['lowest'] == d['C+']['highest'] == P128 and d['C-']['lowest'] == d['C-']['highest'] == NEG),
        ('C, as documented: those results are finite and none is a binary32 number',
         I('C+', 'finite') == W + 1 and I('C-', 'finite') == W + 1 and I('C+', 'binary32') == 0 and I('C-', 'binary32') == 0),
        ('C, as documented: the conversion returns infinity (of v\'s sign) on every one, so narrow equals it on none',
         I('C+', 'cast_is_inf') == W + 1 and I('C-', 'cast_is_inf') == W + 1 and I('C+', 'same_as_cast') == 0 and I('C-', 'same_as_cast') == 0),
        ('plant: the moved result of A is reported, exactly one difference, at OVF - 4097 steps',
         I('A', 'differ', p) == 1 and I('A', 'n', p) == 2 * W and p['A']['first'] == '%016x' % (OVF_BITS - 4097)),
        ('plant: the replaced result of C is reported, exactly one positive result that is not 2^128, at OVF + 4097 steps',
         I('C+', 'is_2p128', p) == W and p['C+']['first_other'] == '%016x' % (OVF_BITS + 4097) and I('C-', 'is_2p128', p) == W + 1),
        ('plant: part B, which it does not touch, is as in the honest run', p['B'] == d['B']),
    ]
    for text, good in req:
        print('  %-4s %s' % ('ok' if good else 'FAIL', text)); ok &= bool(good)
    print('NARROW TOP %s: below OVF %d values, differ from the conversion %d; around FLT_MAX %d values, differ %d; at and above OVF %d values, '
          'narrow returns +-2^128 on %d (finite, not binary32) where the conversion returns infinity on %d' % (
              'HELD' if ok else 'FAILED', I('A', 'n'), I('A', 'differ'), I('B', 'n'), I('B', 'differ'), I('C+', 'n') + I('C-', 'n'),
              I('C+', 'is_2p128') + I('C-', 'is_2p128'), I('C+', 'cast_is_inf') + I('C-', 'cast_is_inf')))
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
