# PLANTED CANARY (not real code). It deliberately imports a Verdandi internal to prove the boundary
# check catches an UPWARD dependency. mathkernel/check.py must report this file as CAUGHT
# (detector: upward-dependency). It is never built, run, or imported by the subsystem.
import graybox.rules_ref  # FORBIDDEN: a kernel source may not depend on Verdandi's simulation
