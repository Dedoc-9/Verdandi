# COQ GRAPH = C PROGRAM (2026-11-14, review finding F6).
# Nothing in the author's checks compared the Coq graph text (p32/Graphs.v, exp32/Graph.v: what the theorems are
# about) with a compiled program (what the sweeps and samples run). This test does, on sampled inputs: it reads the two
# .v files as text, evaluates their definitions exactly with rationals in the model they are written in (RN64 = round
# to nearest even in FLT(-1074, 53): no overflow, no sign of zero), and compares each value with what gen/sweep.exe and
# gen/sweep2.exe return in corpus mode for the same input, bit for bit, up to the sign of zero (which the model lacks).
#
# Where it came from: the reviewer's tier1-review/work2/coqeval.py (2026-11-14). Its rounding (mag, rne_int, rn,
# rn_sqrt), tokenizer, parser and evaluator are kept as they were written, and its input families and seed.
# What was changed, and why (each a weakness found on reading it):
#   1. it printed a summary and always exited 0; here there is one verdict line and an exit status.
#   2. it had no plant. Here the same comparison runs against copies of the Coq text, in memory, with one constant
#      changed, and must report differences in exactly the functions the constant reaches. (One constant change is
#      an equivalent mutant on these inputs, KK = 2^29 for 2^29 + 1: measured and printed, see main.)
#   3. a division by zero in the model returned 0 silently (its comment said "flagged by caller"; no caller did).
#      Here it raises.
#   4. RN64 was hard-wired as FLT(-1074, 53) nearest-even and the files' own Notation lines were never read, so a
#      changed Notation would have gone unseen. Here the Notation lines are held to their exact text (a row, and a
#      plant of it).
#   5. a Definition its pattern could not read was skipped without a word. Here the number of definitions read is held
#      to the number of the word Definition in each text.
#   6. the condition of an `if` was used for its truth as whatever value came back; here it must be a comparison.
#   7. a result of the C program that is not finite was counted with the differences; kept, and named separately; a
#      model value that is not a binary64 number raised an assertion; here it is counted (it is a difference).
#   8. a sign-of-zero difference is accepted only where the model's value is 0 (as before), and the count is printed.
#   9. dead code removed (an unused parameter, a first evaluation overwritten by the next line); sqrt32 of +0 added.
# What it does not show: anything on inputs not sampled; that the Coq text here is what coqc compiled (the gate's
# business); narrow at or above 2^128 - 2^103, where the model has no overflow and the machine does
# (evidence/narrow_top.py); agreement with the Orlog law (emit.py corpus, emit2.py corpus).
#   python -B graph_agree.py       prints COQ GRAPH = C PROGRAM HELD or FAILED, exit status 0 or 1. Writes nothing.
import hashlib, math, os, random, re, struct, subprocess, sys
from fractions import Fraction as F
HERE = os.path.dirname(os.path.abspath(__file__))
ORL = os.path.dirname(HERE); MKF = os.path.dirname(ORL)
GRAPHS, GRAPH = os.path.join(MKF, 'p32', 'Graphs.v'), os.path.join(MKF, 'exp32', 'Graph.v')
SWEEP, SWEEP2 = os.path.join(ORL, 'gen', 'sweep.exe'), os.path.join(ORL, 'gen', 'sweep2.exe')
NOTATIONS = ['Notation fexp64 := (FLT_exp (-1074) 53).', 'Notation format64 := (generic_format radix2 fexp64).',
             'Notation RN64 := (round radix2 fexp64 ZnearestE).']
NAMES = ['KK', 'MM', 'TT', 'HH', 'narrow', 'g_narrow', 'g_sqrt32', 'g_rsqrt32', 'g_hypot32', 'exp32_red', 'exp32_poly', 'exp32_sq', 'g_exp32']
FNS = ['narrow', 'sqrt32', 'rsqrt32', 'hypot32', 'exp32']

# ---------------------------------------------------------------- exact FLT rounding (the reviewer's, unchanged)
def mag(x):
    """e with 2^(e-1) <= |x| < 2^e, x a nonzero Fraction"""
    n, d = abs(x.numerator), x.denominator
    e = n.bit_length() - d.bit_length()
    while F(2) ** e <= abs(x): e += 1
    while F(2) ** (e - 1) > abs(x): e -= 1
    return e
def rne_int(m):
    """nearest integer to the Fraction m, ties to even"""
    fl = m.numerator // m.denominator; r = m - fl
    if r > F(1, 2) or (r == F(1, 2) and fl % 2): fl += 1
    return fl
def rn(x, emin, prec):
    if x == 0: return F(0)
    ex = max(mag(x) - prec, emin)
    return F(rne_int(x / F(2) ** ex)) * F(2) ** ex
class Sqrt:
    def __init__(self, x): self.x = x
def rn_sqrt(x, emin, prec):
    """nearest-even rounding of sqrt(x), x a nonnegative Fraction"""
    if x <= 0: return F(0)                       # Coq's sqrt is 0 on negatives
    e2 = mag(x); e = (e2 + 1) // 2               # 2^(e-1) <= sqrt(x) < 2^e when e2 = 2e or 2e-1
    while F(4) ** e <= x: e += 1
    while F(4) ** (e - 1) > x: e -= 1
    ex = max(e - prec, emin)
    y = x / F(4) ** ex                           # (sqrt(x) / 2^ex)^2
    m = math.isqrt(y.numerator // y.denominator) # floor(sqrt(y))
    half = (F(m) + F(1, 2)) ** 2
    if y > half or (y == half and m % 2): m += 1
    return F(m) * F(2) ** ex
def RN64(v): return rn_sqrt(v.x, -1074, 53) if isinstance(v, Sqrt) else rn(v, -1074, 53)
def RN32(v): return rn(v, -149, 24)

# ---------------------------------------------------------------- a parser for the graphs' expression language (the reviewer's)
TOK = re.compile(r'\s*(\d+|[A-Za-z_][A-Za-z_0-9]*|[()+\-*/])')
def tokens(s):
    out, i = [], 0
    s = s.strip()
    while i < len(s):
        m = TOK.match(s, i)
        if not m: raise SyntaxError('cannot read: ' + s[i:i + 30])
        out.append(m.group(1)); i = m.end()
    return out
class P:
    def __init__(self, toks): self.t, self.i = toks, 0
    def peek(self): return self.t[self.i] if self.i < len(self.t) else None
    def take(self, want=None):
        x = self.peek()
        if x is None or (want is not None and x != want): raise SyntaxError('wanted %r, found %r' % (want, x))
        self.i += 1; return x
    def expr(self):
        if self.peek() == 'if':
            self.take(); c = self.expr(); self.take('then'); a = self.expr(); self.take('else'); b = self.expr()
            return ('if', c, a, b)
        e = self.term()
        while self.peek() in ('+', '-'):
            op = self.take(); e = (op, e, self.term())
        return e
    def term(self):
        e = self.app()
        while self.peek() in ('*', '/'):
            op = self.take(); e = (op, e, self.app())
        return e
    def is_atom_start(self):
        x = self.peek()
        return x is not None and (x == '(' or x[0].isdigit() or (x[0].isalpha() or x[0] == '_') and x not in ('then', 'else', 'if'))
    def app(self):
        if self.peek() == '-':                      # unary minus on an application
            self.take(); return ('neg', self.app())
        h = self.atom(); args = []
        while self.is_atom_start(): args.append(self.atom())
        return ('app', h, args) if args else h
    def atom(self):
        x = self.take()
        if x == '(':
            e = self.expr(); self.take(')'); return e
        if x[0].isdigit(): return ('num', int(x))
        if x in ('then', 'else', 'if') or not (x[0].isalpha() or x[0] == '_'): raise SyntaxError('unexpected %r' % x)
        return ('id', x)
def load(text, defs):
    """reads every Definition of text into defs; returns how many it read and how many times the word stands in the text"""
    text = re.sub(r'\(\*.*?\*\)', ' ', text, flags=re.S); k = 0
    for m in re.finditer(r'Definition\s+(\w+)\s*((?:\([^)]*\)\s*)*):\s*R\s*:=(.*?)\.\s*(?=\n|$)', text, flags=re.S):
        name, params, body = m.group(1), m.group(2), m.group(3)
        ps = []
        for g in re.findall(r'\(([^)]*)\)', params):
            names, ty = g.split(':'); assert ty.strip() == 'R', g
            ps += names.split()
        p = P(tokens(body)); e = p.expr(); assert p.peek() is None, (name, p.t[p.i:])
        assert name not in defs, 'defined twice: ' + name
        defs[name] = (ps, e); k += 1
    return k, len(re.findall(r'\bDefinition\b', text))
def ev(e, env, defs):
    k = e[0]
    if k == 'num': return F(e[1])
    if k == 'neg': return -ev(e[1], env, defs)
    if k == 'id':
        if e[1] in env: return env[e[1]]
        ps, body = defs[e[1]]; assert not ps, e
        return ev(body, {}, defs)
    if k in ('+', '-', '*', '/'):
        a, b = ev(e[1], env, defs), ev(e[2], env, defs)
        assert not isinstance(a, Sqrt) and not isinstance(b, Sqrt), 'a square root used unrounded'
        if k == '/' and b == 0: raise ZeroDivisionError('the model divides by zero (Coq leaves /0 unspecified)')
        return a + b if k == '+' else a - b if k == '-' else a * b if k == '*' else a / b
    if k == 'if':
        c = ev(e[1], env, defs); assert c is True or c is False, 'the condition of an if is not a comparison'
        return ev(e[2], env, defs) if c else ev(e[3], env, defs)
    if k == 'app':
        h = e[1]; assert h[0] == 'id', e
        f, args = h[1], e[2]
        if f == 'bpow':
            assert args[0] == ('id', 'radix2') and len(args) == 2, e
            return F(2) ** int(ev(args[1], env, defs))
        vals = [ev(a, env, defs) for a in args]
        if f == 'RN64': assert len(vals) == 1; return RN64(vals[0])
        if f == 'sqrt': assert len(vals) == 1; return Sqrt(vals[0])
        if f == 'Rabs': assert len(vals) == 1; return abs(vals[0])
        if f == 'Rle_dec': return vals[0] <= vals[1]
        if f == 'Rlt_dec': return vals[0] < vals[1]
        ps, body = defs[f]; assert len(ps) == len(vals), (f, ps, len(vals))
        return ev(body, dict(zip(ps, vals)), defs)
    raise ValueError(e)

def bits(d): return struct.unpack('<Q', struct.pack('<d', d))[0]
def dbl(b): return struct.unpack('<d', struct.pack('<Q', b))[0]
def f32(u): return struct.unpack('<f', struct.pack('<I', u))[0]
def r32(x): return struct.unpack('<f', struct.pack('<f', x))[0]
def sha(path):
    with open(path, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()
def native(exe, fn, rows):
    inp = '\n'.join(' '.join('%x' % bits(v) for v in r) for r in rows) + '\n'
    q = subprocess.run([exe, 'corpus', fn], input=inp, capture_output=True, text=True)
    out = q.stdout.split()
    if q.returncode != 0 or len(out) != len(rows): raise RuntimeError('%s corpus %s: exit %d, %d lines for %d inputs' % (os.path.basename(exe), fn, q.returncode, len(out), len(rows)))
    return [dbl(int(o, 16)) for o in out]

OVF = 2.0 ** 128 - 2.0 ** 103
XMAX_U = 0x42B17217
def inputs():
    """the reviewer's families and seed; one list of rows per function"""
    rnd = random.Random(20261114); I = {}
    vals = [0.0, 2.0 ** -150, math.nextafter(2.0 ** -150, 0), math.nextafter(2.0 ** -150, 1), 2.0 ** -149, 1.5 * 2.0 ** -149, 2.5 * 2.0 ** -149,
            2.0 ** -126, math.nextafter(2.0 ** -126, 0), math.nextafter(2.0 ** -126, 1), 2.0 ** -126 - 2.0 ** -150, 5e-324, 2.0 ** -1022,
            1.0 + 2.0 ** -24, 1.0 + 3 * 2.0 ** -24, 1.0 - 2.0 ** -25, f32(0x7f7fffff), math.nextafter(OVF, 0)]
    for _ in range(6000):
        e = rnd.randint(-160, 127); vals.append(math.ldexp(1.0 + rnd.random(), e))
    for _ in range(3000):
        u = rnd.randrange(0, 0x7f7fffff); m = 0.5 * (f32(u) + f32(u + 1)); vals += [m, math.nextafter(m, 0), math.nextafter(m, math.inf)]
    vals = [v for v in vals if abs(v) < OVF]
    I['narrow'] = [[v] for v in vals] + [[-v] for v in vals]
    us = [1, 2, 0x007fffff, 0x00800000, 0x00800001, 0x3f800000, 0x3f7fffff, 0x3f800001, 0x7f7fffff, 0x7f7ffffe] + [rnd.randrange(1, 0x7f800000) for _ in range(6000)]
    I['rsqrt32'] = [[f32(u)] for u in us]
    I['sqrt32'] = [[0.0]] + I['rsqrt32']
    rows = []
    for _ in range(6000):
        a, b = rnd.randrange(0, 0x7f800000), rnd.randrange(0, 0x7f800000)
        rows.append([f32(a) * rnd.choice((1, -1)), f32(b) * rnd.choice((1, -1))])
    for _ in range(2000):
        a = rnd.randrange(0, 0x7f800000); e = min(max((a >> 23) + rnd.randint(-2, 2), 0), 0xfe)
        rows.append([f32(a), f32((e << 23) | rnd.getrandbits(23))])
    I['hypot32'] = rows
    xs = [0.0, -0.0, f32(1), -f32(1), 1.0, -1.0, f32(XMAX_U), f32(XMAX_U - 1), -160.0, f32(0xc3200001), f32(0xc31fffff), -161.0, -1000.0, -f32(0x7f7fffff), -103.9, -104.0]
    xs = [r32(x) for x in xs] + [r32(rnd.uniform(-170.0, 88.72)) for _ in range(2500)]
    xs += [f32(rnd.randrange(0, XMAX_U + 1)) for _ in range(1500)] + [-f32(rnd.randrange(0, 0x7f800000)) for _ in range(1500)]
    I['exp32'] = [[x] for x in xs if x <= f32(XMAX_U)]
    return I

def compare(defs, I, got):
    """per function: [same bits, equal with the sign of zero different, different, C not finite, first difference]"""
    res = {}
    for fn in FNS:
        ps, body = defs['g_' + fn]; same = zs = diff = nonfin = 0; first = None
        for r, g in zip(I[fn], got[fn]):
            m = ev(body, dict(zip(ps, [F(v) for v in r])), defs)
            if g != g or g in (float('inf'), float('-inf')):
                nonfin += 1; first = first or (r, m, g); continue
            try: mf = float(m)
            except OverflowError: mf = None
            if mf is not None and F(mf) == m and mf == g:
                if bits(mf) == bits(g): same += 1
                elif m == 0: zs += 1
                else: diff += 1; first = first or (r, m, g)
            else:
                diff += 1; first = first or (r, m, g)
        res[fn] = [same, zs, diff, nonfin, first]
    return res

def show(tag, res, I):
    for fn in FNS:
        same, zs, diff, nonfin, first = res[fn]
        f = ''
        if first is not None:
            try: mm = float(first[1]).hex()
            except OverflowError: mm = 'above binary64'
            f = ' | first: %s -> model %s, C %s' % ([x.hex() for x in first[0]], mm, first[2].hex() if first[2] == first[2] else 'nan')
        print('%s%-8s %6d inputs | C = Coq graph, bit for bit: %6d | equal, sign of zero differs: %4d | DIFFERENT: %6d | C not finite: %d%s' % (
            tag, fn, len(I[fn]), same, zs, diff, nonfin, f))

def once(a, old, new):
    assert a.count(old) == 1, 'the plant\'s target stands %d times in the text: %r' % (a.count(old), old)
    return a.replace(old, new)

def main():
    tg = open(GRAPHS, encoding='utf-8').read(); te = open(GRAPH, encoding='utf-8').read()
    print('p32/Graphs.v sha256 %s\nexp32/Graph.v sha256 %s\ngen/sweep.exe sha256 %s\ngen/sweep2.exe sha256 %s' % (sha(GRAPHS), sha(GRAPH), sha(SWEEP), sha(SWEEP2)))
    def notation_ok(a, b):
        la = [l for l in a.splitlines() if l.startswith('Notation')]; lb = [l for l in b.splitlines() if 'Notation' in l]
        return la == NOTATIONS and not lb and a.count('Notation') == 3 and b.count('From MKF.p32 Require Import Graphs.') == 1
    def read(a, b):
        defs = {}; ka, wa = load(a, defs); kb, wb = load(b, defs)
        return defs, (ka, wa, kb, wb)
    defs, cnt = read(tg, te)
    print('definitions read: %s (%d of %d in Graphs.v, %d of %d in Graph.v)' % (', '.join('%s/%d' % (n, len(ps)) for n, (ps, _) in defs.items()), cnt[0], cnt[1], cnt[2], cnt[3]))
    I = inputs()
    got = {fn: native(SWEEP2 if fn == 'exp32' else SWEEP, fn, I[fn]) for fn in FNS}
    res = compare(defs, I, got); show('', res, I)
    t32 = sum(1 for r in I['narrow'] if ev(defs['g_narrow'][1], {'x': F(r[0])}, defs) != RN32(F(r[0])))
    print('the model\'s narrow against rounding to binary32 in FLT(-149, 24), exactly, on the narrow inputs: %d of %d differ' % (t32, len(I['narrow'])))
    over = sum(1 for r in I['hypot32'] if ev(defs['g_hypot32'][1], {'x': F(r[0]), 'y': F(r[1])}, defs) >= F(2) ** 128)
    print('hypot32 pairs among these whose model value is at or above 2^128 (the graph and the program still agree there): %d' % over)
    req = [('the three Notation lines of Graphs.v are the ones this evaluator implements, and Graph.v has none of its own', notation_ok(tg, te)),
           ('every Definition of both texts was read (%d and %d), and they are the thirteen expected' % (cnt[1], cnt[3]), cnt[0] == cnt[1] and cnt[2] == cnt[3] and list(defs) == NAMES)]
    for fn in FNS:
        same, zs, diff, nonfin, _ = res[fn]
        req.append(('%s: the program equals the graph on every one of %d inputs (%d bit for bit, %d in the sign of zero only)' % (fn, len(I[fn]), same, zs),
                    diff == 0 and nonfin == 0 and same + zs == len(I[fn]) and same > 0))
    req.append(('the model\'s narrow is rounding to binary32 on every narrow input', t32 == 0))
    # ---- plants: the same comparison against copies of the Coq text, in memory, one constant changed
    # Run 1 of this test planted KK 536870913 -> 536870912 (2^29 + 1 -> 2^29) and required differences in all five
    # functions: it found none in any (graph-agree-run1-FAILED-plant-KK-2p29-is-equivalent.txt). On these inputs that
    # change is an equivalent mutant: (2^29 * v) - ((2^29 * v) - v) rounds v to 24 bits as the split by 2^29 + 1 does,
    # except where (2^29 * v) - v falls into the binade below, which no input here reaches. It is kept below as a
    # measured line, required of nothing; the required plant of KK is 2^28 + 1 (emit.py's own PLANT_NARROW constant).
    eq = compare(read(once(tg, 'Definition KK : R := 536870913.', 'Definition KK : R := 536870912.'), te)[0], I, got)
    print('measured, required of nothing: Graphs.v with KK 536870913 -> 536870912 differs from the program on %s inputs (%s): %s' % (
        ', '.join('%d' % (eq[fn][2] + eq[fn][3]) for fn in FNS), ', '.join(FNS),
        'an equivalent mutant on these inputs; this comparison says nothing of that constant\'s last bit' if not any(eq[fn][2] + eq[fn][3] for fn in FNS) else 'not equivalent here'))
    plants = [('Graphs.v: KK 536870913 -> 268435457', once(tg, 'Definition KK : R := 536870913.', 'Definition KK : R := 268435457.'), te, FNS),
              ('Graphs.v: g_rsqrt32\'s 1 -> 2', once(tg, 'narrow (RN64 (1 / (RN64 (sqrt x)))).', 'narrow (RN64 (2 / (RN64 (sqrt x)))).'), te, ['rsqrt32']),
              ('Graph.v: exp32_poly\'s 2520 -> 2521', tg, once(te, '(RN64 (2520 + ', '(RN64 (2521 + '), ['exp32']),
              ('Graph.v: exp32_red\'s 4096 -> 4095', tg, once(te, ' / 4096).', ' / 4095).'), ['exp32'])]
    for name, a, b, reach in plants:
        pd, pc = read(a, b); pres = compare(pd, I, got); show('  plant ', pres, I)
        hit = all(pres[fn][2] + pres[fn][3] > 0 for fn in reach); rest = all(pres[fn][:4] == res[fn][:4] for fn in FNS if fn not in reach)
        req.append(('plant %s: differences reported in %s (%s)%s' % (name, ', '.join(reach), ', '.join('%d' % (pres[fn][2] + pres[fn][3]) for fn in reach),
                                                                    '' if len(reach) == len(FNS) else '; the other functions as in the honest run'), hit and rest and notation_ok(a, b)))
    req.append(('plant Graphs.v: Notation fexp64\'s 53 -> 24: refused by the Notation row',
                not notation_ok(once(tg, 'Notation fexp64 := (FLT_exp (-1074) 53).', 'Notation fexp64 := (FLT_exp (-1074) 24).'), te)))
    req.append(('the real files were not written: their bytes are as read at the start', open(GRAPHS, encoding='utf-8').read() == tg and open(GRAPH, encoding='utf-8').read() == te))
    ok = True
    for text, good in req:
        print('  %-4s %s' % ('ok' if good else 'FAIL', text)); ok &= bool(good)
    print('COQ GRAPH = C PROGRAM %s: %s; plants caught %d of %d' % ('HELD' if ok else 'FAILED',
          '; '.join('%s %d inputs %d differ (%d in the sign of zero only, accepted)' % (fn, len(I[fn]), res[fn][2] + res[fn][3], res[fn][1]) for fn in FNS),
          sum(1 for t, g in req if t.startswith('plant') and g), sum(1 for t, g in req if t.startswith('plant'))))
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
