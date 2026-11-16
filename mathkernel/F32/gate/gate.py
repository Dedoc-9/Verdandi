# The shared strict gate for MKF proof folders (2026-11-14). One command, one verdict:
#   docker run --rm --network none -e IMG=<image id> -v <mkf>:/work -w /work <image> python3 gate/gate.py <folder>
# It reads <folder>/gate.json. What it holds, from the lessons of gates v1 and v2:
#   - frozen inputs unchanged (<folder>/FROZEN.txt);
#   - every file compiles; the identity module (which imports nothing) is a Definition of the frozen statement's type;
#   - Print Assumptions of that definition is exactly the tier's expected list, name and type (strict_read.py);
#   - coqchk -norec accepts each module, with <none> under type-in-type, unsafe fixpoints and positivity. With -norec
#     coqchk's "Axioms" block also lists what the admitted dependencies hold, so it is not read as a footprint;
#   - every library of the closure has passed coqchk -norec for this image (libcache, resumable, keyed to the image);
#   - each plant is refused for its stated reason.
import hashlib, json, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import strict_read as S
W = '/work'; GD = sys.argv[1].strip('/'); G = os.path.join(W, GD); O = os.path.join(G, 'out')
cfg = json.load(open(os.path.join(G, 'gate.json'), encoding='utf-8'))
EPA = S.expected_pa(os.path.join(HERE, 'expected-pa-%s.txt' % cfg['tier']))
NONE3 = ('relying on type-in-type: <none>', 'unsafe (co)fixpoints: <none>', 'positivity is assumed: <none>')
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
def clean(d):
    for f in os.listdir(d):
        if f.endswith(('.vo', '.vok', '.vos', '.glob', '.aux')): os.remove(os.path.join(d, f))
def mod(stem, gd=GD): return 'MKF.%s.%s' % (gd.replace('/', '.'), stem)
def build(root, outdir):
    """Compile the folder's files in order under root; returns {stem: exit}."""
    rcs = {}
    for f in cfg['files']:
        stem = f[:-2]
        rcs[stem] = run(['coqc', '-R', root, 'MKF', os.path.join(root, GD, f)], os.path.join(outdir, stem + '.out'))
    return rcs
clean_unsafe = lambda t: all(n in t for n in NONE3)

# 1. boundary
frozen = [l.split(None, 1) for l in rd(os.path.join(G, 'FROZEN.txt')).splitlines() if re.match(r'^[0-9a-f]{64}\s', l)]
bad = [p.strip() for h, p in frozen if sha(os.path.join(W, p.strip())) != h]
rep('frozen inputs unchanged', frozen and not bad, '%d files%s' % (len(frozen), '' if not bad else ', changed: %s' % bad))
img = os.environ.get('IMG', ''); rep('library cache is this image\'s', img and rd(os.path.join(W, 'libcache/IMAGE.txt')).strip() == img, img[:19])
def emitted(spec):
    """The bytes a generator prints for a generated file: [script, args...], run with the container's python3."""
    return subprocess.run(['python3', '-B', os.path.join(W, spec[0])] + spec[1:], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
for path, spec in sorted(cfg.get('generated', {}).items()):
    rep('%s is what %s emits' % (path, spec[0]), open(os.path.join(W, path), 'rb').read() == emitted(spec))
# 2. the proof
shutil.rmtree(O, ignore_errors=True); os.makedirs(O); clean(G)
rcs = build(W, O)
for stem, r in rcs.items():
    rep('compile %s' % stem, r == 0, 'exit %s%s' % (r, '' if r == 0 else ' | ' + ' '.join(rd(os.path.join(O, stem + '.out')).split())[-260:]))
ident = cfg['identity']
ok, entries, viol = S.read_pa_only(rd(os.path.join(O, ident + '.out')), EPA)
rep('identity: Print Assumptions is exactly the %s list' % cfg['tier'], rcs.get(ident) == 0 and ok, '%d axioms' % len(entries) if ok else '; '.join(viol)[:300])
for f in cfg['files']:
    stem = f[:-2]; out = os.path.join(O, stem + '.coqchk.out')
    r = run(['coqchk', '-silent', '-o', '-R', W, 'MKF', '-norec', mod(stem)], out)
    rep('coqchk -norec %s' % stem, r == 0 and clean_unsafe(rd(out)), 'exit %s, unsafe sections %s' % (r, '<none>' if clean_unsafe(rd(out)) else 'NOT clean'))
print('  proof judged: %s' % ', '.join('%s %s' % (f, sha(os.path.join(G, f))[:12]) for f in cfg['files']))
# 3. the closure, through the image's library cache
open(os.path.join(O, 'Closure.v'), 'w').write('From MKF Require %s.\nPrint Libraries.\n' % mod(ident)[4:])
run(['coqc', '-R', W, 'MKF', os.path.join(O, 'Closure.v')], os.path.join(O, 'Closure.out'))
libs = sorted(set(l.strip() for l in rd(os.path.join(O, 'Closure.out')).splitlines() if re.match(r'^ +[A-Za-z_][\w.]*$', l)) )
ext = [l for l in libs if not l.startswith('MKF.')]
LC = os.path.join(W, 'libcache'); plog = os.path.join(LC, 'progress.log')
passed = set(l.split()[0] for l in rd(plog).splitlines() if len(l.split()) >= 2 and l.split()[1] == '0')
new = [l for l in ext if l not in passed]
for l in new:
    r = run(['coqchk', '-silent', '-o', '-R', W, 'MKF', '-norec', l], os.path.join(LC, 'out', l + '.out'))
    open(plog, 'a').write('%s %d gate\n' % (l, r))
    if r == 0: passed.add(l)
dirty = [l for l in ext if l not in passed or not clean_unsafe(rd(os.path.join(LC, 'out', l + '.out')))]
rep('closure: every library passed coqchk -norec, unsafe <none>', ext and not dirty, '%d libraries, %d newly checked%s' % (len(ext), len(new), '' if not dirty else '; not passed: %s' % dirty[:5]))
# 4. the plants
for name, pl in sorted(cfg.get('plants', {}).items()):
    root = '/tmp/gate-plant/%s' % name; shutil.rmtree(root, ignore_errors=True)
    for d in [GD] + cfg.get('deps', []):
        shutil.copytree(os.path.join(W, d), os.path.join(root, d), ignore=shutil.ignore_patterns('out*', 'plants'))
    clean(os.path.join(root, GD))
    for dst, src in pl['replace'].items(): shutil.copyfile(os.path.join(G, src), os.path.join(root, GD, dst))
    po = os.path.join(O, 'plants', name); os.makedirs(po)
    prc = build(root, po)
    if 'generated' in pl:
        caught = open(os.path.join(root, pl['generated']), 'rb').read() != emitted(cfg['generated'][pl['generated']])
        det = 'the planted file is not the generator\'s output'
    elif 'fails' in pl:
        order = [f[:-2] for f in cfg['files']]; k = order.index(pl['fails']); t = rd(os.path.join(po, pl['fails'] + '.out'))
        caught = all(prc[s] == 0 for s in order[:k]) and prc[pl['fails']] not in (0, None) and pl['text'] in t
        det = '%s exit %s: %s' % (pl['fails'], prc[pl['fails']], ' '.join(t.split())[-170:])
    else:
        pok, _, pv = S.read_pa_only(rd(os.path.join(po, ident + '.out')), EPA)
        caught = all(r == 0 for r in prc.values()) and not pok and any(pl['reader'] in v for v in pv)
        det = 'compiled; PA: %s' % '; '.join(pv)[:170]
    rep('plant %s refused' % name, caught, det)
print('%s GATE %s: %d of %d' % (cfg['name'], 'HELD' if all(res) else 'FAILED', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
