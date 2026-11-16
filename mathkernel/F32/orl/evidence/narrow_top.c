// Written by narrow_top.py. The narrow of gen/sweep.c (included as it is) at the top of the binary32 range.
#define main sweep_main
#include "../gen/sweep.c"
#undef main
#include <float.h>
#include <inttypes.h>
#define W ((int64_t)1 << 24)
static double (*volatile nar)(double) = narrow;
static void named(const char *name, double v) { volatile double w = v; double r = nar(w), c = (double)(float)w;
  printf("named %-28s v=%016" PRIx64 " narrow=%016" PRIx64 " cast=%016" PRIx64 "\n", name, bits(w), bits(r), bits(c)); }
int main(void) {
  const uint64_t o = bits(0x1.ffffffp127), f = bits(0x1.fffffep127), INFB = bits(INFINITY), P128 = bits(0x1p128), SIGN = 0x8000000000000000ull;
  double (*g)(double) = nar;
  { uint64_t n = 0, differ = 0, first = 0;                                   // A: below OVF
    for (int64_t d = 1; d <= W; d++) for (int s = 0; s < 2; s++) { double v = frombits((o - (uint64_t)d) | (s ? SIGN : 0));
      double r = g(v), c = (double)(float)v;
#ifdef PLANT_TOP
      if (d == 4097 && s == 0) r = nextafter(r, 0.0);
#endif
      n++; if (bits(r) != bits(c)) { if (!differ) first = bits(v); differ++; } }
    printf("A n=%" PRIu64 " differ=%" PRIu64 " first=%016" PRIx64 "\n", n, differ, first); }
  { uint64_t n = 0, differ = 0, first = 0, above = 0;                        // B: around FLT_MAX
    for (int64_t d = -W; d <= W; d++) for (int s = 0; s < 2; s++) { double v = frombits((f + (uint64_t)d) | (s ? SIGN : 0));
      double r = g(v), c = (double)(float)v; above += !(fabs(v) < 0x1.fffffep127);
      n++; if (bits(r) != bits(c)) { if (!differ) first = bits(v); differ++; } }
    printf("B n=%" PRIu64 " differ=%" PRIu64 " first=%016" PRIx64 " left_out_by_the_sweep=%" PRIu64 "\n", n, differ, first, above); }
  for (int s = 0; s < 2; s++) {                                              // C: OVF and above
    uint64_t n = 0, is128 = 0, finite = 0, b32 = 0, castinf = 0, same = 0, lo = ~0ull, hi = 0, firstother = 0;
    for (int64_t d = 0; d <= W; d++) { double v = frombits((o + (uint64_t)d) | (s ? SIGN : 0));
      double r = g(v), c = (double)(float)v;
#ifdef PLANT_TOP
      if (d == 4097 && s == 0) r = INFINITY;
#endif
      uint64_t rb = bits(r); n++;
      if (rb == (P128 | (s ? SIGN : 0))) is128++; else if (!firstother) firstother = bits(v);
      finite += isfinite(r) ? 1 : 0; b32 += (isfinite(r) && (double)(float)r == r) ? 1 : 0;
      castinf += bits(c) == (INFB | (s ? SIGN : 0)); same += rb == bits(c);
      if (rb < lo) lo = rb; if (rb > hi) hi = rb; }
    printf("C sign=%c n=%" PRIu64 " is_2p128=%" PRIu64 " finite=%" PRIu64 " binary32=%" PRIu64 " cast_is_inf=%" PRIu64 " same_as_cast=%" PRIu64
           " lowest=%016" PRIx64 " highest=%016" PRIx64 " first_other=%016" PRIx64 "\n", s ? '-' : '+', n, is128, finite, b32, castinf, same, lo, hi, firstother); }
  named("FLT_MAX", 0x1.fffffep127); named("OVF-1step", frombits(o - 1)); named("OVF", 0x1.ffffffp127); named("OVF+1step", frombits(o + 1));
  named("2^128", 0x1p128); named("3*2^127", 0x1.8p128); named("2^200", 0x1p200); named("2^994", 0x1p994); named("2^995-1step", 0x1.fffffffffffffp994);
  named("2^995", 0x1p995); named("1e300", 1e300); named("DBL_MAX", DBL_MAX); named("infinity", INFINITY); named("-infinity", -INFINITY); named("NaN", NAN);
  return 0; }
