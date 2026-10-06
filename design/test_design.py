#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""design/test_design.py — the design tool's own checks. Content time: this is not a row of the gate.

    python design/test_design.py

It drives design.py the way a person, a script or a model would, in a scratch project, against a real shell (the
one the gate built, or one it builds here). Each check plants what it claims to catch.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import design  # noqa: E402

RESULTS = []
TEXT = "VERDANDI-DESIGN 0\n"


def run(proj, *argv, text=None):
    env = dict(os.environ, VERDANDI_DESIGN=proj, VERDANDI_DESIGN_NONCE="test")
    cp = subprocess.run([sys.executable, "-B", os.path.join(HERE, "design.py")] + list(argv), capture_output=True, text=True, input=text, env=env,
                        errors="replace")
    return cp.returncode, cp.stdout + cp.stderr


def check(name, fn):
    try:
        said = fn()
        RESULTS.append(("PASS", name, said or ""))
    except AssertionError as e:
        RESULTS.append(("FAIL", name, str(e)))
    print("[%s] %s %s" % RESULTS[-1])


def status(proj):
    return json.loads(run(proj, "status", "--json")[1])


def sessions(proj):
    d = os.path.join(proj, "sessions")
    return sorted(os.listdir(d)) if os.path.isdir(d) else []


def main():
    tmp = tempfile.mkdtemp(prefix="verdandi-design-")
    proj = os.path.join(tmp, "p")
    try:
        shell = design.find_shell(None, tmp)
    except design.Refused as r:
        print("[SKIP] no shell: %s" % r)
        return 0
    rc, out = run(proj, "new", "--shell", shell)
    assert rc == 0, out
    head0 = status(proj)["head"]

    def t_inspect():
        rc, out = run(proj, "inspect", "--json")
        d = json.loads(out)
        assert rc == 0 and d["session"]["head"] == head0 and d["world"]["width"] == 48 and d["world"]["rows"] == 32, out[:200]
        assert d["readings"]["floor_not_reachable"] == 0 and d["world"]["camera"].startswith("28,28"), d["readings"]
        return "the project's identities, head, world and readings are reported; the world is 48 x 32"
    check("inspect", t_inspect)

    def t_parse():
        bad = {"no version line": "open 3,3\n", "an unknown statement": TEXT + "dig 3,3\n", "a cell that is not x,z": TEXT + "open 3;3\n",
               "a leading zero": TEXT + "open 03,3\n", "a cell outside the level": TEXT + "open 48,3\n", "a room with no inside": TEXT + "room 3,3 4,9\n",
               "a colour above 255": TEXT + "paint floor 256,0,0\n", "an unknown class": TEXT + "paint roof 1,2,3\n", "nothing at all": TEXT + "# only a comment\n"}
        for what, text in bad.items():
            rc, out = run(proj, "propose", "-", text=text)
            assert rc == 2 and out.startswith("DESIGN-"), "%s was not refused: %s" % (what, out[:120])
            assert status(proj)["pending"] is None, "%s left a proposal behind" % what
        return "%d malformed design texts are each refused with a code, and leave no proposal" % len(bad)
    check("the design text is bounded", t_parse)

    def t_predict():
        for what, text, code in (("opening the border", TEXT + "open 0,5\n", "DESIGN-BORDER"), ("changing a stair", TEXT + "close 7,26\n", "DESIGN-STAIR"),
                                 ("closing the camera's cell", TEXT + "close 28,28\n", "DESIGN-CAMERA")):
            rc, out = run(proj, "propose", "-", text=text)
            assert rc == 2 and out.startswith(code), "%s: %s" % (what, out[:120])
        return "opening the border, changing a stair and closing the camera's cell are refused before the seam is asked"
    check("what the seam is known to refuse", t_predict)

    def t_seam_is_the_verifier():
        # with the tool's own prediction off, the same border cell goes to the shell, and the shell refuses it
        run(proj, "grant", "--cells", "0,0,47,31", "--classes", "floor")
        rc, out = run(proj, "propose", "--no-predict", "-", text=TEXT + "open 0,5\n")
        assert rc == 0, out
        before = sessions(proj)
        rc, out = run(proj, "preview")
        assert rc == 2 and "SHELL-ADMIT-AUTHORITY" in out and "NOT ADMISSIBLE" in out, out[-300:]
        rc, out = run(proj, "admit")
        assert rc == 2 and out.startswith("DESIGN-NOT-ADMISSIBLE") and sessions(proj) == before and status(proj)["head"] == head0, out
        run(proj, "reject")
        return "with this tool's prediction off, the shell itself refuses an opened border (ADMIT-AUTHORITY); nothing is admitted"
    check("the shell is the verifier, not this tool", t_seam_is_the_verifier)

    def t_grant():
        run(proj, "grant", "--cells", "20,20,30,29", "--classes", "floor")
        rc, out = run(proj, "propose", "-", text=TEXT + "open 3,10\n")
        assert rc == 0, out
        rc, out = run(proj, "preview")
        assert rc == 2 and "SHELL-ADMIT-CAPABILITY" in out, out[-300:]
        rc, out = run(proj, "propose", "-", text=TEXT + "paint wall0 1,2,3\n")
        rc, out = run(proj, "preview")
        assert rc == 2 and "SHELL-ADMIT-CAPABILITY" in out, out[-300:]
        run(proj, "reject")
        return "a cell outside the granted rectangle and a class outside the granted set are refused by the shell (ADMIT-CAPABILITY)"
    check("a proposer does less than its grant", t_grant)

    design_a = TEXT + "room 22,21 26,25\nentrance 24,25\npaint floor 60,70,90\n"

    def t_preview_is_not_authority():
        rc, out = run(proj, "propose", "-", text=design_a)
        assert rc == 0 and "11 operation(s): 6 cell(s) open, 4 close, 1 class(es) painted" in out, out
        before = sessions(proj)
        rc, out = run(proj, "preview", "--json")
        d = json.loads(out)
        assert rc == 0 and d["ok"] and d["admitted_in_scratch"] == d["operations"] == 11 and d["proposed_head"] != head0, out[:300]
        assert sessions(proj) == before and status(proj)["head"] == head0, "a preview changed the project's sessions or its head"
        assert d["readings"]["proposed"]["floor_cells"] == d["readings"]["current"]["floor_cells"] + 6 - 4, d["readings"]
        return "a preview admits %d operations in a scratch root; the project's sessions and head are as they were" % d["operations"]
    check("a preview is state, not authority", t_preview_is_not_authority)

    def t_admit():
        previewed = status(proj)["pending"]["preview"]["head"]
        rc, out = run(proj, "admit")
        st = status(proj)
        assert rc == 0 and st["head"] == previewed != head0 and st["pending"] is None and st["steps_back_available"] == 1, out
        doc = design.savedform.read_file(st["session"])
        edits = [e for e in doc["data"]["log"] if e["kind"] == "edit"]
        assert len(edits) == 11 and all("admit" in e and e["admit"]["language"] == "VRDNP1" for e in edits), "an admitted edit carries no envelope"
        assert edits[-1]["admit"]["head"] == previewed and "cells=20,20,30,29" in edits[0]["admit"]["grant"], edits[-1]["admit"]
        w = design.World(st["session"])
        assert chr(w.at(24, 25)) == "." and chr(w.at(22, 21)) == "#" and w.tiles["floor"] == (60, 70, 90), "the admitted world is not the designed one"
        return "the admitted head is the previewed head; 11 ordinary edits, each with its envelope and the grant it was admitted under"
    check("admit is the previewed proposal, byte for byte", t_admit)

    def t_stale_and_changed():
        head1 = status(proj)["head"]
        rc, out = run(proj, "propose", "-", text=TEXT + "open 27,27\n")
        rc, out = run(proj, "preview")
        assert rc == 0, out
        # the previewed bytes are changed on disk before the admit
        prj = json.load(open(os.path.join(proj, "project.json")))
        p = prj["pending"]["preview"]["steps"][0]["proposal"]
        raw = open(p, "rb").read()
        assert b"target=27,27" in raw
        open(p, "wb").write(raw.replace(b"target=27,27", b"target=26,27"))
        rc, out = run(proj, "admit")
        assert rc == 2 and out.startswith("DESIGN-CHANGED") and status(proj)["head"] == head1, out
        open(p, "wb").write(raw)
        # the project moves on (an undo) while the proposal waits: it is stale
        run(proj, "undo")
        prj2 = json.load(open(os.path.join(proj, "project.json")))
        assert prj2["pending"] is None and status(proj)["head"] == head0, "an undo left a proposal against another head"
        prj["history"] = prj2["history"]
        json.dump(prj, open(os.path.join(proj, "project.json"), "w"))
        rc, out = run(proj, "admit")
        assert rc == 2 and out.startswith("DESIGN-STALE"), out
        run(proj, "reject")
        return "a proposal whose previewed bytes changed, and one made against a head the project has left, are each refused"
    check("what is admitted is what was previewed, against the head it was made for", t_stale_and_changed)

    def t_undo():
        st = status(proj)
        assert st["head"] == head0 and st["steps_back_available"] == 0
        kept = [s for s in sessions(proj)]
        assert len(kept) == 12, "the sessions the project stepped back from are gone (%d)" % len(kept)
        rc, out = run(proj, "undo")
        assert rc == 2 and out.startswith("DESIGN-NOTHING"), out
        rc, out = run(proj, "propose", "-", text=design_a)
        rc, out = run(proj, "preview", "--json")
        assert rc == 0 and json.loads(out)["ok"], out[:200]
        run(proj, "reject")
        return "after an undo the project stands at the earlier head, every session is still on disk, and the same design can be proposed again"
    check("undo steps back and deletes nothing", t_undo)

    def t_net_difference():
        rc, out = run(proj, "propose", "-", text=TEXT + "open 27,27\nclose 27,27\n")
        assert rc == 0 and "0 operation(s)" in out and "changes nothing" in out, out
        rc, out = run(proj, "propose", "-", text=TEXT + "close 21,28 23,28\nopen 21,28 23,28\nclose 22,28\n")
        assert rc == 0 and "1 operation(s)" in out, out
        run(proj, "reject")
        return "statements that cancel compile to nothing, and three statements over one row to the single cell that differs"
    check("the smallest operation set", t_net_difference)

    shutil.rmtree(tmp, ignore_errors=True)
    bad = [r for r in RESULTS if r[0] != "PASS"]
    print("DESIGN TOOL %s  %d checks / %d fail   (content time: not a row of the gate)" % ("FAILED" if bad else "PASSED", len(RESULTS), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
