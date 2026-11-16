// Written by gen_equiv.py. The generated f_sqrt32 and f_rsqrt32 of gen/sweep.c against the expressions that
// sweep.c's exhaustive loop computes by hand, bit for bit, over a range of binary32 patterns.
#define main sweep_main
#include "../gen/sweep.c"
#undef main
// the swept expressions: "double y = is_sqrt ? sqrt(x) : 1.0 / sqrt(x);" then "double r = narrow(y);"
__attribute__((noinline)) static double ref_sqrt(double x) { double y = sqrt(x); double r = narrow(y); return r; }
#ifdef PLANT_REF
__attribute__((noinline)) static double ref_rsqrt(double x) { double y = 1.0 / x; double r = narrow(y); return r; }
#else
__attribute__((noinline)) static double ref_rsqrt(double x) { double y = 1.0 / sqrt(x); double r = narrow(y); return r; }
#endif
static double (*volatile gen_sqrt)(double) = f_sqrt32;
static double (*volatile gen_rsqrt)(double) = f_rsqrt32;
int main(int argc, char **argv) {
  if (argc != 4) return 2;
  int is_sqrt = !strcmp(argv[1], "sqrt32"); if (!is_sqrt && strcmp(argv[1], "rsqrt32")) return 2;
  uint32_t lo_u = (uint32_t)strtoul(argv[2], 0, 16), hi_u = (uint32_t)strtoul(argv[3], 0, 16);
  double (*g)(double) = is_sqrt ? gen_sqrt : gen_rsqrt;
  uint64_t n = 0, differ = 0; uint32_t first = 0; int have = 0;
  for (uint64_t uu = lo_u; uu <= hi_u; uu++) { uint32_t u = (uint32_t)uu;
    if ((u & 0x7f800000u) == 0x7f800000u) continue;                 // infinities and NaNs
    if (u & 0x80000000u) continue; if (!is_sqrt && u == 0) continue;  // domain: x >= 0 (sqrt), x > 0 (rsqrt)
    double x = from32(u); n++;
    double a = g(x), b = is_sqrt ? ref_sqrt(x) : ref_rsqrt(x);
    if (bits(a) != bits(b)) { differ++; if (!have) { first = u; have = 1; } } }
  printf("%s %08x %08x n=%llu differ=%llu first=%08x\n", argv[1], lo_u, hi_u, (unsigned long long)n, (unsigned long long)differ, first);
  return 0; }
