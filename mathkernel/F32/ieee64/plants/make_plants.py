# The plants of ieee64's gate and the folder's gate.json, from one table (2026-11-15). Author: the assistant.
#   python3 -B ieee64/plants/make_plants.py json          prints gate.json
#   python3 -B ieee64/plants/make_plants.py plant NAME    prints the plant NAME's file
#   python3 -B ieee64/plants/make_plants.py write         writes gate.json and every plant file (binary, LF)
#   python3 -B ieee64/plants/make_plants.py check         exit 0 only if gate.json and every plant file are these
#   python3 -B ieee64/plants/make_plants.py list          one line per plant
# A plant is one source of the folder with ONE change (two places of one file for axiom-exp32; the whole of Closed.v
# for five-of-six and guard), put in place of that source; the gate must refuse it for the reason its entry states:
#   "fails": M, "text": T    every file before M compiles, M does not, and M's output holds T;
#   "reader": T              every file compiles and the reading of Print Assumptions holds a violation with T.
# gate.json names this script as the generator of itself and of every plant file, so gate4.py runs it and compares
# byte for byte: a plant is held to "its source and the change written here", not to what a reader is told.
# The text to change must occur exactly once in its source, and a refusal pinned to a line of a proof file is held
# to that line's text here: if a source moves, this script stops and says where.
# What a plant shows: that the gate read the new code and refuses that one defect. What it does not: that the
# loosened statement is false (a "premise" plant is refused by the route of the proof; see "what").
import hashlib, json, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); IEEE = os.path.dirname(HERE)

STATEMENT_SHA256 = '7cbcac51c912286bc9ea64ef2880cf7685ff2027e02902a5ceeae3e693e428de'
DEPS = ['f32', 'p32', 'p32r', 'exp32', 'exp32r']
FILES = ['IEEE64_Statement.v', 'Ops.v', 'P32_IEEE.v', 'P32_IEEE_Check.v', 'EXP32_IEEE.v', 'EXP32_IEEE_Check.v',
         'Closed.v', 'Identity.v']
S, O, P, E, C = 'IEEE64_Statement.v', 'Ops.v', 'P32_IEEE.v', 'EXP32_IEEE.v', 'Closed.v'
ME = 'ieee64/plants/make_plants.py'

# Lines of the proof files that a refusal is pinned to: (file, line, text that line must hold).
PINS = {
    'cst-KK': (O, 209, 'apply (b2r_whole false _ 23 _ 536870913)'),
    'cst-MM': (O, 210, 'rewrite (b2r_fin false _ (-149) _ 3 51)'),
    'cst-TT': (O, 211, 'rewrite (b2r_fin false _ (-178) _ 1 52)'),
    'cst-HH': (O, 212, 'rewrite (b2r_fin false _ (-202) _ 1 52)'),
    'cst-0': (O, 213, '  - reflexivity.'),
    'cst-1': (O, 214, 'apply (b2r_whole false _ 52 _ 1)'),
    'cst-m160': (O, 215, 'apply (b2r_whole true _ 45 _ (-160))'),
    'cst-4096': (O, 216, 'apply (b2r_whole false _ 40 _ 4096)'),
    'cst-5040': (O, 217, 'apply (b2r_whole false _ 40 _ 5040)'),
    'cst-2520': (O, 218, 'apply (b2r_whole false _ 41 _ 2520)'),
    'cst-840': (O, 219, 'apply (b2r_whole false _ 43 _ 840)'),
    'cst-210': (O, 220, 'apply (b2r_whole false _ 45 _ 210)'),
    'cst-42': (O, 221, 'apply (b2r_whole false _ 47 _ 42)'),
    'cst-7': (O, 222, 'apply (b2r_whole false _ 50 _ 7)'),
    'sqrt-intros': (P, 124, 'unfold IEEE_SQRT32. intros b Fb Hf H0 H1.'),
    'hypot-intros': (P, 179, 'unfold IEEE_HYPOT32. intros b1 b2 F1 F2 Hf1 Hf2 H.'),
    'exp-intros': (E, 156, 'unfold IEEE_EXP32. intros b Fb Hf Hx.'),
}
def at(pin):
    f, n, _ = PINS[pin]
    return 'ieee64/%s", line %d, characters' % (f, n)

def cst(name, old, new, what):
    """One constant of ieee_cst one unit in the last place above the graph's: refused at its own line of cst_ok."""
    return ('cst-%s-ulp' % name, 'b constant', S, [(old, new)], ('fails', 'Ops', at('cst-' + name)),
            'the IEEE constant %s' % what)
def mant(c, sign, m, e, m1):
    return ('| C_%s => @B754_finite 53 1024 %s (%s) (%s) eq_refl' % (c, sign, m, e),
            '| C_%s => @B754_finite 53 1024 %s (%s) (%s) eq_refl' % (c, sign, m1, e))
def up(name, c, sign, m, e, graph):
    o, n = mant(c, sign, m, e, m + ' + 1')
    return cst(name, o, n, '%s is one unit in the last place above it (mantissa %s + 1)' % (graph, m))
def mode(name, op, b, m, what):
    return ('mode-%s-%s' % (op, name), 'd mode', S,
            [('o_%s := @%s 53 1024 prec64_gt_0 prec64_lt_emax mode_NE;' % (op, b),
              'o_%s := @%s 53 1024 prec64_gt_0 prec64_lt_emax mode_%s;' % (op, b, m))],
            ('fails', 'Ops', '"is_finite (o_%s ieee_ops x y) = true"' % op if op != 'sqrt' else '"B2R (o_sqrt ieee_ops x) = RN64 (sqrt (B2R x))"'),
            'the IEEE %s rounds %s, not to nearest even' % (what, {'ZR': 'toward zero', 'DN': 'down', 'UP': 'up', 'NA': 'to nearest, ties away from zero'}[m]))

FIVE_OF_SIX = '''(* Plant: under the name IEEE64, a statement of five of the six parts (IEEE_EXP32 left out), and its proof. *)
From MKF.ieee64 Require Import IEEE64_Statement P32_IEEE.
Definition IEEE64 : Prop := IEEE_NARROW /\\ IEEE_SQRT32 /\\ IEEE_RSQRT32 /\\ IEEE_HYPOT32 /\\ IEEE_CST.
Theorem ieee64_holds : IEEE64.
Proof.
  exact (conj IEEE_NARROW_proof
          (conj IEEE_SQRT32_proof (conj IEEE_RSQRT32_proof (conj IEEE_HYPOT32_proof IEEE_CST_proof)))).
Qed.
'''
GUARD = '''(* Plant: False from a recursion whose termination check is switched off. *)
From MKF.ieee64 Require Import IEEE64_Statement.
#[bypass_check(guard)] Fixpoint loop (n : nat) {struct n} : False := loop n.
Theorem ieee64_holds : IEEE64.
Proof. exact (False_ind _ (loop 0)). Qed.
'''
CLOSED_PROOF = '''Proof.
  exact (conj IEEE_NARROW_proof
          (conj IEEE_SQRT32_proof
            (conj IEEE_RSQRT32_proof
              (conj IEEE_HYPOT32_proof
                (conj IEEE_EXP32_proof IEEE_CST_proof))))).
Qed.
'''
OPS_DIV = ('  intros Fx Ny H.\n'
           '  generalize (Bdiv_correct 53 1024 prec64_gt_0 prec64_lt_emax mode_NE x y Ny).\n')
P32_INV = ('  intros Fv [_ H].\n'
           '  destruct (Rlt_or_le (Rabs v) OVF32) as [L | L]; [exact L | exfalso].\n')
EXP_SQB = '  intros Fs HB H. destruct (Rle_or_lt s 1) as [L | L]; [lra |].\n'
EXP_FIN = ('  { destruct (MKF.exp32r.Range.exp32_range (B2R b) Hf Hx) as [He _].\n'
           '    apply (faithful_finite (exp (B2R b))); [| exact (MKF.exp32.Exp32.exp32_faithful (B2R b) Hf Hx)].\n'
           '    rewrite Rabs_pos_eq by (left; apply exp_pos). left. exact He. }\n')

# name, class, source, changes [(old, new)] or the whole text, expectation, what the plant is
PLANTS = [
    # (a) one operation changed in a shape: the definition that holds the shape to its graph (eq_refl) must fail
    ('shape-narrow-add', 'a shape', S,
     [('(o_sub o (o_add o v (o_cst o C_MM)) (o_cst o C_MM))', '(o_add o (o_add o v (o_cst o C_MM)) (o_cst o C_MM))')],
     ('fails', 'IEEE64_Statement', '"G_narrow R model_ops v = narrow v"'),
     'narrow\'s shape: (v + MM) + MM for (v + MM) - MM'),
    ('shape-sqrt-abs', 'a shape', S,
     [('(x : T) : T := G_narrow T o (o_sqrt o x).', '(x : T) : T := G_narrow T o (o_abs o x).')],
     ('fails', 'IEEE64_Statement', '"G_sqrt32 R model_ops x = g_sqrt32 x"'),
     'sqrt32\'s shape: the absolute value for the square root'),
    ('shape-rsqrt-mul', 'a shape', S,
     [('G_narrow T o (o_div o (o_cst o C_1) (o_sqrt o x))', 'G_narrow T o (o_mul o (o_cst o C_1) (o_sqrt o x))')],
     ('fails', 'IEEE64_Statement', '"G_rsqrt32 R model_ops x = g_rsqrt32 x"'),
     'rsqrt32\'s shape: a multiplication for the division'),
    ('shape-hypot-sub', 'a shape', S,
     [('(o_sqrt o (o_add o (o_mul o x x) (o_mul o y y)))', '(o_sqrt o (o_sub o (o_mul o x x) (o_mul o y y)))')],
     ('fails', 'IEEE64_Statement', '"G_hypot32 R model_ops x y = g_hypot32 x y"'),
     'hypot32\'s shape: x*x - y*y for x*x + y*y'),
    ('shape-exp-eleven', 'a shape', S,
     [('    (G_exp32_sq T o (G_exp32_sq T o (G_exp32_sq T o (G_exp32_sq T o\n'
       '    (G_exp32_poly T o (G_exp32_red T o x)))))))))))))).',
       '    (G_exp32_sq T o (G_exp32_sq T o (G_exp32_sq T o\n'
       '    (G_exp32_poly T o (G_exp32_red T o x))))))))))))).')],
     ('fails', 'IEEE64_Statement', '"G_exp32 R model_ops x = g_exp32 x"'),
     'exp32\'s shape: eleven squarings for twelve'),
    # (b) one IEEE constant one unit in the last place off: cst_ok (IEEE_CST's proof) must fail at that constant
    up('KK', 'KK', 'false', '536870913 * 2 ^ 23', '-23', 'KK'),
    up('MM', 'MM', 'false', '3 * 2 ^ 51', '-149', 'MM'),
    up('TT', 'TT', 'false', '2 ^ 52', '-178', 'TT'),
    up('HH', 'HH', 'false', '2 ^ 52', '-202', 'HH'),
    cst('0', '| C_0 => @B754_zero 53 1024 false', '| C_0 => @B754_finite 53 1024 false 1 (-1074) eq_refl',
        '0 is the least positive binary64 number, 2^-1074'),
    up('1', '1', 'false', '2 ^ 52', '-52', '1'),
    up('m160', 'm160', 'true', '160 * 2 ^ 45', '-45', '-160'),
    up('4096', '4096', 'false', '4096 * 2 ^ 40', '-40', '4096'),
    up('5040', '5040', 'false', '5040 * 2 ^ 40', '-40', '5040'),
    up('2520', '2520', 'false', '2520 * 2 ^ 41', '-41', '2520'),
    up('840', '840', 'false', '840 * 2 ^ 43', '-43', '840'),
    up('210', '210', 'false', '210 * 2 ^ 45', '-45', '210'),
    up('42', '42', 'false', '42 * 2 ^ 47', '-47', '42'),
    up('7', '7', 'false', '7 * 2 ^ 50', '-50', '7'),
    # (c) a premise dropped or loosened in one statement: its proof must fail
    ('prem-narrow-loose', 'c premise', S,
     [('forall b : b64, is_finite b = true -> Rabs (B2R b) < OVF32 ->',
       'forall b : b64, is_finite b = true -> Rabs (B2R b) < bpow radix2 1000 ->')],
     ('fails', 'P32_IEEE', 'Cannot find witness'),
     'IEEE_NARROW for every magnitude below 2^1000 (false: KK * v overflows); refused where KK * v is bounded'),
    ('prem-sqrt-no-fmax', 'c premise', S,
     [('forall b : b64, is_finite b = true -> format32 (B2R b) -> 0 <= B2R b -> B2R b <= FMAX32 ->',
       'forall b : b64, is_finite b = true -> format32 (B2R b) -> 0 <= B2R b ->')],
     ('fails', 'P32_IEEE', at('sqrt-intros')),
     'IEEE_SQRT32 without x <= FMAX32; refused by the route of the proof (it takes the premise for p32r\'s range '
     'theorem), not because the statement without it is known false'),
    ('prem-rsqrt-at-zero', 'c premise', S,
     [('forall b : b64, is_finite b = true -> format32 (B2R b) -> 0 < B2R b -> B2R b <= FMAX32 ->',
       'forall b : b64, is_finite b = true -> format32 (B2R b) -> 0 <= B2R b -> B2R b <= FMAX32 ->')],
     ('fails', 'P32_IEEE', '"0 <= B2R b" while it is expected to have type'),
     'IEEE_RSQRT32 with 0 <= x for 0 < x (false at 0: 1 / 0 is infinite); refused where the proof needs 0 < x'),
    ('prem-hypot-no-range', 'c premise', S,
     [('  sqrt (B2R b1 * B2R b1 + B2R b2 * B2R b2) <= FMAX32 ->\n', '')],
     ('fails', 'P32_IEEE', at('hypot-intros')),
     'IEEE_HYPOT32 without its range premise (false: x * x overflows for a large x); refused where the proof '
     'takes the premise'),
    ('prem-exp-no-xmax', 'c premise', S,
     [('  forall b : b64, is_finite b = true -> format32 (B2R b) -> B2R b <= XMAX ->\n',
       '  forall b : b64, is_finite b = true -> format32 (B2R b) ->\n')],
     ('fails', 'EXP32_IEEE', at('exp-intros')),
     'IEEE_EXP32 without x <= XMAX (false: the squarings overflow for a large x); refused where the proof takes '
     'the premise'),
    # (d) the rounding mode of one IEEE operation changed from mode_NE: that operation's lemma must fail
    mode('zr', 'add', 'Bplus', 'ZR', 'addition'),
    mode('dn', 'sub', 'Bminus', 'DN', 'subtraction'),
    mode('up', 'mul', 'Bmult', 'UP', 'multiplication'),
    mode('na', 'div', 'Bdiv', 'NA', 'division'),
    mode('na', 'sqrt', 'Bsqrt', 'NA', 'square root'),
    # an IEEE operation or selection that is another one
    ('ieee-sub-is-add', 'ieee operation', S,
     [('o_sub := @Bminus 53 1024 prec64_gt_0 prec64_lt_emax mode_NE;',
       'o_sub := @Bplus 53 1024 prec64_gt_0 prec64_lt_emax mode_NE;')],
     ('fails', 'Ops', '"is_finite (o_sub ieee_ops x y) = true"'),
     'the IEEE subtraction is an addition'),
    ('ieee-sel-swapped', 'ieee operation', S,
     [('o_sel_lt := fun a b c d => if @Bltb 53 1024 a b then c else d;',
       'o_sel_lt := fun a b c d => if @Bltb 53 1024 a b then d else c;')],
     ('fails', 'Ops', 'Unable to unify "c" with "d"'),
     'the IEEE selection a < b returns the other value'),
    # (e) a proof left out, an assumption put in, another statement under the name
    ('admitted-ops', 'e proof', O,
     [(OPS_DIV, 'Admitted.\n'
       'Lemma op_div_rest (x y : b64) : is_finite x = true -> B2R y <> 0 ->\n'
       '  Rabs (RN64 (B2R x / B2R y)) < bpow radix2 1024 ->\n'
       '  is_finite (o_div ieee_ops x y) = true /\\ B2R (o_div ieee_ops x y) = RN64 (B2R x / B2R y).\n'
       'Proof.\n' + OPS_DIV)],
     ('reader', 'Ops.op_div :', ['Admitted']),
     'Ops.op_div ends with Admitted (its proof text moved to another lemma)'),
    ('admitted-p32', 'e proof', P,
     [(P32_INV, 'Admitted.\n'
       'Lemma narrow_inv_rest (v : R) : format64 v -> finite32 (narrow v) -> Rabs v < OVF32.\n'
       'Proof.\n' + P32_INV)],
     ('reader', 'P32_IEEE.narrow_inv :', ['Admitted']),
     'P32_IEEE.narrow_inv ends with Admitted (its proof text moved to another lemma)'),
    ('admitted-exp32', 'e proof', E,
     [(EXP_SQB, 'Admitted.\n'
       'Lemma sq_back_rest (s B : R) : format64 s -> 1 <= B -> exp32_sq s <= B -> s <= B.\n'
       'Proof.\n' + EXP_SQB)],
     ('reader', 'EXP32_IEEE.sq_back :', ['Admitted']),
     'EXP32_IEEE.sq_back ends with Admitted (its proof text moved to another lemma)'),
    ('admitted-closed', 'e proof', C,
     [(CLOSED_PROOF, 'Proof.\nAdmitted.\n')],
     ('reader', 'Closed.ieee64_holds :', ['Admitted']),
     'the top theorem ieee64_holds ends with Admitted'),
    ('axiom-exp32', 'e proof', E,
     [('(* exp32 *)\n', '(* exp32 *)\nAxiom exp_fin : forall x : R, finite32 (g_exp32 x).\n'),
      (EXP_FIN, '  { apply exp_fin. }\n')],
     ('reader', 'EXP32_IEEE.exp_fin :', ['Axiom']),
     'that exp32\'s result is a finite binary32 number is an Axiom of EXP32_IEEE.v, used by IEEE_EXP32\'s proof'),
    ('five-of-six', 'e proof', C, FIVE_OF_SIX,
     ('fails', 'Identity', 'has type "Closed.IEEE64"'),
     'Closed.v states, under the name IEEE64, five of the six parts (IEEE_EXP32 left out) and proves that'),
    ('guard', 'e proof', C, GUARD,
     ('reader', 'is assumed to be guarded', ['bypass_check']),
     'ieee64_holds from False, by a recursion whose termination check is switched off'),
]
NAMES = [p[0] for p in PLANTS]

class Stop(Exception): pass

def raw(f):
    with open(os.path.join(IEEE, f), 'rb') as fh: return fh.read()
def plant_path(name, src): return 'plants/%s_%s.v' % (src[:-2], name.replace('-', '_'))

def check_sources():
    if hashlib.sha256(raw(S)).hexdigest() != STATEMENT_SHA256:
        raise Stop('%s is not the frozen statement %s' % (S, STATEMENT_SHA256))
    for pin, (f, n, text) in sorted(PINS.items()):
        lines = raw(f).decode('utf-8').split('\n')
        if n > len(lines) or text not in lines[n - 1]:
            raise Stop('%s line %d does not hold %r (pin %s)' % (f, n, text, pin))

def plant_bytes(name):
    _, _, src, changes, _, _ = PLANTS[NAMES.index(name)]
    if isinstance(changes, str): return changes.encode('utf-8')
    text = raw(src).decode('utf-8')
    for old, new in changes:
        if text.count(old) != 1: raise Stop('plant %s: the text to change occurs %d times in %s' % (name, text.count(old), src))
        text = text.replace(old, new)
    return text.encode('utf-8')

def gate_json():
    if len(set(NAMES)) != len(NAMES): raise Stop('a plant name is used twice')
    d = json.dumps
    L = ['{"name": "IEEE64", "tier": "flocq4", "deps": %s,' % d(DEPS),
         ' "files": %s,' % d(FILES),
         ' "identity": "Identity",',
         ' "statement": {"file": %s, "sha256": %s},' % (d(S), d(STATEMENT_SHA256)),
         ' "gate": {"file": "gate_ieee64.py", "sha256": %s},' % d(hashlib.sha256(raw('gate_ieee64.py')).hexdigest()),
         ' "generated": {', '  "ieee64/gate.json": %s,' % d([ME, 'json'])]
    L += ['  %s: %s%s' % (d('ieee64/' + plant_path(n, p[2])), d([ME, 'plant', n]), ',' if n != NAMES[-1] else '')
          for n, p in zip(NAMES, PLANTS)]
    L += [' },', ' "plants": {']
    for name, cls, src, _, exp, what in PLANTS:
        e = {'replace': {src: plant_path(name, src)}}
        if exp[0] == 'fails': e['fails'] = exp[1]; e['text'] = exp[2]
        else: e['reader'] = exp[1]; e['words'] = exp[2]
        e['class'] = cls; e['what'] = what
        L.append('  %s: %s%s' % (d(name), d(e), ',' if name != NAMES[-1] else ''))
    L.append(' }}')
    text = '\n'.join(L) + '\n'
    json.loads(text)
    return text.encode('ascii')

def everything():
    check_sources()
    out = {'gate.json': gate_json()}
    for name, p in zip(NAMES, PLANTS): out[plant_path(name, p[2])] = plant_bytes(name)
    return out

def main():
    a = sys.argv[1:]
    try:
        if a == ['json']:
            check_sources(); sys.stdout.buffer.write(gate_json())
        elif len(a) == 2 and a[0] == 'plant' and a[1] in NAMES:
            check_sources(); sys.stdout.buffer.write(plant_bytes(a[1]))
        elif a == ['write']:
            for path, b in sorted(everything().items()):
                with open(os.path.join(IEEE, path), 'wb') as fh: fh.write(b)
                print('wrote ieee64/%s %s' % (path, hashlib.sha256(b).hexdigest()))
        elif a == ['check']:
            bad = []
            for path, b in sorted(everything().items()):
                try: same = raw(path) == b
                except OSError: same = False
                if not same: bad.append(path)
            have = sorted(f for f in os.listdir(HERE) if f.endswith('.v'))
            want = sorted(os.path.basename(plant_path(n, p[2])) for n, p in zip(NAMES, PLANTS))
            if have != want: bad.append('plants/ holds other .v files than the table\'s: %s' % sorted(set(have) ^ set(want)))
            print('PLANT FILES %s: gate.json and %d plants%s' % ('AS WRITTEN HERE' if not bad else 'DIFFER', len(NAMES), '' if not bad else '; not the same: %s' % ', '.join(bad)))
            return 1 if bad else 0
        elif a == ['list']:
            for name, cls, src, _, exp, what in PLANTS:
                print('%-20s %-15s %-19s %s' % (name, cls, src, what))
        else:
            print('usage: make_plants.py json | plant NAME | write | check | list'); return 2
    except Stop as e:
        sys.stderr.write('make_plants: %s\n' % e); return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
