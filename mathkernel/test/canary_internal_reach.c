/* PLANTED CANARY (not real code). A mock CONSUMER that deliberately reaches a kernel INTERNAL
 * (the oracle header fdlibm.h) instead of binding to the public interface. mathkernel/check.py
 * must report this file as CAUGHT (detector: internal-reach). It is never built or linked.
 *
 * A real consumer includes only interface/c/mathkernel.h. */
#include "../ORACLE/src/fdlibm.h"   /* FORBIDDEN: reaching an implementation internal */

double probe(double x) { return __kernel_sin(x, 0.0, 0); }  /* reaching an oracle-internal symbol */
