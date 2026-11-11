# Independent characterization run: ORACLE (test_oracle.exe, fdlibm) vs CERTIFIED correctly-rounded reference.
# Two rigorous backends must agree to certify (MPFR directed rounding + Arb intervals); escalation on straddle;
# UNRESOLVED (never a silent pass) if neither certifies. sin and cos kept separate. S1-S4 for signed-zero/non-finite.
import struct, math, csv, subprocess, sys
import gmpy2
from gmpy2 import mpfr
import flint

BASE = r"<SCRATCH>"
EXE  = BASE + r"\fdlibm-5.3\build\test_oracle.exe"
FROZEN = BASE + r"\MATH-KERNEL-S5-VECTORS-2026-11-10.csv"
ADVERS = BASE + r"\MATH-KERNEL-CHAR-CORPUS-2026-11-10.csv"
OUT    = BASE + r"\MATH-KERNEL-CHARACTERIZATION-RESULTS-2026-11-10.csv"

def fbits(x): return struct.pack('>d', x).hex()
def bitf(h): return struct.unpack('>d', bytes.fromhex(h))[0]

def rn53_bits(hp):
    with gmpy2.context(gmpy2.get_context(), precision=53, round=gmpy2.RoundToNearest):
        v = +mpfr(hp)
    return fbits(float(v))

def mpfr_cr(xf, which, pmax=300000):
    p = 120
    while p <= pmax:
        with gmpy2.context(gmpy2.get_context(), precision=p, round=gmpy2.RoundDown):
            x = mpfr(xf, 53); lo = gmpy2.sin(x) if which=='sin' else gmpy2.cos(x)
        with gmpy2.context(gmpy2.get_context(), precision=p, round=gmpy2.RoundUp):
            x = mpfr(xf, 53); hi = gmpy2.sin(x) if which=='sin' else gmpy2.cos(x)
        blo, bhi = rn53_bits(lo), rn53_bits(hi)
        if blo == bhi: return blo, True, p
        p *= 2
    return None, False, pmax

def arb_cr(xf, which, pmax=300000):
    x = flint.arb(xf); assert x.is_exact()
    p = 120
    while p <= pmax:
        flint.ctx.prec = p
        r = x.sin() if which=='sin' else x.cos()
        blo = rn53_bits(mpfr(r.lower().str(120, radius=False), 500))
        bhi = rn53_bits(mpfr(r.upper().str(120, radius=False), 500))
        if blo == bhi: return blo, True, p
        p *= 2
    return None, False, pmax

def ulp_dist(a, b):
    def key(h):
        u = int.from_bytes(bytes.fromhex(h),'big')
        return (u ^ 0x7fffffffffffffff) if (u>>63) else (u | 0x8000000000000000)
    return key(a) - key(b)

def truept(xf, which):
    with gmpy2.context(gmpy2.get_context(), precision=400):
        x = mpfr(xf, 53); return gmpy2.sin(x) if which=='sin' else gmpy2.cos(x)

# ---- collect inputs ----
inputs = {}   # input_bits -> set of tags
def tag(b, t): inputs.setdefault(b, set()).add(t)

with open(FROZEN, newline='') as f:
    for row in csv.DictReader(f):
        grp = (row.get('group') or '').strip()
        op  = (row.get('operation') or '').strip()
        ib  = (row.get('input_bits') or '').strip().lower()
        if len(ib)==16 and op in ('sin','cos') and grp in ('direct sin/cos','reduction stress','exceptional values'):
            tag(ib, 'frozen:'+grp)
with open(ADVERS, newline='') as f:
    for row in csv.DictReader(f):
        tag(row['input_bits'].strip().lower(), 'adv:'+row['category'])

allbits = sorted(inputs)
# ---- run the oracle once over all inputs ----
stdin = '\n'.join(allbits) + '\n'
pr = subprocess.run([EXE], input=stdin, capture_output=True, text=True)
oracle = {}
for line in pr.stdout.split('\n'):
    p = line.split()
    if len(p)==3: oracle[p[0].lower()] = (p[1].lower(), p[2].lower())

def is_finite(b): return bitf(b)==bitf(b) and abs(bitf(b))!=math.inf  # not NaN, not inf

rows=[]
disagreements=[]
unresolved=[]
for b in allbits:
    xf = bitf(b)
    osin, ocos = oracle.get(b, ('?','?'))
    tags = ','.join(sorted(inputs[b]))
    for which, ob in (('sin',osin),('cos',ocos)):
        if not is_finite(b):
            rows.append([b, repr(xf), which, ob, 'NON-FINITE', 'n/a','n/a','n/a','n/a',
                         'S3: reaches oracle; no numeric CR reference', tags]); continue
        cm,okm,pm = mpfr_cr(xf, which)
        ca,oka,pa = arb_cr(xf, which)
        ZERO = ('0000000000000000','8000000000000000')
        if okm and oka and cm in ZERO and ca in ZERO:
            # Exact-zero result: S1 governs the sign of zero (Arb's interval type does not track it).
            # MPFR is IEEE-correct (sin(-0) = -0). Certify under S1 with MPFR's signed zero.
            certified = True; cm = cm  # keep MPFR signed zero
            status_note = 'certified-S1-exact-zero (mpfr p=%d)'%pm
        else:
            agree_backends = (cm==ca)
            certified = okm and oka and agree_backends
            status_note = 'certified (mpfr p=%d, arb p=%d)'%(pm,pa)
        if not certified:
            unresolved.append((b,which,pm,pa,cm,ca))
            rows.append([b, repr(xf), which, ob, 'UNRESOLVED', 'n/a','n/a','n/a','n/a',
                         'escalation did not certify (mpfr_ok=%s arb_ok=%s agree=%s)'%(okm,oka,agree_backends), tags]); continue
        cr = cm
        d = ulp_dist(ob, cr)
        agree_cr = (ob==cr)
        t = truept(xf, which)
        ov = mpfr(bitf(ob))
        abserr = abs(ov - t)
        relerr = float(abserr/abs(t)) if t!=0 else 0.0
        uu = math.ulp(bitf(ob)) if bitf(ob)!=0 else math.ulp(0.0)
        ulp_real = float(abserr/mpfr(uu)) if uu!=0 else 0.0
        if not agree_cr: disagreements.append((b,which,ob,cr,d))
        rows.append([b, repr(xf), which, ob, cr, '%+d'%d, 'yes' if agree_cr else 'NO',
                     '%.3e'%float(abserr), '%.3e'%relerr, status_note, tags])

with open(OUT,'w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['input_bits','input_repr','op','oracle_bits','cr_bits','signed_ulp','agrees_cr','abs_err','rel_err','status','tags'])
    w.writerows(rows)

# ---- summary ----
from collections import Counter
fin = [r for r in rows if r[4] not in ('NON-FINITE','UNRESOLVED')]
for op in ('sin','cos'):
    sub=[r for r in fin if r[2]==op]
    dd=[int(r[5]) for r in sub]
    c=Counter(dd)
    print('--- %s : %d certified finite inputs ---'%(op,len(sub)))
    print('   signed ULP distance oracle->CR histogram:', dict(sorted(c.items())))
    print('   max |ULP| =', max(abs(x) for x in dd) if dd else 0,
          '| correctly-rounded (ulp=0):', sum(1 for x in dd if x==0),
          '| off-by-one:', sum(1 for x in dd if abs(x)==1),
          '| >1 ULP:', sum(1 for x in dd if abs(x)>1))
print('TOTAL finite certified rows:', len(fin),
      '| NON-FINITE rows:', sum(1 for r in rows if r[4]=='NON-FINITE'),
      '| UNRESOLVED:', len(unresolved))
print('CR disagreements (oracle != certified CR):', len(disagreements))
for b,which,ob,cr,d in disagreements[:40]:
    print('   %s %s oracle=%s cr=%s ulp=%+d  x=%r'%(b,which,ob,cr,d,bitf(b)))
if unresolved:
    print('UNRESOLVED detail:')
    for u in unresolved[:20]: print('  ', u)
print('wrote', OUT)
