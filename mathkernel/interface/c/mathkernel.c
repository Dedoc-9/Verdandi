/* mathkernel - reference C binding (subordinate to the interface boundary).
 *
 * It exposes ONLY the public API declared in mathkernel.h. It includes no oracle internal header
 * (no fdlibm.h): it forward-declares the normative oracle's top-level entry points, which the build
 * links from the oracle objects (ORACLE/src, built per ORACLE/BUILD-RECIPE.md with
 * -ffp-contract=off -fno-fast-math). This keeps the adapter from exposing any implementation
 * internal or opening an alternate authority path.
 *
 * It opens NO alternate authority path: it neither re-implements nor selects numerics; it forwards
 * the call to the normative oracle unchanged. Admitting a backend other than the normative oracle
 * is the separate backend-admission step (deferred; not done here).
 */
#include "mathkernel.h"

/* fdlibm top-level entry points, linked from ORACLE/src (declared here, not via fdlibm.h). */
extern double sin(double);
extern double cos(double);

double mathkernel_sin(double x) { return sin(x); }
double mathkernel_cos(double x) { return cos(x); }
