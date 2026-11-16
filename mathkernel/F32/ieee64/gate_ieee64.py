# The gate of ieee64, the model-to-binary64 correspondence (2026-11-15). Author: the assistant.
#   docker run --rm --network none [-e ANCHOR=<sha256>] [-e STATEMENT=<sha256>] -v <mkf>:/work -w /work <image> \
#       sh -c 'timeout <seconds> python3 -B /work/ieee64/gate_ieee64.py [--recheck]'
# It ends with one verdict line: IEEE64 GATE HELD or IEEE64 GATE FAILED.
#
# WHY THIS FILE, AND NOT gate/gate4.py ALONE. gate4.py, run on the tree, appends a line to libcache/checked4.log for
# every outside library it checks and writes libcache/out4/; this folder's closure has libraries the log holds no
# line for, and --recheck writes a line for every one. libcache is named in freeze lists and is not this folder's to
# change. gate4.py also has no row that reads the sources' text, and none that holds one file to a hash given by
# name. So this gate:
#   - makes a copy of the tree outside it (under /tmp), of exactly the files ieee64/FROZEN4.txt names, with that
#     list and this file, and an empty libcache;
#   - runs gate/gate4.py there, byte for byte the tree's, with ANCHOR and --recheck passed on. Its rows are gate4's
#     own: the freeze list and the anchor; every source of f32, p32, p32r, exp32, exp32r and ieee64 compiled in a
#     fresh root; Print Assumptions of ieee64's identity read against the tier's expected list; coqchk -norec on
#     every one of those modules; the closure; every outside library checked by coqchk in this run (the copy's log
#     starts empty, so none is taken from a log); gate.json and every plant file held to what plants/make_plants.py
#     emits; every plant refused for its stated reason; nothing written in the copy but its out4 and library log;
#   - adds the rows gate4 does not have, each judged on the tree itself (below);
#   - copies the copy's ieee64/out4, its library log and its library outputs into ieee64/out4/ and prints the
#     identity's Print Assumptions output as coqc wrote it.
#
# THE ROWS OF THIS FILE.
#   this gate is the one gate.json names     sha256 of the bytes running = gate.json "gate" (gate.json is on the
#                                            freeze list, so the anchor holds this file through it).
#   statement has the frozen sha256          IEEE64_Statement.v = gate.json "statement", and = STATEMENT when given.
#   the folder's .v files are the gate's     no .v stands in ieee64/ that the gate does not compile and recheck.
#   text: no assuming word                   none of WORDS, as a whole word, comments included, in any of them.
#   text: finds the word in each proof plant the same search on each plant that an entry gives "words".
#   identity types the top theorem           Identity.v, comments aside, is exactly IDENT: nothing imported, and
#                                            identity_check : MKF.ieee64.IEEE64_Statement.IEEE64 :=
#                                            MKF.ieee64.Closed.ieee64_holds. (That it type-checks is gate4's row.)
#   the tree's freeze list is the anchored   sha256 of ieee64/FROZEN4.txt = ANCHOR (only when ANCHOR is given).
#   copy: the listed files, nothing else     every file of the copy is byte for byte the tree's.
#   gate4.py is the tree's and the one run   the copy's gate4.py = the tree's = the hash its first line prints.
#   gate4.py: exit 0, HELD, every row ok     and its row count is its verdict's.
#   gate4.py: the rows this folder needs     exactly the rows computed here from the gate.json files: none absent,
#                                            none unknown, each once.
#   outside libraries checked in this run    gate4's closure row says 0 from the log.
#   nothing written to the tree              every file of the tree outside ieee64/out4, before and after: path,
#                                            size, sha256.
#
# WHAT A RUN DOES NOT HOLD.
#   - Everything gate4.py's own header says it does not hold. In particular: without ANCHOR a run shows only that the
#     sources agree with a list standing beside them; the image (coqc, coqchk, python3) is trusted.
#   - gate4.py judged the copy, not the tree. What ties the two: the copy is made here from the tree's files, each
#     compared byte for byte, and gate4's own row holds each to its line of the anchored list.
#   - The text row is a search for words. It is not what shows that nothing is assumed: that is the Print Assumptions
#     row, and coqchk. A word in a comment makes the row fail; an assumption spelled another way does not.
#   - Whether IEEE64 says what it should, whether Flocq's binary_float operations are IEEE 754's, and whether the
#     plants are the right plants, is a reader's judgment. A "premise" plant is refused by the route of the proof,
#     which does not show that the statement without the premise is false.
#   - A file another process writes in the tree during the run makes the last row fail; it cannot tell who wrote.
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, traceback
sys.dont_write_bytecode = True
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE); GD = os.path.basename(HERE)
WORDS = ('Axiom', 'Axioms', 'Parameter', 'Parameters', 'Conjecture', 'Conjectures', 'Hypothesis', 'Hypotheses',
         'Variable', 'Variables', 'Context', 'Admitted', 'admit', 'give_up', 'Abort', 'Unset', 'bypass_check', 'Declare')
IDENT = ('From MKF.ieee64 Require IEEE64_Statement Closed. '
         'Definition identity_check : MKF.ieee64.IEEE64_Statement.IEEE64 := MKF.ieee64.Closed.ieee64_holds. '
         'Print Assumptions identity_check.')
LINE = re.compile(r'([0-9a-f]{64})  ([A-Za-z0-9_][A-Za-z0-9_.+-]*(?:/[A-Za-z0-9_][A-Za-z0-9_.+-]*)*)')
ROW = re.compile(r'  (.*?) +(ok|FAIL)  (.*)')
VERDICT = re.compile(r'(\S+) GATE4 (HELD|FAILED): (\d+) of (\d+)  \[anchor ([0-9a-f]{16}|none)\]')
LIBS = re.compile(r'(\d+) libraries by the sha256 of their files: (\d+) from the log, (\d+) checked in this run')
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
def words_in(text): return [w for w in WORDS if re.search(r'\b%s\b' % re.escape(w), text)]
def code(text):
    """The text outside comments (comments nest), white space collapsed."""
    out, depth, i = [], 0, 0
    while i < len(text):
        if text.startswith('(*', i): depth += 1; i += 2
        elif depth and text.startswith('*)', i): depth -= 1; i += 2
        else:
            if not depth: out.append(text[i])
            i += 1
    return ' '.join(''.join(out).split())

def snapshot(skip_dirs):
    """Every file under the tree but the places this run may write: {path: (size, sha256)}."""
    snap = {}
    for dp, dn, fn in os.walk(W):
        rel = os.path.relpath(dp, W).replace(os.sep, '/'); rel = '' if rel == '.' else rel + '/'
        for d in dn:
            if os.path.islink(os.path.join(dp, d)): snap[rel + d] = ('link', os.readlink(os.path.join(dp, d)))
        dn[:] = sorted(d for d in dn if rel + d not in skip_dirs)
        for f in fn:
            full = os.path.join(dp, f)
            if os.path.islink(full): snap[rel + f] = ('link', os.readlink(full)); continue
            b = raw(full); snap[rel + f] = ('unreadable',) if b is None else (len(b), hx(b))
    return snap

def stop(msg):
    print('gate_ieee64: %s' % msg); print('IEEE64 GATE FAILED: the gate could not start (no row was judged)'); sys.exit(2)

def main(T):
    args = sys.argv[1:]; recheck = '--recheck' in args
    if [a for a in args if a != '--recheck']: stop('usage: python3 -B ieee64/gate_ieee64.py [--recheck]')
    G = HERE; O = os.path.join(G, 'out4'); SELF = sha(os.path.abspath(__file__)); G4 = os.path.join(W, 'gate', 'gate4.py')
    cfgs = {}
    def load(d):
        try: cfgs[d] = json.loads(raw(os.path.join(W, d, 'gate.json')).decode('utf-8'))
        except Exception as e: stop('%s/gate.json cannot be read: %s' % (d, e))
        return cfgs[d]
    cfg = load(GD); DIRS = [d.strip('/') for d in cfg.get('deps', [])] + [GD]
    for d in DIRS[:-1]: load(d)
    FILES = {d: list(cfgs[d]['files']) for d in DIRS}; plants = cfg.get('plants', {})
    before = snapshot({GD + '/out4'})
    print('gate_ieee64.py %s judges %s in %s through gate/gate4.py %s on a copy of the listed files%s' % (SELF, GD, W, sha(G4), '  --recheck' if recheck else ''))

    # 1. on the tree itself: this file, the statement, the text of the sources, the identity
    rep('this gate is the one gate.json names', cfg.get('gate', {}).get('sha256') == SELF, 'gate_ieee64.py %s' % SELF[:16])
    st = cfg.get('statement', {}); sfile = st.get('file', ''); have = sha(os.path.join(G, sfile)); given = os.environ.get('STATEMENT')
    if given is None: print('statement hash not given from outside (STATEMENT): judged against gate.json only')
    rep('statement: %s has the frozen sha256' % sfile, have == st.get('sha256') and given in (None, have),
        '%s%s' % (have, '' if given is None else ', the one given from outside' if given == have else '; STATEMENT given %r' % given[:64]))
    here_v = sorted(f for f in os.listdir(G) if f.endswith('.v')); stray = sorted(set(here_v) ^ set(FILES[GD]))
    rep('the folder\'s .v files are exactly the gate\'s files', not stray, '%d files' % len(here_v) if not stray else 'not on both sides: %s' % ', '.join(stray))
    found = ['%s: %s' % (f, ' '.join(words_in(rd(os.path.join(G, f))))) for f in FILES[GD] if words_in(rd(os.path.join(G, f))) or raw(os.path.join(G, f)) is None]
    rep('text: no assuming word in any source', FILES[GD] and not found, '%d files, %d words searched, comments included' % (len(FILES[GD]), len(WORDS)) if not found else '; '.join(found)[:300])
    seen, blind = [], []
    for pname, pl in sorted(plants.items()):
        if 'words' not in pl: continue
        got = set(w for src in pl['replace'].values() for w in words_in(rd(os.path.join(G, src))))
        (seen if pl['words'] and set(pl['words']) <= got else blind).append('%s %s' % (pname, ' '.join(pl['words'])))
    rep('text: the same search finds the word in each proof plant', seen and not blind, '; '.join(seen)[:300] if not blind else 'not found: %s' % '; '.join(blind)[:300])
    ident = cfg['identity']; ic = code(rd(os.path.join(G, ident + '.v')))
    rep('identity: %s.v types Closed.ieee64_holds by the statement\'s IEEE64' % ident, ic == IDENT, 'nothing imported; the definition and one Print Assumptions' if ic == IDENT else 'its text is: %s' % ic[:240])

    # 2. the copy: exactly the files the freeze list names, the list, this file; an empty libcache
    fb = raw(os.path.join(G, 'FROZEN4.txt')); anchor = None if fb is None else hx(fb)
    if 'ANCHOR' in os.environ:
        a = os.environ['ANCHOR']
        rep('the tree\'s freeze list is the anchored one', anchor is not None and a == anchor, 'ANCHOR %s' % a[:16] if a == anchor else 'ANCHOR given %r, this list is %s' % (a[:64], anchor))
    else:
        print('not anchored: no ANCHOR given')
    M = os.path.join(T, 'tree'); listed = [m.group(2) for m in (LINE.fullmatch(l) for l in (fb or b'').decode('latin-1').split('\n')) if m]
    want = sorted(set(listed + [GD + '/FROZEN4.txt', GD + '/' + os.path.basename(__file__)]))
    for p in want:
        b = raw(os.path.join(W, p))
        if b is None: continue
        os.makedirs(os.path.dirname(os.path.join(M, p)), exist_ok=True)
        with open(os.path.join(M, p), 'wb') as f: f.write(b)
    os.makedirs(os.path.join(M, 'libcache'), exist_ok=True)
    got = {os.path.relpath(os.path.join(dp, f), M).replace(os.sep, '/'): sha(os.path.join(dp, f)) for dp, _, fs in os.walk(M) for f in fs}
    off = [p for p in want if got.get(p) is None or got[p] != sha(os.path.join(W, p))] + sorted(set(got) - set(want))
    rep('copy: the listed files, the list and this gate, nothing else', fb is not None and listed and not off,
        '%d files, each byte for byte the tree\'s' % len(got) if not off else 'not so: %s' % ', '.join(off[:6]))

    # 3. gate4.py, unchanged, on the copy
    cmd = ['python3', '-B', os.path.join(M, 'gate', 'gate4.py'), GD] + (['--recheck'] if recheck else [])
    print('gate4.py on the copy (%s); its lines follow, each after "  | ":' % ' '.join(cmd[1:])); sys.stdout.flush()
    lines = []
    try:
        p = subprocess.Popen(cmd, cwd=M, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for b in p.stdout:
            l = b.decode('utf-8', 'replace').rstrip('\r\n'); lines.append(l); print('  | ' + l); sys.stdout.flush()
        rc = p.wait()
    except OSError as e:
        rc = 127; lines.append(str(e)); print('  | ' + str(e))
    rows = [m.groups() for m in (ROW.fullmatch(l) for l in lines) if m]
    v = VERDICT.fullmatch(lines[-1]) if lines else None
    ran = re.match(r'gate4\.py ([0-9a-f]{64}) judges %s ' % re.escape(GD), lines[0]) if lines else None
    same = sha(os.path.join(M, 'gate', 'gate4.py')) == sha(G4) and ran is not None and ran.group(1) == sha(G4)
    rep('gate4.py on the copy is the tree\'s, byte for byte, and the one run', same, 'gate/gate4.py %s' % sha(G4)[:16] if same else 'the copy %s, the tree %s, its first line %r' % (sha(os.path.join(M, 'gate', 'gate4.py'))[:16], sha(G4)[:16], (lines[0] if lines else '')[:90]))
    fails = [n for n, s, _ in rows if s != 'ok']
    held = (rc == 0 and v is not None and v.group(1) == cfg['name'] and v.group(2) == 'HELD' and v.group(3) == v.group(4) == str(len(rows)) and not fails
            and v.group(5) == (anchor or 'none')[:16])
    rep('gate4.py on the copy: exit 0, HELD, every row ok', held, lines[-1] if held else 'exit %s; %d rows read, %d not ok (%s); last line %r' % (rc, len(rows), len(fails), ', '.join(fails[:5]), (lines[-1] if lines else '')[:120]))
    need = ['freeze list: every line is readable', 'freeze list: no path is listed twice', 'freeze list: every required entry is on it',
            'frozen inputs unchanged', 'fresh root holds only the listed sources', 'identity: Print Assumptions is exactly the %s list' % cfg['tier'],
            'closure: every MKF library is one compiled and rechecked above', 'closure: every outside library passed coqchk -norec, unsafe <none>',
            'nothing written to the tree outside out4 and the library log']
    if 'ANCHOR' in os.environ: need.append('freeze list is the anchored one')
    for d in DIRS:
        need += ['compile %s/%s' % (d, f[:-2]) for f in FILES[d]] + ['coqchk -norec %s/%s' % (d, f[:-2]) for f in FILES[d]]
        need += ['%s is what %s emits' % (path, spec[0]) for path, spec in cfgs[d].get('generated', {}).items()]
    need += ['plant %s refused' % n for n in plants]
    okrows = [n for n, s, _ in rows if s == 'ok']; names = [n for n, _, _ in rows]
    absent = sorted(n for n in need if okrows.count(n) != 1); unknown = sorted(set(names) - set(need))
    classes = {}
    for pl in plants.values(): classes[pl.get('class', 'plant')] = classes.get(pl.get('class', 'plant'), 0) + 1
    rep('gate4.py on the copy: the rows this folder needs, no other', need and not absent and not unknown and len(need) == len(set(need)),
        '%d rows; %d plants refused (%s)' % (len(need), len(plants), ', '.join('%s %d' % kv for kv in sorted(classes.items()))) if not absent and not unknown
        else 'not once and ok: %s; not expected: %s' % (', '.join(absent[:5]) or 'none', ', '.join(unknown[:5]) or 'none'))
    lib = next((LIBS.search(d) for n, s, d in rows if n.startswith('closure: every outside library') and LIBS.search(d)), None)
    rep('outside libraries: every one checked by coqchk in this run', lib is not None and lib.group(2) == '0' and lib.group(1) == lib.group(3) != '0',
        '%s libraries, none taken from a log' % lib.group(1) if lib else 'gate4\'s closure row was not read')

    # 4. what the run leaves: ieee64/out4, and nothing else in the tree
    shutil.rmtree(O, ignore_errors=True)
    if os.path.isdir(os.path.join(M, GD, 'out4')): shutil.copytree(os.path.join(M, GD, 'out4'), O)
    else: os.makedirs(O)
    if os.path.isdir(os.path.join(M, 'libcache', 'out4')): shutil.copytree(os.path.join(M, 'libcache', 'out4'), os.path.join(O, 'libcache-out4'))
    if raw(os.path.join(M, 'libcache', 'checked4.log')) is not None: shutil.copyfile(os.path.join(M, 'libcache', 'checked4.log'), os.path.join(O, 'libcache-checked4.log'))
    with open(os.path.join(O, 'gate4-on-the-copy.txt'), 'wb') as f: f.write(('\n'.join(lines) + '\n').encode('utf-8'))
    pa = rd(os.path.join(O, '%s.%s.out' % (GD, ident)))
    print('Print Assumptions of MKF.%s.%s.identity_check, as coqc wrote it (%s/out4/%s.%s.out, sha256 %s):' % (GD, ident, GD, GD, ident, sha(os.path.join(O, '%s.%s.out' % (GD, ident)))))
    for l in pa.splitlines(): print('    ' + l)
    after = snapshot({GD + '/out4'})
    diff = ['appeared %s' % p for p in sorted(set(after) - set(before))] + ['gone %s' % p for p in sorted(set(before) - set(after))] + ['changed %s' % p for p in sorted(set(after) & set(before)) if after[p] != before[p]]
    rep('nothing written to the tree outside %s/out4' % GD, not diff, '%d files as they were' % len(after) if not diff else '%d differ: %s' % (len(diff), ', '.join(diff[:6])))
    print('%s GATE %s: %d of %d rows here, gate4.py %s of %s on the copy  [anchor %s]' % (cfg['name'], 'HELD' if all(res) else 'FAILED', sum(res), len(res),
          v.group(3) if v else len(rows) - len(fails), v.group(4) if v else '?', anchor[:16] if anchor else 'none'))
    return 0 if all(res) else 1

if __name__ == '__main__':
    T = tempfile.mkdtemp(prefix='gate-ieee64-', dir='/tmp'); exit_code = 2
    try:
        exit_code = main(T)
    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else 2
    except BaseException:
        traceback.print_exc(file=sys.stdout)
        print('IEEE64 GATE FAILED: the gate stopped on an error after %d rows (no verdict on the rest)' % len(res))
    finally:
        shutil.rmtree(T, ignore_errors=True)
    sys.exit(exit_code)
