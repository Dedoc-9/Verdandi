# Certified correctly-rounded reference for sin/cos, two independent rigorous backends.
# MPFR directed rounding (gmpy2) + Arb interval arithmetic (python-flint); mpmath for a point cross-check.
# A value is CERTIFIED iff a guaranteed enclosure of the true result rounds (RN, ties-to-even) to a
# single binary64 under escalating precision; otherwise UNRESOLVED (never silently a pass).
import struct
import gmpy2
from gmpy2 import mpfr
import flint

def bits_to_float(h):
    return struct.unpack('>d', bytes.fromhex(h))[0]

def float_to_bits(x):
    return struct.pack('>d', x).hex()

def rn53_bits(hp):
    # round a high-precision gmpy2 mpfr to binary64, round-to-nearest ties-to-even, return bits
    with gmpy2.local_context(gmpy2.context(precision=53, round=gmpy2.RoundToNearest)):
        v = +mpfr(hp)
    return float_to_bits(float(v))

def mpfr_cr(xf, which, pmax=200000):
    # Guaranteed enclosure [lo,hi] via MPFR directed rounding; certified iff RN53(lo)==RN53(hi).
    p = 120
    while p <= pmax:
        with gmpy2.local_context(gmpy2.context(precision=p, round=gmpy2.RoundDown)):
            x = mpfr(xf, 53)  # xf is binary64 -> exact in p>=53 bits
            lo = gmpy2.sin(x) if which == 'sin' else gmpy2.cos(x)
        with gmpy2.local_context(gmpy2.context(precision=p, round=gmpy2.RoundUp)):
            x = mpfr(xf, 53)
            hi = gmpy2.sin(x) if which == 'sin' else gmpy2.cos(x)
        blo, bhi = rn53_bits(lo), rn53_bits(hi)
        if blo == bhi:
            return blo, True, p
        p *= 2
    return None, False, pmax

def arb_cr(xf, which, pmax=200000):
    # Arb ball guaranteed to contain true result; certified iff RN53(lower)==RN53(upper).
    x = flint.arb(xf)
    assert x.is_exact(), "arb(input) not exact"
    p = 120
    while p <= pmax:
        flint.ctx.prec = p
        r = x.sin() if which == 'sin' else x.cos()
        lo = mpfr(r.lower().str(100, radius=False), 400)
        hi = mpfr(r.upper().str(100, radius=False), 400)
        blo, bhi = rn53_bits(lo), rn53_bits(hi)
        if blo == bhi:
            return blo, True, p
        p *= 2
    return None, False, pmax

def mpmath_point_bits(xf, which):
    # High-precision POINT value (discovery, not certification), 300 significant digits.
    import mpmath
    mpmath.mp.dps = 300
    v = mpmath.sin(mpmath.mpf(xf)) if which == 'sin' else mpmath.cos(mpmath.mpf(xf))
    return rn53_bits(mpfr(str(v), 1100))

def ulp_distance(bits_a, bits_b):
    # signed integer ULP distance a-b along the monotonic binary64 ordering (adjacent-representable count)
    def key(h):
        u = int.from_bytes(bytes.fromhex(h), 'big')
        return (u ^ 0x7fffffffffffffff) if (u >> 63) else (u | 0x8000000000000000)
    return key(bits_a) - key(bits_b)

def certify(xf, which):
    # Returns dict with certified CR bits (both backends agreeing), certified flag, point cross-check.
    cm, okm, pm = mpfr_cr(xf, which)
    ca, oka, pa = arb_cr(xf, which)
    agree = (cm == ca)
    certified = okm and oka and agree
    cr = cm if certified else None
    out = {'input_bits': float_to_bits(xf), 'op': which,
           'cr_bits': cr, 'certified': certified,
           'mpfr_bits': cm, 'mpfr_ok': okm, 'mpfr_prec': pm,
           'arb_bits': ca, 'arb_ok': oka, 'arb_prec': pa,
           'backends_agree': agree}
    return out

if __name__ == '__main__':
    import sys
    print("=== VALIDATION of the certified-CR core ===")
    # V1: sin(0)=+0 exact, cos(0)=+1 exact
    for xf, op, want in [(0.0,'sin','0000000000000000'), (0.0,'cos','3ff0000000000000')]:
        r = certify(xf, op)
        print('V1', op, '(0) ->', r['cr_bits'], 'certified' if r['certified'] else 'UNRESOLVED',
              'EXPECT', want, 'OK' if r['cr_bits']==want else 'FAIL')
    # V2: both backends + mpmath point agree on a handful of ordinary inputs
    for xf in [0.5, 1.0, 0.25, 1.4, 0.123456789]:
        r = certify(xf, 'sin'); pt = mpmath_point_bits(xf, 'sin')
        tag = 'OK' if (r['certified'] and r['cr_bits']==pt) else 'FAIL'
        print('V2 sin(%s)' % xf, r['cr_bits'], 'cert' if r['certified'] else 'UNRES',
              'MPFR',r['mpfr_bits'],'ARB',r['arb_bits'],'PT',pt, tag)
    # V3 (teeth / negative control): feed a WRONG oracle value = CR + 1 ULP; harness must report ulp=+1, disagree
    xf = 0.5
    r = certify(xf, 'sin'); cr = r['cr_bits']
    def plus_one_ulp(h):
        u = int.from_bytes(bytes.fromhex(h),'big'); u += 1
        return u.to_bytes(8,'big').hex()
    wrong = plus_one_ulp(cr)
    d = ulp_distance(wrong, cr)
    print('V3 PLANT: wrong oracle = CR+1ulp ->', 'ulp_dist=%+d'%d,
          'agree=%s'%(wrong==cr), 'OK' if (d==1 and wrong!=cr) else 'FAIL')
    # V4: ulp distance self-consistency (CR vs CR = 0)
    print('V4 ulp(CR,CR)=', ulp_distance(cr,cr), 'OK' if ulp_distance(cr,cr)==0 else 'FAIL')
