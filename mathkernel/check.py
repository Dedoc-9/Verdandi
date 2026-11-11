#!/usr/bin/env python
# mathkernel/check.py - standalone subsystem boundary check. NO Verdandi gate row (by the owner's
# gate-stops-growing ruling, 2026-10-09); this is the subsystem's own check, like art/check.py,
# graybox/check.py, design/test_design.py.
#
# It FAILS if any mathkernel source has an UPWARD dependency (imports/includes a Verdandi or Orlog
# component, or the oracle/binding pulls host libm), or if a CONSUMER reaches a kernel INTERNAL
# (the oracle header fdlibm.h) instead of the public interface. The planted canaries in test/ prove
# the detectors bite (an apparatus that catches nothing proves nothing).
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
UP = ('graybox', 'shell', 'kernel', 'art', 'workshop', 'verify', 'design', 'orlog')
RE_PY_IMPORT = re.compile(r'(?m)^\s*(?:import|from)\s+([A-Za-z0-9_.]+)')
RE_C_INCLUDE = re.compile(r'(?m)^\s*#\s*include\s*[<"]([^">]+)[">]')

def violations(path, text):
    v = []
    rel = os.path.relpath(path, HERE).replace('\\', '/')
    in_oracle_src = rel.startswith('ORACLE/src/')
    if path.endswith('.py'):
        for m in RE_PY_IMPORT.finditer(text):
            top = m.group(1).split('.')[0]
            if top in UP:
                v.append(('upward-dependency', 'imports %s' % m.group(1)))
    if path.endswith(('.c', '.h')):
        for m in RE_C_INCLUDE.finditer(text):
            inc = m.group(1); base = os.path.basename(inc).lower()
            if base == 'math.h':
                v.append(('host-libm', 'includes <math.h>; the oracle is self-contained'))
            if base == 'fdlibm.h' and not in_oracle_src:
                v.append(('internal-reach', 'includes the oracle internal fdlibm.h outside ORACLE/src'))
            comps = [c for c in re.split(r'[\\/]', inc.lower()) if c]
            if any(c in UP for c in comps):  # exact path component, not substring (mathkernel.h is internal)
                v.append(('upward-dependency', 'includes %s' % inc))
    return v

def scan():
    real, canaries = [], []
    for root, _, files in os.walk(HERE):
        for f in files:
            if not f.endswith(('.py', '.c', '.h')):
                continue
            p = os.path.join(root, f)
            if os.path.abspath(p) == os.path.abspath(__file__):
                continue  # the checker does not check itself
            (canaries if f.startswith('canary_') else real).append(p)
    return sorted(real), sorted(canaries)

def main():
    real, canaries = scan()
    bad = []
    for p in real:
        v = violations(p, open(p, encoding='utf-8', errors='replace').read())
        if v:
            bad.append((p, v))
    caught = []
    for p in canaries:
        v = violations(p, open(p, encoding='utf-8', errors='replace').read())
        caught.append((p, v))
    print('mathkernel boundary check')
    print('  real sources scanned: %d | violations: %d' % (len(real), sum(len(v) for _, v in bad)))
    for p, v in bad:
        print('   FAIL %s %s' % (os.path.relpath(p, HERE), v))
    print('  planted canaries: %d' % len(canaries))
    all_caught = True
    for p, v in caught:
        ok = len(v) > 0
        all_caught &= ok
        print('   canary %s %s %s' % (os.path.relpath(p, HERE),
              'CAUGHT' if ok else 'NOT CAUGHT (apparatus broken)', [k for k, _ in v]))
    ok = (len(bad) == 0) and all_caught and (len(canaries) >= 2)
    print('MATHKERNEL CHECK %s' % ('PASSED' if ok else 'FAILED'))
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
