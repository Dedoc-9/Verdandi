# GENERATED = SWEPT (2026-11-14, review finding F4).
# The exhaustive sweeps of sqrt32 and rsqrt32 in orl/gen/sweep.c do not call the generated functions f_sqrt32 and
# f_rsqrt32. Their loop computes, written by hand in the harness,
#     double y = is_sqrt ? sqrt(x) : 1.0 / sqrt(x);      then      double r = narrow(y);
# so the sweeps' verdict is about that expression, and about the generated functions only if the two are the same.
# This test writes and builds a C program that includes the generated gen/sweep.c as it is (its main renamed by a
# #define) and, for every input of those two sweeps, compares the bits of the generated function's result with the bits
# of the hand-written expression:
#     sqrt32   every binary32 pattern 0x00000000..0x7F7FFFFF      2139095040 inputs
#     rsqrt32  every binary32 pattern 0x00000001..0x7F7FFFFF      2139095039 inputs
# The generated functions are called through volatile function pointers and the reference expressions are noinline
# functions, so the compiler cannot fold the comparison away: both sides are computed for every input.
# Resumable as emit.py's sweep is: 64 chunks per function, one log line per chunk, the log keyed to the sha256 of
# sweep.c (and of the test program's source); a logged chunk is not run again.
# Plant (compile time, -DPLANT_REF): the reference expression of rsqrt32 becomes narrow(1.0 / x). Required: the plant
# program reports differences in every chunk of rsqrt32, and none for sqrt32 (the plant is of rsqrt32 alone).
#   python -B gen_equiv.py        prints GENERATED = SWEPT HELD or FAILED, exit status 0 or 1
# What it does not show: that gen/sweep.exe (built earlier) is this sweep.c compiled; that the Orlog law or the Coq
# graph compute the same; anything about inputs outside the two sweeps (negative x, infinities, NaN, rsqrt32 of 0).
# The two sides are compared as compiled here, by one compiler with one set of flags.
import concurrent.futures, hashlib, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(os.path.dirname(HERE), 'gen')
SWEEP_C = os.path.join(GEN, 'sweep.c')
SRC = os.path.join(HERE, 'gen_equiv.c')
CFLAGS = ['-O2', '-ffp-contract=off', '-fno-math-errno', '-D_CRT_SECURE_NO_WARNINGS']
THREADS = 10
NCH = 64
EXPECT = {'sqrt32': 2139095040, 'rsqrt32': 2139095039}

# ---- the two lines of sweep.c's exhaustive loop that this test stands for (held to the live file below)
SWEPT_Y = '    double y = is_sqrt ? sqrt(x) : 1.0 / sqrt(x);'
SWEPT_R = '    double r = narrow(y); n++;'
# ---- the generated functions (held to the live file below)
GEN_SQRT = 'static double f_sqrt32(double x) { return narrow(sqrt(x)); }'
GEN_RSQRT = 'static double f_rsqrt32(double x) { return narrow((1.0 / sqrt(x))); }'
# ---- the loop's domain lines (held to the live file below)
SKIP_NAN = '    if ((u & 0x7f800000u) == 0x7f800000u) continue;                 // infinities and NaNs'
SKIP_DOM = '    if (u & 0x80000000u) continue; if (!is_sqrt && u == 0) continue;  // domain: x >= 0 (sqrt), x > 0 (rsqrt)'

C_SRC = r'''// Written by gen_equiv.py. The generated f_sqrt32 and f_rsqrt32 of gen/sweep.c against the expressions that
// sweep.c's exhaustive loop computes by hand, bit for bit, over a range of binary32 patterns.
#define main sweep_main
#include "../gen/sweep.c"
#undef main
// the swept expressions: "double y = is_sqrt ? sqrt(x) : 1.0 / sqrt(x);" then "double r = narrow(y);"
__attribute__((noinline)) static double ref_sqrt(double x) { double y = sqrt(x); double r = narrow(y); return r; }
#ifdef PLANT_REF
__attribute__((noinline)) static double ref_rsqrt(double x) { double y = 1.0 / x; double r = narrow(y); return r; }
#else
__attribute__((noinline)) static double ref_rsqrt(double x) { double y = 1.0 / sqrt(x); double r = narrow(y); return r; }
#endif
static double (*volatile gen_sqrt)(double) = f_sqrt32;
static double (*volatile gen_rsqrt)(double) = f_rsqrt32;
int main(int argc, char **argv) {
  if (argc != 4) return 2;
  int is_sqrt = !strcmp(argv[1], "sqrt32"); if (!is_sqrt && strcmp(argv[1], "rsqrt32")) return 2;
  uint32_t lo_u = (uint32_t)strtoul(argv[2], 0, 16), hi_u = (uint32_t)strtoul(argv[3], 0, 16);
  double (*g)(double) = is_sqrt ? gen_sqrt : gen_rsqrt;
  uint64_t n = 0, differ = 0; uint32_t first = 0; int have = 0;
  for (uint64_t uu = lo_u; uu <= hi_u; uu++) { uint32_t u = (uint32_t)uu;
    if ((u & 0x7f800000u) == 0x7f800000u) continue;                 // infinities and NaNs
    if (u & 0x80000000u) continue; if (!is_sqrt && u == 0) continue;  // domain: x >= 0 (sqrt), x > 0 (rsqrt)
    double x = from32(u); n++;
    double a = g(x), b = is_sqrt ? ref_sqrt(x) : ref_rsqrt(x);
    if (bits(a) != bits(b)) { differ++; if (!have) { first = u; have = 1; } } }
  printf("%s %08x %08x n=%llu differ=%llu first=%08x\n", argv[1], lo_u, hi_u, (unsigned long long)n, (unsigned long long)differ, first);
  return 0; }
'''

def sha(path):
    with open(path, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()

def chunks():
    step = 0x80000000 // NCH
    return [(i * step, (i + 1) * step - 1) for i in range(NCH)]

def expected_n(fn, lo, hi):
    """inputs of the sweep in [lo, hi], from the bit patterns: finite, sign clear, and for rsqrt32 not zero"""
    a = max(lo, 0 if fn == 'sqrt32' else 1); b = min(hi, 0x7f7fffff)
    return max(0, b - a + 1)

def live_rows():
    t = open(SWEEP_C, encoding='utf-8').read().splitlines(); c = C_SRC.splitlines()
    rows = [('gen/sweep.c holds the swept expression, its narrow and the loop\'s two domain lines, each exactly once',
             all(t.count(l) == 1 for l in (SWEPT_Y, SWEPT_R, SKIP_NAN, SKIP_DOM))),
            ('gen/sweep.c holds f_sqrt32 and f_rsqrt32 as read here, each exactly once, and no other definition of either',
             t.count(GEN_SQRT) == 1 and t.count(GEN_RSQRT) == 1 and sum('f_sqrt32(double' in l for l in t) == 1 and sum('f_rsqrt32(double' in l for l in t) == 1),
            ('the test program\'s loop has the sweep\'s two domain lines, character for character', c.count(SKIP_NAN) == 1 and c.count(SKIP_DOM) == 1),
            ('the test program\'s reference functions hold the swept expressions (sqrt(x); 1.0 / sqrt(x); narrow(y))',
             sum('double y = sqrt(x); double r = narrow(y); return r;' in l for l in c) == 1
             and sum('double y = 1.0 / sqrt(x); double r = narrow(y); return r;' in l for l in c) == 1
             and 'is_sqrt ? sqrt(x) : 1.0 / sqrt(x)' in SWEPT_Y and 'double r = narrow(y);' in SWEPT_R),
            ('the test program includes gen/sweep.c itself and defines no narrow, f_sqrt32 or f_rsqrt32 of its own',
             c.count('#include "../gen/sweep.c"') == 1 and not any(l.startswith('static double narrow(') or l.startswith('static double f_') for l in c))]
    return rows

def build(exe, extra):
    q = subprocess.run(['clang'] + CFLAGS + extra + [SRC, '-o', exe], capture_output=True, text=True, cwd=HERE)
    print('build: clang %s gen_equiv.c -o %s -> exit %d' % (' '.join(CFLAGS + extra), os.path.basename(exe), q.returncode))
    if q.returncode != 0: print(q.stdout + q.stderr)
    return q.returncode == 0

def read_log(path):
    done = {}
    if os.path.exists(path):
        for l in open(path, encoding='utf-8'):
            f = l.split()
            if len(f) == 6 and f[0] in EXPECT and f[3].startswith('n=') and f[4].startswith('differ=') and f[5].startswith('first='):   # a torn line is not a chunk
                done.setdefault((f[0], int(f[1], 16), int(f[2], 16)), []).append((int(f[3][2:]), int(f[4][7:]), f[5][6:]))
    return done

def run(exe, log):
    done = read_log(log)
    jobs = [(fn, lo, hi) for fn in EXPECT for lo, hi in chunks() if (fn, lo, hi) not in done]
    def one(j):
        q = subprocess.run([exe, j[0], '%x' % j[1], '%x' % j[2]], capture_output=True, text=True)
        return q.returncode, q.stdout.strip()
    errors = 0
    if jobs:
        with open(log, 'a', encoding='utf-8', newline='\n') as f, concurrent.futures.ThreadPoolExecutor(THREADS) as ex:
            for rc, line in ex.map(one, jobs):
                if rc != 0 or not line: errors += 1; continue
                f.write(line + '\n'); f.flush()
    return read_log(log), len(jobs), errors

def tally(done):
    """per function: (chunks present exactly once and tiling, per-chunk counts as predicted, n, differ, chunks with a difference, first)"""
    out = {}
    for fn in EXPECT:
        tiles = all(len(done.get((fn, lo, hi), [])) == 1 for lo, hi in chunks()) and sum(1 for k in done if k[0] == fn) == NCH
        counts = all(v[0][0] == expected_n(fn, k[1], k[2]) for k, v in done.items() if k[0] == fn)
        rows = [(k, v[0]) for k, v in sorted(done.items()) if k[0] == fn]
        firsts = [v[2] for k, v in rows if v[1]]
        out[fn] = (tiles, counts, sum(v[0] for k, v in rows), sum(v[1] for k, v in rows), sum(1 for k, v in rows if v[1]), firsts[0] if firsts else '-')
    return out

def main():
    ok = True
    open(SRC, 'w', encoding='utf-8', newline='\n').write(C_SRC)
    key = sha(SWEEP_C)[:16]; ckey = sha(SRC)[:8]
    ver = subprocess.run(['clang', '--version'], capture_output=True, text=True).stdout.splitlines()[0]
    print('gen/sweep.c sha256 %s; gen_equiv.c sha256 %s; %s' % (sha(SWEEP_C), sha(SRC), ver))
    exe = os.path.join(HERE, 'gen_equiv.exe'); pexe = os.path.join(HERE, 'gen_equiv_plant.exe')
    if not (build(exe, []) and build(pexe, ['-DPLANT_REF'])):
        print('GENERATED = SWEPT FAILED (the test program did not build)'); return 1
    log = os.path.join(HERE, 'gen-equiv-%s-%s.log' % (key, ckey)); plog = os.path.join(HERE, 'gen-equiv-plant-%s-%s.log' % (key, ckey))
    done, ran, errs = run(exe, log)
    print('%s: %d chunks run now, %d errors, %d lines' % (os.path.basename(log), ran, errs, sum(len(v) for v in done.values())))
    t = tally(done); req = live_rows()
    for fn in EXPECT:
        tiles, counts, n, differ, nch, first = t[fn]
        print('%-8s chunks %d/%d each once over 00000000..7fffffff: %s | per-chunk counts as the bit patterns give: %s | inputs %d (expected %d) | differ %d%s' % (
            fn, sum(1 for k in done if k[0] == fn), NCH, tiles, counts, n, EXPECT[fn], differ, '' if not differ else ' (first %s)' % first))
        req += [('%s: every chunk logged exactly once, counts as predicted, %d inputs' % (fn, EXPECT[fn]), tiles and counts and n == EXPECT[fn]),
                ('%s: the generated function and the swept expression differ on 0 inputs' % fn, differ == 0)]
    pdone, pran, perrs = run(pexe, plog)
    print('%s: %d chunks run now, %d errors' % (os.path.basename(plog), pran, perrs))
    p = tally(pdone)
    print('plant (the reference of rsqrt32 is narrow(1.0 / x)): rsqrt32 inputs %d, differ %d, in %d of %d chunks (first %s); sqrt32 inputs %d, differ %d' % (
        p['rsqrt32'][2], p['rsqrt32'][3], p['rsqrt32'][4], NCH, p['rsqrt32'][5], p['sqrt32'][2], p['sqrt32'][3]))
    req += [('plant: every chunk of rsqrt32 reports differences (over the whole sweep, %d inputs)' % EXPECT['rsqrt32'],
             p['rsqrt32'][0] and p['rsqrt32'][2] == EXPECT['rsqrt32'] and p['rsqrt32'][4] == NCH),
            ('plant: sqrt32, which it does not touch, differs on 0 of %d inputs' % EXPECT['sqrt32'], p['sqrt32'][0] and p['sqrt32'][2] == EXPECT['sqrt32'] and p['sqrt32'][3] == 0),
            ('no chunk failed to run', errs == 0 and perrs == 0)]
    for text, good in req:
        print('  %-4s %s' % ('ok' if good else 'FAIL', text)); ok &= bool(good)
    print('GENERATED = SWEPT %s: sqrt32 %d inputs %d differ; rsqrt32 %d inputs %d differ (plant: rsqrt32 differs on %d of %d; program %s)' % (
        'HELD' if ok else 'FAILED', t['sqrt32'][2], t['sqrt32'][3], t['rsqrt32'][2], t['rsqrt32'][3], p['rsqrt32'][3], p['rsqrt32'][2], key))
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
