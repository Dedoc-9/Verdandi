# Makes the EXP32 gate's plants from the real files (2026-11-14); each replacement must apply exactly once.
import os
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, 'plants'); os.makedirs(P, exist_ok=True)
def rd(n): return open(os.path.join(H, n), encoding='utf-8').read()
def wr(n, t): open(os.path.join(P, n), 'w', encoding='utf-8', newline=chr(10)).write(t)
def sub(t, a, b):
    assert t.count(a) == 1, (a, t.count(a))
    return t.replace(a, b)
g = rd('Graph.v'); e = rd('Exp32.v')
# one squaring fewer: exp(x/4096)^2048
t = sub(g, 'narrow (exp32_sq (exp32_sq (', 'narrow (exp32_sq (')
wr('Graph_sq11.v', sub(t, 'exp32_red x)))))))))))))).', 'exp32_red x))))))))))))).'))
# a wrong coefficient: 43 where the polynomial has 42
wr('Graph_c43.v', sub(g, 'RN64 (42 + ', 'RN64 (43 + '))
# a clamp below the proved range
wr('Graph_clamp.v', sub(g, 'if Rlt_dec x (-160) then (-160) else x', 'if Rlt_dec x (-170) then (-170) else x'))
# a graph that is not the generator's output, though it means the same
wr('Graph_edited.v', sub(g, 'Definition exp32_sq (v : R) : R := RN64 (v * v).', 'Definition exp32_sq (v : R) : R := RN64 (v * v). '))
# an admitted lemma
wr('Exp32_admitted.v', sub(e, '  intros Hs Ha HD. replace (2 * t) with (t + t) by ring. rewrite exp_plus. exact (sq_step _ _ _ Hs Ha HD).' + chr(10) + 'Qed.', 'Admitted.'))
# a proof module that defines a statement of its own
wr('Exp32_shadow.v', 'From Coq Require Import Reals.' + chr(10) + 'Definition EXP32 : Prop := True.' + chr(10)
   + 'Theorem exp32_faithful : EXP32.' + chr(10) + 'Proof. exact I. Qed.' + chr(10))
# a weaker tail bound taken as an axiom in the Taylor file
ty = rd('Taylor.v'); cut = ty.index('Proof.', ty.index('Theorem exp_poly7'))
assert ty.count('Theorem exp_poly7') == 1 and ty.rstrip().endswith('Qed.') and ty.count('Proof.', cut) == 1
wr('Taylor_axiom.v', ty[:cut] + 'Proof.' + chr(10) + 'Admitted.' + chr(10))
print('plants written:', ', '.join(sorted(os.listdir(P))))
