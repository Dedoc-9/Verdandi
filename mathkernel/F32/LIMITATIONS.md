# mathkernel/F32: limitations

A forward note to the candidate family this folder holds. It changes no other file of the folder and adopts nothing.
The folder stays an unfrozen, unadmitted candidate family (see `README.md`).

1. **No rule for the sign of a zero result, for infinite or NaN inputs, or for overflow.** The five functions'
   statements speak of finite binary32 inputs within stated domains. What a function returns outside those premises
   is not stated, so nothing is claimed there.
2. **The exhaustive sweeps skip non-finite inputs.** The emitted sweep programs (`orl/emit.py` line 80, and
   `orl/emit-run1.py` and `orl/emit2.py`) skip every input whose exponent field is all ones; the loop's own comment
   says "infinities and NaNs". No measurement in this folder covers those inputs.
3. **A comment in a frozen statement cites a file that is not here.** The comment at line 195 of
   `ieee64/IEEE64_Statement.v` says "ieee64/STATE.md has the measurements and the reason". That file stayed in the
   preparer's workspace and was not exported with this folder. The statement's bytes stay as frozen; this note
   stands beside them.

What the records do not show is stated claim by claim in `CLAIMS.md`.
