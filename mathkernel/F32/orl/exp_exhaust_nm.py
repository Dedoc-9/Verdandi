# VARIANT of exp_exhaust.py (2026-11-16): the program checked is gen-nm\sweep2.exe; nothing else is changed.
# Exhaustive check of exp32 that does not use the C runtime's exp (2026-11-14).
#
# Coverage: every finite binary32 x <= XMAX, bit patterns 0x00000000..0x42B17217 and 0x80000000..0xFF7FFFFF,
# 3258020376 inputs. Results come from the native program gen/sweep2.exe ("corpus exp32": binary64 bit patterns in,
# the bits of narrow(exp32(x)) out). Each result r is checked for faithfulness:
#     r is a finite binary32 value, its sign bit clear, and pred32(r) < exp(x) < succ32(r)
# (pred32(0) is taken as negative, succ32(FLT_MAX) as +infinity). The verdict logic is exp_check.py's.
#
# Reference: Python's decimal module (libmpdec), Decimal(x).exp() at PREC = 40 significant digits. Decimal(x) of a
# float is exact whatever the context, and decimal's exp is documented as correctly rounded, so the reference f has a
# relative error of at most 5e-40. The neighbours pred32(r), succ32(r) are converted exactly; their products with
# (1 +- EPS) are rounded to 40 digits (relative error at most 5e-40 each). EPS = 1e-30 (relative) is ten orders above
# those errors and twenty-two below the relative spacing of binary32 (2^-24, about 6e-8), so:
#     f strictly inside (lo*(1+EPS), hi*(1-EPS))      -> faithful, proved with margin
#     f <= lo*(1-EPS) or f >= hi*(1+EPS)              -> not faithful, proved with margin
#     otherwise (within EPS of a neighbour)           -> AMBIGUOUS, counted, never a pass
#
# Three exact shortcuts (no decimal exp per input); the premise of each is checked once in decimal at start-up
# (at 60 digits), and exp is increasing:
#  (a) x <= -104: 0 < exp(x) <= exp(-104) < 2^-149, so the only faithful results are +0 and 2^-149 (sign bit clear).
#  (b) 0 < x <= 2^-30: 1 < exp(x) <= exp(2^-30) < 1 + 2^-23, so r must be 1 or 1 + 2^-23.
#  (c) -2^-30 <= x < 0: 1 - 2^-24 < exp(-2^-30) <= exp(x) < 1, so r must be 1 - 2^-24 or 1.
#  x = +0 or -0: exp(x) = 1 exactly, r must be exactly 1.
# A shortcut compares the program's output bits with the allowed set; nothing else is accepted there.
#
# Resumable: the 32-bit pattern space is 4096 chunks of 2^20 patterns; one log line per finished chunk in
# gen/exp-exhaust-KEY.log (KEY = first 16 hex digits of sha256 of gen/sweep2.c; the log's first line pins the sha256 of
# sweep2.exe too). Logged chunks are skipped. --seconds N: no chunk is started after N seconds; those running finish.
# When every chunk is logged it prints one line, EXP32 EXHAUSTIVE (decimal) HELD or FAILED.
#   --time            time 200000 decimal checks and print the projected wall time; writes nothing
#   --plant           move every result two binary32 steps up before checking; log gen/exp-exhaust-plant-KEY.log
#   --chunks a,b,..   only these chunks (hex, pattern >> 20); with --plant
# Depends on: sweep2.exe for the results; libmpdec (Python decimal) for exp; the three shortcuts above; Python's
# struct/array for exact float <-> bits conversion.
import array, decimal, hashlib, multiprocessing, os, struct, subprocess, sys, time
from decimal import Decimal as D

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, 'gen-nm')
EXE = os.path.join(GEN, 'sweep2.exe')
PREC = 40
decimal.getcontext().prec = PREC
EPS = D(10) ** -30
ONE_UP = 1 + EPS
ONE_DN = 1 - EPS
XMAX_U = 0x42B17217
TOTAL = 3258020376
WORKERS = 10
NCHUNK = 4096
BATCH = 1 << 16              # patterns per call of the program, within a chunk
TINY = 0x30800000            # 2^-30
UNDER = 0x42D00000           # 104.0

def f32(u): return struct.unpack('<f', struct.pack('<I', u))[0]
def u32(x): return struct.unpack('<I', struct.pack('<f', x))[0]
def bits(d): return struct.unpack('<Q', struct.pack('<d', d))[0]
def dbl(b): return struct.unpack('<d', struct.pack('<Q', b))[0]
def hx(d): return '%016x' % bits(d)

# segments of the covered pattern space: (first, last, kind)
SEGS = [(0x00000000, 0x00000000, 'zero'), (0x00000001, TINY, 'pos'), (TINY + 1, XMAX_U, 'dec'),
        (0x80000000, 0x80000000, 'zero'), (0x80000001, 0x80000000 | TINY, 'neg'),
        (0x80000000 | (TINY + 1), 0x80000000 | (UNDER - 1), 'dec'), (0x80000000 | UNDER, 0xFF7FFFFF, 'under')]
ALLOWED = {'zero': {hx(1.0)}, 'pos': {hx(1.0), hx(1.0 + 2.0 ** -23)}, 'neg': {hx(1.0 - 2.0 ** -24), hx(1.0)},
           'under': {hx(0.0), hx(2.0 ** -149)}}

def is32(r):
    """r (a float) is a finite binary32 value."""
    if r != r or r in (float('inf'), float('-inf')): return False
    try: return struct.unpack('<f', struct.pack('<f', r))[0] == r
    except OverflowError: return False

def verdict(f, r):
    """1 faithful, 0 not, -1 ambiguous. f = exp(x) to PREC digits; r the result as a float."""
    if not is32(r): return 0
    u = u32(r)
    if u >> 31: return 0                                        # sign bit set (r < 0 or -0)
    hi = D(f32(u + 1)); lo = D(f32(u - 1)) if u else D(-1)      # u+1 past FLT_MAX is +inf: Decimal('Infinity')
    if lo * ONE_UP < f and f < hi * ONE_DN: return 1
    if f <= lo * ONE_DN or f >= hi * ONE_UP: return 0
    return -1

def planted(r):
    """two binary32 steps up; a result that is not a finite binary32 value is left as it is (already refused)."""
    if not is32(r): return r
    return f32(u32(r) + 2)                                      # may become inf or nan: refused by verdict / the sets

def premises():
    c = decimal.Context(prec=60)
    two = D(2)
    p = [('(a) exp(-104) < 2^-149', c.exp(D(-104)) < c.power(two, -149)),
         ('(b) exp(2^-30) < 1 + 2^-23', c.exp(D(2.0 ** -30)) < 1 + D(2.0 ** -23)),
         ('(b) exp(2^-149) > 1', c.exp(D(2.0 ** -149)) > 1),
         ('(c) exp(-2^-30) > 1 - 2^-24', c.exp(D(-(2.0 ** -30))) > 1 - D(2.0 ** -24)),
         ('(c) exp(-2^-149) < 1', c.exp(D(-(2.0 ** -149))) < 1),
         ('boundary patterns', f32(TINY) == 2.0 ** -30 and f32(UNDER) == 104.0 and f32(UNDER - 1) < 104.0),
         ('segments cover %d' % TOTAL, sum(b - a + 1 for a, b, _ in SEGS) == TOTAL)]
    # the allowed sets against the decimal verdict itself, at the ends of each shortcut range
    def agree(x, kind, cands):
        f = D(x).exp()
        return all((verdict(f, r) == 1) == (hx(r) in ALLOWED[kind]) and verdict(f, r) != -1 for r in cands)
    one = [1.0 - 2.0 ** -23, 1.0 - 2.0 ** -24, 1.0, 1.0 + 2.0 ** -23, 1.0 + 2.0 ** -22]
    sub = [0.0, 2.0 ** -149, 2.0 ** -148, 3 * 2.0 ** -149]
    # (only where the 40-digit verdict can decide: nearer zero, or further down, exp(x) is within EPS of 1, or
    #  underflows decimal's own range, and the verdict would say ambiguous; there the shortcut's argument alone stands)
    p += [('sets agree with the verdict, (b) at 2^-30 and 2^-80', agree(2.0 ** -30, 'pos', one) and agree(2.0 ** -80, 'pos', one)),
          ('sets agree with the verdict, (c) at -2^-30 and -2^-80', agree(-(2.0 ** -30), 'neg', one) and agree(-(2.0 ** -80), 'neg', one)),
          ('sets agree with the verdict, (a) at -104 and -1000', agree(-104.0, 'under', sub) and agree(-1000.0, 'under', sub))]
    return p

def run_exe(us):
    """us: array('I') of binary32 patterns. Returns (xs as floats, output lines)."""
    af = array.array('f'); af.frombytes(us.tobytes())
    ad = array.array('d', af)
    aq = array.array('Q'); aq.frombytes(ad.tobytes())
    p = subprocess.run([EXE, 'corpus', 'exp32'], input='\n'.join(map('%x'.__mod__, aq)) + '\n', capture_output=True, text=True)
    out = p.stdout.split()
    if p.returncode != 0 or len(out) != len(us):
        raise RuntimeError('sweep2.exe: exit %d, %d lines for %d inputs' % (p.returncode, len(out), len(us)))
    return ad, out

def check_dec(xs, out, plant):
    bad = amb = 0; first = None
    for i, o in enumerate(out):
        r = dbl(int(o, 16))
        if plant: r = planted(r)
        v = verdict(D(xs[i]).exp(), r)
        if v == 1: continue
        if v == 0: bad += 1
        else: amb += 1
        if first is None: first = i
    return bad, amb, first

def do_chunk(job):
    c, plant, deadline = job
    if deadline is not None and time.time() > deadline: return None
    lo = c << 20; hi = lo + (1 << 20) - 1
    n = sn = dn = bad = amb = 0; first = None
    parts = []                                                  # each segment's share of the chunk, BATCH patterns at a time
    for a, b, kind in SEGS:                                     # (memory: ten workers share the machine with other jobs)
        a = max(a, lo); b = min(b, hi)
        parts += [(s, min(s + BATCH - 1, b), kind) for s in range(a, b + 1, BATCH)]
    for a, b, kind in parts:
        us = array.array('I', range(a, b + 1))
        try: xs, out = run_exe(us)
        except (RuntimeError, OSError, MemoryError) as e:       # the chunk is not logged; a later invocation takes it again
            return 'ERROR chunk=%03x at %08x: %s' % (c, a, e)
        n += len(us)
        if kind == 'dec':
            dn += len(us); k, m, fi = check_dec(xs, out, plant); bad += k; amb += m
        else:
            sn += len(us); ok = ALLOWED[kind]; fi = None
            if plant: out = [hx(planted(dbl(int(o, 16)))) for o in out]
            if not set(out) <= ok:
                for i, o in enumerate(out):
                    if o not in ok:
                        bad += 1
                        if fi is None: fi = i
        if fi is not None and first is None: first = '%08x' % (a + fi)
    return 'chunk=%03x n=%d shortcut_n=%d decimal_n=%d not_faithful=%d ambiguous=%d first=%s' % (c, n, sn, dn, bad, amb, first or '-')

def sha(path):
    with open(path, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()

def read_log(path, head):
    done = {}
    if not os.path.exists(path): return done
    with open(path, 'r', encoding='utf-8', newline='') as f: lines = f.read().split('\n')
    if lines[0] != head: sys.exit('log %s was begun for another program: %r' % (os.path.basename(path), lines[0]))
    for ln in lines[1:]:
        if not ln.startswith('chunk='): continue
        d = dict(kv.split('=', 1) for kv in ln.split())
        if len(d) == 7: done[int(d['chunk'], 16)] = d                    # a torn last line is not a finished chunk
    return done

def timing():
    step = 3061; us = array.array('I')
    for a, b, kind in SEGS:
        if kind == 'dec': us.extend(range(a, b + 1, step))
    us = us[:200000] if len(us) >= 200000 else us
    stride = len(us) // 200000 or 1
    t0 = time.perf_counter(); xs, out = run_exe(us); t1 = time.perf_counter()
    bad, amb, _ = check_dec(xs, out, False); t2 = time.perf_counter()
    dec_total = sum(b - a + 1 for a, b, k in SEGS if k == 'dec'); n = len(us)
    per = (t2 - t1) / n; exe = (t1 - t0) / n
    proj = (dec_total * per + TOTAL * exe * 1.5) / WORKERS
    print('timing: %d decimal checks (prec %d) in %.2f s = %.2f us each (not faithful %d, ambiguous %d); sweep2.exe with its text %.2f us per input'
          % (n, PREC, t2 - t1, per * 1e6, bad, amb, exe * 1e6))
    print('projected: %d decimal-checked inputs and %d inputs through the program, %d workers: %.0f s = %.2f h wall, if the workers scale'
          % (dec_total, TOTAL, WORKERS, proj, proj / 3600))
    return 0

def main():
    args = sys.argv[1:]; plant = '--plant' in args; seconds = None; only = None
    if '--seconds' in args: seconds = float(args[args.index('--seconds') + 1])
    if '--chunks' in args: only = sorted(int(t, 16) for t in args[args.index('--chunks') + 1].split(','))
    for name, ok in premises():
        if not ok: sys.exit('PREMISE FAILED: ' + name)
    print('premises of the three shortcuts and the zero rule hold in decimal (%d checks)' % len(premises()))
    if '--time' in args: return timing()
    if only is not None and not plant: sys.exit('--chunks is for --plant; the full run takes every chunk')
    key = sha(os.path.join(GEN, 'sweep2.c'))[:16]
    head = '# exp_exhaust sweep2.c %s sweep2.exe sha256 %s prec %d eps 1e-30%s' % (key, sha(EXE), PREC, ' PLANT two steps up' if plant else '')
    path = os.path.join(GEN, 'exp-exhaust-%s%s.log' % ('plant-' if plant else '', key))
    done = read_log(path, head)
    want = only if only is not None else list(range(NCHUNK))
    todo = [c for c in want if c not in done]
    t0 = time.time(); deadline = None if seconds is None else t0 + seconds
    if todo:
        new = not os.path.exists(path)
        with open(path, 'a', encoding='utf-8', newline='') as log:
            if new: log.write(head + '\n'); log.flush()
            with multiprocessing.Pool(WORKERS) as pool:
                for line in pool.imap_unordered(do_chunk, [(c, plant, deadline) for c in todo]):
                    if line is None: continue
                    if line.startswith('ERROR'): print(line, flush=True); continue
                    log.write(line + '\n'); log.flush()
        done = read_log(path, head)
    left = [c for c in want if c not in done]
    rows = [done[c] for c in want if c in done]
    tot = {k: sum(int(d[k]) for d in rows) for k in ('n', 'shortcut_n', 'decimal_n', 'not_faithful', 'ambiguous')}
    firsts = [d['first'] for d in rows if d['first'] != '-']
    print('%s: %d of %d chunks logged (%d this run, %.0f s), %d left' % (os.path.basename(path), len(rows), len(want), len(todo) - len(left), time.time() - t0, len(left)))
    if left: print('NOT FINISHED: run again'); return 3
    tail = 'chunks %d, inputs %d, shortcut inputs %d, decimal-checked inputs %d, not faithful %d, ambiguous %d%s' % (
        len(rows), tot['n'], tot['shortcut_n'], tot['decimal_n'], tot['not_faithful'], tot['ambiguous'],
        '' if not firsts else ', first failing pattern %s' % firsts[0])
    if plant:
        ok = tot['decimal_n'] > 0 and tot['not_faithful'] == tot['n'] and tot['ambiguous'] == 0
        print('EXP32 EXHAUSTIVE PLANT (two binary32 steps up) %s: %s' % ('CAUGHT ON EVERY INPUT' if ok else 'NOT CAUGHT', tail))
    else:
        ok = len(rows) == NCHUNK and tot['n'] == TOTAL and tot['shortcut_n'] + tot['decimal_n'] == TOTAL and tot['not_faithful'] == 0 and tot['ambiguous'] == 0
        print('EXP32 EXHAUSTIVE (decimal) %s: %s' % ('HELD' if ok else 'FAILED', tail))
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
