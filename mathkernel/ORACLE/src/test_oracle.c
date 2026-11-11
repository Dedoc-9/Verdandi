/* test_oracle.c  — scratch driver for the controlled fdlibm 5.3 sin/cos oracle.
 *
 * Reads whitespace-separated 16-hex-digit input doubles (big-endian IEEE-754
 * bit patterns) on stdin.  For each input it prints one line:
 *     <inputhex> <sin_outhex> <cos_outhex>
 * where each field is the 16-hex-digit big-endian bit pattern of the double.
 *
 * It calls the fdlibm top-level sin() and cos() (from s_sin.c / s_cos.c).
 * No reliance on the host libm.
 *
 * NOT a frozen file; a scratch build input written for the differential.
 */

#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <inttypes.h>

/* fdlibm top-level entry points (declared in fdlibm.h, but we keep the driver
 * independent of that header's namespace and just forward-declare them). */
extern double sin(double);
extern double cos(double);

static double bits_to_double(uint64_t b) {
    double d;
    memcpy(&d, &b, sizeof d);
    return d;
}

static uint64_t double_to_bits(double d) {
    uint64_t b;
    memcpy(&b, &d, sizeof b);
    return b;
}

int main(void) {
    char buf[64];
    /* read whitespace-separated tokens */
    while (scanf("%63s", buf) == 1) {
        uint64_t in = 0;
        /* parse 16 hex digits, big-endian */
        if (sscanf(buf, "%16" SCNx64, &in) != 1) {
            fprintf(stderr, "bad input token: %s\n", buf);
            return 2;
        }
        double x = bits_to_double(in);
        double s = sin(x);
        double c = cos(x);
        uint64_t sb = double_to_bits(s);
        uint64_t cb = double_to_bits(c);
        printf("%016" PRIx64 " %016" PRIx64 " %016" PRIx64 "\n", in, sb, cb);
    }
    return 0;
}
