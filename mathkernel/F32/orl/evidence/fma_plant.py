# FMA CONTRACTION PLANT (2026-11-15). A permanent negative control: the tier's five functions (narrow, sqrt32, rsqrt32,
# hypot32, exp32) built with a fused multiply-add where the definitions have a multiply and then an add or subtract,
# and put to the references the tier's own checks use. The tier's contract is binary64 +, -, *, /, sqrt, each rounded
# once; a fused a*b+c rounds once where the contract rounds twice, so a build that contracts is a different function.
#   python -B fma_plant.py [--record FILE]     one verdict line, last: FMA PLANT HELD or FMA PLANT FAILED; exit 0 or 1
#   python -B fma_plant.py --break NAME        the test's own plants (BREAKS below): a run that must end FAILED, never HELD
# What it does, all in a temporary folder outside the tree (nothing under mkf/ is written but FILE, if asked for):
#   1. copies orl/emit.py and orl/emit2.py there and runs them: they write gen/sweep.c, gen/sweep2.c and the corpus
#      laws with their inputs, each held to the tier's orl/gen/ file byte for byte. The contraction sites are listed
#      from the emitters' own expression trees (an add or subtract with a product as an operand) and from the
#      generated narrow line; the sites that exist only across statements (a product in one statement, its add in
#      another) are named too.
#   2. builds the generated sources, each function behind one exported symbol (the generated file is included as it
#      is, its main renamed; the wrapper adds no arithmetic), ten times:
#        normal    clang -O2 -ffp-contract=off -fno-math-errno          the tier's flags
#        offmfma   the tier's flags and -mfma                           control: the instruction is there to use, unused
#        fast      -ffp-contract=fast -mfma                             PLANT: the compiler contracts where it chooses
#        dropped   -O2 -mfma -fno-math-errno (no -ffp-contract flag)    PLANT: what dropping the tier's flag gives there
#        n_outer   offmfma, narrow's  c - (c - v)  ->  fma(KK, v, -(c - v))            PLANT: explicit, outer use of KK*v
#        n_inner   offmfma, narrow's  c - (c - v)  ->  c - fma(KK, v, -v)              PLANT: explicit, inner use
#        n_both    offmfma, narrow's  c - (c - v)  ->  fma(KK, v, -fma(KK, v, -v))     PLANT: explicit, both uses
#        x_ctl     offmfma, exp32's twelfth v * v moved into narrow_sq(u), a copy of narrow    control of the next two
#        x_mm      x_ctl with  (v + MM) - MM  ->  fma(u, u, MM) - MM                   PLANT: explicit, across statements
#        x_cv      x_ctl with  c - (c - v)    ->  c - fma(-u, u, c)                    PLANT: explicit, across statements
#      (the explicit plants are edits of copies of the generated text; narrow needs them because this compiler does not
#      fuse a product that has two uses, and the twelfth square of exp32 because it does not fuse across statements).
#   3. disassembles the objects (llvm-objdump) and counts fused multiply-add instructions in each function under test:
#      none in normal, offmfma and x_ctl; a planted build is a plant for a function only where that function holds
#      one. The arithmetic instructions of each function are printed in address order, and fast and dropped are held
#      to normal's with exactly the functions' own sites fused.
#   4. runs every build on stated, seeded input sets and compares the result bits with: the emitters' Python graph
#      (py_narrow(py_eval(...)), py_narrow(py_g(x)): what emit.py corpus and emit2.py corpus compare with), the Coq
#      graph evaluated exactly (graph_agree.py's evaluator and its comparison, on p32/Graphs.v and exp32/Graph.v), for
#      narrow the IEEE conversion (narrow_regress.py's), and for hypot32 hypot_check2.py's exact faithfulness. Input
#      sets, the tier's own: the emitters' corpus inputs, graph_agree.inputs(), narrow_regress.inputs(),
#      hypot_check2.sample(); then, build against build in one program, every input of exp32, sqrt32 and rsqrt32; the
#      two inputs of exp32 that scan finds, pinned in this file (PINNED_EXP32) and held to what the scan finds now;
#      and constructed inputs (below).
#   5. expected: normal, offmfma and x_ctl agree with every reference on every input; a planted build is refused
#      (differs on at least one input of the function's domain) for every function it contracts, or it is an
#      equivalent mutant there and the run says which inputs distinguish it or why none can. fast and dropped are
#      also held, bit for bit, to the emitters' graphs with the fused sites rounded once (exact arithmetic): what a
#      contraction computes.
#      x_mm and x_cv are also run through narrow_sq's own symbol on constructed values of the number squared, against
#      their control: a plant no input of exp32 distinguishes is still shown to be live. normal is held to the tier's
#      linked gen/sweep.exe and gen/sweep2.exe (corpus mode) on every input of every set.
# What it does not show: anything about a compiler, a target or flags other than these (another compiler may fuse
# other sites, or narrow's); a fused 7.0 + x * 2^-12 in exp32 (no plant: the product is exact, so it is the same
# value); the Orlog backends (their programs are not rebuilt here); that the tier's linked gen/sweep.exe and
# gen/sweep2.exe hold no contraction (evidence/FMA-LINKED.md); inputs not listed. The Python graph, the Coq graph and
# the faithfulness checks are the tier's references, taken as they are: this test adds no reference of its own (the
# fused graphs describe the plant, they judge nothing). The exact arithmetic in construct_* only proposes inputs; what
# is reported about them is what the builds returned.
import sys
sys.dont_write_bytecode = True          # the tier's modules are imported below: nothing may be written beside them
import array, concurrent.futures, decimal, hashlib, json, math, os, re, shutil, struct, subprocess, tempfile, traceback
from fractions import Fraction as F
HERE = os.path.dirname(os.path.abspath(__file__))
ORL = os.path.dirname(HERE); MKF = os.path.dirname(ORL)
sys.path[:0] = [HERE, ORL]
import graph_agree as ga, hypot_check2 as h2, narrow_regress as nr      # the tier's checks: their inputs and references

FNS = ['narrow', 'sqrt32', 'rsqrt32', 'hypot32', 'exp32']
TIER_FLAGS = ['-O2', '-ffp-contract=off', '-fno-math-errno']
QUIET = ['-D_CRT_SECURE_NO_WARNINGS']                # diagnostics only; the tier's evidence scripts pass it too
NARROW_LINE = ('static double narrow(double v) { if (fabs(v) <= HH) return v * 0.0; if (fabs(v) < TT) return (v + MM) - MM; '
               'double c = KK * v; return c - (c - v); }')
TAIL = 'double c = KK * v; return c - (c - v); }'
PATCH = {'n_outer': 'double c = KK * v; return __builtin_fma(KK, v, -(c - v)); }',
         'n_inner': 'double c = KK * v; return c - __builtin_fma(KK, v, -v); }',
         'n_both': 'return __builtin_fma(KK, v, -__builtin_fma(KK, v, -v)); }'}
VARIANTS = [   # tag, flags, the patch of the generated text (PATCH: narrow; XPATCH: exp32), planted or not, what it is
    ('normal', TIER_FLAGS, None, False, "the tier's flags"),
    ('offmfma', TIER_FLAGS + ['-mfma'], None, False, "control: the tier's flags on a target that has FMA"),
    ('fast', ['-O2', '-ffp-contract=fast', '-mfma', '-fno-math-errno'], None, True, 'PLANT: the compiler contracts where it chooses'),
    ('dropped', ['-O2', '-mfma', '-fno-math-errno'], None, True, "PLANT: the tier's flags without -ffp-contract=off, on a target that has FMA"),
    ('n_outer', TIER_FLAGS + ['-mfma'], 'n_outer', True, 'PLANT: explicit fma at the outer use of KK*v in narrow'),
    ('n_inner', TIER_FLAGS + ['-mfma'], 'n_inner', True, 'PLANT: explicit fma at the inner use of KK*v in narrow'),
    ('n_both', TIER_FLAGS + ['-mfma'], 'n_both', True, 'PLANT: explicit fma at both uses of KK*v in narrow'),
    ('x_ctl', TIER_FLAGS + ['-mfma'], 'x_ctl', False, "control of the two plants below: exp32's twelfth v * v moved into narrow_sq, a copy of narrow; nothing fused"),
    ('x_mm', TIER_FLAGS + ['-mfma'], 'x_mm', True, "PLANT: explicit fma across statements in exp32, the twelfth v * v into narrow's v + MM"),
    ('x_cv', TIER_FLAGS + ['-mfma'], 'x_cv', True, "PLANT: explicit fma across statements in exp32, the twelfth v * v into narrow's c - v"),
]
COMPILER_PLANTS = ('fast', 'dropped'); NARROW_PLANTS = ('n_outer', 'n_inner', 'n_both'); X_PLANTS = ('x_mm', 'x_cv')
# The sites across statements, exp32 alone: in a copy of the generated sweep2.c the twelfth squaring leaves g_exp32 for
# narrow_sq, narrow's text with the value to square as its argument (x_ctl: the same operations in the same order as
# the generated code, nothing fused); the two plants fuse that product into the one add or subtract it is an operand of.
LAST_SQ = '  v = (v * v);\n  return v; }'
NSQ = 'static double narrow_sq(double u) { double v = u * u; if (fabs(v) <= HH) return v * 0.0; if (fabs(v) < TT) return %s; double c = KK * v; return %s; }'
XPATCH = {'x_ctl': NSQ % ('(v + MM) - MM', 'c - (c - v)'),
          'x_mm': NSQ % ('__builtin_fma(u, u, MM) - MM', 'c - (c - v)'),
          'x_cv': NSQ % ('(v + MM) - MM', 'c - __builtin_fma(-u, u, c)')}
XSHOW = {'x_ctl': 'v = u * u; ... (v + MM) - MM; ... c - (c - v)', 'x_mm': 'v = u * u; ... __builtin_fma(u, u, MM) - MM', 'x_cv': 'v = u * u; ... c - __builtin_fma(-u, u, c)'}
BREAKS = {   # the test's own plants: each breaks the apparatus in one way, and the run must then end FAILED
    'normal-contracted': ('the build called normal is compiled with the flags of fast', {'normal': ['-O2', '-ffp-contract=fast', '-mfma', '-fno-math-errno']}),
    'plant-uncontracted': ('fast and dropped are compiled without -mfma: the compiler has nothing to fuse with',
                           {'fast': ['-O2', '-ffp-contract=fast', '-fno-math-errno'], 'dropped': ['-O2', '-fno-math-errno']}),
}
THREADS = 8
CHUNK = 1 << 24
FMA = re.compile(r'^vfn?m(add|sub)\d*[sp][sd]\b')     # the four mnemonic families evidence/fma_scan.py counts
ARITH = [('F', FMA), ('m', re.compile(r'^v?mulsd\b')), ('a', re.compile(r'^v?(add|sub)sd\b')), ('d', re.compile(r'^v?divsd\b')), ('q', re.compile(r'^v?sqrtsd\b'))]
EMITTED = sorted(['sweep.c', 'sweep2.c'] + ['corpus_%s.%s' % (fn, x) for fn in FNS for x in ('json', 'orl')])
# The binary32 inputs (bit patterns) on which exp32 with its six polynomial steps fused differs from exp32: found by
# this test's scan of every input (2026-11-15, clang 22.1.8) and held, at every run, to what the scan finds then. They
# are pinned so that a build is put to the references on them whatever it is scanned against: a "normal" that
# contracts is then refused by the references on exp32 too, and not only by its disassembly.
PINNED_EXP32 = [0x41185934, 0xc251681b]

LIB1 = r'''// Written by fma_plant.py. The generated functions of sweep.c, each behind one exported symbol. No arithmetic here.
#define CAT_(a, b) a##b
#define CAT(a, b) CAT_(a, b)
#define main CAT(gen_main1__, TAG)
#include "%s"
#undef main
__attribute__((noinline)) double CAT(ut_narrow__, TAG)(double x) { return f_narrow(x); }
__attribute__((noinline)) double CAT(ut_sqrt32__, TAG)(double x) { return f_sqrt32(x); }
__attribute__((noinline)) double CAT(ut_rsqrt32__, TAG)(double x) { return f_rsqrt32(x); }
__attribute__((noinline)) double CAT(ut_hypot32__, TAG)(double x, double y) { return f_hypot32(x, y); }
'''
LIB2 = r'''// Written by fma_plant.py. The generated exp32 of sweep2.c behind one exported symbol: what sweep2.c's corpus
// mode prints the bits of, narrow(g_exp32(x)); in the x_ builds narrow_sq(g_exp32(x)) of the edited copy, and
// narrow_sq by itself behind a second symbol. No arithmetic here.
#define CAT_(a, b) a##b
#define CAT(a, b) CAT_(a, b)
#define main CAT(gen_main2__, TAG)
#include "%s"
#undef main
__attribute__((noinline)) double CAT(ut_exp32__, TAG)(double x) { return %s; }
%s'''
NSQ_WRAP = '__attribute__((noinline)) double CAT(ut_nsq__, TAG)(double u) { return narrow_sq(u); }\n'     # the x_ builds alone: narrow_sq by itself
CALL2 = 'narrow(g_exp32(x))'           # what sweep2.c's corpus mode calls; the x_ builds call narrow_sq(g_exp32(x)), their g_exp32 one squaring short
DRV = r'''// Written by fma_plant.py. Binary64 bit patterns in hex on standard input, one input per line (two patterns for
// hypot32); the bits of the result on standard output. No floating-point arithmetic here.
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define CAT_(a, b) a##b
#define CAT(a, b) CAT_(a, b)
double CAT(ut_narrow__, TAG)(double), CAT(ut_sqrt32__, TAG)(double), CAT(ut_rsqrt32__, TAG)(double), CAT(ut_exp32__, TAG)(double);
double CAT(ut_hypot32__, TAG)(double, double);
#ifdef NSQ
double CAT(ut_nsq__, TAG)(double);
#define NSQ_FN CAT(ut_nsq__, TAG)
#else
#define NSQ_FN 0
#endif
static double (*volatile p1[5])(double) = { CAT(ut_narrow__, TAG), CAT(ut_sqrt32__, TAG), CAT(ut_rsqrt32__, TAG), CAT(ut_exp32__, TAG), NSQ_FN };
static double (*volatile p2)(double, double) = CAT(ut_hypot32__, TAG);
static uint64_t tobits(double d) { uint64_t u; memcpy(&u, &d, 8); return u; }
static double ofbits(uint64_t u) { double d; memcpy(&d, &u, 8); return d; }
int main(int argc, char **argv) {
  static const char *names[6] = { "narrow", "sqrt32", "rsqrt32", "exp32", "nsq", "hypot32" };
  int w = -1; char line[128]; unsigned long long a, b;
  if (argc != 2) return 2;
  for (int i = 0; i < 6; i++) if (!strcmp(argv[1], names[i])) w = i;
  if (w < 0 || (w == 4 && !p1[4])) return 2;
  while (fgets(line, sizeof line, stdin)) { int k = sscanf(line, "%llx %llx", &a, &b); double r;
    if (k < (w == 5 ? 2 : 1)) return 3;
    if (w == 5) r = p2(ofbits(a), ofbits(b)); else r = p1[w](ofbits(a));
    printf("%016llx\n", (unsigned long long)tobits(r)); }
  return 0; }
'''
SCAN = r'''// Written by fma_plant.py. One function of one input as two builds made it (FA, FB: two objects linked into this
// program), over a range of binary32 patterns, result bits against result bits. Called through volatile pointers.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
double FA(double), FB(double);
static double (*volatile pa)(double) = FA;
static double (*volatile pb)(double) = FB;
int main(int argc, char **argv) {
  if (argc != 3) return 2;
  uint32_t lo = (uint32_t)strtoul(argv[1], 0, 16), hi = (uint32_t)strtoul(argv[2], 0, 16); uint64_t n = 0, d = 0;
  double (*a)(double) = pa, (*b)(double) = pb;
  for (uint64_t uu = lo; uu <= hi; uu++) { uint32_t u = (uint32_t)uu; float f; double x, r, s; uint64_t rb, sb;
    memcpy(&f, &u, 4); x = (double)f; r = a(x); s = b(x); memcpy(&rb, &r, 8); memcpy(&sb, &s, 8); n++;
    if (rb != sb) { d++; if (d <= 256) printf("DIFF %08x %016llx %016llx\n", u, (unsigned long long)rb, (unsigned long long)sb); } }
  printf("END %08x %08x n=%llu differ=%llu\n", lo, hi, (unsigned long long)n, (unsigned long long)d);
  return 0; }
'''

class Stop(Exception): pass
LINES = []
def say(s=''):
    for l in str(s).split('\n'): LINES.append(l); print(l)
    sys.stdout.flush()
def sha(path):
    with open(path, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()
def run(cmd, cwd=None, inp=None):
    return subprocess.run(cmd, cwd=cwd, input=inp, capture_output=True, text=True)
def bits(d): return struct.unpack('<Q', struct.pack('<d', d))[0]
def dbl(b): return struct.unpack('<d', struct.pack('<Q', b))[0]
def hx(v): return '%s (bits %016x)' % (v.hex(), bits(v))
def scrub(s, T):
    for p, name in ((T, '<tmp>'), (MKF, '<tier>'), (os.path.expanduser('~'), '<home>'), (tempfile.gettempdir(), '<tmp>')):
        for q in (p, p.replace('\\', '/'), p.replace('/', '\\')): s = s.replace(q, name)
    return s

# ---------------------------------------------------------------- the tier's files: read, hashed, never written
WATCH = ['f32', 'p32', 'p32r', 'exp32', 'exp32r', 'gate', 'libcache', 'orl']      # mkf/ieee64 belongs to another task
def snapshot():
    snap = {}
    for d in WATCH:
        for root, dirs, files in os.walk(os.path.join(MKF, d)):
            for f in files:
                p = os.path.join(root, f)
                try: snap[os.path.relpath(p, MKF).replace(os.sep, '/')] = sha(p)
                except OSError: snap[os.path.relpath(p, MKF).replace(os.sep, '/')] = 'unreadable'
    return snap
def freeze_lists():
    """every line of the ten freeze lists against the file's sha256 now: (entries, the ones that do not match)"""
    n = 0; bad = []
    for d in ('f32', 'p32', 'p32r', 'exp32', 'exp32r'):
        for name in ('FROZEN.txt', 'FROZEN4.txt'):
            for line in open(os.path.join(MKF, d, name), encoding='utf-8').read().splitlines():
                if not line.strip() or line.startswith('#'): continue
                f = line.split('  ', 1); n += 1
                p = os.path.join(MKF, f[1].strip()) if len(f) == 2 else ''
                if len(f) != 2 or len(f[0]) != 64 or not os.path.isfile(p) or sha(p) != f[0]: bad.append('%s/%s: %s' % (d, name, line[66:]))
    return n, bad

# ---------------------------------------------------------------- the emitters' definitions, without running a command
def load_defs(path):
    """the module body of an emitter up to its last line, which is the command dispatch"""
    src = open(path, encoding='utf-8').read().splitlines()
    if not src[-1].startswith("{'emit': emit") or sum(l.startswith("{'emit': emit") for l in src) != 1:
        raise Stop('%s does not end in its command dispatch as read here' % os.path.basename(path))
    ns = {'__file__': path, '__name__': 'emitter_definitions'}
    exec(compile('\n'.join(src[:-1]) + '\n', os.path.basename(path), 'exec'), ns)
    return ns
def tree_sites(e):
    """every add or subtract of an expression tree that has a product as an operand: (node, how many operands are products)"""
    out = []
    if isinstance(e, tuple):
        if e[0] in ('add', 'sub'):
            k = sum(1 for i in (1, 2) if isinstance(e[i], tuple) and e[i][0] == 'mul')
            if k: out.append((e, k))
        for c in e[1:]: out += tree_sites(c)
    return out

# ---------------------------------------------------------------- building and disassembling
def build(T, tag, flags, patch, g1, g2):
    d = os.path.join(T, tag); os.makedirs(d)
    inc1, inc2, call2, extra2, nsq = '../gen/sweep.c', '../gen/sweep2.c', CALL2, '', []
    if patch in PATCH:
        for name, g in (('sweep.c', g1), ('sweep2.c', g2)):
            if g.count(TAIL) != 1: raise Stop('the text the plant %s replaces stands %d times in the generated %s' % (tag, g.count(TAIL), name))
            open(os.path.join(d, name), 'w', encoding='utf-8', newline='\n').write(g.replace(TAIL, PATCH[patch]))
        inc1, inc2 = 'sweep.c', 'sweep2.c'
    elif patch in XPATCH:
        if g2.count(LAST_SQ) != 1 or g2.count(NARROW_LINE + '\n') != 1 or g2.count('  v = (v * v);\n') != 12:
            raise Stop('the generated sweep2.c does not hold its twelve squarings and its narrow as the build %s reads them' % tag)
        text = g2.replace(LAST_SQ, '  return v; }').replace(NARROW_LINE + '\n', NARROW_LINE + '\n' + XPATCH[patch] + '\n')
        open(os.path.join(d, 'sweep2.c'), 'w', encoding='utf-8', newline='\n').write(text)
        inc2, call2, extra2, nsq = 'sweep2.c', 'narrow_sq(g_exp32(x))', NSQ_WRAP, ['-DNSQ']
    elif patch: raise Stop('no such patch: %s' % patch)
    for name, text in (('lib1.c', LIB1 % inc1), ('lib2.c', LIB2 % (inc2, call2, extra2)), ('drv.c', DRV)):
        open(os.path.join(d, name), 'w', encoding='utf-8', newline='\n').write(text)
    for src, fl in (('lib1', flags), ('lib2', flags), ('drv', TIER_FLAGS + nsq)):
        q = run(['clang'] + fl + QUIET + ['-DTAG=' + tag, '-c', src + '.c', '-o', src + '.o'], cwd=d)
        if q.returncode != 0: raise Stop('build %s: %s.c did not compile: %s' % (tag, src, (q.stdout + q.stderr).strip()[-400:]))
    q = run(['clang', 'lib1.o', 'lib2.o', 'drv.o', '-o', 'run.exe'], cwd=d)
    if q.returncode != 0: raise Stop('build %s did not link: %s' % (tag, (q.stdout + q.stderr).strip()[-400:]))
    return os.path.join(d, 'run.exe')
def listing(obj):
    """{symbol: {'insn': [text], 'rel': [relocation targets]}} of an object file"""
    q = run(['llvm-objdump', '-d', '-r', '--no-show-raw-insn', obj])
    if q.returncode != 0: raise Stop('llvm-objdump failed on an object file')
    syms = {}; cur = None
    for l in q.stdout.splitlines():
        m = re.match(r'^[0-9a-f]+ <(.+)>:$', l)
        if m: cur = syms.setdefault(m.group(1), {'insn': [], 'rel': []}); continue
        if cur is None: continue
        if 'IMAGE_REL' in l: cur['rel'].append(l.split()[-1]); continue
        m = re.match(r'^\s*[0-9a-f]+:\s+(\S.*)$', l)
        if m: cur['insn'].append(m.group(1).split('#')[0].strip())
    return syms
def facts(sym):
    ins = sym['insn']; f = [t for t in ins if FMA.match(t)]
    kinds = {}
    for t in f: kinds[t.split()[0]] = kinds.get(t.split()[0], 0) + 1
    skel = ''.join(next((c for c, rx in ARITH if rx.match(t)), '') for t in ins)      # the arithmetic instructions, in address order
    return {'n': len(ins), 'fma': len(f), 'kinds': ', '.join('%s x%d' % kv for kv in sorted(kinds.items())), 'skel': skel,
            'calls': sum(1 for t in ins if t.startswith('call')), 'ijmp': sum(1 for t in ins if re.match(r'jmp\w*\s+\*', t)),
            'foreign': sorted(set(r for r in sym['rel'] if not (r.startswith('__real@') or r.startswith('__xmm@'))))}
def shape(sym, tag):
    """a function's instructions and constants with the build's tag and the absolute jump targets taken out"""
    return [re.sub(r'0x[0-9a-f]+ <', '<', t).replace('__' + tag, '') for t in sym['insn']] + sorted(sym['rel'])

def body(T, brk):
    req = []; snap0 = snapshot()
    variants = [(tag, BREAKS[brk][1].get(tag, flags) if brk else flags, patch, planted, what) for tag, flags, patch, planted, what in VARIANTS]
    ver = run(['clang', '--version']).stdout.splitlines()
    over = [l.strip() for l in run(['llvm-objdump', '--version']).stdout.splitlines() if 'LLVM version' in l]
    if len(ver) < 2 or not over: raise Stop('clang or llvm-objdump is not on the path')
    say('FMA CONTRACTION PLANT: the tier\'s five functions built with fused multiply-add, against the tier\'s references')
    if brk: say('THE TEST\'S OWN PLANT (--break %s): %s. This run must end FMA PLANT FAILED.' % (brk, BREAKS[brk][0]))
    say('%s; %s; llvm-objdump %s; Python %d.%d' % (ver[0], ver[1], over[0], sys.version_info[0], sys.version_info[1]))
    used = ['orl/emit.py', 'orl/emit2.py', 'orl/gen/sweep.c', 'orl/gen/sweep2.c', 'orl/gen/sweep.exe', 'orl/gen/sweep2.exe', 'p32/Graphs.v', 'exp32/Graph.v',
            'orl/evidence/graph_agree.py', 'orl/evidence/narrow_regress.py', 'orl/hypot_check2.py']
    say('this test: orl/evidence/fma_plant.py sha256 %s' % sha(os.path.abspath(__file__)))
    say('the tier\'s files this run reads (sha256, first 16): ' + '; '.join('%s %s' % (u, sha(os.path.join(MKF, u))[:16]) for u in used))

    # ---- 1. generate
    env = dict(os.environ, PYTHONHASHSEED='0', PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    for name in ('emit.py', 'emit2.py'):
        shutil.copyfile(os.path.join(ORL, name), os.path.join(T, name))
        q = subprocess.run([sys.executable, '-B', name, 'emit'], cwd=T, capture_output=True, text=True, env=env)
        if q.returncode != 0: raise Stop('%s emit did not run in the temporary folder: %s' % (name, q.stderr.strip()[-300:]))
    g1 = open(os.path.join(T, 'gen', 'sweep.c'), encoding='utf-8').read(); g2 = open(os.path.join(T, 'gen', 'sweep2.c'), encoding='utf-8').read()
    say('\n1. generated in a temporary folder outside the tree by copies of orl/emit.py and orl/emit2.py (python -B emit.py emit; python -B emit2.py emit):')
    say('   gen/sweep.c sha256 %s\n   gen/sweep2.c sha256 %s' % (sha(os.path.join(T, 'gen', 'sweep.c')), sha(os.path.join(T, 'gen', 'sweep2.c'))))
    req += [('the emitters run in the temporary folder are the tier\'s orl/emit.py and orl/emit2.py, byte for byte',
             all(sha(os.path.join(T, n)) == sha(os.path.join(ORL, n)) for n in ('emit.py', 'emit2.py'))),
            ('run there, they write %d files (sweep.c, sweep2.c, the five corpus laws and their inputs) and no other, each the file the tier holds in orl/gen, byte for byte' % len(EMITTED),
             sorted(os.listdir(os.path.join(T, 'gen'))) == EMITTED and all(sha(os.path.join(T, 'gen', n)) == sha(os.path.join(ORL, 'gen', n)) for n in EMITTED)),
            ('both generated sources name the tier\'s flags on their Build line (clang %s)' % ' '.join(TIER_FLAGS),
             g1.splitlines().count('// Build: clang %s sweep.c -o sweep.exe' % ' '.join(TIER_FLAGS)) == 1
             and g2.splitlines().count('// Build: clang %s sweep2.c -o sweep2.exe' % ' '.join(TIER_FLAGS)) == 1),
            ('both hold the narrow read here, once, and no other definition of narrow',
             all(g.splitlines().count(NARROW_LINE) == 1 and sum(l.startswith('static double narrow(') for l in g.splitlines()) == 1 for g in (g1, g2)))]
    E1 = load_defs(os.path.join(T, 'emit.py')); E2 = load_defs(os.path.join(T, 'emit2.py'))
    if list(E1['FUNCS']) + ['exp32'] != FNS: raise Stop('the emitters define other functions than the five this test wraps: %s' % list(E1['FUNCS']))
    req.append(('the wrappers call what the generated corpus modes call (f_narrow, f_sqrt32, f_rsqrt32, f_hypot32; narrow(g_exp32(...)))',
                all(g1.count('r = f_%s(' % fn) == 1 and g1.count('static double f_%s(' % fn) == 1 for fn in FNS[:4]) and g2.count('bits(narrow(g_exp32(frombits(a))))') == 1))

    # ---- the sites
    say('\n   contraction sites (a product that is an operand of an add or subtract), from the emitters\' expression trees and the narrow line:')
    own = {}
    for fn in FNS[:4]:
        ins, e = E1['FUNCS'][fn]; s = tree_sites(e); own[fn] = len(s)
        say('   %-8s E = %-34s %s' % (fn, E1['c_expr'](e), 'no site in E' if not s else '; '.join(
            '%d site: %s (%s)' % (len(s), E1['c_expr'](n), 'either product can be the fused one' if k == 2 else 'one product') for n, k in s)))
    steps = list(E2['steps']()); es = [(t, e) for t, e in steps if e[0] != 'clamplo' and tree_sites(e)]; own['exp32'] = len(es)
    say('   %-8s %d steps; %d sites: %s; no site in the other %d steps (the clamp, x / 4096.0, 7.0 + r, n / 5040.0, twelve v * v)' % (
        'exp32', len(steps), len(es), ', '.join('%s = %s' % (t, E2['c_expr'](e)) for t, e in es), len(steps) - len(es)))
    say('   narrow   (every function ends in it)  %s' % TAIL[:-2])
    say('            one product, KK * v, with two uses: the outer subtraction c - (...) and the inner c - v. Each use is a site; fusing')
    say('            both recomputes the product. The other branches have none: v * 0.0 is a product alone, (v + MM) - MM has no product.')
    own['narrow'] = 2
    say('   across statements (the product in one statement, the add or subtract in a later one or, once inlined, in narrow; -ffp-contract=fast lets a compiler')
    say('            fuse these, the C rule for one expression does not): in exp32 the twelfth v * v is narrow\'s v, an operand of its v + MM and of its c - v;')
    say('            and x / 4096.0, where a compiler makes it x * 2^-12 (an exact product), is an operand of 7.0 + r (fused or not, the same value). In the')
    say('            other functions narrow\'s v is a square root, a quotient or the input itself: no such site. Whether a compiler build here fuses one is read')
    say('            from its instructions, under 2-3; the two of the twelfth v * v have explicit plants (x_mm, x_cv, with their control x_ctl); 7.0 + r has none.')
    say('   not under test: the arithmetic of the generated harness (the sweeps\' own reference side) and of the references.')

    # ---- 2. build, 3. disassemble
    say('\n2-3. builds and their fused multiply-add instructions (llvm-objdump -d -r of the objects that are then linked and run):')
    exe = {}; fact = {}; syms = {}; whole = {}; nsqf = {}
    for tag, flags, patch, planted, what in variants:
        exe[tag] = build(T, tag, flags, patch, g1, g2)
        L = {o: listing(os.path.join(T, tag, o + '.o')) for o in ('lib1', 'lib2', 'drv')}
        whole[tag] = sum(facts(s)['fma'] for o in L for s in L[o].values())
        for fn in FNS:
            name = 'ut_%s__%s' % (fn, tag); s = L['lib2' if fn == 'exp32' else 'lib1'].get(name)
            if s is None: raise Stop('build %s: the symbol %s is not in the object' % (tag, name))
            syms[tag, fn] = s; fact[tag, fn] = facts(s)
        if patch in XPATCH:                                            # narrow_sq by itself, behind a symbol of its own
            if 'ut_nsq__' + tag not in L['lib2']: raise Stop('build %s: the symbol ut_nsq__%s is not in the object' % (tag, tag))
            nsqf[tag] = facts(L['lib2']['ut_nsq__' + tag])
        say('   %-8s clang %s%s   [%s]' % (tag, ' '.join(flags), '' if not patch else '; narrow: ... %s' % PATCH[patch][:-2] if patch in PATCH else
                                           '; exp32: narrow_sq(u): %s' % XSHOW[patch], what))
        say('            ' + '; '.join('%s %d instr, FMA %d%s' % (fn, fact[tag, fn]['n'], fact[tag, fn]['fma'],
                                        '' if not fact[tag, fn]['fma'] else ' (%s)' % fact[tag, fn]['kinds']) for fn in FNS)
            + '; in the three objects together: %d' % whole[tag])
    same = all(shape(syms['dropped', fn], 'dropped') == shape(syms['fast', fn], 'fast') for fn in FNS)
    say('   dropped and fast: the five functions have the same instructions and constants in both builds: %s%s' % (
        'yes' if same else 'no', ' (so what the scan of every input finds for fast holds for dropped)' if same else ''))
    say('   the arithmetic instructions of each function, in address order (m multiply, a add or subtract, d divide, q square root, F fused multiply-add):')
    for tag in [v[0] for v in variants]:
        say('   %-8s %s' % (tag, '; '.join('%s %s' % (fn, fact[tag, fn]['skel']) for fn in FNS)))
    say('   read with the generated text: every function ends in narrow\'s a a | m a a (v + MM, - MM | KK * v, c - v, c - ...); hypot32 begins m m a q (x * x, y * y, +, sqrt);')
    say('   exp32 begins m a (x * 2^-12, 7.0 + r), then six m a (r * n, c + ...), d (n / 5040.0), twelve m (v * v). In fast and dropped an F stands for the m a it fused;')
    say('   in the explicit plants of narrow, whose product has two uses, an F stands for one a and the m stays (n_outer, n_inner), or for each a with no m left (n_both);')
    say('   in x_mm and x_cv the twelfth m stays too (narrow_sq needs v = u * u for its comparisons and for KK * v) and an F stands for v + MM, or for c - v.')
    m4096 = all('__real@3f30000000000000' in syms[tag, 'exp32']['rel'] and fact[tag, 'exp32']['skel'].count('d') == 1 for tag in [v[0] for v in variants])
    say('   exp32\'s x / 4096.0 is a multiplication by the constant 2^-12 in every build, n / 5040.0 its one division: %s' % ('yes' if m4096 else 'no'))
    say('   (the linked programs also hold the C runtime, whose own FMA paths are described in evidence/FMA-LINKED.md; not counted here)')
    req += [('normal (the tier\'s flags): no fused multiply-add in any function under test, nor anywhere in its three objects',
             whole['normal'] == 0 and all(fact['normal', fn]['fma'] == 0 for fn in FNS)),
            ('offmfma and x_ctl (the controls: the tier\'s flags on a target that has FMA): none either', whole['offmfma'] == 0 and whole['x_ctl'] == 0),
            ('x_ctl: its five functions have normal\'s arithmetic instructions, in normal\'s order (moving the twelfth squaring into narrow_sq changes none)',
             all(fact['x_ctl', fn]['skel'] == fact['normal', fn]['skel'] for fn in FNS)),
            ('every function under test, in every build: no call, no indirect jump, relocations to floating constants only (its listing is all of it)',
             all(f['calls'] == 0 and f['ijmp'] == 0 and not f['foreign'] for f in list(fact.values()) + list(nsqf.values())))]
    for tag in COMPILER_PLANTS:
        want = [fn for fn in FNS if fn != 'narrow' and own[fn]]
        req.append(('%s: a fused multiply-add in every function whose own expression has a site (%s)' % (tag, ', '.join(want)), all(fact[tag, fn]['fma'] > 0 for fn in want)))
        sites = {fn: 0 if fn == 'narrow' else own[fn] for fn in FNS}
        req.append(('%s: its arithmetic is normal\'s with the functions\' own sites fused and nothing else: each function holds as many fused multiply-adds as its expression has sites (%s), '
                    'and with each F read as m a its instructions are normal\'s; so the six c + r * n of exp32 are fused, and KK * v, the twelfth v * v and x * 2^-12 are not' % (
                        tag, ', '.join('%s %d' % (fn, sites[fn]) for fn in FNS)),
                    all(fact[tag, fn]['fma'] == sites[fn] and fact[tag, fn]['skel'].replace('F', 'ma') == fact['normal', fn]['skel'] for fn in FNS)
                    and fact[tag, 'exp32']['skel'] == 'ma' + 'F' * 6 + 'd' + 'm' * 12 + 'aamaa'))
    for tag in NARROW_PLANTS:
        req.append(('%s: a fused multiply-add in all five functions (each ends in narrow)' % tag, all(fact[tag, fn]['fma'] > 0 for fn in FNS)))
    for tag in X_PLANTS:
        req.append(('%s: one fused multiply-add in exp32, where the plant puts it (%s), and none in the other four functions, which it does not touch' % (
            tag, 'for narrow\'s v + MM' if tag == 'x_mm' else 'for narrow\'s c - v'),
            [fact[tag, fn]['fma'] for fn in FNS] == [0, 0, 0, 0, 1] and fact[tag, 'exp32']['skel'] == fact['normal', 'exp32']['skel'][:-5] + ('Famaa' if tag == 'x_mm' else 'aamFa')))
    req.append(('narrow_sq by itself (the symbol the x_ builds add): m a a m a a in x_ctl; the same with one fused multiply-add in x_mm (m F a m a a) and in x_cv (m a a m F a)',
                [nsqf[t]['skel'] for t in ('x_ctl', 'x_mm', 'x_cv')] == ['maamaa', 'mFamaa', 'maamFa']))
    plants = [v[0] for v in variants if v[3]]; honest = [v[0] for v in variants if not v[3]]
    contracted = lambda tag, fn: fact[tag, fn]['fma'] > 0

    def run_fn(tag, fn, rows):
        inp = ''.join(' '.join('%x' % bits(v) for v in r) + '\n' for r in rows)
        q = run([exe[tag], fn], inp=inp); out = q.stdout.split()
        if q.returncode != 0 or len(out) != len(rows):
            raise Stop('the program of build %s returned %d lines for %d inputs of %s, exit %d%s' % (
                tag, len(out), len(rows), fn, q.returncode, ' (a planted build needs a processor that executes FMA3)' if tag not in ('normal',) else ''))
        return array.array('Q', [int(o, 16) for o in out])
    for tag in [v[0] for v in variants]:
        if list(run_fn(tag, 'sqrt32', [[4.0]])) != [bits(2.0)]: raise Stop('build %s: sqrt32(4) is not 2' % tag)
    req.append(('all %d programs ran on this host (the planted ones execute FMA3 instructions)' % len(variants), True))

    # ---- the scanner: two builds of one function in one program, every binary32 pattern of a range
    XMAX_U = E2['XMAX_U']
    RANGES = {'exp32': [(0, XMAX_U), (0x80000000, 0xff7fffff)], 'sqrt32': [(0, 0x7f7fffff)], 'rsqrt32': [(1, 0x7f7fffff)]}
    EXPECT = {'exp32': E2['N_INPUTS'], 'sqrt32': 2139095040, 'rsqrt32': 2139095039}
    scan_exe = {}
    def scanner(fn, a, b):
        if (fn, a, b) not in scan_exe:
            d = os.path.join(T, 'scan_%s_%s_%s' % (fn, a, b)); os.makedirs(d); lib = 'lib2.o' if fn == 'exp32' else 'lib1.o'
            open(os.path.join(d, 'scan.c'), 'w', encoding='utf-8', newline='\n').write(SCAN)
            q = run(['clang'] + TIER_FLAGS + QUIET + ['-DFA=ut_%s__%s' % (fn, a), '-DFB=ut_%s__%s' % (fn, b), '-c', 'scan.c', '-o', 'scan.o'], cwd=d)
            if q.returncode == 0: q = run(['clang', 'scan.o', os.path.join('..', a, lib), os.path.join('..', b, lib), '-o', 'scan.exe'], cwd=d)
            if q.returncode != 0: raise Stop('the scanner for %s (%s, %s) did not build: %s' % (fn, a, b, (q.stdout + q.stderr).strip()[-300:]))
            scan_exe[fn, a, b] = os.path.join(d, 'scan.exe')
        return scan_exe[fn, a, b]
    def scan(fn, a, b, ranges):
        x = scanner(fn, a, b); jobs = [(lo, min(hi, lo + CHUNK - 1)) for r0, hi in ranges for lo in range(r0, hi + 1, CHUNK)]
        def one(j): q = run([x, '%x' % j[0], '%x' % j[1]]); return j, q.returncode, q.stdout
        res = {'n': 0, 'differ': 0, 'diffs': [], 'bad': 0, 'cut': False, 'chunks': len(jobs)}
        with concurrent.futures.ThreadPoolExecutor(THREADS) as ex:
            for j, rc, out in ex.map(one, jobs):
                lines = out.splitlines(); end = lines[-1].split() if lines else []
                if rc != 0 or len(end) != 5 or end[0] != 'END' or int(end[3][2:]) != j[1] - j[0] + 1: res['bad'] += 1; continue
                dl = [l.split() for l in lines[:-1]]; res['n'] += int(end[3][2:]); res['differ'] += int(end[4][7:])
                res['diffs'] += [(int(f[1], 16), int(f[2], 16), int(f[3], 16)) for f in dl]; res['cut'] |= int(end[4][7:]) != len(dl)
        res['diffs'].sort(); return res
    say('\n4. the scanner (one function as two builds made it, in one program, result bits against result bits):')
    lo, hi = 0x3f800000, 0x3f80ffff; chk = scan('sqrt32', 'normal', 'n_outer', [(lo, hi)])
    rows = [[h2.f32(u)] for u in range(lo, hi + 1)]; oa = run_fn('normal', 'sqrt32', rows); ob = run_fn('n_outer', 'sqrt32', rows)
    by_corpus = [(lo + i, a, b) for i, (a, b) in enumerate(zip(oa, ob)) if a != b]
    say('   its own check: sqrt32, normal against n_outer, patterns %08x..%08x: the scanner reports %d of %d differing; the two programs run separately on the same inputs: %d' % (
        lo, hi, chk['differ'], chk['n'], len(by_corpus)))
    req.append(('the scanner reports differences where two builds differ, the same count and the same first 256 as the programs run separately (%d of %d)' % (len(by_corpus), hi - lo + 1),
                chk['bad'] == 0 and chk['n'] == hi - lo + 1 and chk['differ'] == len(by_corpus) > 0 and chk['diffs'] == by_corpus[:256]))
    scans = {}
    for fn, b in (('exp32', 'fast'), ('exp32', 'n_inner'), ('sqrt32', 'n_inner'), ('rsqrt32', 'n_inner'), ('exp32', 'x_ctl'), ('exp32', 'x_mm'), ('exp32', 'x_cv')):
        if b != 'x_ctl' and not contracted(b, fn): continue              # not a plant for this function: nothing to scan
        s = scans[fn, b] = scan(fn, 'normal', b, RANGES[fn])
        say('   %-8s normal against %-8s every input of the function, patterns %s: %d inputs in %d chunks, %d differ%s' % (
            fn, b, ' and '.join('%08x..%08x' % r for r in RANGES[fn]), s['n'], s['chunks'], s['differ'],
            '' if not s['diffs'] else ': ' + ', '.join('%08x' % d[0] for d in s['diffs'][:12]) + (' ...' if s['differ'] > 12 else '')))
        req.append(('%s, normal against %s: every chunk ran, the inputs are the %d of the function\'s sweep, and every differing input is listed' % (fn, b, EXPECT[fn]),
                    s['bad'] == 0 and s['n'] == EXPECT[fn] and not s['cut'] and len(s['diffs']) == s['differ']))
    req.append(('exp32, normal against x_ctl, the control of x_mm and x_cv: 0 of %d inputs differ (with the twelfth squaring moved into narrow_sq it is the same function)' % EXPECT['exp32'],
                ('exp32', 'x_ctl') in scans and scans['exp32', 'x_ctl']['differ'] == 0 and scans['exp32', 'x_ctl']['n'] == EXPECT['exp32']))
    req.append(('the scan of every input of exp32, normal against fast, finds the inputs this file pins (%s) and no other' % ', '.join('%08x' % u for u in PINNED_EXP32),
                ('exp32', 'fast') in scans and [d[0] for d in scans['exp32', 'fast']['diffs']] == sorted(PINNED_EXP32)))

    # ---- constructed inputs (exact arithmetic proposes; the builds decide)
    KK, TT, nar = E1['KK'], E1['TT'], E1['py_narrow']
    def construct_outside(want=8):
        """pairs of binary64 numbers that are not binary32 numbers, near the tie 1 + 2^-24 between the binary32 neighbours
        1 and 1 + 2^-23: y = 0.6 + j * 2^-30, x within 48 units in the last place of sqrt((1 + 2^-24)^2 - y^2), kept when
        fusing x*x + y*y (one way or the other) changes the result after sqrt and narrow"""
        fx, fy = [], []; tie = 1.0 + 2.0 ** -24; j = 0
        while (len(fx) < want or len(fy) < want) and j < 4000:
            y = 0.6 + j * 2.0 ** -30; x0 = math.sqrt(tie * tie - y * y); j += 1
            for k in range(-48, 49):
                x = x0 + k * math.ulp(x0); plain = nar(math.sqrt(x * x + y * y))
                if nar(math.sqrt(float(F(x) * F(x) + F(y * y)))) != plain and len(fx) < want: fx.append([x, y])      # fma(x, x, y*y)
                if nar(math.sqrt(float(F(y) * F(y) + F(x * x)))) != plain and len(fy) < want: fy.append([x, y])      # fma(y, y, x*x)
        return fx + [p for p in fy if p not in fx]
    def construct_inner(want=8):
        """pairs of binary32 numbers, x = 1 - 2^-24 and y stepping down from 0.000345, whose binary64 hypotenuse v is so
        close below 1 that KK*v is rounded in the next binade: kept when c - fma(KK, v, -v) is not narrow(v)"""
        x = h2.f32(0x3f7fffff); out = []; u = h2.u32(0.000345)
        for u in range(u, u - 5000, -1):
            y = h2.f32(u); v = math.sqrt(x * x + y * y)
            if abs(v) >= TT and KK * v - float(F(KK) * F(v) - F(v)) != nar(v): out.append([x, y])
            if len(out) == want: break
        return out
    MM, HH = E1['MM'], E1['HH']
    def construct_sq(tag, want=8):
        """binary64 values u for narrow_sq alone: u near the square root of a tie t of the grid the plant's fused operation rounds to (x_mm: t = (k + 1/2) * 2^-149,
        the grid of v + MM; x_cv: t = 1 + (2k + 1) * 2^-24, halfway between two binary32 numbers), kept when the plant, in exact arithmetic, is not narrow(u * u)"""
        out = []; k = 0
        while len(out) < want and k < 100000:
            k += 1; t = (2 * k + 1) * 2.0 ** -150 if tag == 'x_mm' else 1.0 + (2 * k + 1) * 2.0 ** -24; u0 = math.sqrt(t)
            for j in (-2, -1, 0, 1, 2):
                u = u0 + j * math.ulp(u0); v = u * u
                if tag == 'x_mm':
                    if not HH < v < TT: continue
                    fused = float(F(u) * F(u) + F(MM)) - MM            # fma(u, u, MM) - MM
                else:
                    c = KK * v; fused = c - float(F(c) - F(u) * F(u))  # c - fma(-u, u, c)
                if fused != nar(v) and [u] not in out and len(out) < want: out.append([u])
        return out
    c_out = construct_outside(); c_in = construct_inner(); c_sq = {tag: construct_sq(tag) for tag in X_PLANTS}

    # ---- the input sets
    A = ga.inputs(); names, pairs, reg, known = h2.sample()
    S = {fn: [dict(short='graph_agree.inputs()', label='graph_agree.inputs(), seed 20261114', rows=A[fn], dom=True, coq=True)] for fn in FNS}
    for fn in FNS:                                                     # the corpus inputs, as the emitters wrote them in the temporary folder (the tier's, byte for byte)
        c = json.load(open(os.path.join(T, 'gen', 'corpus_%s.json' % fn)))
        S[fn].append(dict(short='the emitters\' corpus', label='the corpus inputs the emitter writes, gen/corpus_%s.json (what emit%s.py corpus compares on; its seed 20261114)' % (fn, '2' if fn == 'exp32' else ''),
                          rows=[[dbl(b)] for b in c] if fn == 'exp32' else [[dbl(b) for b in r] for r in c], dom=True, coq=True))
    S['exp32'].append(dict(short='pinned (found by the scan of every input)', label='pinned in this file, binary32 patterns %s: the inputs on which exp32 with its six polynomial steps fused '
                           'differs from exp32, of all %d (held to what the scan under 4 finds now)' % (', '.join('%08x' % u for u in PINNED_EXP32), EXPECT['exp32']),
                           rows=[[h2.f32(u)] for u in PINNED_EXP32], dom=True, coq=True))
    S['narrow'].append(dict(short='narrow_regress.inputs()', label='narrow_regress.inputs(), seed 20261114', rows=[[v] for _, vs in nr.inputs() for v in vs], dom=True, coq=True))
    S['hypot32'].append(dict(short='hypot_check2.sample()', label='hypot_check2.sample(), seed %d: pairs of finite binary32 numbers in its seven regimes and three known pairs' % h2.SEED,
                             rows=[[h2.f32(a), h2.f32(b)] for a, b in pairs], dom=True, coq=False))
    S['hypot32'].append(dict(short='constructed, in the domain', label='constructed, binary32 pairs: x = 1 - 2^-24 and y stepping down from 0.000345, hypotenuse just below 1 '
                             '(aimed at narrow\'s inner site)', rows=c_in, dom=True, coq=True))
    S['hypot32'].append(dict(short='constructed, outside the domain', label='constructed, OUTSIDE the domain: binary64 pairs that are not binary32 numbers, near the binary32 tie 1 + 2^-24 '
                             '(y = 0.6 + j * 2^-30, x near sqrt((1 + 2^-24)^2 - y^2))', rows=c_out, dom=False, coq=True))
    for (fn, b), s in sorted(scans.items()):                           # whatever a scan finds that is not pinned: put to the references too
        extra = [d[0] for d in s['diffs'] if not (fn == 'exp32' and d[0] in PINNED_EXP32)]
        if extra: S[fn].append(dict(short='found by the scan of every input', label='found: inputs where normal and %s differ, of all %d, that this file does not pin' % (b, s['n']),
                                    rows=[[h2.f32(u)] for u in extra], dom=True, coq=True))
    def py_ref(fn, rows):
        if fn == 'exp32': return [bits(E2['py_narrow'](E2['py_g'](r[0]))) for r in rows]
        ins, e = E1['FUNCS'][fn]; ev = E1['py_eval']
        return [bits(nar(ev(e, dict(zip(ins, r))))) for r in rows]
    say('\n5. input sets (deterministic) and references:')
    for fn in FNS:
        for st in S[fn]:
            st['py'] = array.array('Q', py_ref(fn, st['rows'])); st['cast'] = array.array('Q', [bits(nr.py_cast(r[0])) for r in st['rows']]) if fn == 'narrow' else None
            say('   %-8s %7d inputs  %s  [Python graph%s%s]' % (fn, len(st['rows']), st['label'], ', Coq graph' if st['coq'] else '', ', IEEE conversion' if fn == 'narrow' else ''))
    say('   and, build against build: every input of exp32 (%d), sqrt32 (%d) and rsqrt32 (%d), as listed under 4.' % (EXPECT['exp32'], EXPECT['sqrt32'], EXPECT['rsqrt32']))
    say('   and, for narrow_sq by itself in the x_ builds (not inputs of exp32: values of u, the number its twelfth squaring squares): constructed, %s' % '; '.join(
        '%d binary64 values for %s, near the square root of %s' % (len(c_sq[tag]), tag, 'a tie (k + 1/2) * 2^-149 of the grid v + MM rounds to' if tag == 'x_mm' else
                                                                    'a tie 1 + (2k + 1) * 2^-24 between two binary32 numbers') for tag in X_PLANTS))
    req += [('the constructed hypot32 inputs outside the domain are not binary32 numbers (%d pairs)' % len(c_out), len(c_out) > 0 and all(nr.py_cast(x) != x for x, y in c_out)),
            ('the constructed hypot32 inputs inside the domain are binary32 numbers (%d pairs)' % len(c_in), len(c_in) > 0 and all(nr.py_cast(x) == x and nr.py_cast(y) == y for x, y in c_in))]
    tg = open(ga.GRAPHS, encoding='utf-8').read(); te = open(ga.GRAPH, encoding='utf-8').read()
    DEFS = {}; ka, wa = ga.load(tg, DEFS); kb, wb = ga.load(te, DEFS)
    req.append(('every Definition of p32/Graphs.v and exp32/Graph.v was read by graph_agree\'s reader (%d and %d), the thirteen it expects' % (wa, wb),
                ka == wa and kb == wb and list(DEFS) == ga.NAMES))
    def coq_cmp(fn, rows, out):
        """graph_agree.compare, as it is: [same bits, equal with the sign of zero different (accepted), different, C not finite, first]"""
        I = {f: [] for f in ga.FNS}; G = {f: [] for f in ga.FNS}; I[fn] = rows; G[fn] = [dbl(b) for b in out]
        return ga.compare(DEFS, I, G)[fn]
    def coq_value(fn, row):
        ps, bd = DEFS['g_' + fn]; m = ga.ev(bd, dict(zip(ps, [F(v) for v in row])), DEFS)
        try: f = float(m)
        except OverflowError: return 'above binary64'
        return '%016x' % bits(f) if F(f) == m else 'not a binary64 number'

    # ---- 4. compare
    R = {}; OUT = {}
    for tag in [v[0] for v in variants]:
        for fn in FNS:
            cell = []
            for i, st in enumerate(S[fn]):
                out = OUT[tag, fn, i] = run_fn(tag, fn, st['rows']) if st['rows'] else array.array('Q')
                idx = [k for k, (o, r) in enumerate(zip(out, st['py'])) if o != r]
                c = coq_cmp(fn, st['rows'], out) if st['coq'] else None
                cell.append(dict(n=len(out), d=len(idx), first=None if not idx else (idx[0], out[idx[0]]), coq=c,
                                 dcast=None if st['cast'] is None else sum(1 for o, r in zip(out, st['cast']) if o != r)))
            R[tag, fn] = cell
    tier_same = True; tier_n = 0
    for fn in FNS:                                                     # the tier's linked programs, read and run, never written
        for i, st in enumerate(S[fn]):
            if not st['rows']: continue
            t = ga.native(ga.SWEEP2 if fn == 'exp32' else ga.SWEEP, fn, st['rows']); tier_n += len(t)
            tier_same &= array.array('Q', [bits(v) for v in t]) == OUT['normal', fn, i]
    req.append(('normal prints what the tier\'s own gen/sweep.exe and gen/sweep2.exe print in corpus mode, on every input of every set (%d inputs, five functions)' % tier_n, tier_same))
    def tot(tag, fn, dom=True):
        cs = [(c, st) for c, st in zip(R[tag, fn], S[fn]) if st['dom'] == dom]
        return dict(n=sum(c['n'] for c, _ in cs), d=sum(c['d'] for c, _ in cs), nc=sum(c['n'] for c, st in cs if st['coq']),
                    dc=sum(c['coq'][2] + c['coq'][3] for c, st in cs if st['coq']), zs=sum(c['coq'][1] for c, st in cs if st['coq']),
                    dcast=sum(c['dcast'] or 0 for c, _ in cs))
    say('\n6. each build against the references, on the inputs inside each function\'s domain (binary32 inputs; for narrow, binary64 values below the overflow threshold):')
    say('   %-8s %-8s %4s %9s | %-13s | %-25s | %-10s | %s' % ('build', 'function', 'FMA', 'inputs', 'differ from', 'differ from the Coq graph', 'differ from', ''))
    say('   %-8s %-8s %4s %9s | %-13s | %-25s | %-10s | %s' % ('', '', '', '', 'Python graph', '(of; sign of zero only)', 'IEEE conv.', ''))
    status = {}
    for tag, flags, patch, planted, what in variants:
        for fn in FNS:
            t = tot(tag, fn); refused = t['d'] > 0 or t['dc'] > 0
            if not planted: st = 'agrees' if not refused and t['dcast'] == 0 else 'DISAGREES'
            elif not contracted(tag, fn): st = 'not contracted in this build' + ('' if not refused else ', yet it DIFFERS')
            else: st = 'REFUSED' if refused else 'equivalent mutant on this input set'
            status[tag, fn] = st
            say('   %-8s %-8s %4d %9d | %-13d | %-25s | %-10s | %s' % (tag, fn, fact[tag, fn]['fma'], t['n'], t['d'], '%d (of %d; %d)' % (t['dc'], t['nc'], t['zs']),
                                                                      '%d' % t['dcast'] if fn == 'narrow' else '-', st))
    for tag in honest:
        req.append(('%s agrees with every reference on every input of every set, the constructed ones outside the domain included (%d inputs)' % (
            tag, sum(c['n'] for fn in FNS for c in R[tag, fn])),
            all(c['d'] == 0 and (c['coq'] is None or c['coq'][2] + c['coq'][3] == 0) and not c['dcast'] for fn in FNS for c in R[tag, fn])))
    req.append(('a planted build that does not contract a function leaves it as it was (agrees on every input)',
                all(tot(tag, fn)['d'] == 0 and tot(tag, fn)['dc'] == 0 for tag in plants for fn in FNS if not contracted(tag, fn))))

    # ---- hypot_check2's own reference, on the pairs of binary32 numbers: exact faithfulness inside the domain of HYPOT32_FINITE
    hT = {}
    for i, st in enumerate(S['hypot32']):
        if st['dom']:
            L = []
            for x, y in st['rows']:
                X, Y = h2.scaled(h2.u32(abs(x))), h2.scaled(h2.u32(abs(y))); t2 = X * X + Y * Y
                L.append(t2 if t2 <= h2.FMAXI * h2.FMAXI else None)
            hT[i] = L
    memo = {}
    def h2_count(tag):
        """(pairs inside the domain, results there that hypot_check2.faithful refuses), over the sets of binary32 pairs"""
        ind = bad = 0
        for i, L in hT.items():
            out = OUT[tag, 'hypot32', i]; key = (i, hashlib.sha256(out.tobytes()).digest())
            if key not in memo: memo[key] = (sum(1 for t2 in L if t2 is not None), sum(1 for t2, o in zip(L, out) if t2 is not None and not h2.faithful(t2, dbl(o))))
            ind += memo[key][0]; bad += memo[key][1]
        return ind, bad
    H2 = {tag: h2_count(tag) for tag in [v[0] for v in variants]}
    say('   hypot32 by hypot_check2.py\'s own reference (exact integers; on the pairs inside the domain of HYPOT32_FINITE the result must be a binary32 number r >= 0 with')
    say('   pred(r)^2 < x^2 + y^2 < succ(r)^2), over the same sets of binary32 pairs: not faithful, of the %d pairs inside the domain: %s' % (
        H2['normal'][0], '; '.join('%s %d' % (tag, H2[tag][1]) for tag in [v[0] for v in variants])))
    req.append(('hypot32, by hypot_check2\'s faithfulness reference: the builds without a plant (%s) are faithful on every pair inside the domain (%d pairs)' % (', '.join(honest), H2['normal'][0]),
                H2['normal'][0] > 0 and all(H2[tag] == (H2['normal'][0], 0) for tag in honest)))

    # ---- what the compiler's contraction computes: the emitters' graphs with the fused sites rounded once, in exact arithmetic (they describe the plant; they judge nothing)
    def fused_exp(x):
        env = {'x': x}
        for t, e in steps:
            if e[0] == 'clamplo': env[t] = float(e[2]) if env[e[1][1]] < float(e[2]) else env[e[1][1]]
            elif tree_sites(e):                                        # c + r * n: the exact sum, rounded once
                if not (e[0] == 'add' and e[1][0] == 'const' and e[2][0] == 'mul' and e[2][1][0] == 'var' and e[2][2][0] == 'var'): raise Stop('a site of exp32 is not of the form c + a * b')
                env[t] = float(F(float(e[1][1])) + F(env[e[2][1][1]]) * F(env[e[2][2][1]]))
            else: env[t] = E2['py_tree'](e, env)
        return E2['py_narrow'](env['v'])
    def fused_hyp(x, y, which):                                        # sqrt(a*a + b*b) with a*a unrounded in the sum: fma(a, a, b*b)
        a, b = (x, y) if which == 'x' else (y, x)
        return nar(math.sqrt(float(F(a) * F(a) + F(b * b))))
    say('   what fast and dropped compute: the emitters\' graph with the fused sites rounded once (exact arithmetic), against the build, bit for bit, on the sets the Coq graph is evaluated on:')
    model = {}
    for tag in COMPILER_PLANTS:
        if contracted(tag, 'exp32'):
            n = d = live = 0
            for i, st in enumerate(S['exp32']):
                for r, o, p in zip(st['rows'], OUT[tag, 'exp32', i], st['py']):
                    f = bits(fused_exp(r[0])); n += 1; d += f != o; live += f != p
            model[tag, 'exp32'] = (n, d, live, 'its six c + r * n each rounded once')
        if contracted(tag, 'hypot32'):
            for which in ('x', 'y'):
                n = d = live = 0
                for i, st in enumerate(S['hypot32']):
                    if not st['coq']: continue
                    for r, o, p in zip(st['rows'], OUT[tag, 'hypot32', i], st['py']):
                        f = bits(fused_hyp(r[0], r[1], which)); n += 1; d += f != o; live += f != p
                model[tag, 'hypot32'] = (n, d, live, '%s * %s unrounded in the sum (the other product rounded)' % (which, which))
                if d == 0: break
    for (tag, fn), (n, d, live, what) in sorted(model.items()):
        say('   %-8s %-8s with %s: the build differs from it on %d of %d inputs; it differs from the plain graph on %d of them' % (tag, fn, what, d, n, live))
    req.append(('fast and dropped compute the fused graphs: exp32 with its six c + r * n each rounded once, hypot32 with one product unrounded in the sum, bit for bit on every input of '
                'those sets, the inputs where the fused graph and the plain graph differ included',
                all((tag, fn) in model and model[tag, fn][1] == 0 and model[tag, fn][2] > 0 for tag in COMPILER_PLANTS for fn in ('hypot32', 'exp32'))))

    # ---- the plants across statements as functions of the value squared: narrow_sq(u) on the constructed u, the plant against its control
    alive = {}
    say('   narrow_sq(u) by itself, x_mm and x_cv against their control x_ctl, on the constructed u (the control held to py_narrow(u * u)):')
    for tag in X_PLANTS:
        rows = c_sq[tag]; ctl = run_fn('x_ctl', 'nsq', rows) if rows else []; got = run_fn(tag, 'nsq', rows) if rows else []
        d = [i for i in range(len(rows)) if ctl[i] != got[i]]
        alive[tag] = (len(rows), len(d), list(ctl) == [bits(nar(u * u)) for u, in rows])
        say('   %-8s differs from x_ctl on %d of %d%s; x_ctl is py_narrow(u * u) on every one: %s' % (tag, len(d), len(rows), '' if not d else
            ' (first: u = %s -> x_ctl %016x, %s %016x)' % (hx(rows[d[0]][0]), ctl[d[0]], tag, got[d[0]]), 'yes' if alive[tag][2] else 'no'))
    req.append(('x_mm and x_cv are live as functions of the value squared: on constructed u each differs from its control (%s), and the control returns py_narrow(u * u) on every one' % (
        '; '.join('%s on %d of %d' % (tag, alive[tag][1], alive[tag][0]) for tag in X_PLANTS)), all(alive[tag][1] > 0 and alive[tag][2] for tag in X_PLANTS)))

    # ---- 5. per contracted cell: refused, or equivalent and accounted for
    def first_diff(tag, fn, dom=True):
        for i, (c, st) in enumerate(zip(R[tag, fn], S[fn])):
            if st['dom'] == dom and c['first'] is not None:
                k, o = c['first']; row = st['rows'][k]
                return '%s -> normal %016x, %s %016x; Python graph %016x, Coq graph %s   [%s]' % (
                    ', '.join(hx(v) for v in row), OUT['normal', fn, i][k], tag, o, st['py'][k], coq_value(fn, row) if st['coq'] else 'not evaluated on this set', st['short'])
        return None
    say('\n7. findings, function by function:')
    account = {}
    for fn in FNS:
        cells = [tag for tag in plants if contracted(tag, fn)]
        say('   %s: %s' % (fn, ('%d site%s of its own' % (own[fn], '' if own[fn] == 1 else 's') if own[fn] else 'no site of its own') + ('' if fn == 'narrow' else '; ends in narrow')
                           + ('; two more across statements, its twelfth v * v into narrow (x_mm, x_cv)' if fn == 'exp32' else '')))
        for tag in plants:
            if not contracted(tag, fn):
                say('     %-8s not contracted: the function holds no fused multiply-add in this build (not a plant for it)' % tag); continue
            if status[tag, fn] == 'REFUSED':
                per = '; '.join('%d of %d' % (c['d'], c['n']) for c, st in zip(R[tag, fn], S[fn]) if st['dom'])
                say('     %-8s REFUSED: differs from the references on %d of %d inputs (set by set: %s)' % (tag, tot(tag, fn)['d'], tot(tag, fn)['n'], per))
                say('              first: ' + first_diff(tag, fn)); account[tag, fn] = 'refused'
                continue
            why = []
            if fn == 'hypot32' and tag in COMPILER_PLANTS:
                o = tot(tag, fn, dom=False)
                why.append('none can inside the domain: a binary32 number has 24 significant bits, so x*x and y*y have at most 48 and are exact in '
                           'binary64 (their exponents are far inside its range); fused either way, the one rounding is of the same exact sum')
                if o['d'] > 0:
                    why.append('outside the domain it is live: on %d of the %d constructed binary64 pairs the fused result differs' % (o['d'], o['n']))
                    account[tag, fn] = 'equivalent, accounted: exact products; live outside the domain'
                    say('     %-8s equivalent mutant on this input set (%d pairs of binary32 numbers, 0 differ). %s. %s.' % (tag, tot(tag, fn)['n'], why[0].capitalize(), why[1].capitalize()))
                    say('              first outside the domain: ' + first_diff(tag, fn, dom=False)); continue
            if (fn, tag) in scans and scans[fn, tag]['differ'] == 0 and scans[fn, tag]['bad'] == 0 and scans[fn, tag]['n'] == EXPECT[fn]:
                account[tag, fn] = 'equivalent, accounted: every input measured'
                say('     %-8s equivalent mutant on this input set, and on every input of the function: 0 of %d differ from normal, build against build. %s' % (
                    tag, scans[fn, tag]['n'], 'Why none can: the inner site changes narrow\'s result only where KK*v is rounded in the next binade, that is for v within '
                    'about 2^-29 (relative) below a power of two, with an odd last bit; the square root of a number of 24 significant bits, and its reciprocal, stay at least '
                    'about 2^-25 away from that.' if fn in ('sqrt32', 'rsqrt32') and tag == 'n_inner' else
                    'Measured, on every input. Argued, not measured, where a difference could arise: only at an input whose rounded twelfth square lies exactly halfway between two '
                    '%s, and the exact square to the side the tie does not go. The plant is live all the same: narrow_sq by itself differs from its control on %d of %d '
                    'constructed values of u, which exp32 does not reach.' % ('multiples of 2^-149 (the grid v + MM rounds to)' if tag == 'x_mm' else 'binary32 numbers',
                                                                               alive[tag][1], alive[tag][0]) if tag in X_PLANTS else
                    'No argument is offered why: it is measured, on every input.'))
                continue
            account[tag, fn] = None
            say('     %-8s equivalent mutant on this input set, and this run has NO ACCOUNT of which inputs would distinguish it' % tag)
    for tag in ('n_outer', 'n_both'):                                  # what the outer site does to narrow: it stops narrowing
        nb = [(st['rows'][k][0], o) for i, st in enumerate(S['narrow']) for k, o in enumerate(OUT[tag, 'narrow', i]) if abs(st['rows'][k][0]) >= TT]
        say('   narrow under %s, on its inputs of magnitude at least 2^-126 (the branch that holds the product): the result is the input itself, bit for bit, on %d of %d, '
            'of which %d are not binary32 numbers' % (tag, sum(1 for v, o in nb if bits(v) == o), len(nb), sum(1 for v, o in nb if bits(v) == o and nr.py_cast(v) != v)))
    say('   (the subtrahend of the outer use is 2^29 * v, or within a rounding of it, and KK*v - 2^29*v is v itself: fused, the outer subtraction returns v unrounded)')
    if ('exp32', 'fast') in scans and scans['exp32', 'fast']['diffs']:
        decimal.getcontext().prec = 60; D = decimal.Decimal; EPS = D(10) ** -50
        def verdict(f, r):                                             # copied from orl/exp_check.py: 1 faithful, 0 not, -1 ambiguous
            if r < 0 or h2.as32(r) is None: return 0
            u = h2.u32(r); hi_ = D(h2.f32(u + 1)); lo_ = D(h2.f32(u - 1)) if u else D(-1)
            if lo_ * (1 + EPS) < f and f < hi_ * (1 - EPS): return 1
            if f <= lo_ * (1 - EPS) or f >= hi_ * (1 + EPS): return 0
            return -1
        both = True
        for u, a, b in scans['exp32', 'fast']['diffs']:
            x = h2.f32(u); f = D(x).exp(); va, vb = verdict(f, dbl(a)), verdict(f, dbl(b)); both &= va == 1 and vb == 1
            say('   exp32 at x = %s: normal %016x is %s, fast %016x is %s (pred32(r) < exp(x) < succ32(r), decimal exp at 60 digits, exp_check.py\'s verdict)' % (
                x.hex(), a, 'faithful' if va == 1 else 'NOT faithful', b, 'faithful' if vb == 1 else 'NOT faithful'))
        say('   so a faithfulness check %s the contracted exp32 on the inputs where it differs: only a bit-for-bit comparison that reaches these inputs refuses it;'
            % ('accepts' if both else 'does not accept'))
        own2 = [(st['short'], c['d'], c['n']) for c, st in zip(R['fast', 'exp32'], S['exp32'])][:2]
        say('   on the tier\'s own inputs for a bit-for-bit comparison of exp32 (%s) fast differs on %d: there the contraction is an equivalent mutant;' % (
            '; '.join('%s, %d inputs' % (s, n) for s, d, n in own2), sum(d for s, d, n in own2)))
        say('   it is refused on the pinned inputs alone, which this test brings (found by its scan of every input).')
    for tag in plants:
        if contracted(tag, 'hypot32') and status[tag, 'hypot32'] == 'REFUSED':
            say('   hypot32 under %s: hypot_check2\'s faithfulness reference refuses %d of the %d results inside the domain%s' % (tag, H2[tag][1], H2[tag][0], '' if H2[tag][1] else
                ': it accepts this plant (a result that differs is still a binary32 neighbour of the exact value); the bit-for-bit comparison alone refuses it'))
    cells = [(tag, fn) for tag in plants for fn in FNS if contracted(tag, fn)]
    req.append(('every function a planted build contracts is refused there, or is an equivalent mutant with an account (%d contracted cells: %d refused, %d equivalent and accounted for)' % (
        len(cells), sum(1 for c in cells if account.get(c) == 'refused'), sum(1 for c in cells if account.get(c) and account[c] != 'refused')), all(account.get(c) for c in cells)))
    attributed = {fn: [tag for tag in plants if contracted(tag, fn) and (tag in COMPILER_PLANTS or tag in X_PLANTS or fn == 'narrow')] for fn in FNS if own[fn]}
    req.append(('every function with a site of its own is contracted by at least one planted build (%s)' % '; '.join('%s: %s' % (fn, ', '.join(t) or 'none') for fn, t in attributed.items()),
                all(attributed.values())))

    # ---- the tier, after
    n, bad = freeze_lists()
    req.append(('every file the tier\'s ten freeze lists name (f32, p32, p32r, exp32, exp32r: FROZEN.txt, FROZEN4.txt) has its listed sha256: %d entries%s' % (
        n, '' if not bad else '; NOT: ' + '; '.join(bad[:6])), n > 0 and not bad))
    snap1 = snapshot(); changed = sorted(k for k in snap0 if snap1.get(k) != snap0[k]); new = sorted(k for k in snap1 if k not in snap0)
    mine = [k for k in new if not k.startswith('orl/evidence/')]
    req.append(('the tier as it was: each of the %d files under %s present at the start has the same sha256 at the end%s; files that appeared meanwhile: %d%s' % (
        len(snap0), ', '.join(WATCH), '' if not changed else ' EXCEPT ' + ', '.join(changed[:8]), len(new), '' if not new else ' (%s; this test writes none)' % ', '.join(new[:8])),
        not changed and not mine))
    say('\n8. requirements:')
    ok = True
    for text, good in req:
        say('  %-4s %s' % ('ok' if good else 'FAIL', text)); ok &= bool(good)
    ref = [fn for fn in attributed if any(account.get((t, fn)) == 'refused' for t in attributed[fn])]
    eqv = [fn for fn in attributed if any(account.get((t, fn)) != 'refused' for t in attributed[fn])]
    def note(fn, tag, want):
        s = scans.get((fn, tag)) or (scans.get((fn, 'fast')) if tag == 'dropped' and same else None)     # dropped's five functions are fast's, instruction for instruction
        if s and want: return ': on %d of its %d inputs' % (s['differ'], s['n'])
        if s and not want and s['differ'] == 0: return ': 0 of its %d inputs differ' % s['n']
        if fn == 'hypot32' and not want: return ': 0 of %d pairs of binary32 inputs differ, and none can' % tot(tag, 'hypot32')['n']
        return ''
    def lst(fns, want):
        out = []
        for fn in fns:
            groups = []                                                # the plants of one function, grouped where they share a note
            for t in attributed[fn]:
                if (account.get((t, fn)) == 'refused') != want: continue
                nt = note(fn, t, want)
                if groups and groups[-1][1] == nt: groups[-1][0].append(t)
                else: groups.append(([t], nt))
            out.append('%s (%s)' % (fn, '; '.join(', '.join(ts) + nt for ts, nt in groups)))
        return ', '.join(out) or 'none'
    nos = [fn for fn in FNS if not own[fn]]
    tail = 'contracted build refused for %s; equivalent mutant for %s; no contraction site in %s' % (
        lst(ref, True), lst(eqv, False), (', '.join(nos) + ' (none of their own; narrow\'s, which every function ends in, is counted under narrow)') if nos else 'none')
    if ok: return True, 'FMA PLANT HELD: ' + tail
    failed = [text for text, good in req if not good]
    return False, 'FMA PLANT FAILED: %d of %d requirements not met; the first: %s' % (len(failed), len(req), failed[0])

def main():
    a = sys.argv[1:]; record = os.path.abspath(a[a.index('--record') + 1]) if '--record' in a else None
    brk = a[a.index('--break') + 1] if '--break' in a else None
    if record and os.path.exists(record):
        print('refused: %s exists; a run gets a record of its own' % os.path.basename(record)); return 2
    if brk is not None and (brk not in BREAKS or record):
        print('refused: --break takes one of %s, and its run is not a record' % ', '.join(BREAKS)); return 2
    T = tempfile.mkdtemp(prefix='fma-plant-')
    try: ok, verdict = body(T, brk)
    except Stop as e: ok, verdict = False, 'FMA PLANT FAILED: %s' % scrub(str(e), T)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        ok, verdict = False, 'FMA PLANT FAILED: the test itself stopped (%s: %s)' % (type(e).__name__, scrub(str(e), T))
    finally:
        if '--keep' not in a: shutil.rmtree(T, ignore_errors=True)
    if brk and ok:                                                     # a broken apparatus that passes every requirement
        say('FMA PLANT FAILED: the test\'s own plant %s was NOT caught: every requirement passed on a broken apparatus' % brk); return 3
    if brk: verdict += '   [as it must: the test\'s own plant %s]' % brk
    say(verdict)
    if record:
        with open(record, 'wb') as f: f.write(('\n'.join(LINES) + '\n').encode('utf-8'))
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
