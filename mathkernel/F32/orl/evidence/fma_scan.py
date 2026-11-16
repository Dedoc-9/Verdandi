# Fused multiply-add instructions in a linked program, attributed to functions through the linker map (2026-11-14).
#   python -B fma_scan.py PROGRAM.exe [PROGRAM.map]
# Disassembles with llvm-objdump, lists every vfmadd / vfmsub / vfnmadd / vfnmsub instruction, and with a map names the
# function (the map symbol with the greatest address not above the instruction) and the library and object it came from.
# With a map it also prints, for each function holding one, the direct call and jump sites that target it or any address
# inside it, and the functions those sites are in (one level; indirect calls through pointers are not followed).
import re, subprocess, sys
FMA = re.compile(r'\bvfn?m(add|sub)\d*[sp][sd]\b')
INSN = re.compile(r'^\s*([0-9a-f]+):\s+(.*)$')
TARGET = re.compile(r'^(call|jmp|j[a-z]+)[a-z]*\s+0x([0-9a-f]+)')

def disasm(exe):
    out = subprocess.run(['llvm-objdump', '-d', '--no-show-raw-insn', exe], capture_output=True, text=True).stdout
    rows = []
    for l in out.splitlines():
        m = INSN.match(l)
        if m: rows.append((int(m.group(1), 16), m.group(2).split('#')[0].strip()))
    return rows

def read_map(path):
    """[(address, name, lib:object)] sorted, from a Microsoft-format linker map (public and static symbols)."""
    syms = []
    for l in open(path, encoding='utf-8', errors='replace'):
        f = l.split()
        if len(f) >= 4 and re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{8}', f[0]) and re.fullmatch(r'[0-9a-f]{16}', f[2]):
            if f[0].startswith('0000:'): continue                        # absolute symbols, not code
            syms.append((int(f[2], 16), f[1], f[-1]))
    return sorted(set(syms))

def main():
    exe = sys.argv[1]; mp = sys.argv[2] if len(sys.argv) > 2 else None
    rows = disasm(exe)
    hits = [(a, t) for a, t in rows if FMA.search(t)]
    kinds = {}
    for a, t in hits:
        k = re.match(r'vfn?m(?:add|sub)', t.split()[0]).group(0); kinds[k] = kinds.get(k, 0) + 1
    print('%s: %d instructions disassembled, %d fused multiply-add (%s)' % (
        exe.replace('\\', '/').split('/')[-1], len(rows), len(hits),
        ', '.join('%s %d' % (k, kinds.get(k, 0)) for k in ('vfmadd', 'vfmsub', 'vfnmadd', 'vfnmsub'))))
    if not mp: return 0
    syms = read_map(mp); addrs = [s[0] for s in syms]
    import bisect
    def owner(a):
        i = bisect.bisect_right(addrs, a) - 1
        return i if i >= 0 else None
    def end(i): return addrs[i + 1] if i + 1 < len(addrs) else 1 << 62
    holders = {}
    for a, t in hits:
        i = owner(a); holders.setdefault(i, []).append((a, t))
        print('  %x  %-13s in %s  [%s]  (symbol at %x, +0x%x)' % (a, t.split()[0], syms[i][1], syms[i][2], syms[i][0], a - syms[i][0]))
    for i, hs in holders.items():
        lo, hi = syms[i][0], end(i)
        print('function %s  [%s]  %x..%x holds %d' % (syms[i][1], syms[i][2], lo, hi, len(hs)))
        # symbols that share the address (aliases)
        al = [s[1] for s in syms if s[0] == lo and s[1] != syms[i][1]]
        if al: print('  other names at this address: %s' % ', '.join(al))
        n = 0
        for a, t in rows:
            m = TARGET.match(t)
            if m and lo <= int(m.group(2), 16) < hi and not (lo <= a < hi):
                j = owner(a); n += 1
                print('  entered from %x  %-40s in %s  [%s]' % (a, t, syms[j][1], syms[j][2]))
        if not n: print('  no direct call or jump from outside targets it')
    return 0

if __name__ == '__main__':
    sys.exit(main())
