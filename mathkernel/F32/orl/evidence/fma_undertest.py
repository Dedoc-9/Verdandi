# The code under test alone, as an object file (2026-11-14).
#   python -B fma_undertest.py
# Copies from orl/gen/sweep.c and orl/gen/sweep2.c only the constants, narrow, and the functions under test (f_sqrt32,
# f_rsqrt32, f_hypot32, g_exp32), with "static" removed so that the compiler keeps them, compiles each with the sweep
# programs' options, and reports: undefined symbols, relocations, call instructions and fused multiply-add instructions.
import os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); GEN = os.path.join(HERE, '..', 'gen'); OUT = os.path.join(HERE, 'fma')
CFLAGS = ['-O2', '-ffp-contract=off', '-fno-math-errno', '-D_CRT_SECURE_NO_WARNINGS']
FMA = re.compile(r'\bvfn?m(add|sub)\d*[sp][sd]\b')

def extract(name):
    src = open(os.path.join(GEN, name + '.c'), encoding='utf-8').read().split('\n')
    keep = ['// Extracted by fma_undertest.py from orl/gen/%s.c: the code under test only.' % name, '#include <math.h>']
    i = 0
    while i < len(src):
        l = src[i]
        if l.startswith('static const double KK'): keep.append(l)
        elif re.match(r'static double (narrow|f_sqrt32|f_rsqrt32|f_hypot32)\(', l): keep.append(l[len('static '):])
        elif l.startswith('static double g_exp32('):
            keep.append(l[len('static '):])
            while not src[i].rstrip().endswith('}'):
                i += 1; keep.append(src[i])
        i += 1
    return '\n'.join(keep) + '\n'

def run(*a): return subprocess.run(list(a), capture_output=True, text=True)

def main():
    for name in ('sweep', 'sweep2'):
        c = os.path.join(OUT, 'undertest_%s.c' % name); o = os.path.join(OUT, 'undertest_%s.o' % name)
        open(c, 'w', newline='\n', encoding='utf-8').write(extract(name))
        q = run('clang', *CFLAGS, '-c', c, '-o', o)
        if q.returncode: print(q.stderr); return 1
        defined = [l.split()[-1] for l in run('llvm-nm', '--defined-only', o).stdout.splitlines() if ' T ' in l]
        undef = [l.split()[-1] for l in run('llvm-nm', '-u', o).stdout.splitlines() if l.strip()]
        dis = run('llvm-objdump', '-d', '-r', '--no-show-raw-insn', o).stdout.splitlines()
        insn = [l.split(':', 1)[1].strip() for l in dis if re.match(r'^\s+[0-9a-f]+:\s+\S', l) and 'IMAGE_REL' not in l]
        rel = sorted(set(l.split()[-1] for l in dis if 'IMAGE_REL' in l))
        calls = [t for t in insn if t.startswith('call')]
        jumps_out = [t for t in insn if re.match(r'jmp\s+\*', t)]
        print('undertest_%s.o: functions %s' % (name, ', '.join(defined)))
        print('  undefined symbols: %s' % (', '.join(undef) or 'none'))
        print('  relocation targets: %s' % (', '.join(rel) or 'none'))
        print('  instructions %d; call instructions %d; indirect jumps %d; fused multiply-add %d; sqrtsd %d' % (
            len(insn), len(calls), len(jumps_out), sum(1 for t in insn if FMA.search(t)), sum(1 for t in insn if t.startswith('sqrtsd'))))
    return 0

if __name__ == '__main__':
    sys.exit(main())
