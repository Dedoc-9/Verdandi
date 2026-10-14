# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director/contract.py — ADMISSION-0: every evaluation's record, complete by construction (0222).
#
#   record(intent, verdict, ran, trusted, exported)  -> the record an evaluation carries beside its verdict
#   missing(record, verdict, evidence)               -> what an admission of it still lacks ([] when nothing)
#
# By the owner's ruling of 2026-10-13: "Four candidate rungs, classified by the host … The model must not choose its
# own rung, and filenames alone must not determine it."; "Classify the effective change, not only its direct diff …
# calculate the rung from the candidate's dependency closure and changed semantics, conservatively escalating when that
# analysis is incomplete."; "Every verdict states what it did not check."; and, of the verdict, "certifies (derived
# from checks that ran and passed), not_checked, horizon, rung, trusted-component versions; a skipped check is not a
# pass" (his scope's third item, in the words the plan gave it).
#
# THE RUNG of an intent is computed here from its effective change — the addresses the scope protocol found changed
# or affected (DIRECTOR-0's realized and affected), not the intent's own lines and never its declared scope — against
# the kinds of the admitted language as this classifier knows them (restated below, not imported):
#   A  content: every changed address is an instance or a parameter of an admitted kind (a piece of dressing of a known
#      kind, play geometry of a known kind through a layout grant, a material, the air, a view, an asset, a region)
#   C  an address of a kind this classifier does not know: new behaviour until the language that has it is admitted
#   D  the candidate did not export, so its effective change is unknown, and unknown is classified at the top
# An intent cannot carry code or touch the checker, and the language has no form for defining vocabulary, so B does
# not arise from an intent today (tools/rung.py classifies changes to the program itself). A model's words about its
# own rung, scope or effects are never read here.
#
# CERTIFIES is derived: the checks that ran and passed, by name, and the scope protocol's finding when it found one.
# NOT_CHECKED is every expected check that did not run (a skip is never a pass) and what the director never checks.
# HORIZON: no tick is run and none is claimed. A scene without movers has nothing that moves; a scene with movers
#   (0226) has each one held to rules 2's table and its travel checked as a swept box (art/check.py), not played.
# TRUSTED: the sha256 of each component the verdict rests on, as the files stood when it was made.
# REQUIRES, for rung A: the verdict CLEAN (or LEAKAGE accepted by the person, recorded); every expected check ran and
#   passed; and a still of the candidate as drawn, its detectors read by the host (art/quality.py) — a still they flag
#   admitted only despite them, recorded — unless the candidate is the exact inverse of an admission (an undo), whose
#   picture is the one admitted before. Rungs C and D are not admitted by the director at all.
#
# Pure: no files, no clock. The record is in the ledger's restricted form (art/director/intent.py): text, lists, objects.

import intent as canon

PROTOCOL, VERSION = "ADMISSION-0", "0"

# the checks every evaluation runs (art/check.py's verify and QUALITY-0's), by name; a name missing from what ran is a
# skip, and a renamed check shows here as a skip, not as a pass
EXPECTED_CHECKS = (
    "play holds: the graybox map's own checks",
    "collision is C, exactly",
    "no dressing where a player can be",
    "the art carries no collision and no false ceiling",
    "every mesh names its source and licence",
    "quality: the scene's bytes are finite JSON in its one byte form",
    "quality: every field is known and inside its bounds",
    "quality: the scene is inside the native renderer's budgets",
    "movers: rules 2 holds them and their paths are clear",
)

# what the director never checks, said on every record
NEVER_CHECKED = (
    "whether the candidate does what its prompt asked: a person judges it",
    "whether the picture is good: a person judges it; the still's detectors flag and prove nothing",
    "the scene in Unreal: the importer is not run here",
    "anything over time: nothing in the scene moves, so no tick was run",   # with movers, MOVING below in its place
    "the provider's account of itself (its rationale, its outcome, its scope's intent): text, not evidence",
)

# the kinds of VERDANDI-ART 0 as this classifier knows them (restated from art/dress.py and art/director/scope.py)
DRESSING_KINDS = ("canopy", "lamp", "neon", "puddle", "skyline", "tower")
PLAY_KINDS = ("cover", "floor", "ground", "mover", "raised", "stair", "wall")
NAMED = ("asset", "env", "material", "region", "view")
ENV_FIELDS = ("bloom", "exposure", "fog", "light", "rain", "time", "title")

MOVING = ("anything over time: the scene's %d mover(s) were held to rules 2's table and their travel checked as swept boxes; "
          "no tick was run, so how they meet a player over time is not checked")

UNDO_STILL = "the exact inverse of admission #%s: its picture is the one admitted before it"


def classify(verdict, exported, regions):
    """(rung, basis): the candidate rung from the effective change. regions: the region names of the base and the
    candidate scenes (an address's first segment may be one)."""
    if not exported:
        return "D", ["the candidate did not export (%s), so its effective change is unknown, and unknown classifies at the top" % ",".join(verdict["codes"])]
    unknown = []
    for a in sorted(set(verdict["realized"]) | set(verdict["affected"])):
        s = a.split("/")
        if s[0] == "play":
            ok = len(s) >= 3 and s[1] in PLAY_KINDS
        elif s[0] == "env":
            ok = len(s) == 2 and s[1] in ENV_FIELDS
        elif s[0] in NAMED:
            ok = len(s) == 2 and s[1] != ""
        elif s[0] == "city" or s[0] in regions:
            ok = len(s) == 3 and s[1] in DRESSING_KINDS
        else:
            ok = False
        if not ok:
            unknown.append(a)
    n = len(set(verdict["realized"]) | set(verdict["affected"]))
    if unknown:
        return "C", ["%d changed address(es) of a kind this classifier does not know: %s" % (len(unknown), ", ".join(unknown[:6]))]
    return "A", ["the candidate exported in the admitted language, and each of the %d address(es) it changed or affected is an "
                 "instance or a parameter of an admitted kind" % n,
                 "it is an intent: it carries no code and names no file of the checker",
                 "classified from the scope protocol's realized and affected addresses, not from the intent's words"]


def record(intent, verdict, ran, trusted, exported, regions=(), movers=0):
    """The record of one evaluation. ran: [{name, ok}] of the checks that ran (None if none did); trusted: [(path,
    sha256)] of the components the verdict rests on, and the exporter's; movers: how many the candidate scene has."""
    ran = list(ran or [])
    names = {c["name"]: c["ok"] for c in ran}
    rung, basis = classify(verdict, exported, set(regions))
    certifies = []
    if exported and verdict["verdict"] in ("CLEAN", "LEAKAGE"):
        certifies.append("scope (DIRECTOR-0): everything that changed or was affected is declared" if verdict["verdict"] == "CLEAN" else
                         "scope (DIRECTOR-0): %d changed or affected address(es) are not declared, listed in the verdict" % len(verdict["unclaimed"]))
    if exported and verdict["cells_changed"]:
        certifies.append("the layout changed %d cell(s), each inside a region the intent grants" % len(verdict["cells_changed"]) if "SCOPE-LAYOUT" not in verdict["codes"]
                         else "the layout changed cells outside every grant (refused)")
    certifies += ["check: " + n for n in EXPECTED_CHECKS if names.get(n) is True]
    certifies += ["check: " + n for n in sorted(names) if names[n] is True and n not in EXPECTED_CHECKS]
    skipped = [n for n in EXPECTED_CHECKS if n not in names]
    never = [MOVING % movers if movers and n.startswith("anything over time") else n for n in NEVER_CHECKED]
    not_checked = ["did not run: " + n for n in skipped] + never
    requires = []
    if rung == "A":
        requires = ["verdict: CLEAN, or LEAKAGE accepted by the person and recorded",
                    "checks: every expected check ran and passed (%d)" % len(EXPECTED_CHECKS),
                    "still: a still of the candidate as drawn, its detectors read by the host; a flagged still only despite them, recorded"]
    else:
        requires = ["not admitted by the director: a rung %s candidate needs an admission outside the studio" % rung]
    return {
        "protocol": PROTOCOL, "version": VERSION,
        "rung": rung, "rung_basis": basis,
        "certifies": certifies,
        "not_checked": not_checked,
        "horizon": {"ticks": "0", "why": "nothing in VERDANDI-ART-SCENE 0 moves: no tick was run and none is claimed" if not movers else
                    "the scene's %d mover(s) move under rules 2: no tick was run and none is claimed" % movers},
        "trusted": ["%s %s" % (p, h) for p, h in sorted(trusted)],
        "requires": requires,
        "intent_sha256": canon.sha256(canon.dumps(intent)) if intent is not None else "",
    }


def missing(rec, verdict, evidence, inverse_ok=False):
    """What an admission of this evaluation lacks, given the evidence the admission brings ({accepted_leakage,
    still_sha256, detectors, despite_detectors, inverse_of}); [] when nothing. inverse_ok: the caller has checked that
    the intent is the exact inverse of the admission evidence["inverse_of"] names."""
    out = []
    if rec is None:
        return ["the evaluation has no ADMISSION-0 record (it predates 0222): evaluate it again"]
    if rec.get("protocol") != PROTOCOL or rec.get("version") != VERSION:
        return ["the record is not ADMISSION-0 version 0"]
    for k in ("rung", "rung_basis", "certifies", "not_checked", "horizon", "trusted", "requires"):
        if k not in rec:
            out.append("the record has no %s" % k)
    if out:
        return out
    if rec["rung"] != "A":
        return ["rung %s: %s" % (rec["rung"], "; ".join(rec["requires"]))]
    v = verdict["verdict"]
    if v == "REFUSED":
        out.append("the verdict is REFUSED (%s)" % ",".join(verdict["codes"]))
    elif v == "LEAKAGE" and not evidence.get("accepted_leakage"):
        out.append("the verdict is LEAKAGE and the person has not accepted it")
    certified = set(rec["certifies"])
    for n in EXPECTED_CHECKS:
        if "check: " + n not in certified:
            out.append("check not passed or not run: " + n)
    if evidence.get("inverse_of"):
        if not inverse_ok:
            out.append("the candidate is said to undo #%s, and it is not that admission's exact inverse" % evidence["inverse_of"])
    elif not evidence.get("still_sha256"):
        out.append("no still of the candidate: draw it and give the still (the studio takes it as you admit; the director: --still FILE.png)")
    else:
        det = evidence.get("detectors") or {}
        if "not_checked" in det and not evidence.get("despite_detectors"):
            out.append("the still's detectors did not run (%s): admit only despite them" % det["not_checked"])
        elif det.get("flags") and not evidence.get("despite_detectors"):
            out.append("the still's detectors flag %s: admit only despite them" % ", ".join(det["flags"]))
        elif "not_checked" not in det and "flags" not in det:
            out.append("the still's detectors are not recorded")
    return out
