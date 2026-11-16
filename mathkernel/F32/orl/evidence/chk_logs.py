# SWEEP LOGS TILE (2026-11-14, review finding F12).
# emit.py's tally of its sweep log asks for 64 lines a function and zero in the bad counters. It checks neither the
# ranges the lines name nor the number of inputs each line reports, so a log in which one chunk is missing and another
# stands twice, or in which a chunk visited fewer inputs than its range holds, tallies as a full sweep. (emit2.py's
# tally does hold the total to N_INPUTS, but not the ranges; exp_exhaust.py keys chunks by number and holds the totals.)
# This test reads the logs under orl/gen of the current programs and requires, for each function in each log:
#   - every line well formed, of a function the log is for;
#   - the chunks tile the pattern space exactly: sorted, the first starts at 0, each starts where the one before
#     ended, the last ends at the top (0x7fffffff for sqrt32 and rsqrt32, 0xffffffff for narrow and exp32), none twice;
#   - every chunk's count n equals the number of inputs its range holds, computed here from the bit patterns alone;
#   - the totals are the stated ones, and the counters the authors' tallies read are zero (repeated here, not new).
# Logs covered: gen/sweeps-KEY.log (sqrt32, rsqrt32, narrow; KEY from sha256 of gen/sweep.c), gen/sweep2-KEY2.log
# (exp32; KEY2 from gen/sweep2.c), gen/exp-exhaust-KEY2.log (4096 numbered chunks: each number once, n and its split
# into shortcut_n and decimal_n as the patterns give, the header's key and sweep2.exe's sha256 as they are now), and
# gen/exp-exhaust-plant-KEY2.log (a partial log by design: its chunks each once and their counts, no tiling asked).
# A log of another key (an earlier program) is listed and not judged.
# The count rules are held to the live programs: gen/sweep.exe and gen/sweep2.exe are run on a few small ranges and
# must report the n computed here (narrow's rule has two special patterns, 0x7f7fffff and 0xff7fffff).
# Plants (copies in memory, never a file): each log with one chunk line removed, with one chunk's count altered, and
# with one chunk replaced by a second copy of its neighbour, must each fail; for exp-exhaust also one input moved from
# decimal_n to shortcut_n. Printed beside them: whether emit.py's own criterion would have accepted the copy.
#
# Where it came from: the reviewer's tier1-review/work2/chk_logs.py (2026-11-14): its count_range, its finite ranges
# and its count rule for each function are kept. What was changed, and why (each a weakness found on reading it):
#   1. it printed True or False and gave no verdict or exit status; a mismatch could not fail anything.
#   2. it had no plant.
#   3. `ch.sort()` sorted tuples whose third member is a dict: two lines for one range raise TypeError instead of
#      being reported. Here a chunk named twice is a reported defect.
#   4. a function absent from a log was not noticed (it looped over what was there); here each log's set is required.
#   5. a malformed line raised; here it is a reported defect.
#   6. narrow's two special counts (5 inputs left out at 0x7f7fffff, 2 at 0xff7fffff) were asserted from reading the
#      code; here they are also measured from sweep.exe.
#   7. it read every log matching the name, of any key, with one rule; here the current keys are computed from the
#      sources and only their logs are judged.
#   8. the exp-exhaust logs were not covered; a `kind` argument was passed and never used.
#   python -B chk_logs.py          prints SWEEP LOGS TILE HELD or FAILED, exit status 0 or 1. Writes nothing.
# What it does not show: that a log's lines were written by the program whose key names it (a log is a text file);
# that the inputs counted were the inputs of the range (only how many); anything about the checks made per input.
import hashlib, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ORL = os.path.dirname(HERE); GEN = os.path.join(ORL, 'gen')
XMAX_U = 0x42B17217
POS_FIN = (0x00000000, 0x7f7fffff)
NEG_FIN = (0x80000000, 0xff7fffff)
TOP = {'sqrt32': 0x80000000, 'rsqrt32': 0x80000000, 'narrow': 0x100000000, 'exp32': 0x100000000}
TOTAL = {'sqrt32': 2139095040, 'rsqrt32': 2139095039, 'narrow': 21390950393, 'exp32': 3258020376}
FIELDS = {'sqrt32': ['n', 'bad_narrow', 'unfaithful', 'not_cr', 'first'], 'exp32': ['n', 'bad_narrow', 'unfaithful', 'amb', 'not_cr', 'first']}
FIELDS['rsqrt32'] = FIELDS['narrow'] = FIELDS['sqrt32']
ZERO = {'sqrt32': ['bad_narrow', 'unfaithful', 'not_cr'], 'rsqrt32': ['bad_narrow', 'unfaithful'], 'narrow': ['bad_narrow', 'unfaithful'], 'exp32': ['bad_narrow', 'unfaithful', 'amb']}
# ---- copied from orl/exp_exhaust.py (held to the live file below)
EXH = ['TINY = 0x30800000            # 2^-30',
       'UNDER = 0x42D00000           # 104.0',
       "SEGS = [(0x00000000, 0x00000000, 'zero'), (0x00000001, TINY, 'pos'), (TINY + 1, XMAX_U, 'dec'),",
       "        (0x80000000, 0x80000000, 'zero'), (0x80000001, 0x80000000 | TINY, 'neg'),",
       "        (0x80000000 | (TINY + 1), 0x80000000 | (UNDER - 1), 'dec'), (0x80000000 | UNDER, 0xFF7FFFFF, 'under')]"]
TINY = 0x30800000
UNDER = 0x42D00000
SEGS = [(0x00000000, 0x00000000, 'zero'), (0x00000001, TINY, 'pos'), (TINY + 1, XMAX_U, 'dec'),
        (0x80000000, 0x80000000, 'zero'), (0x80000001, 0x80000000 | TINY, 'neg'),
        (0x80000000 | (TINY + 1), 0x80000000 | (UNDER - 1), 'dec'), (0x80000000 | UNDER, 0xFF7FFFFF, 'under')]
# ----
EXH_FIELDS = ['chunk', 'n', 'shortcut_n', 'decimal_n', 'not_faithful', 'ambiguous', 'first']

def count_range(lo, hi, ranges):
    """count of u in [lo, hi] within the union of the inclusive (disjoint) ranges"""
    n = 0
    for a, b in ranges:
        l, h = max(lo, a), min(hi, b)
        if l <= h: n += h - l + 1
    return n

def expected(fn, lo, hi):
    if fn == 'sqrt32': return count_range(lo, hi, [POS_FIN])
    if fn == 'rsqrt32': return count_range(lo, hi, [(1, 0x7f7fffff)])
    if fn == 'exp32': return count_range(lo, hi, [(0, XMAX_U), NEG_FIN])
    n = 5 * count_range(lo, hi, [POS_FIN, NEG_FIN])        # narrow: five values a pattern, less those of magnitude >= FLT_MAX:
    if lo <= 0x7f7fffff <= hi: n -= 5                      # all five at the largest positive pattern,
    if lo <= 0xff7fffff <= hi: n -= 2                      # two at the largest negative one
    return n

def sha(path):
    with open(path, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()

def check_sweep(lines, fns):
    """lines of a sweeps- or sweep2- log. Returns (defects, summary per function)."""
    bad = []; by = {}
    for i, l in enumerate(lines):
        f = l.split()
        if not f: continue
        try:
            fn = f[0]; lo, hi = int(f[1], 16), int(f[2], 16); kv = [x.split('=') for x in f[3:]]
            assert fn in fns and len(f[1]) == 8 and len(f[2]) == 8 and [k for k, _ in kv] == FIELDS[fn] and lo <= hi
            d = {k: int(v, 16 if k == 'first' else 10) for k, v in kv}
        except (AssertionError, ValueError, IndexError, KeyError):
            bad.append('line %d is not a chunk line of %s: %r' % (i + 1, '/'.join(fns), l[:80])); continue
        by.setdefault(fn, []).append((lo, hi, d))
    summ = {}
    for fn in fns:
        ch = sorted(by.get(fn, []), key=lambda c: (c[0], c[1]))
        if not ch: bad.append('%s: no chunk in the log' % fn); summ[fn] = (0, 0); continue
        if ch[0][0] != 0: bad.append('%s: the first chunk starts at %08x, not 0' % (fn, ch[0][0]))
        if ch[-1][1] != TOP[fn] - 1: bad.append('%s: the last chunk ends at %08x, not %08x' % (fn, ch[-1][1], TOP[fn] - 1))
        for a, b in zip(ch, ch[1:]):
            if (a[0], a[1]) == (b[0], b[1]): bad.append('%s: chunk %08x..%08x stands twice' % (fn, a[0], a[1]))
            elif a[1] + 1 < b[0]: bad.append('%s: patterns %08x..%08x are in no chunk' % (fn, a[1] + 1, b[0] - 1))
            elif a[1] + 1 > b[0]: bad.append('%s: chunks %08x..%08x and %08x..%08x overlap' % (fn, a[0], a[1], b[0], b[1]))
        for lo, hi, d in ch:
            e = expected(fn, lo, hi)
            if d['n'] != e: bad.append('%s: chunk %08x..%08x reports n=%d, its range holds %d' % (fn, lo, hi, d['n'], e))
            for k in ZERO[fn]:
                if d[k]: bad.append('%s: chunk %08x..%08x has %s=%d' % (fn, lo, hi, k, d[k]))
        tot = sum(d['n'] for _, _, d in ch)
        if tot != TOTAL[fn]: bad.append('%s: %d inputs in all, not %d' % (fn, tot, TOTAL[fn]))
        summ[fn] = (len(ch), tot)
    return bad, summ

def exh_expected(c):
    lo = c << 20; hi = lo + (1 << 20) - 1
    return (count_range(lo, hi, [(a, b) for a, b, k in SEGS]), count_range(lo, hi, [(a, b) for a, b, k in SEGS if k != 'dec']),
            count_range(lo, hi, [(a, b) for a, b, k in SEGS if k == 'dec']))

def check_exhaust(lines, head, full):
    """lines of an exp-exhaust log (the first is its header). full: every chunk 000..fff once; otherwise a partial (plant) log."""
    bad = []; seen = {}
    if not lines or lines[0] != head: bad.append('the header is not the one of the current sweep2.c and sweep2.exe: %r' % (lines[0][:120] if lines else ''))
    for i, l in enumerate(lines[1:]):
        f = l.split()
        if not f: continue
        try:
            kv = [x.split('=') for x in f]; assert [k for k, _ in kv] == EXH_FIELDS and len(kv[0][1]) == 3
            d = dict(kv); c = int(d['chunk'], 16); v = [int(d[k]) for k in EXH_FIELDS[1:6]]
        except (AssertionError, ValueError, IndexError):
            bad.append('line %d is not a chunk line: %r' % (i + 2, l[:80])); continue
        if c in seen: bad.append('chunk %03x stands twice' % c); continue
        seen[c] = v
        e = exh_expected(c)
        if tuple(v[:3]) != e: bad.append('chunk %03x reports n=%d shortcut_n=%d decimal_n=%d, its range holds %d = %d + %d' % ((c,) + tuple(v[:3]) + e))
        if full and (v[3] or v[4]): bad.append('chunk %03x has not_faithful=%d ambiguous=%d' % (c, v[3], v[4]))
        if not full and v[3] != v[0]: bad.append('chunk %03x of the plant log: not_faithful=%d of n=%d' % (c, v[3], v[0]))
    tot = sum(v[0] for v in seen.values())
    if full:
        miss = [c for c in range(4096) if c not in seen]
        if miss: bad.append('%d chunks are not in the log (first %03x)' % (len(miss), miss[0]))
        if tot != TOTAL['exp32']: bad.append('%d inputs in all, not %d' % (tot, TOTAL['exp32']))
    elif not seen: bad.append('no chunk in the log')
    return bad, (len(seen), tot)

def emit_tally_accepts(lines, fns, nchunks):
    """emit.py's own criterion for a sweeps log (emit2.py's for exp32 adds the total): the line count and the bad counters"""
    tot = {}
    for l in lines:
        f = l.split()
        if not f: continue
        d = tot.setdefault(f[0], {'chunks': 0, 'n': 0, 'bad': 0}); d['chunks'] += 1
        kv = dict(x.split('=') for x in f[3:]); d['n'] += int(kv['n']); d['bad'] += int(kv['bad_narrow']) + int(kv['unfaithful']) + int(kv.get('amb', 0))
    return set(tot) == set(fns) and all(d['chunks'] == nchunks and d['bad'] == 0 and (fns != ['exp32'] or d['n'] == TOTAL['exp32']) for d in tot.values())

def probe(exe, args):
    q = subprocess.run([exe, 'sweep'] + args, capture_output=True, text=True)
    for l in q.stdout.splitlines():
        for t in l.split():
            if t.startswith('n=') and not l.startswith('AMB'): return int(t[2:])
    return None

def main():
    rd = lambda p: open(p, encoding='utf-8', newline='').read().split('\n')
    def body(p):
        L = rd(p)
        return L[:-1] if L and L[-1] == '' else L
    key = sha(os.path.join(GEN, 'sweep.c'))[:16]; key2 = sha(os.path.join(GEN, 'sweep2.c'))[:16]
    print('gen/sweep.c key %s; gen/sweep2.c key %s' % (key, key2))
    req = []; ok = True
    # ---- the count rules against the live programs
    sw, sw2 = os.path.join(GEN, 'sweep.exe'), os.path.join(GEN, 'sweep2.exe')
    P = [('narrow', a, b) for a, b in ((0x7f7fffff, 0x7f7fffff), (0xff7fffff, 0xff7fffff), (0x7f7ffffe, 0x7f7ffffe), (0xff7ffffe, 0xff7ffffe), (0, 0), (0x80000000, 0x80000000),
                                       (0x7f800000, 0x7f800000), (0xffffffff, 0xffffffff), (0x7f7fff00, 0x800000ff), (0xff7fff00, 0xffffffff), (0x3f800000, 0x3f8003ff))]
    P += [('sqrt32', 0, 0), ('rsqrt32', 0, 0), ('sqrt32', 0x7f7ffff0, 0x8000000f), ('rsqrt32', 0x7f7ffff0, 0x8000000f), ('rsqrt32', 0, 0xfff),
          ('exp32', XMAX_U - 15, XMAX_U + 16), ('exp32', 0x7ffffff0, 0x8000000f), ('exp32', 0xff7ffff0, 0xff80000f), ('exp32', 0, 0)]
    got = [probe(sw2, ['%x' % a, '%x' % b]) if fn == 'exp32' else probe(sw, [fn, '%x' % a, '%x' % b]) for fn, a, b in P]
    wrong = [(fn, '%08x' % a, '%08x' % b, g, expected(fn, a, b)) for (fn, a, b), g in zip(P, got) if g != expected(fn, a, b)]
    print('count rules against the live programs on %d small ranges: %d differ%s; narrow at 7f7fffff: n=%s, at ff7fffff: n=%s, at 7f7ffffe: n=%s' % (
        len(P), len(wrong), '' if not wrong else ' %s' % (wrong[:3],), got[0], got[1], got[2]))
    req.append(('the count rule of each function is what gen/sweep.exe and gen/sweep2.exe report on %d small ranges' % len(P), not wrong and None not in got))
    req.append(('the totals follow from the rules: %s' % ', '.join('%s %d' % (fn, TOTAL[fn]) for fn in TOP), all(expected(fn, 0, TOP[fn] - 1) == TOTAL[fn] for fn in TOP)))
    ex = rd(os.path.join(ORL, 'exp_exhaust.py'))
    req.append(('orl/exp_exhaust.py holds the segments copied here, line for line, and its XMAX_U and TOTAL',
                all(ex.count(l) == 1 for l in EXH) and ex.count('XMAX_U = 0x42B17217') == 1 and ex.count('TOTAL = 3258020376') == 1 and ex.count('NCHUNK = 4096') == 1
                and sum(b - a + 1 for a, b, _ in SEGS) == TOTAL['exp32'] and sum(exh_expected(c)[0] for c in range(4096)) == TOTAL['exp32']))
    # ---- the logs
    logs = [('sweeps-%s.log' % key, 'sweep', ['sqrt32', 'rsqrt32', 'narrow'], 64), ('sweep2-%s.log' % key2, 'sweep', ['exp32'], 256),
            ('exp-exhaust-%s.log' % key2, 'exhaust', True, 4096), ('exp-exhaust-plant-%s.log' % key2, 'exhaust', False, None)]
    held = {}
    for name, kind, arg, nch in logs:
        path = os.path.join(GEN, name)
        if not os.path.exists(path):
            req.append(('%s exists' % name, False)); continue
        L = body(path); held[name] = L
        if kind == 'sweep':
            bad, summ = check_sweep(L, arg)
            print('%s: %s' % (name, '; '.join('%s %d chunks, %d inputs' % (fn, summ[fn][0], summ[fn][1]) for fn in arg)))
            what = '%s: every line well formed; %s each tile [0, top) exactly, no chunk twice; every chunk\'s n as its range holds; totals %s; bad counters zero' % (
                name, ', '.join(arg), ', '.join('%d' % TOTAL[fn] for fn in arg))
        else:
            head = '# exp_exhaust sweep2.c %s sweep2.exe sha256 %s prec 40 eps 1e-30%s' % (key2, sha(sw2), '' if arg else ' PLANT two steps up')
            bad, summ = check_exhaust(L, head, arg)
            print('%s: %d chunks, %d inputs' % (name, summ[0], summ[1]))
            what = ('%s: header of the current sweep2.c and sweep2.exe; chunks 000..fff each exactly once; n, shortcut_n, decimal_n as each range holds; total %d; none not faithful or ambiguous' % (name, TOTAL['exp32'])
                    if arg else '%s (partial by design, %d chunks): header current; each chunk once; n, shortcut_n, decimal_n as each range holds; every input not faithful' % (name, summ[0]))
        for b in bad[:8]: print('   DEFECT %s' % b)
        if len(bad) > 8: print('   ... and %d more' % (len(bad) - 8))
        req.append((what, not bad))
    for name in sorted(os.listdir(GEN)):
        if name.endswith('.log') and (name.startswith('sweeps-') or name.startswith('sweep2-') or name.startswith('exp-exhaust-')) and name not in [l[0] for l in logs]:
            print('%s: a log of another key (not the current program): listed, not judged' % name)
    # ---- plants, on copies in memory
    def mutants(L, first):
        """(what, copy) for a list of chunk lines starting at index first; the chunk altered is in the middle"""
        k = first + (len(L) - first) // 2; f = L[k].split()
        j = next(i for i, t in enumerate(f) if t.startswith('n=')); g = list(f); g[j] = 'n=%d' % (int(f[j][2:]) - 1)
        return [('one chunk line removed', L[:k] + L[k + 1:]), ('one chunk\'s count altered (n less by one)', L[:k] + [' '.join(g)] + L[k + 1:]),
                ('one chunk replaced by a second copy of the one before it', L[:k] + [L[k - 1]] + L[k + 1:])]
    for name, kind, arg, nch in logs[:3]:
        if name not in held: continue
        L = held[name]; M = mutants(L, 0 if kind == 'sweep' else 1)
        if kind == 'exhaust':
            k = next(i for i, l in enumerate(L) if l.startswith('chunk=') and int(dict(x.split('=') for x in l.split())['decimal_n']) > 0); d = L[k].split()
            d[2] = 'shortcut_n=%d' % (int(d[2].split('=')[1]) + 1); d[3] = 'decimal_n=%d' % (int(d[3].split('=')[1]) - 1)
            M.append(('one input moved from decimal_n to shortcut_n', L[:k] + [' '.join(d)] + L[k + 1:]))
            head = L[0]
        for what, C in M:
            assert C != L
            bad = check_sweep(C, arg)[0] if kind == 'sweep' else check_exhaust(C, head, True)[0]
            note = ''
            if kind == 'sweep':
                acc = emit_tally_accepts(C, arg, nch)
                note = '; %s own tally %s this copy' % ('emit.py\'s' if nch == 64 else 'emit2.py\'s', 'ACCEPTS' if acc else 'refuses')
            print('plant %s, %s: %d defect%s%s%s' % (name, what, len(bad), '' if len(bad) == 1 else 's', ' (%s)' % bad[0] if bad else '', note))
            req.append(('plant: %s with %s fails' % (name, what), bool(bad)))
        clean = check_sweep(L, arg)[0] if kind == 'sweep' else check_exhaust(L, head, True)[0]
        if kind == 'sweep': req.append(('%s as it is: the authors\' own tally accepts it (the criterion copied here reads the log as they do)' % name, emit_tally_accepts(L, arg, nch) and not clean))
    for text, good in req:
        print('  %-4s %s' % ('ok' if good else 'FAIL', text)); ok &= bool(good)
    np = sum(1 for t, g in req if t.startswith('plant')); nc = sum(1 for t, g in req if t.startswith('plant') and g)
    print('SWEEP LOGS TILE %s: sweeps-%s.log (sqrt32, rsqrt32, narrow), sweep2-%s.log (exp32), exp-exhaust-%s.log and its plant log; %d of %d rows ok; plants failed as required %d of %d' % (
        'HELD' if ok else 'FAILED', key, key2, key2, sum(1 for t, g in req if g), len(req), nc, np))
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
