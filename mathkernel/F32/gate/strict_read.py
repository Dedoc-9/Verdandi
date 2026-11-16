# Strict readers for Coq's Print Assumptions and coqchk -o output (gate v2, 2026-11-14). Gate v1's readers took only
# the names under "Axioms:" and coqchk's "* Axioms:" block, and a substring "Closed under the global context"; the
# adversarial review built three non-proofs that passed v1 (A6, A6c, A9). These readers accept nothing they do not
# recognise: every line must be an expected axiom (name and type), an expected section, or blank.
import re

# An assumption entry starts with its name, then " :", then either its type or, when Coq breaks a long type, the end
# of the line (the type follows, indented). Run 1 of gate v2 (2026-11-14, out-run1-failed) required text after the
# colon and so misread the honest output; this pattern is the repair.
ENTRY = re.compile(r"^([A-Za-z_][\w.']*) :(\s|$)")

def norm(s): return ' '.join(s.split())

def expected_pa(path):
    """Expected Print Assumptions entries, one 'name : type' per line, whitespace-normalised."""
    return set(norm(l) for l in open(path, encoding='utf-8').read().splitlines() if l.strip())

def expected_chk(path):
    return set(l.strip() for l in open(path, encoding='utf-8').read().splitlines() if l.strip())

def read_pa_only(text, expected):
    """For an output that is ONE Print Assumptions and nothing else. Returns (ok, entries, violations)."""
    lines = text.splitlines()
    entries, cur, viol, seen_header = [], None, [], False
    for ln in lines:
        if not ln.strip():
            continue
        if ln[0].isspace():                               # continuation of the current entry
            if cur is None: viol.append('continuation outside an entry: ' + ln.strip()); continue
            cur.append(ln); continue
        if cur is not None: entries.append(norm(' '.join(cur))); cur = None
        if ln == 'Axioms:' and not seen_header: seen_header = True; continue
        if seen_header and ENTRY.match(ln): cur = [ln]; continue
        viol.append('unexpected line: ' + ln)            # guarded/positive/unsafe-hierarchy notes, Closed, errors, warnings
    if cur is not None: entries.append(norm(' '.join(cur)))
    extra = sorted(set(entries) - expected); missing = sorted(expected - set(entries))
    viol += ['unexpected assumption: ' + e for e in extra] + ['expected assumption absent: ' + m for m in missing]
    if len(entries) != len(set(entries)): viol.append('an assumption is listed twice')
    return (not viol), entries, viol

UNSAFE = ('* Constants/Inductives relying on type-in-type:', '* Constants/Inductives relying on unsafe (co)fixpoints:',
          '* Inductives whose positivity is assumed:')
THEORY = ('* Theory: Set is predicative', '* Theory: Rewrite rules are not allowed')

def read_coqchk(text, expected_names):
    """coqchk -silent -o: the CONTEXT SUMMARY must be exactly the two theory lines, the expected axioms, and <none>
    under each unsafe section. Returns (ok, axioms, violations)."""
    viol, axioms, sec, seen = [], set(), None, set()
    body = text.split('CONTEXT SUMMARY', 1)
    if len(body) != 2: return False, set(), ['no CONTEXT SUMMARY']
    if body[0].strip(): viol.append('output before the summary: ' + norm(body[0])[:120])
    for ln in body[1].splitlines():
        s = ln.strip()
        if not s or set(s) == {'='}: continue
        if ln.startswith('* '):
            sec = None
            if s in THEORY: seen.add(s); continue
            if s == '* Axioms:': sec = 'ax'; seen.add(s); continue
            hit = [u for u in UNSAFE if s.startswith(u)]
            if hit:
                seen.add(hit[0])
                if s != hit[0] + ' <none>': viol.append('unsafe section not empty: ' + s); sec = 'unsafe'
                continue
            viol.append('unknown section: ' + s); continue
        if sec == 'ax': axioms.add(s); continue
        if sec == 'unsafe': viol.append('unsafe entry: ' + s); continue
        viol.append('unexpected line: ' + s)
    for need in THEORY + ('* Axioms:',) + UNSAFE:
        if need not in seen: viol.append('section absent: ' + need)
    if axioms != expected_names:
        viol.append('axioms differ: extra %s, absent %s' % (sorted(axioms - expected_names), sorted(expected_names - axioms)))
    return (not viol), axioms, viol

def read_pa_blocks(text, expected):
    """For an output that mixes Check printouts with several Print Assumptions (K1, K2): every line that marks an
    unsafe construct is a violation anywhere, and every entry under each 'Axioms:' is expected. Returns
    (ok, n_blocks, n_closed, violations)."""
    viol, blocks, closed, cur, entry = [], 0, 0, False, None
    marks = re.compile(r'is assumed to be (guarded|positive)|relies on an unsafe hierarchy|relying on|bypass')
    for ln in text.splitlines():
        if marks.search(ln): viol.append('unsafe mark: ' + ln.strip())
        if ln.startswith('Closed under the global context'): closed += 1; continue
        if ln == 'Axioms:':
            if entry: viol += check_entry(entry, expected)
            blocks += 1; cur, entry = True, None; continue
        if cur:
            if ln[:1].isspace() and entry is not None: entry.append(ln); continue
            if entry: viol += check_entry(entry, expected); entry = None
            if ENTRY.match(ln):          # any entry inside a block is checked, expected name or not (run 1 skipped others)
                entry = [ln]; continue
            cur = False
    if entry: viol += check_entry(entry, expected)
    return (not viol), blocks, closed, viol

def check_entry(entry, expected):
    e = norm(' '.join(entry))
    return [] if e in expected else ['assumption not as expected: ' + e]
