# The shared strict gate, third form (2026-11-14). As gate.py, with one hole closed: gate.py compiled only its own
# folder and took the compiled files of the folders it depends on as it found them. Here nothing compiled is taken:
# the folder and every folder it depends on are copied as sources into a fresh root, compiled there in order, and every
# one of their modules is rechecked by coqchk. gate.py is kept as it was (the F32 and P32 gates froze it).
#   docker run --rm --network none -e IMG=<image id> -v <mkf>:/work -w /work <image> python3 gate/gate3.py <folder>
# It reads <folder>/gate.json. What it holds:
#   - frozen inputs unchanged (<folder>/FROZEN.txt); each generated file is what its generator prints;
#   - every source of the folder and of its dependencies compiles in a fresh root; the identity module (which imports
#     nothing) is a Definition of the frozen statement's type;
#   - Print Assumptions of that definition is exactly the tier's expected list, name and type (strict_read.py);
#   - coqchk -norec accepts each of those modules, with <none> under type-in-type, unsafe fixpoints and positivity. With
#     -norec coqchk's "Axioms" block also lists what the admitted dependencies hold, so it is not read as a footprint;
#   - every outside library of the closure has passed coqchk -norec for this image (libcache, resumable);
#   - each plant is refused for its stated reason.
import hashlib, json, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import strict_read as S
W = '/work'; GD = sys.argv[1].strip('/'); G = os.path.join(W, GD); O = os.path.join(G, 'out'); B = '/tmp/gate-build'
cfg = json.load(open(os.path.join(G, 'gate.json'), encoding='utf-8'))
DIRS = cfg.get('deps', []) + [GD]
FILES = {d: (cfg['files'] if d == GD else json.load(open(os.path.join(W, d, 'gate.json'), encoding='utf-8'))['files']) for d in DIRS}
EPA = S.expected_pa(os.path.join(HERE, 'expected-pa-%s.txt' % cfg['tier']))
NONE3 = ('relying on type-in-type: <none>', 'unsafe (co)fixpoints: <none>', 'positivity is assumed: <none>')
COMPILED = ('*.vo', '*.vok', '*.vos', '*.glob', '*.aux', '.*.aux')
res = []
def rep(name, ok, det=''): res.append(bool(ok)); print('  %-62s %s  %s' % (name, 'ok' if ok else 'FAIL', det)); sys.stdout.flush()
def sha(p):
    try: return hashlib.sha256(open(p, 'rb').read()).hexdigest()
    except OSError: return 'MISSING'
def rd(p):
    try: return open(p, encoding='utf-8', errors='replace').read()
    except OSError: return ''
def run(cmd, out, timeout=3600):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        r, t = p.returncode, p.stdout
    except subprocess.TimeoutExpired as e:
        r, t = 124, (e.stdout or b'')
    open(out, 'wb').write(t); return r
def build(root, outdir, dirs):
    """Compile the given folders' files, in order, under root; returns {(folder, stem): exit}."""
    rcs = {}
    for d in dirs:
        for f in FILES[d]:
            rcs[(d, f[:-2])] = run(['coqc', '-R', root, 'MKF', os.path.join(root, d, f)], os.path.join(outdir, '%s.%s.out' % (d.replace('/', '.'), f[:-2])))
    return rcs
def mod(d, stem): return 'MKF.%s.%s' % (d.replace('/', '.'), stem)
clean_unsafe = lambda t: all(n in t for n in NONE3)

# 1. boundary
frozen = [l.split(None, 1) for l in rd(os.path.join(G, 'FROZEN.txt')).splitlines() if re.match(r'^[0-9a-f]{64}\s', l)]
bad = [p.strip() for h, p in frozen if sha(os.path.join(W, p.strip())) != h]
rep('frozen inputs unchanged', frozen and not bad, '%d files%s' % (len(frozen), '' if not bad else ', changed: %s' % bad))
img = os.environ.get('IMG', ''); rep('library cache is this image\'s', img and rd(os.path.join(W, 'libcache/IMAGE.txt')).strip() == img, img[:19])
def emitted(spec):
    return subprocess.run(['python3', '-B', os.path.join(W, spec[0])] + spec[1:], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
for path, spec in sorted(cfg.get('generated', {}).items()):
    rep('%s is what %s emits' % (path, spec[0]), open(os.path.join(W, path), 'rb').read() == emitted(spec))
# 2. the proof, from sources, in a fresh root
shutil.rmtree(O, ignore_errors=True); os.makedirs(O); shutil.rmtree(B, ignore_errors=True)
for d in DIRS: shutil.copytree(os.path.join(W, d), os.path.join(B, d), ignore=shutil.ignore_patterns('out*', 'plants', *COMPILED))
left = [os.path.join(dp, f) for dp, _, fs in os.walk(B) for f in fs if f.endswith(('.vo', '.vos', '.vok'))]
rep('fresh root holds no compiled file', not left, '%d folders copied as sources' % len(DIRS))
rcs = build(B, O, DIRS)
for (d, stem), r in rcs.items():
    rep('compile %s/%s' % (d, stem), r == 0, 'exit %s%s' % (r, '' if r == 0 else ' | ' + ' '.join(rd(os.path.join(O, '%s.%s.out' % (d.replace('/', '.'), stem))).split())[-260:]))
ident = cfg['identity']; iout = os.path.join(O, '%s.%s.out' % (GD.replace('/', '.'), ident))
ok, entries, viol = S.read_pa_only(rd(iout), EPA)
rep('identity: Print Assumptions is exactly the %s list' % cfg['tier'], rcs.get((GD, ident)) == 0 and ok, '%d axioms' % len(entries) if ok else '; '.join(viol)[:300])
for d in DIRS:
    for f in FILES[d]:
        stem = f[:-2]; out = os.path.join(O, '%s.%s.coqchk.out' % (d.replace('/', '.'), stem))
        r = run(['coqchk', '-silent', '-o', '-R', B, 'MKF', '-norec', mod(d, stem)], out)
        rep('coqchk -norec %s/%s' % (d, stem), r == 0 and clean_unsafe(rd(out)), 'exit %s, unsafe sections %s' % (r, '<none>' if clean_unsafe(rd(out)) else 'NOT clean'))
print('  sources judged: %s' % ', '.join('%s/%s %s' % (d, f, sha(os.path.join(W, d, f))[:12]) for d in DIRS for f in FILES[d]))
# 3. the closure, through the image's library cache
open(os.path.join(O, 'Closure.v'), 'w').write('From MKF Require %s.\nPrint Libraries.\n' % mod(GD, ident)[4:])
run(['coqc', '-R', B, 'MKF', os.path.join(O, 'Closure.v')], os.path.join(O, 'Closure.out'))
libs = sorted(set(l.strip() for l in rd(os.path.join(O, 'Closure.out')).splitlines() if re.match(r'^ +[A-Za-z_][\w.]*$', l)))
ext = [l for l in libs if not l.startswith('MKF.')]
ours = set(mod(d, f[:-2]) for d in DIRS for f in FILES[d])
stray = [l for l in libs if l.startswith('MKF.') and l not in ours]
rep('closure: every MKF library is one compiled and rechecked above', libs and not stray, '%d of ours in the closure%s' % (len([l for l in libs if l in ours]), '' if not stray else '; stray: %s' % stray[:5]))
LC = os.path.join(W, 'libcache'); plog = os.path.join(LC, 'progress.log')
passed = set(l.split()[0] for l in rd(plog).splitlines() if len(l.split()) >= 2 and l.split()[1] == '0')
new = [l for l in ext if l not in passed]
for l in new:
    r = run(['coqchk', '-silent', '-o', '-R', B, 'MKF', '-norec', l], os.path.join(LC, 'out', l + '.out'))
    open(plog, 'a').write('%s %d gate\n' % (l, r))
    if r == 0: passed.add(l)
dirty = [l for l in ext if l not in passed or not clean_unsafe(rd(os.path.join(LC, 'out', l + '.out')))]
rep('closure: every outside library passed coqchk -norec, unsafe <none>', ext and not dirty, '%d libraries, %d newly checked%s' % (len(ext), len(new), '' if not dirty else '; not passed: %s' % dirty[:5]))
# 4. the plants: the verified root, one file replaced, the folder rebuilt
order = [f[:-2] for f in cfg['files']]
for name, pl in sorted(cfg.get('plants', {}).items()):
    root = '/tmp/gate-plant/%s' % name; shutil.rmtree(root, ignore_errors=True); shutil.copytree(B, root)
    for f in os.listdir(os.path.join(root, GD)):
        if f.endswith(('.vo', '.vok', '.vos', '.glob', '.aux')): os.remove(os.path.join(root, GD, f))
    for dst, src in pl['replace'].items(): shutil.copyfile(os.path.join(G, src), os.path.join(root, GD, dst))
    po = os.path.join(O, 'plants', name); os.makedirs(po)
    prc = build(root, po, [GD]); pout = lambda s: rd(os.path.join(po, '%s.%s.out' % (GD.replace('/', '.'), s)))
    if 'generated' in pl:
        caught = open(os.path.join(root, pl['generated']), 'rb').read() != emitted(cfg['generated'][pl['generated']])
        det = 'the planted file is not the generator\'s output'
    elif 'fails' in pl:
        k = order.index(pl['fails']); t = pout(pl['fails'])
        caught = all(prc[(GD, s)] == 0 for s in order[:k]) and prc[(GD, pl['fails'])] not in (0, None) and pl['text'] in t
        det = '%s exit %s: %s' % (pl['fails'], prc[(GD, pl['fails'])], ' '.join(t.split())[-170:])
    else:
        pok, _, pv = S.read_pa_only(pout(ident), EPA)
        caught = all(r == 0 for r in prc.values()) and not pok and any(pl['reader'] in v for v in pv)
        det = 'compiled; PA: %s' % '; '.join(pv)[:170]
    rep('plant %s refused' % name, caught, det)
print('%s GATE %s: %d of %d' % (cfg['name'], 'HELD' if all(res) else 'FAILED', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
