#ifndef MATHKERNEL_H
#define MATHKERNEL_H
/* mathkernel - the ONE logical public API (first capability: sin/cos over the declared game domain).
 *
 * This header is the single surface consumers bind to. A consumer includes ONLY this header; it must
 * not include the oracle sources or fdlibm.h, or reach any implementation internal (the boundary
 * check mathkernel/check.py enforces this). Language-specific adapters are subordinate to this API
 * and expose only it.
 *
 * Conformance (the frozen contract, FROZEN/): a backend conforms iff its output bits agree exactly
 * with the normative oracle over the corpus. The guarantee is specified-frozen-algorithm conformance
 * (controlled-build-scoped), NOT correct rounding - the oracle is faithfully rounded (<=1 ULP), with
 * eight certified 1-ULP cases that are properties of the algorithm (see CHARACTERIZATION/), never
 * errors against the contract.
 *
 * Declared domain (FROZEN/MATH-KERNEL-S5-DOMAIN-SPEC): yaw argument in [0, 2*pi), pitch in
 * [-1.45, 1.45]. Out-of-domain finite inputs are a deterministic capability error (no numeric
 * output); non-finite inputs reach the oracle (the two adopted interface policies).
 */

#ifdef __cplusplus
extern "C" {
#endif

/* Sine of x. x is an angle in radians within the declared domain. */
double mathkernel_sin(double x);

/* Cosine of x. x is an angle in radians within the declared domain. */
double mathkernel_cos(double x);

#ifdef __cplusplus
}
#endif

#endif /* MATHKERNEL_H */
