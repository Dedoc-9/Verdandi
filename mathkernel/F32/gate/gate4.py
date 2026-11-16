# The shared strict gate, fourth form (2026-11-14). gate3.py is kept byte for byte beside it. An independent review of
# gate3 reproduced four weaknesses (F3, F7, F13, F14); this form closes what a gate can close and says what it cannot.
#   docker run --rm --network none [-e ANCHOR=<sha256>] -v <mkf>:/work -w /work <image> python3 -B gate/gate4.py <folder> [--recheck]
# The tree it judges is the one it stands in (<tree>/gate/gate4.py; /work in the line above). It reads <folder>/gate.json.
#
# WHAT A RUN JUDGES. One folder's identity: Print Assumptions is read for the identity definition of <folder> only. The
# folders it depends on are compiled from their sources and rechecked by coqchk, but their own identities, plants and
# statements are judged only by a run on each of them. What it holds:
#   - the freeze list <folder>/FROZEN4.txt: every line readable (blank, a # comment, or 64 lower-case hex digits, two
#     spaces, a path relative to the tree), no path twice, every required entry on it (for the folder and each folder
#     it depends on: gate.json and every file of "files"; every plant file of the folder; every generator script named
#     under "generated"; gate/gate4.py, gate/strict_read.py and the tier's expected-pa file), every listed file with its
#     listed hash. The hashes held for gate/gate4.py and gate/strict_read.py are those of the bytes that ran;
#   - the anchor: the sha256 of FROZEN4.txt, printed, its first 16 digits in the verdict line, and compared with the
#     environment variable ANCHOR when one is given. The gate never reads an anchor from inside the tree;
#   - each generated file (the folder's and its dependencies') is what its generator prints;
#   - a fresh root outside the tree that holds only the listed sources, byte for byte as listed; every one of them
#     compiles there, in order; nothing compiled is taken from the tree;
#   - Print Assumptions of the folder's identity definition is exactly the tier's expected list, name and type;
#   - coqchk -norec accepts each of those modules, with <none> under type-in-type, unsafe fixpoints and positivity. With
#     -norec coqchk's "Axioms" block also lists what the admitted dependencies hold, so it is not read as a footprint;
#   - the closure holds no MKF library other than the ones compiled and rechecked here;
#   - every outside library of the closure is bound by content: the sha256 of the .vo file coqc loaded it from, in the
#     running image, has a line "<library> <sha256> <coqchk exit> <clean|notclean>" in libcache/checked4.log saying
#     exit 0 and clean. A library with no line for its present hash is checked now and its line appended (--recheck
#     checks every one now, whatever the log says);
#   - each plant is refused for its stated reason;
#   - the run wrote nothing in the tree but <folder>/out4/, libcache/checked4.log and libcache/out4/ (every other file
#     listed before and after: path, size, sha256). coqc and coqchk run with the fresh root as working directory.
#
# WHAT A RUN DOES NOT HOLD.
#   - A party who rewrites both the sources and the freeze list is caught ONLY by the anchor, and only when the anchor
#     was recorded outside the tree and is given to the run (ANCHOR). Without ANCHOR the run says "not anchored" and
#     shows no more than that the sources agree with a list standing beside them.
#   - FROZEN4.txt is a manifest of the judged sources written after the proofs. It does not show that a statement was
#     fixed before its proof: that is the older FROZEN.txt's claim, which this gate does not read.
#   - A line of checked4.log that claims "0 clean" under a library's true hash is believed (--recheck does not believe
#     it). coqchk 8.20 takes a logical name, not a file: that it reads the file coqc loaded rests on the two reporting
#     one library root (compared) and on that file standing outside the tree and the fresh root (compared).
#   - The image itself (coqc, coqchk, python3) is trusted; -norec admits each module's dependencies, so the outside
#     libraries are held one by one through the log, not by one recursive check.
#   - A generator's own inputs and imports are pinned only if someone lists them; a required entry is the script alone.
#   - Whether the statement says what it should, and whether the plants are the right plants, is a reader's judgment.
#   - A file another process writes in the tree during the run makes the last row fail; the row cannot tell who wrote.
import hashlib, json, os, posixpath, re, shutil, subprocess, sys, tempfile, traceback, types
sys.dont_write_bytecode = True
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
NONE3 = ('relying on type-in-type: <none>', 'unsafe (co)fixpoints: <none>', 'positivity is assumed: <none>')
COMPILED = ('.vo', '.vok', '.vos', '.glob', '.aux')
LINE = re.compile(r'([0-9a-f]{64})  ([A-Za-z0-9_][A-Za-z0-9_.+-]*(?:/[A-Za-z0-9_][A-Za-z0-9_.+-]*)*)')
LOGLINE = re.compile(r'(\S+) ([0-9a-f]{64}) (-?\d+) (clean|notclean)')
res = []

def rep(name, ok, det=''):
    res.append(bool(ok)); print('  %-62s %s  %s' % (name, 'ok' if ok else 'FAIL', det)); sys.stdout.flush()
def raw(p):
    try:
        with open(p, 'rb') as f: return f.read()
    except OSError: return None
def hx(b): return 'MISSING' if b is None else hashlib.sha256(b).hexdigest()
def sha(p): return hx(raw(p))
def rd(p):
    b = raw(p); return '' if b is None else b.decode('utf-8', 'replace')
def run(cmd, out, cwd, timeout=3600):
    try:
        p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        r, t = p.returncode, p.stdout
    except subprocess.TimeoutExpired as e:
        r, t = 124, (e.stdout or b'')
    except OSError as e:
        r, t = 127, str(e).encode('utf-8', 'replace')
    with open(out, 'wb') as f: f.write(t)
    return r
def said(cmd):
    try: return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=120).stdout.decode('utf-8', 'replace').strip()
    except (OSError, subprocess.TimeoutExpired): return ''
def clean_unsafe(t): return all(n in t for n in NONE3)
def mod(d, stem): return 'MKF.%s.%s' % (d.replace('/', '.'), stem)
def tag(d): return d.replace('/', '.')

def snapshot(skip_dirs, skip_files):
    """Every file under the tree but the places a run may write: {path: (size, sha256)}."""
    snap = {}
    for dp, dn, fn in os.walk(W):
        rel = os.path.relpath(dp, W).replace(os.sep, '/'); rel = '' if rel == '.' else rel + '/'
        for d in dn:
            if os.path.islink(os.path.join(dp, d)): snap[rel + d] = ('link', os.readlink(os.path.join(dp, d)))
        dn[:] = sorted(d for d in dn if rel + d not in skip_dirs)
        for f in fn:
            if rel + f in skip_files: continue
            full = os.path.join(dp, f)
            if os.path.islink(full): snap[rel + f] = ('link', os.readlink(full)); continue
            b = raw(full); snap[rel + f] = ('unreadable',) if b is None else (len(b), hx(b))
    return snap

def stop(msg):
    print('gate4: %s' % msg); print('GATE4 FAILED: the gate could not start (no row was judged)'); sys.exit(2)

def main(T):
    args = sys.argv[1:]; recheck = '--recheck' in args; args = [a for a in args if a != '--recheck']
    if len(args) != 1 or args[0].startswith('-'): stop('usage: python3 -B gate/gate4.py <folder> [--recheck]')
    if os.path.relpath(os.path.abspath(__file__), W).replace(os.sep, '/') != 'gate/gate4.py':
        stop('the gate runs as <tree>/gate/gate4.py; this file is %s' % os.path.abspath(__file__))
    GD = args[0].strip('/'); G = os.path.join(W, GD); O = os.path.join(G, 'out4')
    LC = os.path.join(W, 'libcache'); LOG = os.path.join(LC, 'checked4.log'); LO = os.path.join(LC, 'out4')
    SELF = sha(os.path.abspath(__file__)); srb = raw(os.path.join(HERE, 'strict_read.py'))
    if srb is None: stop('gate/strict_read.py cannot be read')
    S = types.ModuleType('strict_read'); exec(compile(srb, os.path.join(HERE, 'strict_read.py'), 'exec'), S.__dict__)   # the source, never a cached .pyc
    RAN = {'gate/gate4.py': SELF, 'gate/strict_read.py': hx(srb)}
    cfgs = {}
    def load(d):
        try: cfgs[d] = json.loads(raw(os.path.join(W, d, 'gate.json')).decode('utf-8'))
        except Exception as e: stop('%s/gate.json cannot be read: %s' % (d, e))
        return cfgs[d]
    cfg = load(GD); DIRS = [d.strip('/') for d in cfg.get('deps', [])] + [GD]
    for d in DIRS[:-1]: load(d)
    FILES = {d: list(cfgs[d]['files']) for d in DIRS}
    for d in DIRS:
        for f in FILES[d]:
            if not re.fullmatch(r'[A-Za-z_]\w*\.v', f): stop('%s/gate.json names a file that is not a plain .v name: %r' % (d, f))
    ident = cfg['identity']; name = cfg['name']; epa_path = 'gate/expected-pa-%s.txt' % cfg['tier']
    if ident + '.v' not in FILES[GD]: stop('the identity module %s is not one of the folder\'s files' % ident)
    try: EPA = S.expected_pa(os.path.join(W, epa_path))
    except OSError as e: stop('%s cannot be read: %s' % (epa_path, e))
    before = snapshot({GD + '/out4', 'libcache/out4'}, {'libcache/checked4.log'})
    print('gate4.py %s judges %s (identity %s.%s; sources of %s) in %s%s' % (SELF, GD, tag(GD), ident, ', '.join(DIRS), W, '  --recheck' if recheck else ''))

    # 1. the boundary: the freeze list, the anchor, the generated files
    fb = raw(os.path.join(G, 'FROZEN4.txt')); anchor = None if fb is None else hx(fb)
    print('anchor %s' % (anchor if anchor else 'none: %s/FROZEN4.txt cannot be read' % GD))
    entries, unread = [], ([] if fb is not None else ['no %s/FROZEN4.txt' % GD])
    for n, l in enumerate((fb or b'').decode('latin-1').split('\n'), 1):
        if l == '' or l.startswith('#'): continue
        m = LINE.fullmatch(l)
        if m: entries.append((m.group(1), m.group(2)))
        else: unread.append('line %d %r' % (n, l[:110]))
    rep('freeze list: every line is readable', fb is not None and not unread, '%d entries' % len(entries) if not unread else '%d unreadable: %s' % (len(unread), '; '.join(unread[:4])))
    paths = [p for _, p in entries]; twice = sorted(set(p for p in paths if paths.count(p) > 1))
    rep('freeze list: no path is listed twice', entries and not twice, '' if not twice else 'twice: %s' % ', '.join(twice[:6]))
    need = set(['gate/gate4.py', 'gate/strict_read.py', epa_path])
    for d in DIRS:
        need.add(d + '/gate.json'); need.update(d + '/' + f for f in FILES[d])
        need.update(posixpath.normpath(spec[0]) for spec in cfgs[d].get('generated', {}).values())
    for pl in cfg.get('plants', {}).values(): need.update(posixpath.normpath(GD + '/' + s) for s in pl['replace'].values())
    missing = sorted(need - set(paths))
    rep('freeze list: every required entry is on it', entries and not missing, '%d required, %d listed' % (len(need), len(set(paths))) if not missing else 'missing: %s' % ', '.join(missing[:8]))
    bad = ['%s%s' % (p, ' (absent)' if sha(os.path.join(W, p)) == 'MISSING' else '') for h, p in entries if (RAN.get(p) or sha(os.path.join(W, p))) != h]
    rep('frozen inputs unchanged', entries and not bad, '%d files' % len(entries) if not bad else '%d of %d differ from their line: %s' % (len(bad), len(entries), ', '.join(bad[:6])))
    listed = {}
    for h, p in entries: listed.setdefault(p, h)
    if 'ANCHOR' in os.environ:
        given = os.environ['ANCHOR']
        rep('freeze list is the anchored one', anchor is not None and given == anchor, 'ANCHOR %s' % given[:16] if given == anchor else 'ANCHOR given %r, this list is %s' % (given[:64], anchor))
    else:
        print('not anchored: no ANCHOR given')
    gencwd = os.path.join(T, 'gen'); os.makedirs(gencwd)
    def emitted(spec):
        try:
            p = subprocess.run(['python3', '-B', os.path.join(W, spec[0])] + list(spec[1:]), cwd=gencwd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3600)
            return p.stdout if p.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired): return None
    gens = {}
    for d in DIRS:
        for path, spec in sorted(cfgs[d].get('generated', {}).items()):
            gens[path] = spec; e = emitted(spec); b = raw(os.path.join(W, path))
            rep('%s is what %s emits' % (path, spec[0]), e is not None and b is not None and b == e, '' if e is not None else 'the generator did not end with exit 0')

    # 2. the proof, from the listed sources, in a fresh root outside the tree
    shutil.rmtree(O, ignore_errors=True); os.makedirs(O)
    B = os.path.join(T, 'root'); want = [d + '/' + f for d in DIRS for f in FILES[d]]
    for d in DIRS:
        os.makedirs(os.path.join(B, d))
        for f in FILES[d]:
            b = raw(os.path.join(W, d, f))
            if b is not None:
                with open(os.path.join(B, d, f), 'wb') as fh: fh.write(b)
    have = {os.path.relpath(os.path.join(dp, f), B).replace(os.sep, '/'): sha(os.path.join(dp, f)) for dp, _, fs in os.walk(B) for f in fs}
    off = [p for p in want if have.get(p) is None or listed.get(p) != have.get(p)] + sorted(set(have) - set(want))
    rep('fresh root holds only the listed sources', want and not off, '%d sources of %d folders, no other file' % (len(want), len(DIRS)) if not off else 'not as listed: %s' % ', '.join(off[:6]))
    def build(root, outdir, dirs):
        """Compile the given folders' files, in order, under root (the working directory); {(folder, stem): exit}."""
        rcs = {}
        for d in dirs:
            for f in FILES[d]:
                rcs[(d, f[:-2])] = run(['coqc', '-R', root, 'MKF', os.path.join(root, d, f)], os.path.join(outdir, '%s.%s.out' % (tag(d), f[:-2])), root)
        return rcs
    rcs = build(B, O, DIRS)
    for (d, stem), r in rcs.items():
        rep('compile %s/%s' % (d, stem), r == 0, 'exit %s%s' % (r, '' if r == 0 else ' | ' + ' '.join(rd(os.path.join(O, '%s.%s.out' % (tag(d), stem))).split())[-260:]))
    ok, pa, viol = S.read_pa_only(rd(os.path.join(O, '%s.%s.out' % (tag(GD), ident))), EPA)
    rep('identity: Print Assumptions is exactly the %s list' % cfg['tier'], rcs.get((GD, ident)) == 0 and ok, '%d axioms' % len(pa) if ok else '; '.join(viol)[:300])
    for d in DIRS:
        for f in FILES[d]:
            stem = f[:-2]; out = os.path.join(O, '%s.%s.coqchk.out' % (tag(d), stem))
            r = run(['coqchk', '-silent', '-o', '-R', B, 'MKF', '-norec', mod(d, stem)], out, B)
            rep('coqchk -norec %s/%s' % (d, stem), r == 0 and clean_unsafe(rd(out)), 'exit %s, unsafe sections %s' % (r, '<none>' if clean_unsafe(rd(out)) else 'NOT clean'))
    print('  sources judged: %s' % ', '.join('%s %s' % (p, have.get(p, 'MISSING')[:12]) for p in want))

    # 3. the closure: ours compiled here, the outside libraries bound by the content of the files loaded
    X = os.path.join(T, 'aux'); os.makedirs(X); E = os.path.join(T, 'empty'); os.makedirs(E)
    with open(os.path.join(X, 'Closure.v'), 'w') as f: f.write('From MKF Require %s.\nPrint Libraries.\n' % mod(GD, ident)[4:])
    rc = run(['coqc', '-R', B, 'MKF', os.path.join(X, 'Closure.v')], os.path.join(O, 'Closure.out'), B)
    libs = sorted(set(l.strip() for l in rd(os.path.join(O, 'Closure.out')).splitlines() if re.match(r'^ +[A-Za-z_][\w.]*$', l))) if rc == 0 else []
    ext = [l for l in libs if not l.startswith('MKF.')]
    ours = set(mod(d, f[:-2]) for d in DIRS for f in FILES[d])
    stray = [l for l in libs if l.startswith('MKF.') and l not in ours]
    rep('closure: every MKF library is one compiled and rechecked above', libs and not stray, '%d of ours in the closure%s' % (len([l for l in libs if l in ours]), '' if not stray else '; stray: %s' % stray[:5]))
    with open(os.path.join(X, 'Locate.v'), 'w') as f: f.write('From MKF Require %s.\n%s' % (mod(GD, ident)[4:], ''.join('Locate Library %s.\n' % l for l in ext)))
    run(['coqc', '-R', B, 'MKF', os.path.join(X, 'Locate.v')], os.path.join(O, 'Locate.out'), B)
    where = dict(re.findall(r'(\S+) has been loaded from file (\S+)', ' '.join(rd(os.path.join(O, 'Locate.out')).split())))
    roots = (said(['coqc', '-where']), said(['coqchk', '-where']))
    known, unreadable = {}, 0
    if not recheck:
        for l in rd(LOG).split('\n'):
            m = LOGLINE.fullmatch(l)
            if m: known[(m.group(1), m.group(2))] = (int(m.group(3)), m.group(4))     # a later line replaces an earlier one
            elif l != '': unreadable += 1
    if unreadable: print('  libcache/checked4.log: %d lines not of the form "<library> <sha256> <exit> <clean|notclean>", not read' % unreadable)
    dirty, from_log, now = [], 0, 0
    for l in ext:
        vo = where.get(l)
        if vo is None or raw(vo) is None: dirty.append('%s: no file reported loaded' % l); continue
        inside = [r for r in (W, T) if os.path.realpath(vo).startswith(os.path.realpath(r) + os.sep)]
        if inside: dirty.append('%s: loaded from %s, not from the image' % (l, vo)); continue
        h = sha(vo)
        if (l, h) in known: from_log += 1; r, c = known[(l, h)]
        else:
            os.makedirs(LO, exist_ok=True); out = os.path.join(LO, l + '.out')
            r = run(['coqchk', '-silent', '-o', '-norec', l], out, E); c = 'clean' if clean_unsafe(rd(out)) else 'notclean'; now += 1
            if sha(vo) != h: dirty.append('%s: its file changed while it was checked' % l); continue
            with open(LOG, 'a') as f: f.write('%s %s %d %s\n' % (l, h, r, c))
            print('  checked in this run: %s %s exit %d %s' % (l, h, r, c)); sys.stdout.flush()
        if r != 0 or c != 'clean': dirty.append('%s %s: exit %d %s' % (l, h[:12], r, c))
    same_root = roots[0] != '' and roots[0] == roots[1]
    rep('closure: every outside library passed coqchk -norec, unsafe <none>', ext and not dirty and same_root,
        '%d libraries by the sha256 of their files: %d from the log, %d checked in this run%s%s' % (len(ext), from_log, now, '' if not dirty else '; not passed: %s' % '; '.join(dirty[:5]), '' if same_root else '; coqc and coqchk name different library roots: %s' % (roots,)))

    # 4. the plants: the verified root, one file replaced, the folder rebuilt
    order = [f[:-2] for f in FILES[GD]]
    for pname, pl in sorted(cfg.get('plants', {}).items()):
        root = os.path.join(T, 'plant', pname); shutil.copytree(B, root)
        for f in os.listdir(os.path.join(root, GD)):
            if f.endswith(COMPILED): os.remove(os.path.join(root, GD, f))
        gone = [src for src in pl['replace'].values() if raw(os.path.join(G, src)) is None]
        if gone: rep('plant %s refused' % pname, False, 'plant file absent: %s' % ', '.join(gone)); continue
        for dst, src in pl['replace'].items(): shutil.copyfile(os.path.join(G, src), os.path.join(root, GD, dst))
        po = os.path.join(O, 'plants', pname); os.makedirs(po)
        prc = build(root, po, [GD]); pout = lambda s: rd(os.path.join(po, '%s.%s.out' % (tag(GD), s)))
        if 'generated' in pl:
            e = emitted(gens[pl['generated']]) if pl['generated'] in gens else None
            caught = e is not None and raw(os.path.join(root, pl['generated'])) != e
            det = 'the planted file is not the generator\'s output'
        elif 'fails' in pl:
            k = order.index(pl['fails']); t = pout(pl['fails'])
            caught = all(prc[(GD, s)] == 0 for s in order[:k]) and prc[(GD, pl['fails'])] not in (0, None) and pl['text'] in t
            det = '%s exit %s: %s' % (pl['fails'], prc[(GD, pl['fails'])], ' '.join(t.split())[-170:])
        else:
            pok, _, pv = S.read_pa_only(pout(ident), EPA)
            caught = all(r == 0 for r in prc.values()) and not pok and any(pl['reader'] in v for v in pv)
            det = 'compiled; PA: %s' % '; '.join(pv)[:170]
        rep('plant %s refused' % pname, caught, det)

    # 5. the run's own footprint in the tree
    after = snapshot({GD + '/out4', 'libcache/out4'}, {'libcache/checked4.log'})
    diff = ['appeared %s' % p for p in sorted(set(after) - set(before))] + ['gone %s' % p for p in sorted(set(before) - set(after))] + ['changed %s' % p for p in sorted(set(after) & set(before)) if after[p] != before[p]]
    rep('nothing written to the tree outside out4 and the library log', not diff, '%d files as they were' % len(after) if not diff else '%d differ: %s' % (len(diff), ', '.join(diff[:6])))
    print('%s GATE4 %s: %d of %d  [anchor %s]' % (name, 'HELD' if all(res) else 'FAILED', sum(res), len(res), anchor[:16] if anchor else 'none'))
    return 0 if all(res) else 1

if __name__ == '__main__':
    T = tempfile.mkdtemp(prefix='gate4-', dir='/tmp'); code = 2
    try:
        code = main(T)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 2
    except BaseException:
        traceback.print_exc(file=sys.stdout)
        print('GATE4 FAILED: the gate stopped on an error after %d rows (no verdict on the rest)' % len(res))
    finally:
        shutil.rmtree(T, ignore_errors=True)
    sys.exit(code)
