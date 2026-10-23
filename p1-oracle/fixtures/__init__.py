"""Independent fixtures. hand_calculated/ derives expected bytes from the written grammar with LOCAL primitives (never
the oracle's encoders) + hashlib, so oracle==fixture is a genuine cross-check, not a self round-trip."""
