# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/providers/scripted.py — a provider for the director gateway (art/studio.py) that is not a model: a fixed set of
# variations of a selected canopy, so that the studio can be tried, and tested, without a model or a key.
#
#   art/providers/scripted.json      {"provider": "cli", "argv": ["{python}", "art/providers/scripted.py"], ...}
#
# It reads a VERDANDI-STUDIO-REQUEST 0 on standard input and writes a VERDANDI-STUDIO-RESPONSE 0 on standard output
# (art/STUDIO.md). For a selected canopy it proposes three candidates, the three of the owner's sketch of the studio:
# "Monolithic" (lower by 1.2 m, to no less than 4.6 m, and 2.2 m deep), "Lit underside" (a narrow row of fixtures along
# its edge, magenta if the prompt says so, warm otherwise, at a restrained 60 cd) and "Deeper canopy" (2.6 m deep). For
# anything else it proposes nothing. It reads the prompt only for the word "magenta"; it understands nothing.

import json
import sys


def options(tokens):
    out, i = {}, 0
    while i < len(tokens):
        k = tokens[i]
        n = {"deep": 1, "ribs": 1, "lit": 2, "edgelit": 2}.get(k)
        if n is None:
            return None
        out[k] = tokens[i + 1:i + 1 + n]
        i += 1 + n
    return out


def statement(head, opts):
    words = list(head)
    for k in ("deep", "ribs", "lit", "edgelit"):
        if k in opts:
            words += [k] + list(opts[k])
    return " ".join(words)


def main():
    req = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    out = {"format": "VERDANDI-STUDIO-RESPONSE", "version": "0", "id": req["id"],
           "provider": {"name": "scripted", "model": "scripted-1 (fixed variations, not a model)"}, "candidates": []}
    sel = req.get("selection") or {}
    st = (sel.get("statement") or {}).get("text", "")
    words = st.split()
    if len(words) >= 6 and words[0] == "canopy" and "," in words[4] and "," in words[5]:
        head, opts = words[:6], options(words[6:])
        if opts is not None:
            height = float(head[3])
            scope = [sel["patterns"][0]]
            keep = ["the player's route and every wall", "the other slabs, the lamps and the neon"]
            low = dict(opts, deep=["2.2"])
            low_head = head[:3] + ["%.1f" % max(4.6, height - 1.2)] + head[4:]
            colour = "255,40,190" if "magenta" in req.get("prompt", "").lower() else "255,178,112"
            lit = dict(opts, edgelit=[colour, "60"])
            deep = dict(opts, deep=["2.6"])
            out["candidates"] = [
                {"title": "Monolithic", "rationale": "The slab brought down to %.1f m and made 2.2 m deep, so that it fills more of the frame and reads as one heavy mass." % max(4.6, height - 1.2),
                 "revision": ["= " + statement(low_head, low)], "scope": scope, "preserve": keep},
                {"title": "Lit underside", "rationale": "The slab where it is, with a narrow row of small fixtures along its edge at a restrained 60 cd, so that its underside reads against the dark.",
                 "revision": ["= " + statement(head, lit)], "scope": scope, "preserve": keep},
                {"title": "Deeper canopy", "rationale": "The slab where it is, made 2.6 m deep: the same plan, a heavier section.",
                 "revision": ["= " + statement(head, deep)], "scope": scope, "preserve": keep},
            ]
    sys.stdout.buffer.write(json.dumps(out, sort_keys=True).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
