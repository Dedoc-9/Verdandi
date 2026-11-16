# Mutation tests of gate4.py's own rows (2026-11-14). Run inside ONE container:
#   docker run --rm --network none -v <mkf>:/work -w /tmp <image> sh -c 'timeout 5400 python3 -B /work/gate/gate4_selftest.py'
# It works on temp copies of the smallest folder, f32, under /tmp/g4st: f32's sources and plants, gate/gate4.py,
# gate/freeze4.py, gate/strict_read.py, the expected-pa file, and a libcache holding checked4.log. Each copy also holds
# honest compiled files beside the sources (compiled here), so every run shows that nothing compiled is taken.
# A mutant counts as caught only if the gate's verdict is FAILED (exit 1) and the row named for it is among the failing
# rows; the forged-log mutant counts only if the run reports the library as checked in this run. One honest run must
# hold. Of the mounted tree it writes only what gate4 itself may: after the honest run has held, the lines that run
# added to its copy's libcache/checked4.log, and their coqchk outputs under libcache/out4/. Nothing a mutant wrote
# goes back. Two mutants install a library in the container's own Coq library root and remove it afterwards.
#   Names given as arguments run only those mutants; the last line then says PARTIAL, never HELD.
# What it does not test: the row "fresh root holds only the listed sources" has no mutant of its own (the gate makes
# that root itself; mutant 05 shows the property through Print Assumptions), nor has --recheck, nor a plant's refusal.
import hashlib, json, os, re, shutil, subprocess, sys, time
sys.dont_write_bytecode = True
try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); W0 = os.path.dirname(HERE); T = '/tmp/g4st'; CWD = os.path.join(T, 'cwd')
NL = chr(10)
IGN = shutil.ignore_patterns('out*', 'FROZEN4.txt', '*.vo', '*.vok', '*.vos', '*.glob', '*.aux', '.*.aux', '__pycache__')
ROW = re.compile(r'^  (.+?) +(ok|FAIL)  (.*)$')
VERD = re.compile(r'^(\S+) GATE4 (HELD|FAILED): (\d+) of (\d+)  \[anchor ([0-9a-f]{16}|none)\]$')
R_READ = 'freeze list: every line is readable'
R_TWICE = 'freeze list: no path is listed twice'
R_REQ = 'freeze list: every required entry is on it'
R_HASH = 'frozen inputs unchanged'
R_ANCHOR = 'freeze list is the anchored one'
R_PA = 'identity: Print Assumptions is exactly the flocq4 list'
R_CHK = 'coqchk -norec f32/F32'
R_OURS = 'closure: every MKF library is one compiled and rechecked above'
R_OUTSIDE = 'closure: every outside library passed coqchk -norec, unsafe <none>'
R_WRITE = 'nothing written to the tree outside out4 and the library log'
STMT, PROOF, LIST = 'f32/F32_Statement.v', 'f32/F32.v', 'f32/FROZEN4.txt'

def say(s): print(s); sys.stdout.flush()
def sh(cmd, cwd=CWD, env=None):
    p = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode('utf-8', 'replace')
def rdb(p):
    with open(p, 'rb') as f: return f.read()
def rd(d, p): return rdb(os.path.join(d, p)).decode('utf-8')
def wr(d, p, t):
    with open(os.path.join(d, p), 'wb') as f: f.write(t.encode('utf-8'))
def sha(d, p): return hashlib.sha256(rdb(os.path.join(d, p))).hexdigest()
def sub(d, p, a, b):
    t = rd(d, p); assert t.count(a) == 1, (p, a, t.count(a)); wr(d, p, t.replace(a, b))
def line_of(d, p):
    lines = rd(d, LIST).split(NL); hit = [i for i, l in enumerate(lines) if l.endswith('  ' + p)]
    assert len(hit) == 1, (p, hit); return lines, hit[0]
def rehash(d, p):
    """p's line of the freeze list gets the file's present hash"""
    lines, i = line_of(d, p); lines[i] = '%s  %s' % (sha(d, p), p); wr(d, LIST, NL.join(lines))
def setup_failed(what, text=''):
    say(text[-3000:]); say('GATE4 SELFTEST FAILED: setup: %s' % what); sys.exit(1)

class Run:
    def __init__(self, d, anchor=None):
        env = dict(os.environ); env.pop('ANCHOR', None)
        if anchor is not None: env['ANCHOR'] = anchor
        t0 = time.time(); self.rc, self.text = sh(['python3', '-B', os.path.join(d, 'gate', 'gate4.py'), 'f32'], env=env); self.secs = time.time() - t0
        self.anchored = anchor is not None; lines = self.text.splitlines()
        self.rows = [(m.group(1), m.group(2) == 'ok', m.group(3)) for m in (ROW.match(l) for l in lines if not l.startswith(('  checked in this run:', '  sources judged:', '  libcache/checked4.log:'))) if m]
        self.failing = [n for n, ok, _ in self.rows if not ok]
        self.checked = [l.split()[4] for l in lines if l.startswith('  checked in this run: ')]
        self.verdict = VERD.match(lines[-1]) if lines else None
        self.said_unanchored = 'not anchored: no ANCHOR given' in lines
        self.has_anchor_row = any(n == R_ANCHOR for n, _, _ in self.rows)
        v = self.verdict
        # the reading is believed only if it agrees with the gate's own count and exit status
        self.sound = bool(v) and int(v.group(4)) == len(self.rows) and int(v.group(3)) == sum(1 for _, ok, _ in self.rows if ok) \
            and (self.rc == 0) == (v.group(2) == 'HELD') and (v.group(2) == 'HELD') == (not self.failing) \
            and self.said_unanchored == (not self.anchored) and self.has_anchor_row == self.anchored
        self.failed = self.sound and v.group(2) == 'FAILED' and self.rc == 1
        self.held = self.sound and v.group(2) == 'HELD' and self.rc == 0
    def detail(self, name): return ' | '.join(det for n, _, det in self.rows if n == name)
    def last(self): return self.text.splitlines()[-1] if self.text.strip() else '(no output)'

def make_base():
    base = os.path.join(T, 'base'); shutil.copytree(os.path.join(W0, 'f32'), os.path.join(base, 'f32'), ignore=IGN)
    os.makedirs(os.path.join(base, 'gate')); os.makedirs(os.path.join(base, 'libcache'))
    for f in ('gate4.py', 'freeze4.py', 'strict_read.py', 'expected-pa-flocq4.txt'): shutil.copyfile(os.path.join(HERE, f), os.path.join(base, 'gate', f))
    if os.path.exists(os.path.join(W0, 'libcache', 'checked4.log')): shutil.copyfile(os.path.join(W0, 'libcache', 'checked4.log'), os.path.join(base, 'libcache', 'checked4.log'))
    for f in json.loads(rd(base, 'f32/gate.json'))['files']:          # honest compiled files, left beside the sources
        rc, t = sh(['coqc', '-R', base, 'MKF', os.path.join(base, 'f32', f)])
        if rc != 0: setup_failed('the honest %s does not compile' % f, t)
    rc, t = sh(['python3', '-B', os.path.join(base, 'gate', 'freeze4.py'), 'f32'])
    got = [l.split()[1] for l in t.splitlines() if l.startswith('anchor ')]
    if rc != 0 or len(got) != 1 or got[0] != sha(base, LIST): setup_failed('freeze4.py did not write the list and print its sha256', t)
    say('setup: f32 copied to %s with honest compiled files beside the sources; freeze4.py: %s' % (base, ' / '.join(t.split(NL)[:2])))
    return base, got[0]

# the mutations
FIX = '#[bypass_check(guard)] Fixpoint loop (n : nat) {struct n} : False := loop n.'
def weaken(d):
    """the statement weakened (the bound 2^-27 becomes 2^-28: fewer inputs covered), the proof adjusted so that it
    still compiles: a tree that every row but the list's and the anchor's accepts"""
    sub(d, STMT, 'bpow radix2 (-27) * Rabs f -> faithful32', 'bpow radix2 (-28) * Rabs f -> faithful32')
    sub(d, PROOF, "  assert (H' : Rabs (y - f) <= / 134217728 * Rabs f) by exact H.",
        "  assert (H0 : Rabs (y - f) <= / 268435456 * Rabs f) by exact H." + NL +
        "  assert (H' : Rabs (y - f) <= / 134217728 * Rabs f) by (pose proof (Rabs_pos f); lra).")
def proof_of(d, head, new):
    t = rd(d, PROOF); assert t.count(head) == 1; i = t.index(head); a = t.index('Proof.', i); b = t.index('Qed.', a) + len('Qed.')
    wr(d, PROOF, t[:a] + new + t[b:])

def m01(d, c):
    weaken(d)
def m02(d, c):
    weaken(d); rehash(d, STMT); rehash(d, PROOF)
def m03(d, c):
    weaken(d); rehash(d, PROOF); lines, i = line_of(d, STMT); del lines[i]; wr(d, LIST, NL.join(lines))
def m04(d, c):
    weaken(d); rehash(d, PROOF); rehash(d, STMT); lines, i = line_of(d, STMT)
    h, p = lines[i].split('  ', 1); assert h.upper() != h; lines[i] = h.upper() + '  ' + p; wr(d, LIST, NL.join(lines))
def m05(d, c):
    proof_of(d, 'Lemma ulp32_gt', 'Admitted.'); rehash(d, PROOF)
    assert sha(d, 'f32/F32.vo') == sha(c['base'], 'f32/F32.vo')          # the honest compiled proof is still beside it
def m06(d, c):
    sub(d, PROOF, 'Lemma ulp32_gt', FIX + NL + 'Lemma ulp32_gt')
    proof_of(d, 'Lemma ulp32_gt', 'Proof. intros. exact (False_ind _ (loop 0)). Qed.'); rehash(d, PROOF)
def m07(d, c):
    lines = rd(d, 'libcache/checked4.log').split(NL); pick = [i for i, l in enumerate(lines) if l.startswith('Flocq.Core.Core ')] or [0]
    f = lines[pick[0]].split(' '); assert len(f) == 4 and f[2:] == ['0', 'clean'], f
    c['lib'], c['true'] = f[0], f[1]; f[1] = hashlib.sha256(b'another file').hexdigest(); lines[pick[0]] = ' '.join(f)
    wr(d, 'libcache/checked4.log', NL.join(lines))
def m08(d, c):
    wr(d, 'f32/gen_stmt.py', "import os, sys" + NL + "here = os.path.dirname(os.path.abspath(__file__))" + NL
       + "sys.stdout.buffer.write(open(os.path.join(here, 'F32_Statement.v'), 'rb').read())" + NL
       + "open(os.path.join(here, 'written-during-the-run.txt'), 'w').write('x')" + NL)
    g = json.loads(rd(d, 'f32/gate.json')); g['generated'] = {'f32/F32_Statement.v': ['f32/gen_stmt.py']}; wr(d, 'f32/gate.json', json.dumps(g))
    rc, t = sh(['python3', '-B', os.path.join(d, 'gate', 'freeze4.py'), 'f32', '--replace']); assert rc == 0, t
def install(c, top, rel, text):
    """compile a one-file library and put it in the container's own Coq library root (removed by uninstall)"""
    src = os.path.join(T, 'lib-' + top); os.makedirs(os.path.join(src, os.path.dirname(rel)), exist_ok=True)
    with open(os.path.join(src, rel + '.v'), 'w') as f: f.write(text)
    rc, t = sh(['coqc', '-R', src, top, os.path.join(src, rel + '.v')]); assert rc == 0, t
    dst = os.path.join(c['coqlib'], 'user-contrib', top); assert not os.path.exists(dst), dst
    os.makedirs(os.path.join(dst, os.path.dirname(rel))); shutil.copyfile(os.path.join(src, rel + '.vo'), os.path.join(dst, rel + '.vo')); c['installed'] = dst
def uninstall(c):
    if c.get('installed'): shutil.rmtree(c.pop('installed'), ignore_errors=True)
def m09(d, c):
    install(c, 'MKF', 'zz/Extra', 'Definition extra : nat := 0.' + NL)
    sub(d, PROOF, 'From MKF.f32 Require Import F32_Statement.' + NL, 'From MKF.f32 Require Import F32_Statement.' + NL + 'From MKF.zz Require Extra.' + NL); rehash(d, PROOF)
def m10(d, c):
    install(c, 'Evil', 'Loop', FIX + NL)
    sub(d, PROOF, 'From MKF.f32 Require Import F32_Statement.' + NL, 'From MKF.f32 Require Import F32_Statement.' + NL + 'From Evil Require Loop.' + NL); rehash(d, PROOF)
def m11(d, c):
    lines, i = line_of(d, STMT); lines.insert(i, lines[i]); wr(d, LIST, NL.join(lines))

# name, what is done, the row that must fail, ANCHOR given (the honest anchor), the mutation
MUTANTS = [
 ('01-statement-edited', 'statement weakened (proof adjusted to compile), list untouched', R_HASH, True, m01),
 ('02-statement-rehashed', 'the same, both lines of the list re-hashed, ANCHOR the honest anchor', R_ANCHOR, True, m02),
 ('03-statement-line-removed', 'the same, the statement\'s line removed from the list, no ANCHOR', R_REQ, False, m03),
 ('04-statement-line-uppercase', 'the same, the statement\'s line re-hashed with its hash in upper case, no ANCHOR', R_READ, False, m04),
 ('05-admitted-beside-honest-vo', 'a lemma of the proof Admitted, list re-hashed, the honest compiled F32.vo left beside the source', R_PA, False, m05),
 ('06-guard-bypassed', 'a fixpoint with its guard check bypassed proves a lemma, list re-hashed', R_CHK, False, m06),
 ('07-log-line-forged', 'a line of checked4.log claims "0 clean" for one library under another hash', None, True, m07),
 ('08-file-written-in-tree', 'a listed generator that also writes a file into the tree', R_WRITE, False, m08),
 ('09-stray-mkf-library', 'an MKF library standing in the image\'s library root, required by the proof, list re-hashed', R_OURS, False, m09),
 ('10-unclean-outside-library', 'an outside library with a bypassed guard check, required by the proof, list re-hashed', R_OUTSIDE, False, m10),
 ('11-path-listed-twice', 'the statement\'s line twice in the list, no ANCHOR', R_TWICE, False, m11),
]

def main():
    only = set(sys.argv[1:]); unknown = only - set(n for n, _, _, _, _ in MUTANTS)
    if unknown: say('unknown mutant: %s' % ', '.join(sorted(unknown))); return 2
    shutil.rmtree(T, ignore_errors=True); os.makedirs(CWD); t0 = time.time()
    say('gate4_selftest.py %s on gate4.py %s, freeze4.py %s' % tuple(hashlib.sha256(rdb(os.path.join(HERE, f))).hexdigest() for f in ('gate4_selftest.py', 'gate4.py', 'freeze4.py')))
    base, A = make_base(); c = {'base': base, 'coqlib': sh(['coqc', '-where'])[1].strip()}; results = []; runs = []
    say('honest anchor %s' % A)

    d = os.path.join(T, 'honest'); shutil.copytree(base, d); r = Run(d, A); runs.append(r)
    for l in r.text.splitlines():
        if not l.startswith('  checked in this run:'): say('    | ' + l[:330])
    ok = r.held and r.detail(R_ANCHOR).startswith('ANCHOR ' + A[:16]) and r.verdict.group(5) == A[:16] and ('anchor ' + A) in r.text.splitlines()
    results.append(ok)
    say('honest run: %s  (%d libraries checked in this run, %.0f s)  %s' % ('holds' if ok else 'DOES NOT HOLD', len(r.checked), r.secs, r.last()))
    if not ok:
        say('GATE4 SELFTEST FAILED: the honest run does not hold; no mutant was run'); return 1
    # the honest run's library lines: into the base for the mutants, and (what a gate run may write) into the mounted tree
    shutil.copyfile(os.path.join(d, 'libcache', 'checked4.log'), os.path.join(base, 'libcache', 'checked4.log'))
    os.makedirs(os.path.join(W0, 'libcache', 'out4'), exist_ok=True); log0 = os.path.join(W0, 'libcache', 'checked4.log')
    have = set(rdb(log0).decode('utf-8', 'replace').split(NL)) if os.path.exists(log0) else set()
    new = [l for l in rd(d, 'libcache/checked4.log').split(NL) if l and l not in have]
    if new:
        with open(log0, 'ab') as f: f.write((NL.join(new) + NL).encode('utf-8'))
        for l in new:
            o = os.path.join(d, 'libcache', 'out4', l.split(' ')[0] + '.out')
            if os.path.exists(o): shutil.copyfile(o, os.path.join(W0, 'libcache', 'out4', os.path.basename(o)))
    say('library log: %d lines of the honest run added to %s (%d were there)' % (len(new), log0, len(have - {''})))

    for name, what, must, anchored, mutate in MUTANTS:
        if only and name not in only: continue
        d = os.path.join(T, name); shutil.copytree(base, d)
        try:
            mutate(d, c); r = Run(d, A if anchored else None); runs.append(r)
        except AssertionError as e:
            uninstall(c); results.append(False); say('mutant %-30s NOT MADE: %r' % (name, e)); continue
        finally:
            uninstall(c)
        if must is None:      # the forged line: the library must be checked in this run, and its true line written again
            again = '%s %s 0 clean' % (c['lib'], c['true']) in rd(d, 'libcache/checked4.log').split(NL)
            ok = r.sound and r.checked == [c['lib']] and ', 1 checked in this run' in r.detail(R_OUTSIDE) and again
            note = 'must check %s itself; checked in this run: %s; its true line appended: %s' % (c['lib'], r.checked, again)
        else:
            ok = r.failed and must in r.failing
            note = 'must fail [%s]; failing rows: %s' % (must, ' / '.join('[%s]' % n for n in r.failing) or 'none')
        results.append(ok)
        say('mutant %-30s %s  %s; %s; %s  (%.0f s)' % (name, 'caught' if ok else 'NOT CAUGHT', what, note, r.last(), r.secs))
        for n, good, det in r.rows:
            if not good: say('    | %s: %s' % (n, det[:260]))
        if not ok or not r.sound:
            for l in r.text.splitlines(): say('    : ' + l[:400])
    said = [r for r in runs if not r.anchored]; ok = all(r.sound for r in runs)
    results.append(ok)
    say('every run\'s reading agrees with its verdict line and exit status; %d runs without ANCHOR said "not anchored: no ANCHOR given" and had no anchor row, %d with ANCHOR had the row: %s' % (len(said), len(runs) - len(said), 'ok' if ok else 'FAIL'))
    left = os.path.exists(os.path.join(c['coqlib'], 'user-contrib', 'Evil')) or os.path.exists(os.path.join(c['coqlib'], 'user-contrib', 'MKF'))
    if left: results.append(False); say('a library installed for a mutant is still in the library root: FAIL')
    n, k = len(results), sum(results)
    word = ('HELD' if k == n else 'FAILED') if not only else ('PARTIAL (only %s; holds so far)' % ', '.join(sorted(only)) if k == n else 'FAILED')
    say('GATE4 SELFTEST %s: %d of %d  (%.0f s)' % (word, k, n, time.time() - t0))
    return 0 if k == n and not only else 1

if __name__ == '__main__':
    sys.exit(main())
