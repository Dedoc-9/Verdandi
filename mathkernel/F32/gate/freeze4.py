# Writes <folder>/FROZEN4.txt, the freeze list gate4.py reads (2026-11-14), and prints its sha256: the anchor.
#   python3 -B gate/freeze4.py <folder> [--replace]
# The list is exactly the set gate4.py requires, sorted by path: for the folder and every folder in its "deps", its
# gate.json and every file of its "files"; every plant file of the folder; every generator script named under
# "generated" (the folder's and its deps'); gate/gate4.py, gate/strict_read.py and the tier's expected-pa file.
# The rule is written here a second time, apart from gate4.py's: if the two part, gate4's row "every required entry is
# on it" fails. Nothing in the list depends on the clock, so the same sources give the same list and the same anchor.
# It is a manifest of the judged sources written AFTER the proofs. The anchor it prints is worth something only when it
# is recorded outside the tree; this script writes it nowhere. An existing FROZEN4.txt with other bytes is left as it
# is unless --replace is given (the anchor recorded for the old one then no longer holds, which is the point).
import hashlib, json, os, posixpath, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
HEAD = ('# FROZEN4 of %s: a manifest of the sources gate4.py judges, written after the proofs (the older FROZEN.txt, written '
        'before the proofs, is kept beside it); each line is sha256, two spaces, path from the tree\'s root; the sha256 of '
        'this file is the anchor, to be recorded outside the tree.\n')

def required(folder):
    def load(d): return json.loads(open(os.path.join(W, d, 'gate.json'), 'rb').read().decode('utf-8'))
    cfg = load(folder); need = set(['gate/gate4.py', 'gate/strict_read.py', 'gate/expected-pa-%s.txt' % cfg['tier']])
    for d in [x.strip('/') for x in cfg.get('deps', [])] + [folder]:
        c = cfg if d == folder else load(d)
        need.add(d + '/gate.json')
        for f in c['files']: need.add(d + '/' + f)
        for spec in c.get('generated', {}).values(): need.add(posixpath.normpath(spec[0]))
    for pl in cfg.get('plants', {}).values():
        for src in pl['replace'].values(): need.add(posixpath.normpath(folder + '/' + src))
    return sorted(need)

def main():
    args = [a for a in sys.argv[1:] if a != '--replace']; replace = '--replace' in sys.argv[1:]
    if len(args) != 1 or args[0].startswith('-'):
        print('usage: python3 -B gate/freeze4.py <folder> [--replace]'); return 2
    folder = args[0].strip('/'); lines = [HEAD % folder]
    for p in required(folder):
        try: b = open(os.path.join(W, p), 'rb').read()
        except OSError:
            print('freeze4: %s cannot be read; nothing written' % p); return 1
        lines.append('%s  %s\n' % (hashlib.sha256(b).hexdigest(), p))
    data = ''.join(lines).encode('ascii'); out = os.path.join(W, folder, 'FROZEN4.txt')
    try: old = open(out, 'rb').read()
    except OSError: old = None
    if old == data:
        print('%s/FROZEN4.txt is already this list: %d entries, not rewritten' % (folder, len(lines) - 1))
    elif old is not None and not replace:
        print('freeze4: %s/FROZEN4.txt exists with other bytes (sha256 %s); nothing written. --replace writes the new list.' % (folder, hashlib.sha256(old).hexdigest()))
        return 1
    else:
        with open(out, 'wb') as f: f.write(data)
        print('wrote %s/FROZEN4.txt: %d entries%s' % (folder, len(lines) - 1, '' if old is None else ' (replaced the list %s)' % hashlib.sha256(old).hexdigest()))
    print('anchor %s' % hashlib.sha256(data).hexdigest())
    return 0

if __name__ == '__main__':
    sys.exit(main())
