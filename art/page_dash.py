# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/page_dash.py — DASHBOARD-0 (0249, 0250): the dashboard's checks, the host's and the page's.
#
#   python art/play.py --cards-selftest       PAGE-CARDS: the cards half of the dashboard executed in a real browser
#   python art/play.py --worlds-selftest      PAGE-WORLDS (0250): the worlds, the outline and import, in worlds mode
#   (and, called from art/play.py's own self-tests, the host's rows: STUDIO's, studio_rows; LIVE's, live_rows)
#
# THE RULE THE CHECKS HOLD (the owner's text, 2026-10-17): "At the time a panel claims to represent host revision H, its
# displayed facts must be derivable from H—or the panel must identify itself as stale." The host computes every fact a
# panel shows and the revision it is of (art/play.py, Live._read: rev, VERDANDI-REV 0); the page compares identities and
# says current, stale, settling, unknown or refused. "Current" is an observation — the panel's stamp equalled the host's
# revision when the page last read it — never an authority: Admit is enabled only by the host's own account, and the
# press is checked again by the host.
#
# THE ADMISSION'S ACCOUNT (his nuance, 2026-10-17: "One nuance: the first-blocker test should compare the host’s
# displayed admission account with the host’s actual refusal under the same revision and conditions. It must not create a
# second, dashboard-owned admission policy."). The account is admit()'s own predicate run dry (art/studio.py, Gateway._admission;
# the director's admit_dry: append_evaluation's guard, cmd_admit's checks, the commit's shared map), its still pending.
# STUDIO's row reads the account /live displays for a planted state, then presses Admit with a clean still at the same
# revision, and requires the two to name the same refusal (or both to admit), each the answer its state must give; two
# plants make the dry run differ from the press and are caught by their own divergence. Undo's account is undo()'s own
# checks run dry (Gateway._undoing), held against the press the same way. PAGE and PAGE-CARDS make the comparison through
# the page: the still given first, the card read at the revision that makes, the revision read again before and after the
# press. Standard library only.

import json
import os
import re
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def _get(port, path, timeout=60):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path), timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        raw = e.read() or b""
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"body": raw[:200].decode("utf-8", "replace")}


class Gate:
    """The live loop's recompiles held (PAGE-0's gate, 0247): closed, a write is seen by the watcher and waits to compile,
    so the files stand ahead of what is served for as long as the test needs."""

    def __init__(self, live):
        self.live, self.open_ = live, threading.Event()
        self.open_.set()
        self.real = live.recompile

        def gated(only=None):
            self.open_.wait(300)
            return self.real(only)
        live.recompile = gated

    def close(self):
        self.open_.clear()

    def open(self):
        self.open_.set()

    def remove(self):
        self.open_.set()
        self.live.recompile = self.real


# ------------------------------------------------------------------------------------------------ STUDIO's rows
def studio_rows(row, c):
    """DASHBOARD-0's rows of the STUDIO self-test, in its fixture's world (plaza-night) and on its server. `c` holds what
    the self-test made: play (the module), live, srv, tok, tmp, brief, art, original, held_led, piece, cam, wait,
    post, post_still, scripted() and provider(name) (gateways). Returns the scripted gateway, the world as it was."""
    import studio
    play, live, srv, tok, brief, art = c["play"], c["live"], c["srv"], c["tok"], c["brief"], c["art"]
    D = play.director()
    port = srv.server_address[1]
    led_path = os.path.join(c["tmp"], "art", "ledger", brief + ".ledger")
    piece, cam, wait, post, post_still = c["piece"], c["cam"], c["wait"], c["post"], c["post_still"]
    ws = lambda: play.workspace(brief)

    def now():
        return _get(port, "/live?world=%s" % brief)[1]

    def settle(secs=90):
        t = time.time()
        while time.time() - t < secs:
            r = now()["rev"]
            if r["settled"] is True and r["read"]["consistent"] and not r["compiling"]:
                return r
            time.sleep(0.1)
        return None

    def displayed(rid, letter, secs=120):
        """The account /live displays for (rid, letter), once the host computed it at the revision it shows."""
        t, st = time.time(), {}
        while time.time() - t < secs:
            st = now()
            a = st.get("accounts") or {}
            if st["rev"]["read"]["consistent"] and a.get("rev") == st["rev"]["id"] and a.get("request") == rid and letter in a.get("by_letter", {}):
                return st["rev"], a["by_letter"][letter]
            time.sleep(0.1)
        return st.get("rev"), None

    def restore():
        """The fixture's world as the section found it: the brief, the ledger, no certificate past the ledger's end."""
        open(art, "wb").write(c["original"])
        open(led_path, "wb").write(c["held_led"])
        n = len(D.led.read(led_path)[0])
        certs = os.path.join(c["tmp"], "art", "build", "studio", brief, "certificates")
        for f in sorted(os.listdir(certs)) if os.path.isdir(certs) else []:
            if f.split(".")[0].isdigit() and int(f.split(".")[0]) >= n:
                os.remove(os.path.join(certs, f))
        return settle()

    def recorded(note):
        open(art, "ab").write(("# dash: %s\n" % note).encode("ascii"))
        studio.quiet(D.cmd_rebase, ws(), note)

    def compare(rid, letter):
        """The account the host displays and admit()'s answer, at one revision: the still the press brings posted first
        (a clean one: the account's pending condition, met), the account read once computed at the revision /live shows,
        that revision read again, and Admit pressed. (equal, shown, answered, detail)."""
        _c, s_ = post_still(srv, rid, letter, tok)
        rev1, acc = displayed(rid, letter)
        rev2 = now()["rev"]
        code, body = post(srv, "/studio/admit", {"id": rid, "candidate": letter, "still": s_.get("still", "")}, tok)
        answered = "admitted" if code == 200 else "%s/%s" % (body.get("code"), body.get("director_code", ""))
        shown = "none shown" if acc is None else "admitted" if acc["ok"] else "%s/%s" % (acc["first"]["code"], acc["first"]["director_code"])
        same_rev = rev1 is not None and acc is not None and rev2["id"] == rev1["id"]
        return same_rev and shown == answered, shown, answered, "%s %s at %s" % (rid[-4:], letter, (rev1 or {}).get("id", "?")[:8]), same_rev

    def ask(g, prompt="heavier"):
        rid = g.ask(prompt, piece, cam)
        wait(g, rid, 120)
        return rid

    results, g = [], c["scripted"]()
    restore()
    # 1. admissible: the account says so, and the press admits; then undone, exactly (the restoration's first row)
    rid1 = ask(g)
    # each state with the answer its set-up must give (a state that did not take hold fails, never passes as an agreement)
    results.append(("admissible", "admitted") + compare(rid1, "A"))
    code, u = post(srv, "/studio/undo", {}, tok)
    res = u.get("restoration") or {}
    row("the undo of an exact admission proves its restoration from the ledger: exact, the head before it back, its certificate kept and exact",
        code == 200 and res.get("verdict") == "exact" and res.get("head") is True and res.get("art_bytes") is True and res.get("parts_differ") == []
        and (res.get("undone_certificate") or {}).get("made") == "kept" and (res.get("undone_certificate") or {}).get("exact") is True
        and res.get("expected_head") == res.get("head_after") and (res.get("ledger") or {}).get("held_after") == "held",
        "%s; expected %s, after %s; certificate of #%s %s" % (res.get("verdict"), (res.get("expected_head") or "")[:12], (res.get("head_after") or "")[:12],
                                                              res.get("of"), (res.get("undone_certificate") or {}).get("made")))
    # 2. decided (A was admitted); 3. stale (a change recorded since B was drawn)
    results.append(("decided", "STUDIO-DECIDED/") + compare(rid1, "A"))
    recorded("a change recorded after the cards were drawn")
    settle()
    results.append(("stale", "STUDIO-STALE/") + compare(rid1, "B"))
    restore()
    # 4. the files ahead of what is served (the loop held), a candidate drawn at the files: admissible, and admitted
    gate = Gate(live)
    try:
        gate.close()
        recorded("a change the loop has not compiled")
        t = time.time()
        while now()["rev"]["compiling"] != [0] and time.time() - t < 60:
            time.sleep(0.1)
        held = now()["rev"]
        rid4 = ask(g)
        r4 = ("files ahead of slot 0, drawn at the files (settled %s, compiling %s)" % (held["settled"], held["compiling"]),
              "admitted" if held["settled"] is False and held["compiling"] == [0] else "the loop was not held") + compare(rid4, "A")
        results.append(r4)
    finally:
        gate.remove()
    restore()
    # 5. the files the exporter refuses; 6. a hand edit the ledger does not hold, the candidate drawn at it; 7. a broken ledger
    rid5 = ask(g)
    open(art, "ab").write(b"bogus_statement x\n")
    settle()            # the refusal compiled: the same revision and conditions at the read and the press
    results.append(("the files refused by the exporter", "STUDIO-FAILED/") + compare(rid5, "A"))
    restore()
    open(art, "ab").write(b"# a hand edit, not recorded\n")
    settle()
    rid6 = ask(g)
    settle()
    results.append(("a hand edit the ledger does not hold", "STUDIO-DIRECTOR-REFUSED/LEDGER-UNLOGGED") + compare(rid6, "A"))
    restore()
    rid7 = ask(g)
    open(led_path, "ab").write(b"not a canonical document\n")
    settle()
    results.append(("a ledger that does not read", "STUDIO-DIRECTOR-REFUSED/LEDGER-LINE") + compare(rid7, "A"))
    restore()
    # 8. not drawn; 9. drawn and not CLEAN (LEAKAGE)
    gb = c["provider"]("one_bad")
    rid8 = ask(gb)
    results.append(("not drawn", "STUDIO-NOT-ADMISSIBLE/") + compare(rid8, "A"))
    results.append(("drawn, LEAKAGE", "STUDIO-NOT-ADMISSIBLE/") + compare(rid8, "C"))
    g = c["scripted"]()
    restore()
    row("the admission's account the host displays is admit()'s own refusal at the same revision, in %d states, each the answer its state must give (one predicate, run dry)" % len(results),
        all(r[2] and r[3] == r[1] for r in results),
        "; ".join("%s: %s%s" % (r[0], r[3], "" if r[2] and r[3] == r[1] else " (the press: %s; expected %s; at the same revision %s)" % (r[4], r[1], r[6])) for r in results))

    # the plants: the dry run made to differ from the press, each caught by the comparison
    for plant, label in (("account-drops-stale", "stale"), ("account-director-skipped", "a hand edit the ledger does not hold")):
        studio.ACCOUNT_PLANT = plant
        try:
            if plant == "account-drops-stale":
                rid = ask(g)
                recorded("a change recorded after the cards were drawn (plant)")
                settle()
            else:
                open(art, "ab").write(b"# a hand edit, not recorded (plant)\n")
                rid = ask(g)
            same, shown, answered, _d, same_rev = compare(rid, "A")
        finally:
            studio.ACCOUNT_PLANT = ""
        restore()
        # caught only by the plant's own divergence, at one revision: the dry run's answer where the press gives the honest one
        want = {"account-drops-stale": ("STUDIO-DIRECTOR-REFUSED/HEAD-MOVED", "STUDIO-STALE/"),
                "account-director-skipped": ("admitted", "STUDIO-DIRECTOR-REFUSED/LEDGER-UNLOGGED")}[plant]
        row("plant %s: the account made to differ from the press is caught by the comparison (%s)" % (plant, label),
            same_rev and not same and (shown, answered) == want, "displayed %s; the press answered %s; at the same revision %s" % (shown, answered, same_rev))

    # the restoration: an admission made by the command line, of a statement written aligned; undone through the studio
    def aligned_admission():
        text = c["original"].decode("utf-8")
        line = "canopy plaza concrete_slab 7.0 19,10 28,11"
        open(art, "wb").write(text.replace(line, line.replace(" ", "   ", 2), 1).encode("utf-8"))
        studio.quiet(D.cmd_rebase, ws(), "the canopy's statement written aligned")
        w = ws()
        _o, parts, _c = w.export()
        doc = {"base": {k: parts[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": brief, "candidate": "A",
               "format": "VERDANDI-INTENT", "layout": [], "prompt": "deeper (a command line's admission)", "rationale": "deeper",
               "revision": ["= " + line + " deep 2.6"], "scope": ["plaza/canopy/*"], "version": "0"}
        raw = D.canon.dumps(doc)
        verdict, after, timings, _o1, _o0, _t, rec = D.evaluate_doc(w, D.canon.load_intent(raw))
        ev = studio.quiet(D.append_evaluation, w, raw, verdict, after, timings, rec)
        a = studio.quiet(D.cmd_admit, w, ev["seq"], chooser="a command line (DASHBOARD-0's self-test)", still=D.selftest_still())
        settle()
        return verdict["verdict"], a

    v, a = aligned_admission()
    certs = os.path.join(c["tmp"], "art", "build", "studio", brief, "certificates")
    kept_before = os.path.exists(os.path.join(certs, "%s.json" % a["seq"]))
    _c, t1 = _get(port, "/undo.json?world=%s" % brief)
    kept_after_get = os.path.exists(os.path.join(certs, "%s.json" % a["seq"]))
    uc = t1.get("undone_certificate") or {}
    row("GET /undo.json names what Undo would undo (a command line's admission) and its certificate made from the ledger, not kept: a GET writes nothing",
        v == "CLEAN" and t1.get("can") is True and t1.get("of") == a["seq"] and t1.get("would_restore") == a["head_before"] and uc.get("made") == "from the ledger now; not kept"
        and uc.get("exact") is False and uc.get("statements") is True and not kept_before and not kept_after_get,
        "#%s (%s); would restore %s; its certificate: exact %s, statements %s, %s" % (t1.get("of"), v, (t1.get("would_restore") or "")[:12], uc.get("exact"),
                                                                                     uc.get("statements"), uc.get("made")))
    code, u = post(srv, "/studio/undo", {}, tok)
    res = u.get("restoration") or {}
    uc = res.get("undone_certificate") or {}
    row("undone, NOT restored exactly, and said: the statements came back, the bytes did not (an aligned statement's '='); its certificate kept by the POST",
        code == 200 and res.get("verdict") == "statements-not-bytes" and res.get("head") is False and res.get("statements") is True and res.get("art_bytes") is False
        and res.get("parts_differ") == ["art"] and uc.get("made") == "from the ledger, kept now" and os.path.exists(os.path.join(certs, "%s.json" % a["seq"]))
        and (u.get("certificate") or {}).get("ok") is True,
        "%s (%s); expected %s, after %s; parts differing %s; the undone certificate %s" % (res.get("verdict"), res.get("said"), (res.get("expected_head") or "")[:12],
                                                                                         (res.get("head_after") or "")[:12], res.get("parts_differ"), uc.get("made")))
    restore()
    studio.ACCOUNT_PLANT = "restoration-from-own-certificate"
    try:
        aligned_admission()
        code, u = post(srv, "/studio/undo", {}, tok)
    finally:
        studio.ACCOUNT_PLANT = ""
    res = u.get("restoration") or {}
    # caught by the plant's own divergence: what came back is the aligned case's (the statements, not the bytes, the art
    # part), and only the verdict, read from the undo's own certificate (exact), says otherwise
    row("plant restoration-from-own-certificate: the verdict read from the undo's own certificate (a redo's inverse) is caught: it does not say what came back",
        code == 200 and res.get("verdict") == "exact" and res.get("statements") is True and res.get("art_bytes") is False and res.get("parts_differ") == ["art"]
        and (u.get("certificate") or {}).get("exact") is True,
        "the plant's verdict %s over statements %s, bytes %s, parts %s; the undo's own certificate exact %s" % (
            res.get("verdict"), res.get("statements"), res.get("art_bytes"), res.get("parts_differ"), (u.get("certificate") or {}).get("exact")))
    restore()

    # the literal case: the art's bytes back, another part moved (the exporter, recorded by a rebase between)
    rid = ask(g)
    _c, s_ = post_still(srv, rid, "A", tok)
    code_a, _b = post(srv, "/studio/admit", {"id": rid, "candidate": "A", "still": s_.get("still", "")}, tok)
    moved = os.path.join(c["tmp"], "dress_moved.py")
    shutil.copyfile(D.dress.__file__, moved)
    open(moved, "ab").write(b"\n# DASHBOARD-0's self-test: an exporter of other bytes\n")
    saved, memo = D.dress.__file__, D.MEMO["on"]
    D.MEMO["on"] = False
    D.dress.__file__ = moved
    try:
        studio.quiet(D.cmd_rebase, ws(), "the exporter moved")
        code, u = post(srv, "/studio/undo", {}, tok)
    finally:
        D.dress.__file__, D.MEMO["on"] = saved, memo
    res = u.get("restoration") or {}
    row("undone, NOT restored: the art's bytes came back and the exporter part did not (a rebase between); the verdict names the part",
        code_a == 200 and code == 200 and res.get("verdict") == "not-restored" and res.get("art_bytes") is True and res.get("head") is False
        and res.get("parts_differ") == ["exporter"],
        "%s: %s; parts differing %s; art bytes %s" % (res.get("verdict"), res.get("said"), res.get("parts_differ"), res.get("art_bytes")))
    restore()

    # the GETs write nothing; an answer made while the host moved says so; the new routes name their world
    rid = ask(g)

    def tree():
        out = {}
        for top in (os.path.join(c["tmp"], "art", "ledger"), os.path.join(c["tmp"], "art", "briefs"), os.path.join(c["tmp"], "art", "build", "studio")):
            for d, _ds, fs in os.walk(top):
                for f in fs:
                    p = os.path.join(d, f)
                    out[p] = open(p, "rb").read()
        return out
    before = tree()
    answers = [_get(port, "/evidence.json?world=%s&id=%s&candidate=A" % (brief, rid)) for _i in range(10)] + \
              [_get(port, "/undo.json?world=%s" % brief) for _i in range(10)]
    ev = answers[0][1]
    chk = ev.get("checklist") or {}
    row("GET /evidence.json and /undo.json, ten reads each, write nothing (the ledger, the brief, the requests' records byte for byte); "
        "the account is the admission's, the checklist EVIDENCE-0 and advisory",
        all(a_[0] == 200 for a_ in answers) and tree() == before and (ev.get("admission") or {}).get("ok") is True
        and chk.get("name") == "EVIDENCE-0" and chk.get("advisory") is True and "preview" in chk.get("missing", []) and ev.get("moved") is False,
        "%d answers; the account %s; EVIDENCE-0 missing %s, next %s" % (len(answers), "admissible" if (ev.get("admission") or {}).get("ok") else ev.get("admission"),
                                                                      chk.get("missing"), chk.get("next")))
    hooked = []

    def meanwhile(name):
        if name == "evidence:computed" and not hooked:
            hooked.append(name)
            recorded("a change recorded while the evidence was read")
    D.durable.HOOK = meanwhile
    try:
        _c, ev = _get(port, "/evidence.json?world=%s&id=%s&candidate=A" % (brief, rid))
    finally:
        D.durable.HOOK = None
    row("an answer computed while the host moved says so: moved, and its facts of the revision before", hooked and ev.get("moved") is True
        and (ev.get("rev_before") or {}).get("id") != (ev.get("rev_after") or {}).get("id"),
        "rev %s -> %s, moved %s" % ((ev.get("rev_before") or {}).get("id"), (ev.get("rev_after") or {}).get("id"), ev.get("moved")))
    restore()
    na = [_get(port, "/evidence.json?id=%s&candidate=A" % rid), _get(port, "/undo.json"), _get(port, "/undo.json?world=elsewhere")]
    row("the new routes name their world; without it (or with one that is not) they answer STUDIO-WORLD, never the default's",
        all(a_[0] == 404 and a_[1].get("code") == "STUDIO-WORLD" for a_ in na), ", ".join("%d %s" % (a_[0], a_[1].get("code")) for a_ in na))
    # a world that exists and is not open is never opened by a GET (opening one recovers its ledger and starts it); a host
    # refusal names the world it answers for; a ledger that does not read is answered, never a dropped connection
    other = os.path.join(c["tmp"], "art", "briefs", "plaza-copy.art")
    shutil.copyfile(art, other)
    try:
        t0 = tree()
        u_other = _get(port, "/undo.json?world=plaza-copy")
        e_other = _get(port, "/evidence.json?world=plaza-copy&id=x&candidate=A")
        t1_ = tree()
        opened = "plaza-copy" in getattr(live.hub, "worlds", {})
    finally:
        os.remove(other)
    nc = _get(port, "/evidence.json?world=%s&id=nope&candidate=A" % brief)
    open(led_path, "ab").write(b"not a canonical document\n")
    try:
        torn = _get(port, "/undo.json?world=%s" % brief)
    finally:
        restore()
    row("a GET never opens a world (STUDIO-WORLD, nothing written, its ledger not started); a host refusal names its world; a ledger that does not read is answered with the director's code",
        u_other[0] == 404 and u_other[1].get("code") == "STUDIO-WORLD" and e_other[1].get("code") == "STUDIO-WORLD" and t1_ == t0 and not opened
        and not os.path.exists(os.path.join(c["tmp"], "art", "ledger", "plaza-copy.ledger"))
        and nc[0] == 404 and nc[1].get("code") == "STUDIO-NO-CANDIDATE" and nc[1].get("world") == brief and (nc[1].get("rev_before") or {}).get("id")
        and torn[0] in (404, 409) and torn[1].get("code") == "STUDIO-DIRECTOR-REFUSED" and torn[1].get("director_code") == "LEDGER-LINE" and torn[1].get("world") == brief,
        "an unopened world: %d %s, opened %s; a refusal: %s for world %s; a broken ledger: %d %s %s" % (
            u_other[0], u_other[1].get("code"), opened, nc[1].get("code"), nc[1].get("world"), torn[0], torn[1].get("code"), torn[1].get("director_code")))

    # what /undo.json says Undo would do is undo()'s own checks run dry: held against the press at the same revision
    def undo_compare():
        _c, t_ = _get(port, "/undo.json?world=%s" % brief)
        r_ = now()["rev"]
        code_, u_ = post(srv, "/studio/undo", {}, tok)
        said = "undoes" if t_.get("can") else "%s/%s" % (t_.get("code"), t_.get("director_code", ""))
        did = "undoes" if code_ == 200 else "%s/%s" % (u_.get("code"), u_.get("director_code", ""))
        return said, did, (t_.get("rev_before") or {}).get("id") == r_["id"]
    undos = []
    for plant in ("", "undo-dry-skipped"):
        restore()
        studio.ACCOUNT_PLANT = plant
        try:
            got = [("nothing to undo", "STUDIO-NOTHING-TO-UNDO/") + undo_compare()]
            rid = ask(g)
            _c, s_ = post_still(srv, rid, "A", tok)
            post(srv, "/studio/admit", {"id": rid, "candidate": "A", "still": s_.get("still", "")}, tok)
            settle()
            admitted = open(art, "rb").read()
            open(art, "ab").write(b"# a hand edit, not recorded (Undo's account)\n")
            settle()
            got.append(("a hand edit the ledger does not hold", "STUDIO-DIRECTOR-REFUSED/LEDGER-UNLOGGED") + undo_compare())
            open(art, "wb").write(admitted)
            settle()
            got.append(("an admission to undo", "undoes") + undo_compare())
        finally:
            studio.ACCOUNT_PLANT = ""
        undos.append(got)
    restore()
    honest, planted = undos
    row("what /undo.json says Undo would do is undo()'s own answer at the same revision, in %d states, each the answer its state must give (one predicate, run dry)" % len(honest),
        all(said == did == want and same for _l, want, said, did, same in honest),
        "; ".join("%s: said %s, the press %s%s" % (l_, said, did, "" if same else " (NOT at the same revision)") for l_, _w, said, did, same in honest))
    hand = planted[1]
    row("plant undo-dry-skipped: an undo account that does not run the director's checks says Undo would undo a hand edit the press refuses, and is caught",
        hand[4] and hand[2] == "undoes" and hand[3] == "STUDIO-DIRECTOR-REFUSED/LEDGER-UNLOGGED", "said %s, the press %s, at the same revision %s" % (hand[2], hand[3], hand[4]))

    # a request drawn again over another: no candidate shown pointing at a slot that serves another scene
    for plant in ("", "publishing-unflagged"):
        restore()
        g = c["scripted"]()
        rid_a = ask(g, "heavier")
        gm = c["provider"]("material")
        # a request's id is the second and its gateway's count: a new gateway asking in rid_a's second would be given
        # rid_a's id and write over its record (two gateways of one world, which the fixture makes and a studio does not)
        while time.strftime("%Y%m%dT%H%M%S", time.gmtime()) == (rid_a or "").split("-")[0]:
            time.sleep(0.05)
        rid_b = ask(gm, "lighter")
        drawn_b = [x for x in ((gm.state().get("request") or {}).get("candidates") or []) if x.get("slot") is not None]
        seen = []

        def at_publish(name):
            if name == "studio:published" and not seen:
                st = live.state()
                cands = ((st["studio"].get("request") or {}).get("candidates") or [])
                wrong = [x["letter"] for x in cands if x.get("slot") is not None and x["slot"] < len(st["slots"])
                         and (st["slots"][x["slot"]].get("served") or {}).get("sha") != x.get("scene")]
                seen.append((st["rev"]["read"]["consistent"], wrong,
                             ["%s@%s %s/%s" % (x["letter"], x.get("slot"), (x.get("scene") or "")[:8],
                                               ((st["slots"][x["slot"]].get("served") or {}).get("sha") or "")[:8] if x.get("slot") is not None and x["slot"] < len(st["slots"]) else "-")
                              for x in cands]))
        studio.ACCOUNT_PLANT = plant
        D.durable.HOOK = at_publish
        try:
            gm.restore(rid_a)
        finally:
            D.durable.HOOK, studio.ACCOUNT_PLANT = None, ""
        ok = bool(seen) and (seen[0][0] is False or not seen[0][1])
        if not plant:
            row("a request drawn again over another: while its slots are given, the state says it is not one read (never a card pointing at another scene)",
                ok and bool(drawn_b) and rid_a != rid_b, "requests %s and %s; the request shown drew %d; at the publish: consistent %s, cards pointing at another scene %s (cards %s)" % (
                    rid_a, rid_b, len(drawn_b), *(seen[0] if seen else ("not reached", [], []))))
        else:
            # caught by the plant's own divergence: the publish reached, read as one, and a card pointing at another scene
            row("plant publishing-unflagged: the state not saying it is publishing shows a card pointing at another scene, and is caught",
                bool(drawn_b) and rid_a != rid_b and bool(seen) and seen[0][0] is True and bool(seen[0][1]),
                "requests %s and %s; the request shown drew %d; at the publish: consistent %s, cards pointing at another scene %s (cards %s)" % (
                    rid_a, rid_b, len(drawn_b), *(seen[0] if seen else ("not reached", [], []))))
    g = c["scripted"]()
    restore()

    # the preview's binding: recorded, never refused on. A request's camera path is seeded by its id (PATH-0), and a seed
    # can find too few clear poses (PREVIEW-NO-PATH): asked again, a new id, up to four times, and said
    plan, tries = None, 0
    while plan is None and tries < 4:
        tries += 1
        rid = ask(g)
        try:
            plan = g.preview_plan(rid, "A")
        except studio.StudioError as e:
            if e.code != "PREVIEW-NO-PATH":
                raise
    if plan is None:
        row("the preview's binding recorded and never refused on", False, "no request of four had a camera path (PREVIEW-NO-PATH)")
        restore()
        live.acc_seen = 0.0
        return g
    png = D.selftest_still()
    b = plan.get("binding") or {}
    one = g.preview_still(rid, "A", "base", 0, png, scene="0" * 64)
    two = g.preview_still(rid, "A", "candidate", 0, png, scene=b.get("candidate_sha", ""))
    rep = g.preview_finish(rid, "A")
    st = g.state()["request"]["candidates"][0]["preview"] or {}
    log = [json.loads(ln) for ln in open(os.path.join(g.records, "requests.jsonl"), "rb").read().splitlines()]
    line_ = [e for e in log if e.get("decision") == "preview" and e.get("id") == rid][-1]
    rep_file = json.loads(open(os.path.join(g.records, rid, "A.preview.report.json"), "rb").read())
    row("the preview's binding recorded and never refused on: a base still named from another scene is kept, said (drawn_ok false), and kept out of the report",
        set(b) == {"head", "base_sha", "candidate_sha"} and one.get("scene") == "0" * 64 and two.get("scene") == b.get("candidate_sha")
        and st.get("drawn_ok") is False and line_.get("drawn_ok") is False and "binding" not in rep_file and "drawn" not in rep_file and rep.get("files"),
        "binding of %s; the line's drawn %s; drawn_ok %s; the request asked %d time%s for a camera path" % (
            (b.get("head") or "")[:12], sorted(line_.get("drawn", {})), st.get("drawn_ok"), tries, "" if tries == 1 else "s"))
    restore()
    live.acc_seen = 0.0                 # the accounts' worker stops; the rows after this section read no /live
    return g


# ------------------------------------------------------------------------------------------------ LIVE's rows
def live_rows(row, c):
    """DASHBOARD-0's rows of the LIVE self-test (art/play.py selftest): the revision's heads, settled, and the request's
    identity. `c` holds play, live (watched), brief, art (its file), tmp, until(live, v0)."""
    play, live, brief, art = c["play"], c["live"], c["brief"], c["art"]
    D = play.director()

    def settled_rev(secs=60):
        t = time.time()
        while time.time() - t < secs:
            r = live.state()["rev"]
            if r["settled"] is True and not r["compiling"]:
                return r
            time.sleep(0.1)
        return live.state()["rev"]

    r = settled_rev()
    text = open(art, "rb").read().decode("utf-8")
    want = D.canon.head(play.workspace(brief).export(text)[1])
    row("rev-head", r["slots"][0]["head"] == want and r["slots"][0]["latest_head"] == want and r["settled"] is True,
        "the head of slot 0 in the revision is the director's head of the files (Workspace.export): %s" % want[:12])
    v0, sha0 = live.version, live.slot(0)["sha"]
    open(art, "ab").write(b"# a comment: the scene's bytes do not change, its head does\n")
    moved = c["until"](live, v0)
    r2 = settled_rev()
    row("rev-comment-moves-head", moved and live.slot(0)["sha"] == sha0 and r2["slots"][0]["head"] not in ("", r["slots"][0]["head"]) and r2["live"] != r["live"],
        "a comment: the version moved (v%s -> v%s), the scene %s the same, the head %s -> %s" % (r["live"], r2["live"], sha0[:12], r["slots"][0]["head"][:12], r2["slots"][0]["head"][:12]))
    gate = Gate(live)
    try:
        gate.close()
        open(art, "ab").write(b"# held behind the gate\n")
        t = time.time()
        while live.state()["rev"]["compiling"] != [0] and time.time() - t < 60:
            time.sleep(0.1)
        held = live.state()["rev"]
        gate.open()
        after = settled_rev()
    finally:
        gate.remove()
    row("rev-settled", held["settled"] is False and held["compiling"] == [0] and after["settled"] is True and after["compiling"] == [],
        "a write behind the held loop: settled %s, compiling %s; let go: settled %s" % (held["settled"], held["compiling"], after["settled"]))
    # settled is the stamps' comparison: a write before the watcher's next look is unsettled (a Live with no watcher,
    # its stamps taken by hand), and a Live that no watcher has looked at is unknown, never settled
    other = os.path.join(c["tmp"], "unwatched.art")
    shutil.copyfile(art, other)
    lv = play.Live(brief, other, [], poll=0.15)
    unknown = lv.settled()[0]
    lv.seen = lv.stamp(lv.watched_now())
    before = lv.settled()[0]
    time.sleep(0.05)
    open(other, "ab").write(b"# written after the stamps\n")
    for plant in ("", "settled-ignores-stamps"):
        play.DASH_PLANT = plant
        try:
            s = lv.settled()[0]
        finally:
            play.DASH_PLANT = ""
        if not plant:
            row("rev-settled-stamps", unknown is None and before is True and s is False,
                "no watcher yet: %s (unknown); stamps as taken: %s; a write since: %s" % (unknown, before, s))
        else:
            row("rev-settled-stamps plant settled-ignores-stamps: a write the loop has not looked at read as settled, caught", s is True, "the plant reads %s" % s)
    a = play.state_sha256({"request": {"id": "r", "state": "running", "elapsed_ms": 10}})
    b = play.state_sha256({"request": {"id": "r", "state": "running", "elapsed_ms": 99999}})
    d = play.state_sha256({"request": {"id": "r", "state": "done", "elapsed_ms": 10}})
    row("rev-request-identity", a == b and a != d, "a running request's elapsed time is not a change of it; its state is")


# ------------------------------------------------------------------------------------------------ PAGE-CARDS
# The plants of the page (PAGE-CARDS), each a copy of play.js with one text changed (it must occur exactly once), run in
# its scenario on the same browser and tree, and caught only when its row fails and every row before it in its scenario
# passed: (its scenario, the row it must fail, (the text, its replacement))
CARDS_PLANTS = {
    "cards-settle-hidden": ("open", "cards: case 1", ('else if (r.settled === false) { state = "settling";', 'else if (false) { state = "settling";')),
    "cards-stale-hidden": ("cards", "cards: case 2a", ("const said = x.why;", 'const said = /^STUDIO-STALE/.test(x.why) ? "" : x.why;')),
    "cards-admit-own-predicate": ("cards", "cards: case 2a", ('for (const b of card.querySelectorAll("button[data-act=admit]")) b.disabled = !x.ok;',
                                                           'for (const b of card.querySelectorAll("button[data-act=admit]")) b.disabled = !(c.slot !== null && c.verdict === "CLEAN" && !c.decided);')),
    "cards-validation-old-pass": ("validation", "cards: case 3", ("if (v.refused) {", "if (false) {")),
    "cards-evidence-chip-dropped": ("evidence", "cards: case 4", ("      if (ev) {", "      if (false) {")),
    "cards-undo-toast-only": ("undo", "cards: case 5a", ('if (x.verdict === "exact" && !which) return {', "if (r.ok) return {")),
    "cards-answer-unchecked": ("world", "cards: case 7", ("if (w === brief) { if (node) delete node.dataset.refused; return true; }",
                                                       "if (true) { if (node) delete node.dataset.refused; return true; }")),
}
SCENARIOS = ("open", "cards", "validation", "evidence", "undo", "world")
# seconds: a run's deadline (every wait in it is capped by it), and the whole suite's (its runs, its browser's start and
# end, each step's 30 s of grace) inside art/selftests.py's 1800 s for a suite
CARDS_LIMITS = {"honest": 720, "plant": 150, "suite": 1500}


class Stop(Exception):
    """A plant's run ends at its row."""


def sha256_text(s):
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def frames_compare(page, studio_marks, box):
    """The page's face frames (studio_ui.js) against MARK-0's (art/studio_marks.py), as integers: [] when equal, else
    the faces that differ."""
    bad = []
    for f in ("+x", "-x", "+y", "-y", "+z", "-z"):
        o, u, v, W, H = studio_marks.frame(box, f)
        p = page.get(f) or {}
        mine = [[int(x) for x in o], [int(x) for x in u], [int(x) for x in v], int(W), int(H), [int(x) for x in studio_marks.NORMALS[f]]]
        theirs = [p.get("o"), p.get("u"), p.get("v"), p.get("W"), p.get("H"), p.get("n")]
        if mine != theirs:
            bad.append(f)
    return bad


def cards_selftest(argv=()):
    """PAGE-CARDS SELFTEST n/n (python art/play.py --cards-selftest): DASHBOARD-0's page, executed in a real browser."""
    import page_test as PT
    if PT.WINDOWS:
        try:
            import studio_app
            studio_app.Job()
        except (OSError, ImportError, AttributeError):
            pass
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    browser, headed = PT.find_browser(argv), "--headed" in argv
    rows, caught, seen = cards_run(browser, headed, say=lambda s_: print(s_, flush=True))
    for ln in seen:
        print(ln)
    ok = all(o for _n, o, _d in rows) and all(caught) and len(caught) == len(CARDS_PLANTS)
    print("PAGE-CARDS SELFTEST %d/%d" % (sum(o for _n, o, _d in rows) + sum(caught), len(rows) + len(CARDS_PLANTS)))
    return 0 if ok else 1


def cards_run(browser, headed, say=None):
    """The honest run (every scenario, its rows printed), then each plant's run in its scenario; one browser and one tree.
    Returns (rows, the plants caught, OBSERVED lines)."""
    import page_test as PT
    import play
    import flagship
    import studio
    import studio_marks
    import studio_queue
    import impact
    rows, caught, seen = [], [], []
    END = time.time() + CARDS_LIMITS["suite"]
    tmp = PT.scratch("page-cards-")
    marker, profile = PT.profile_of(tmp)
    saved = (play.ROOT, dict(play.FILES), play.validate_info, play.dash_get, impact.report)
    live = srv = proc = gate = None
    alive = []
    D = play.director()
    W = flagship.WORLD
    mode = {"out": rows, "say": say, "stop": ""}

    def row(name, ok, detail):
        mode["out"].append((name, bool(ok), detail))
        if mode["say"]:
            mode["say"]("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail))
        if mode["stop"] and name.startswith(mode["stop"]):
            raise Stop()
    try:
        os.makedirs(os.path.join(tmp, "art", "briefs"))
        os.makedirs(os.path.join(tmp, "graybox", "maps"))
        for f in os.listdir(os.path.join(REPO, "graybox", "maps")):
            shutil.copy(os.path.join(REPO, "graybox", "maps", f), os.path.join(tmp, "graybox", "maps", f))
        art = os.path.join(tmp, "art", "briefs", W + ".art")
        original = open(os.path.join(HERE, "briefs", W + ".art"), "rb").read().replace(b"\r\n", b"\n")
        open(art, "wb").write(original)
        ws = D.Workspace(W, tmp)
        D.cmd_genesis_quiet(ws)
        genesis = open(ws.ledger, "rb").read()
        play.ROOT = tmp
        live = play.Live(W, art, [], poll=0.15, root=tmp)
        gate = Gate(live)
        threading.Thread(target=live.watch, kwargs={"say": lambda s_: None}, daemon=True).start()
        scripted = os.path.join(HERE, "providers", "scripted.json")
        play.start_studio(live, scripted, say=lambda s_: None)
        srv = play.server(live)
        base = "http://127.0.0.1:%d" % srv.server_address[1]
        port = srv.server_address[1]
        live.hub.queue = studio_queue.Queue(live.hub, os.path.join(tmp, "queue.jsonl"), say=lambda s_: None)    # not started: its routes only
        http = flagship.Http(base, live.hub.token)
        ch = PT.Channel(min(time.time() + CARDS_LIMITS["honest"], END), alive=lambda: proc is not None and proc.poll() is None)
        live.hub.page_test = ch
        get = lambda path: _get(port, path)[1]

        def rev():
            return get("/live?world=%s" % W).get("rev") or {}

        def snapshot():
            out, parts, _c = ws.export()
            return {"head": D.canon.head(parts), "scene_sha256": flagship.sha256(out["scene_bytes"]), "ledger": open(ws.ledger, "rb").read()}

        def until(fn, limit, step=0.1):
            limit = min(limit, max(0.0, ch.deadline - time.time()))
            t0 = time.time()
            while True:
                v = fn()
                if v or time.time() - t0 > limit:
                    return v
                time.sleep(step)

        def served_head(limit=120):
            """the live loop serves the files' own scene, and is settled"""
            return until(lambda: (live.slot(0) or {}).get("sha") == snapshot()["scene_sha256"] and live.settled()[0] is True and not live.compiling, limit, 0.2)

        def compiling0(limit=60):
            return until(lambda: rev().get("compiling") == [0], limit, 0.1)

        def recorded(note, line=None):
            open(art, "ab").write((line or "# dash: %s" % note).encode("ascii") + b"\n")
            studio.quiet(D.cmd_rebase, ws, note)

        def ask_host(prompt="panel #bay", strict=False):
            c_, r_ = http.post("/studio/ask", {"prompt": prompt, "strict": strict})
            until(lambda: ((live.studio.state()["request"] or {}).get("state") not in (None, "running")), 120, 0.1)
            return (live.studio.state()["request"] or {}).get("id"), c_

        def save_shape():
            mass = next(v for v in ws.export()[0]["scene"]["visuals"] if v["id"] == flagship.FLAGSHIP)
            return http.post("/studio/shapes/save", {"shape": {"name": "bay", "operation": "region",
                                                               "anchor": {"piece": flagship.FLAGSHIP, "face": "+z", "box": mass["box"], "scene": live.slot(0)["sha"], "view": {}},
                                                               "vertices": flagship.VERTICES, "constraints": {"within": True, "supports": False, "collision": False, "material": "keep"}}})

        def cand(title):
            st = live.studio.state()["request"] or {}
            return next((c for c in st.get("candidates", []) if c["title"] == title), None), st

        def first_blocker(title, rid, letter):
            """the owner's first-blocker test: the refusal a card displays and the host's own answer to Admit under the same
            revision and conditions. The clean still the press brings is given first (the account's pending condition,
            met, and the revision it makes); the card is read once the page shows the host's account at that revision; the
            revision is read again just before the press, and after it (a refusal writes nothing). (equal, displayed,
            answered, same revision, the director's code, the card)"""
            _c, s_ = http.post("/studio/still?id=%s&candidate=%s" % (rid, letter), D.selftest_still(), "image/png")
            r1 = rev().get("id")
            card = ch.do({"do": "card_now", "title": title, "rev": r1}, 90)
            r2 = rev().get("id")
            c_a, a_a = http.post("/studio/admit", {"id": rid, "candidate": letter, "still": s_.get("still", "")})
            r3 = rev().get("id")
            answered = "admitted" if c_a == 200 else a_a.get("code", "?")
            shown = "admitted" if card.get("admit") == "admissible" else card.get("admit")
            same = bool(r1) and card.get("rev") == r1 == r2 and (c_a == 200 or r3 == r2)
            return same and answered == shown, card.get("admit"), answered, same, a_a.get("director_code", ""), card

        def open_page():
            m0 = time.monotonic()
            r_ = ch.do({"do": "open", "url": "/play.html?world=%s&slot=0&w=%d&h=%d" % (W, PT.VIEW[0], PT.VIEW[1])}, 120)
            if not r_.get("ok"):
                raise RuntimeError("the page did not open: %s; the server answered: %s" % (r_.get("error"), ch.answered(m0)))
            return r_

        def reset(page=True):
            """the tree as at its start (the brief, the ledger of its genesis, no shape, no certificate), a gateway with no
            request, the loop let go and serving the files; then the page opened again"""
            gate.open()
            open(art, "wb").write(original)
            open(ws.ledger, "wb").write(genesis)
            try:
                live.shapes.delete("bay")
            except (studio_marks.ShapeError, OSError, KeyError):
                pass
            shutil.rmtree(os.path.join(tmp, "art", "build", "studio", W, "certificates"), ignore_errors=True)
            play.start_studio(live, scripted, say=lambda s_: None)
            served_head(120)
            return open_page() if page else None

        # ============================================================ the scenarios
        def sc_open():
            # case 1: the page renders before the host has compiled what the files say (the loop held behind a recorded edit)
            gate.close()
            recorded("a change before the page opened")
            held = compiling0()
            r0 = open_page()
            ch.do({"do": "panels", "panels": ["chips"], "wait": ["settling", "stale", "current", "refused"]}, 30)
            t = ch.do({"do": "tab", "tab": "validation"}, 30)
            p = ch.do({"do": "panels"}, 30)
            r1 = rev()
            P = p.get("panels") or {}
            said = {k: (P.get(k) or {}).get("state") for k in ("chips", "cards", "validation")}
            # (0250: a panel of no revision, the briefs to import, is never settling: it is left out, and must say it is so)
            row("cards: case 1, the page renders before the host settles — every panel of the host's revision says settling (or stale), none current, while the host's revision says the files are not compiled",
                r0.get("ok") and held and r1.get("settled") is False and r1.get("compiling") == [0] and all(v in ("settling", "stale") for v in said.values())
                and "current" not in [x.get("state") for x in P.values() if not x.get("revless")] and P.get("import", {}).get("revless") is True
                and t.get("state") in ("settling", "stale"),
                "the host: settled %s, compiling %s; the page: %s" % (r1.get("settled"), r1.get("compiling"), said))
            gate.open()
            served_head()
            ch.do({"do": "tab", "tab": "candidates"}, 30)
            p = ch.do({"do": "panels", "panels": ["chips", "cards"], "wait": ["current"]}, 60)
            P = p.get("panels") or {}
            r2 = rev()
            with live.lock:
                checks = list((live.latest[0] or {}).get("checks") or [])
            events = D.led.read(ws.ledger)[0]
            head = D.replay(ws, events)["head"]
            t = ch.do({"do": "tab", "tab": "validation", "want": "checks passed", "state": ["current"]}, 30)
            n_ok = sum(1 for c_ in checks if c_[1])
            row("cards: settled, every panel current and its facts the host's — the Source chip names the scene slot 0 serves, the Revision chip the ledger's replayed head, Validation the checks as compiled",
                all((P.get(k) or {}).get("state") == "current" for k in ("chips", "cards")) and t.get("state") == "current" and r2.get("settled") is True
                and ("[0] " + ((r2.get("slots") or [{}])[0].get("sha") or "")[:8]) in p.get("source", "") and ("#%d · %s" % (len(events), head[:8])) in p.get("revision", "")
                and ("%d of %d checks passed" % (n_ok, len(checks))) in t.get("sum", "") and n_ok == len(checks) > 0,
                "the page: %s, validation %s; source %r; revision %r; validation %r; the host: %d events, head %s, %d of %d checks" % (
                    {k: (P.get(k) or {}).get("state") for k in ("chips", "cards")}, t.get("state"), p.get("source"), p.get("revision"), t.get("sum"), len(events), head[:12], n_ok, len(checks)))
            s = ch.do({"do": "stats"}, 30)
            sr = s.get("rows") or {}
            row("cards: the statistics say what they are — a software timing of this page's clock, its step, a title on every row, VRAM not measured",
                "software timing" in s.get("stitle", "") and "not GPU time" in s.get("stitle", "") and sr and all(v.get("title") for v in sr.values())
                and (sr.get("VRAM") or {}).get("value") == "n/a"
                and (bool(re.search(r"step ≈ (?!0(\.0+)? )[0-9.]+ µs", s.get("stitle", ""))) or "step not measured" in s.get("stitle", "")),
                "%r; rows %s" % (s.get("stitle", s.get("error", ""))[-120:], sorted(sr)))
            box = [1, 2, 4, 9, 18, 36]
            fr = ch.do({"do": "frames", "box": box}, 30)
            bad = frames_compare(fr.get("frames") or {}, studio_marks, box)
            row("cards: the page's face frames are MARK-0's — six faces of a box of distinct whole numbers, compared as integers with art/studio_marks.py",
                fr.get("ok") and not bad and len(fr.get("frames") or {}) == 6, "faces differing: %s" % (bad or "none"))
            flipped = json.loads(json.dumps(fr.get("frames") or {}))
            if "-z" in flipped:
                flipped["-z"]["u"] = [1, 0, 0]
            row("cards: plant, the comparator refuses a flipped table (the page's -z with u turned): the face named", frames_compare(flipped, studio_marks, box) == ["-z"],
                "faces differing: %s" % frames_compare(flipped, studio_marks, box))
            ch.do({"do": "tab", "tab": "candidates"}, 30)
            k = ch.do({"do": "strip"}, 60)
            row("cards: the strip's Undo and its restoration chip stand through a redraw (the same elements, in the page); a card beside them is built again (the positive control)",
                k.get("ok") and k.get("undo_same") and k.get("chip_same") and k.get("menus_rebuilt") and k.get("card_replaced"),
                "Undo the same %s, the chip the same %s, the menus built again %s, the card replaced %s%s" % (
                    k.get("undo_same"), k.get("chip_same"), k.get("menus_rebuilt"), k.get("card_replaced"), "" if k.get("ok") else "; " + k.get("error", "")))

        def sc_cards():
            save_shape()
            ch.do({"do": "shapes", "name": "bay"}, 30)
            r = ch.do({"do": "ask", "words": "panel ", "shape": "bay", "strict": True}, 240)
            c1, st = cand("Panelled bay")
            if c1 is None:
                raise RuntimeError("the request drew no Panelled bay (%s)" % r.get("error", ""))
            rid = st["id"]
            r = ch.do({"do": "card", "title": "Panelled bay"}, 120)
            fresh = D.canon.head(ws.export()[1])
            row("cards: a card names the head it was drawn at, the request and its scene, as the host holds them; its account current and admissible",
                r.get("ok") and r.get("head") == c1["head"] == fresh and r.get("request") == rid and r.get("scene") == c1["scene"] and c1["scene"]
                and c1["head"][:12] in r.get("drawn", "") and rid in r.get("drawn", "") and r.get("acc") == "current" and r.get("admit") == "admissible"
                and "HEAD-MOVED" not in (c1.get("codes") or []),
                "the card: %r, %s %s; the host: head %s, scene %s" % (r.get("drawn", r.get("error", ""))[:120], r.get("acc"), r.get("admit"), c1["head"][:12], (c1["scene"] or "")[:12]))
            # case 2a: the loop held, a change recorded after the card was drawn
            h0 = ch.do({"do": "hold", "title": "Panelled bay"}, 30)
            gate.close()
            # a change to the scene (a material added), recorded: the head and the scene both move
            recorded("a change recorded after the cards were drawn", "material dash_probe 10,20,30 0.5 0.0")
            before = snapshot()
            compiling0()
            r_h = rev().get("id")
            h = ch.do({"do": "held", "title": "Panelled bay", "rev": r_h}, 60)
            hc = h.get("card") or {}
            pr = ch.do({"do": "press", "title": "Panelled bay", "button": "Admit", "rev": r_h}, 60)
            after = snapshot()
            fb = first_blocker("Panelled bay", rid, c1["letter"])
            row("cards: case 2a, the host's head moved after the card was drawn (the loop held) — the same card says the host's STUDIO-STALE, its Admit cannot be pressed, and the host answers Admit with that refusal at that revision",
                h0.get("ok") and h.get("same") and hc.get("admit") == "STUDIO-STALE" and "STUDIO-STALE" in hc.get("why", "") and hc.get("badge", "").upper() == "STUDIO-STALE"
                and h.get("cards_state") == "settling" and pr.get("pressed") == "disabled" and after["ledger"] == before["ledger"] and fb[0],
                "the held card: the same %s, %s, %r, badge %s, cards %s; Admit %s; the host answered %s (displayed %s, same revision %s); the ledger %s" % (
                    h.get("same"), hc.get("admit"), hc.get("why", h.get("error", ""))[:90], hc.get("badge"), h.get("cards_state"), pr.get("pressed", pr.get("error")),
                    fb[2], fb[1], fb[3], "unchanged" if after["ledger"] == before["ledger"] else "CHANGED"))
            # case 2b: the loop let go; the card drawn again from the new slots, its account the same refusal
            gate.open()
            served_head()
            r = ch.do({"do": "card_now", "title": "Panelled bay", "rev": rev().get("id"), "state": ["current"]}, 90)
            pr = ch.do({"do": "press", "title": "Panelled bay", "button": "Admit"}, 60)
            fb = first_blocker("Panelled bay", rid, c1["letter"])
            after2 = snapshot()
            row("cards: case 2b, settled — the card drawn again says the host's STUDIO-STALE, current; Admit cannot be pressed; the host's answer the same",
                r.get("ok") and r.get("admit") == "STUDIO-STALE" and r.get("acc") == "current" and r.get("cards_state") == "current" and pr.get("pressed") == "disabled"
                and fb[0] and after2["ledger"] == after["ledger"],
                "the card: %s, %s, cards %s; Admit %s; the host answered %s at the same revision %s" % (r.get("admit", r.get("error")), r.get("acc"), r.get("cards_state"),
                                                                                                         pr.get("pressed", pr.get("error")), fb[2], fb[3]))
            s0 = (rev().get("slots") or [{}])[0].get("sha")
            k = ch.do({"do": "compare"}, 60)
            row("cards: Compare outside Mark mode names the candidate and says Current is NOT its base when the host serves another scene",
                k.get("ok") and "NOT this candidate's base" in k.get("said", "") and k.get("base") == "no" and s0 != c1.get("base_sha"),
                "%r (base %s, %s); the host serves %s, the base %s" % (k.get("said", k.get("error", ""))[:120], k.get("base"), k.get("state"), (s0 or "")[:12], (c1.get("base_sha") or "")[:12]))
            # a card drawn at the files while the loop is behind them: admissible (its account is of the files)
            gate.close()
            recorded("a second change, behind the held loop", "material dash_probe_two 30,20,10 0.5 0.0")
            compiling0()
            ch.do({"do": "ask", "words": "panel ", "shape": "bay", "strict": True}, 240)
            c2, st2 = cand("Panelled bay")
            r = ch.do({"do": "card_now", "title": "Panelled bay", "wait": ["admissible"], "state": ["settling"]}, 120)
            settling = rev().get("settled")
            gate.open()
            served_head()
            r2 = ch.do({"do": "card_now", "title": "Panelled bay", "wait": ["admissible"], "state": ["current"]}, 90)
            k = ch.do({"do": "compare"}, 60)
            row("cards: a card drawn at the files while the loop is held behind them — admissible (its account is of the files), the cards settling; then current, and Compare says Current is its base",
                c2 is not None and r.get("admit") == "admissible" and r.get("request") == st2.get("id") and r.get("cards_state") == "settling" and settling is False
                and c2["head"] == D.canon.head(ws.export()[1]) and r2.get("admit") == "admissible" and r2.get("cards_state") == "current"
                and "this candidate's base" in k.get("said", "") and "NOT" not in k.get("said", "") and k.get("base") == "yes" and k.get("state") == "current",
                "held: %s, cards %s (host settled %s); let go: %s, cards %s; Compare %r" % (r.get("admit", r.get("error")), r.get("cards_state"), settling,
                                                                                         r2.get("admit"), r2.get("cards_state"), k.get("said", "")[:80]))

        def sc_validation():
            save_shape()
            rid, _c = ask_host()
            c1, _st = cand("Panelled bay")
            t = ch.do({"do": "tab", "tab": "validation", "want": "checks passed", "state": ["current"]}, 60)
            with live.lock:
                checks = list((live.latest[0] or {}).get("checks") or [])
            n_ok = sum(1 for c_ in checks if c_[1])
            row("cards: Validation current — the checks as compiled for slot 0, n of n, equal to the host's (read under its lock)",
                t.get("state") == "current" and ("%d of %d checks passed" % (n_ok, len(checks))) in t.get("sum", "") and n_ok == len(checks) > 0 and not t.get("refusedRow"),
                "%r (%s)" % (t.get("sum", t.get("error", "")), t.get("state")))
            # case 3: the files refused by the exporter while the old pass stands
            v = live.version
            open(art, "ab").write(b"bogus_statement x\n")
            until(lambda: live.version != v, 60)
            r1 = rev()
            t = ch.do({"do": "tab", "tab": "validation", "live": r1.get("live")}, 60)
            s0 = (r1.get("slots") or [{}])[0]
            with live.lock:
                msg = (live.latest[0] or {}).get("message", "")
            hist = get("/history.json?world=%s" % W)
            ch.do({"do": "tab", "tab": "candidates"}, 30)
            fb = first_blocker("Panelled bay", rid, c1["letter"]) if c1 else (False, "", "", False, "", {})
            card = fb[5]
            insp = hist.get("inspect") or {}
            row("cards: case 3, validation fails while an old pass stands — the tab leads with the host's refusal at the new version and names its rows the scene before's; a card's Admit says the host's STUDIO-FAILED, the host's answer the same; the ledger's read says not verified (FILES-REFUSED)",
                t.get("state") == "current" and "The files are refused" in t.get("first", "") and "of scene" in t.get("text", "") and s0.get("refused_sha256")
                and s0.get("refused_sha256") == sha256_text(msg) and card.get("admit") == "STUDIO-FAILED" and fb[0]
                and insp.get("verified") is False and str(insp.get("error", "")).startswith("FILES-REFUSED"),
                "the tab: %r (%s); the host refused v%s %s; the card %s, the host answered %s (same revision %s); history: %s" % (
                    t.get("first", t.get("error", ""))[:100], t.get("state"), r1.get("live"), (s0.get("refused_sha256") or "")[:12], card.get("admit", card.get("error")), fb[2], fb[3],
                    str(insp.get("error", ""))[:60]))
            v = live.version
            open(art, "wb").write(original)
            until(lambda: live.version != v, 60)
            t = ch.do({"do": "tab", "tab": "validation", "want": "checks passed", "state": ["current"]}, 60)
            row("cards: validation restored — the files the ledger holds again: no refusal, n of n, current",
                t.get("state") == "current" and not t.get("refusedRow") and "checks passed" in t.get("sum", "") and "of scene" not in t.get("sum", ""),
                "%r (%s)" % (t.get("sum", t.get("error", "")), t.get("state")))

        def sc_evidence():
            save_shape()

            def broken(*_a, **_k):
                raise impact.ImpactError("planted by PAGE-CARDS: the impact not computed")
            impact.report = broken
            try:
                rid, _c = ask_host()
            finally:
                impact.report = saved[4]
            c1, _st = cand("Panelled bay")
            r = ch.do({"do": "card", "title": "Panelled bay"}, 120)
            d = os.path.join(live.studio.records, rid or "")
            L = c1["letter"] if c1 else "A"
            read = lambda f: json.loads(open(os.path.join(d, L + f), "rb").read()) if os.path.exists(os.path.join(d, L + f)) else {}
            want = [k for k, ok in (("held", flagship.held_ok({"held": read(".held.json")})), ("impact", flagship.impact_ok({"impact": read(".impact.json")})),
                                    ("preview", os.path.exists(os.path.join(d, L + ".preview.report.json")))) if not ok]
            e = ch.do({"do": "evidence", "title": "Panelled bay"}, 90)
            host = get("/evidence.json?world=%s&id=%s&candidate=%s" % (W, rid, L))
            row("cards: case 4, evidence missing though the page looks ready — the card admissible (Admit reads none of the evidence) and its line says what EVIDENCE-0 finds missing, the kept files' own; the Evidence tab says advisory and next",
                r.get("admit") == "admissible" and not (r.get("buttons") or {}).get("Admit", {}).get("disabled", True) and want == ["impact", "preview"]
                and "2 of 3 missing (impact, preview)" in r.get("ev", "") and "advisory" in r.get("ev", "")
                and (host.get("checklist") or {}).get("missing") == want and (host.get("admission") or {}).get("ok") is True
                and e.get("state") == "current" and "admissible" in e.get("adm", "") and "next: impact" in e.get("next", "") and "advisory" in e.get("text", "")
                and {x["item"]: x["status"] for x in e.get("items") or []} == {x["item"]: x["status"] for x in (host.get("checklist") or {}).get("items", [])},
                "the card: %s, %r; from the kept files: missing %s; the tab: %r, %r (%s)" % (r.get("admit", r.get("error")), r.get("ev", "")[:80], want,
                                                                                           e.get("adm", e.get("error", ""))[:60], e.get("next", "")[:60], e.get("state")))
            c_q, r_q = http.post("/studio/queue/add", {"world": W, "prompt": "dash queue probe", "provider": "scripted.json"})
            t = ch.do({"do": "tab", "tab": "queue", "want": "dash queue probe"}, 30)
            x = ch.do({"do": "queue_cancel", "words": "dash queue probe"}, 30)
            gone = until(lambda: [t_ for t_ in live.hub.queue.state()["tasks"] if t_["id"] == r_q.get("id") and t_["status"] == "cancelled"], 15)
            ch.do({"do": "tab", "tab": "candidates"}, 30)
            row("cards: the Queue tab lists the host's queue, and its Cancel cancels the host's task",
                c_q == 200 and t.get("ok") and any("dash queue probe" in s_ for s_ in t.get("tasks", [])) and x.get("pressed") == "pressed" and gone,
                "queued %s; the tab %s; Cancel %s; the host's task %s" % (r_q.get("id"), (t.get("tasks") or [t.get("error", "")])[:2], x.get("pressed", x.get("error")),
                                                                          "cancelled" if gone else "NOT cancelled"))

        def sc_undo():
            save_shape()
            rid0, _c = ask_host()
            text0 = open(art, "rb").read()

            def director_admit(rev_, scope):
                _o, parts, _x = ws.export()
                doc = {"base": {k: parts[k] for k in ("art_sha256", "exporter_sha256", "world_sha256")}, "brief": W, "candidate": "A", "format": "VERDANDI-INTENT",
                       "layout": [], "prompt": "a command line's admission (PAGE-CARDS)", "rationale": "r", "revision": rev_, "scope": scope, "version": "0"}
                raw = D.canon.dumps(doc)
                v_, aft, tim, _o1, _o0, _t, rec = D.evaluate_doc(ws, D.canon.load_intent(raw))
                ev = studio.quiet(D.append_evaluation, ws, raw, v_, aft, tim, rec)
                return v_["verdict"], studio.quiet(D.cmd_admit, ws, ev["seq"], chooser="a command line (PAGE-CARDS)", still=D.selftest_still())
            verdict, a = director_admit(["= building north-lane brick 16 10,2 17,2 face window glass_wired storey 3.5"], ["north-lane/building/*"])
            certs = os.path.join(live.studio.records, "certificates")
            listing = lambda: sorted(os.listdir(certs)) if os.path.isdir(certs) else []
            row("cards: a command line's admission of an aligned statement landed: CLEAN, admitted, and no certificate kept for it",
                verdict == "CLEAN" and a.get("seq") and "%s.json" % a["seq"] not in listing(), "#%s %s; certificates kept %s" % (a.get("seq"), verdict, listing()))
            served_head()
            l0 = listing()
            u = get("/undo.json?world=%s" % W)
            m = ch.do({"do": "undo_strip", "menu": True, "press": False, "rev": rev().get("id")}, 60)
            uc = u.get("undone_certificate") or {}
            row("cards: the Edit menu's Undo names what the host would undo (GET /undo.json), its certificate made from the ledger and not kept: a GET writes nothing",
                u.get("can") is True and u.get("of") == a["seq"] and ("Undo admission #%s" % a["seq"]) in m.get("label", "") and uc.get("made") == "from the ledger now; not kept"
                and uc.get("exact") is False and uc.get("statements") is True and listing() == l0,
                "the menu %r; the host: #%s, its certificate %s (exact %s, statements %s); kept %s" % (m.get("label", m.get("error", "")), u.get("of"), uc.get("made"),
                                                                                                     uc.get("exact"), uc.get("statements"), listing()))
            # case 5a: undone, the statements back and not the bytes
            gate.close()
            r = ch.do({"do": "undo_strip", "rev": rev().get("id")}, 120)
            last = live.studio.state().get("last") or {}
            res = last.get("restoration") or {}
            lag = ch.do({"do": "chip", "phrase": "the world drawn is still the admitted scene", "has": True}, 30)
            gate.open()
            served_head()
            gone = ch.do({"do": "chip", "phrase": "the world drawn is still the admitted scene", "has": False}, 60)
            st_ = r.get("status") or {}
            row("cards: case 5a, Undo restores the statements but not the bytes — the page says so (NOT restored exactly, both heads), in its toast too, never success alone; while the loop is behind, the chip says the world drawn is the admitted scene",
                r.get("ok") and st_.get("bad") and "NOT restored exactly" in st_.get("text", "") and (res.get("head_after") or "?")[:12] in st_.get("text", "")
                and (res.get("expected_head") or "?")[:12] in st_.get("text", "") and any(t_.get("bad") and "NOT restored" in t_.get("text", "") for t_ in r.get("toasts") or [])
                and res.get("verdict") == "statements-not-bytes" and res.get("parts_differ") == ["art"] and (res.get("undone_certificate") or {}).get("made") == "from the ledger, kept now"
                and lag.get("ok") and gone.get("ok"),
                "the page: %r; the host: %s %s; the chip while held %r" % (st_.get("text", r.get("error", ""))[:140], res.get("verdict"), res.get("parts_differ"),
                                                                          lag.get("chip", lag.get("error", ""))[:80]))
            # case 5b: an exact admission, a change recorded after it, then Undo from the Edit menu: NOT restored
            verdict, _a2 = director_admit(["+ bay 10,2-17,2:s-b3-f2 panel brick"], ["north-lane/building/10,2-17,2:s-b3-f2"])
            recorded("a material added after the bay", "material dash_probe 10,20,30 0.5 0.0")
            served_head()
            r = ch.do({"do": "undo_strip", "menu": True, "press": True, "rev": rev().get("id")}, 120)
            last = live.studio.state().get("last") or {}
            res = last.get("restoration") or {}
            st_ = r.get("status") or {}
            row("cards: case 5b, undone and NOT restored (a change recorded between) — the host's verdict names the art part, the statements not back; the page says NOT restored and the part",
                verdict == "CLEAN" and r.get("ok") and st_.get("bad") and "NOT restored" in st_.get("text", "") and "art" in st_.get("text", "")
                and res.get("verdict") == "not-restored" and res.get("parts_differ") == ["art"] and res.get("statements") is False,
                "the page: %r; the host: %s, %s, statements %s" % (st_.get("text", r.get("error", ""))[:140], res.get("verdict"), res.get("parts_differ"), res.get("statements")))
            # case 5c: the files written back by hand to the head the cards were drawn at, which the ledger does not hold
            v = live.version
            open(art, "wb").write(text0)
            until(lambda: live.version != v, 60)
            served_head()
            try:
                D.held_head(ws, D.led.read(ws.ledger)[0])
                held = "held"
            except (SystemExit, D.led.LedgerError) as e:
                held = studio.director_code(e)
            c1, _st = cand("Panelled bay")
            ch.do({"do": "card_now", "title": "Panelled bay", "rev": rev().get("id"), "state": ["current"]}, 90)
            p = ch.do({"do": "panels", "panels": ["chips"], "wait": ["current"]}, 60)
            fb = first_blocker("Panelled bay", rid0, c1["letter"]) if c1 else (False, "", "", False, "", {})
            card = fb[5]
            row("cards: case 5c, the files restored by hand and not the ledger's head — the card says the host's STUDIO-DIRECTOR-REFUSED (LEDGER-UNLOGGED), the host answers the same at that revision; the Revision chip says not verified, and the restoration chip that the world has moved since the undo",
                held == "LEDGER-UNLOGGED" and card.get("admit") == "STUDIO-DIRECTOR-REFUSED" and "LEDGER-UNLOGGED" in card.get("why", "") and fb[0] and fb[4] == "LEDGER-UNLOGGED"
                and "not verified" in p.get("revision", "") and "still the admitted scene" not in p.get("undo_chip", "") and "moved since" in p.get("undo_chip", ""),
                "the host: %s; the card: %s %r; the host answered %s %s (same revision %s); the Revision chip %r; the restoration chip %r" % (
                    held, card.get("admit", card.get("error")), card.get("why", "")[:80], fb[2], fb[4], fb[3], p.get("revision"), p.get("undo_chip", "")[-60:]))
            v = live.version
            open(art, "wb").write(D.replay(ws, D.led.read(ws.ledger)[0])["art"].encode("utf-8"))
            until(lambda: live.version != v, 60)

        def sc_world():
            save_shape()
            ask_host()
            MARK = "f" * 64
            vi, dg = play.validate_info, play.dash_get

            def other_v(live_, k):
                return dict(vi(live_, k), world="elsewhere", sha=MARK)

            def other_e(hub_, path_, q_):
                c_, a_ = dg(hub_, path_, q_)
                return (c_, dict(a_, world="elsewhere", request=MARK)) if path_ == "/evidence.json" else (c_, a_)
            play.validate_info, play.dash_get = other_v, other_e
            try:
                t = ch.do({"do": "tab", "tab": "validation"}, 30)
                e = ch.do({"do": "evidence", "title": "Panelled bay"}, 60)
                p = ch.do({"do": "panels", "marker": MARK}, 30)
            finally:
                play.validate_info, play.dash_get = vi, dg
            t2 = ch.do({"do": "tab", "tab": "validation", "want": "checks passed", "state": ["current"]}, 60)
            e2 = ch.do({"do": "evidence", "title": "Panelled bay"}, 60)
            row("cards: case 7, a panel given another world's data — Validation and Evidence say refused (an answer for world elsewhere), nothing of it in the page; given its own again, current",
                "elsewhere" in t.get("refused", "") and "elsewhere" in e.get("refused", "") and p.get("html_has") is False
                and ((p.get("panels") or {}).get("evidence") or {}).get("state") == "refused" and t2.get("state") == "current" and e2.get("state") == "current" and not e2.get("refused"),
                "validation %r, evidence %r; the marker in the page %s; then %s and %s" % (t.get("refused", t.get("error", ""))[:60], e.get("refused", e.get("error", ""))[:60],
                                                                                    p.get("html_has"), t2.get("state"), e2.get("state")))

        RUN = {"open": sc_open, "cards": sc_cards, "validation": sc_validation, "evidence": sc_evidence, "undo": sc_undo, "world": sc_world}

        if not browser:
            row("cards: a browser to drive the page (Edge or Chrome; elsewhere Edge, Chrome or Chromium on PATH; --browser EXE)", False, "none found")
            return rows, caught, seen
        proc = PT.launch(browser, base + "/page_test.html", profile, headed, os.path.join(tmp, "browser.log"))
        t_run = time.time()
        for name in SCENARIOS:
            try:
                reset(page=name != "open")
                if not alive:
                    alive = [x for x in PT.leftovers(marker) if x == "unknown" or not x.split()[-1].lower().startswith("python")]
                RUN[name]()
            except PT.PageLost as e:
                row("cards: the scenario %s ran to its end" % name, False, "the page was lost: %s" % e)
                break
            except Exception as e:  # noqa: BLE001 — the self-test says what stopped a scenario, and goes on to the next
                import traceback
                traceback.print_exc()
                row("cards: the scenario %s ran to its end" % name, False, "%s: %s" % (type(e).__name__, str(e)[:200]))
        seen.append("OBSERVED cards: the honest run's six scenarios in %.0f s (a software timing)" % (time.time() - t_run))
        # the plants: each in its scenario, its rows silenced, stopped at its row
        js = open(saved[1]["/play.js"][0], "rb").read().decode("utf-8")
        for plant, (scen, want, (old, new)) in CARDS_PLANTS.items():
            if ch.lost and not (proc is not None and proc.poll() is None):
                caught.append(False)
                print("[FAIL] cards plant %s caught — NOT RUN: the page was lost (%s)" % (plant, ch.lost), flush=True)
                continue
            if js.count(old) != 1:
                caught.append(False)
                print("[FAIL] cards plant %s caught — NOT PLANTED: its text occurs %d times in play.js, not once" % (plant, js.count(old)), flush=True)
                continue
            if END - time.time() < 60:
                caught.append(False)
                print("[FAIL] cards plant %s caught — NOT RUN: the suite's time was spent" % plant, flush=True)
                continue
            planted = os.path.join(tmp, "play-%s.js" % plant)
            open(planted, "wb").write(js.replace(old, new).encode("utf-8"))
            play.FILES["/play.js"] = (planted, saved[1]["/play.js"][1])
            got = []
            mode.update(out=got, say=None, stop=want)
            ch.deadline = min(time.time() + CARDS_LIMITS["plant"], END)
            if proc is not None and proc.poll() is None:
                ch.lost = ""            # a deadline spent by the plant before stands for that plant alone
            stopped = ""
            try:
                reset(page=scen != "open")
                RUN[scen]()
            except Stop:
                pass
            except Exception as e:  # noqa: BLE001
                stopped = "%s: %s" % (type(e).__name__, str(e)[:160])
            finally:
                play.FILES["/play.js"] = saved[1]["/play.js"]
                mode.update(out=rows, say=say, stop="")
            mine = [x for x in got if x[0].startswith(want)]
            ok = not stopped and bool(mine) and not mine[0][1] and all(x[1] for x in got[:got.index(mine[0])])
            caught.append(ok)
            print("[%s] cards plant %s caught — %s" % ("PASS" if ok else "FAIL", plant,
                                                     ("by: " + mine[0][0][:90] + " — " + mine[0][2][:240]) if ok else ("the run stopped: " + stopped) if stopped
                                                     else "NOT CAUGHT: " + ("; ".join("%s %s" % ("PASS" if x[1] else "FAIL", x[0][:60]) for x in got) or "no row")), flush=True)
            if ch.lost and not (proc is not None and proc.poll() is None):
                break
    except Exception as e:  # noqa: BLE001 — the self-test says what stopped it
        import traceback
        traceback.print_exc()
        row("cards: the self-test ran to its end", False, "%s: %s" % (type(e).__name__, str(e)[:200]))
    finally:
        mode.update(out=rows, say=say, stop="")
        if gate is not None:
            gate.remove()
        try:
            if live is not None and getattr(live, "hub", None) is not None and getattr(live.hub, "page_test", None) is not None:
                live.hub.page_test.steps.put({"do": "end"})
                time.sleep(1.0)
        except Exception:  # noqa: BLE001
            pass
        if proc is not None:
            left, first, took = PT.end_browser(proc, marker)
            row("cards: the browser ended, and nothing of it is left (the query that says so found the browser's processes while it ran)",
                not left and bool(alive) and alive != ["unknown"], "while it ran: %d process%s; left: %s" % (
                    len(alive) if alive != ["unknown"] else 0, "" if len(alive) == 1 else "es", left or "nothing"))
            seen.append("OBSERVED cards: the browser ended in %.1f s%s" % (took, ("; standing at the first look: %s" % first) if first else ""))
        play.ROOT = saved[0]
        play.FILES.clear()
        play.FILES.update(saved[1])
        play.validate_info, play.dash_get, impact.report = saved[2], saved[3], saved[4]
        if live:
            live.stopping = True
            if live.studio:
                live.studio.shutdown()
        if srv:
            srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    return rows, caught, seen


# ================================================================================================ PAGE-WORLDS (0250)
# DASHBOARD-0's second half, executed in a real browser in worlds mode (the desktop studio's): a worlds folder seeded from
# a scratch source (foundry-yard), a second world made by duplicating it (foundry-copy, which the page shows: not the
# default), and the import's source a scratch checkout holding foundry-yard (a world already), harbor-day (no ledger) and
# plaza-night (its ledger left unlogged). Its rows: the worlds panel against Hub.inspect, another world unverified and
# verified again, this world's files refused by the loop, the collapse, the outline against the host's object rule with its search and a selection, the
# importable briefs, the owner's case 6 (an import that fails partway), a stage and a commit, a refused stage, his case 7
# across two worlds, and nothing of the browser left. Four plants, copies of play.js with one line changed, are caught by
# the row each names with every row before it in its scenario passed.
WORLDS_LABEL = "the scratch checkout"
WORLDS_PLANTS = {
    "worlds-import-unsaid": ("import", "worlds: case 6", ('const said = (r.code || "IMPORT-FAILED") + (r.director_code ? " (" + r.director_code + ")" : "") + " · " + (r.source_label || "the source") + " · " + (r.name || name || "") + ": " + (r.message || "");',
                                                         'const said = (r.message || "");')),
    "worlds-world-dropped": ("world", "worlds: case 7", ('getJSON("/validate.json?world=" + W + "&slot=" + k)', 'getJSON("/validate.json?slot=" + k)')),
    "worlds-other-drawn": ("world", "worlds: case 7", ('if (!answerFor(o, $("lp-outline"), "Outline")) { ui.outline = null; panelState("outline"); return; }',
                                                      'answerFor(o, $("lp-outline"), "Outline");')),
    "worlds-mark-unrefused": ("worlds", "worlds: this world's files refused", ('return JSON.stringify([s0.head || "", s0.latest_head || "", s0.refused_sha256 || ""]);',
                                                                            'return JSON.stringify([s0.head || ""]);')),
}
WORLDS_SCENARIOS = ("worlds", "outline", "import", "world")
WORLDS_LIMITS = {"honest": 480, "plant": 150, "suite": 1100}


def worlds_selftest(argv=()):
    """PAGE-WORLDS SELFTEST n/n (python art/play.py --worlds-selftest): DASHBOARD-0's worlds, outline and import, executed
    in a real browser in worlds mode."""
    import page_test as PT
    if PT.WINDOWS:
        try:
            import studio_app
            studio_app.Job()
        except (OSError, ImportError, AttributeError):
            pass
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    browser, headed = PT.find_browser(argv), "--headed" in argv
    rows, caught, seen = worlds_run(browser, headed, say=lambda s_: print(s_, flush=True))
    for ln in seen:
        print(ln)
    ok = all(o for _n, o, _d in rows) and all(caught) and len(caught) == len(WORLDS_PLANTS)
    print("PAGE-WORLDS SELFTEST %d/%d" % (sum(o for _n, o, _d in rows) + sum(caught), len(rows) + len(WORLDS_PLANTS)))
    return 0 if ok else 1


def worlds_run(browser, headed, say=None):
    """The honest run (every scenario), then each plant's run in its scenario; one browser and one worlds folder."""
    import page_test as PT
    import play
    import studio_refs
    rows, caught, seen = [], [], []
    END = time.time() + WORLDS_LIMITS["suite"]
    tmp = PT.scratch("page-worlds-")
    marker, profile = PT.profile_of(tmp)
    saved = (play.ROOT, dict(play.FILES), play.validate_info, play.outline)
    hub = srv = proc = None
    gates, alive = [], []
    D = play.director()
    PAGE, OTHER = "foundry-copy", "foundry-yard"
    mode = {"out": rows, "say": say, "stop": ""}

    def row(name, ok, detail):
        mode["out"].append((name, bool(ok), detail))
        if mode["say"]:
            mode["say"]("[%s] %s — %s" % ("PASS" if ok else "FAIL", name, detail))
        if mode["stop"] and name.startswith(mode["stop"]):
            raise Stop()

    def tree_bytes(root):
        out = {}
        for dp, _dn, fn in os.walk(root):
            for f in fn:
                rel = os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")
                if not rel.startswith("art/build/") and not rel.endswith(".lock"):
                    out[rel] = open(os.path.join(dp, f), "rb").read()
        return out
    try:
        maps = os.path.join(REPO, "graybox", "maps")
        seed = os.path.join(tmp, "seed")                    # the worlds' first source: foundry-yard alone
        os.makedirs(os.path.join(seed, "art", "briefs"))
        shutil.copytree(maps, os.path.join(seed, "graybox", "maps"))
        shutil.copy(os.path.join(HERE, "briefs", OTHER + ".art"), os.path.join(seed, "art", "briefs", OTHER + ".art"))
        src = os.path.join(tmp, "source")                   # the import's source: a scratch checkout
        D.selftest_tree(src)                                # plaza-night, its ledger started (the fixture's maps are the checkout's)
        with open(os.path.join(src, "art", "briefs", "plaza-night.art"), "ab") as fh:
            fh.write(b"# a hand edit, not recorded\n")    # its ledger left unlogged
        for b in (OTHER, "harbor-day"):
            shutil.copy(os.path.join(HERE, "briefs", b + ".art"), os.path.join(src, "art", "briefs", b + ".art"))
        src_before = tree_bytes(src)
        worlds = os.path.join(tmp, "worlds")
        play.seed_worlds(worlds, source=seed, say=lambda s_: None, source_label=WORLDS_LABEL)
        scripted = os.path.join(HERE, "providers", "scripted.json")
        hub = play.Hub(config=scripted, say=lambda s_: None, watch=False, worlds_dir=worlds, source=src, source_label=WORLDS_LABEL)
        hub.default = OTHER
        hub.world(OTHER)
        hub.duplicate(OTHER, PAGE)
        for lv in hub.worlds.values():                     # the gate on each Live before its watcher starts (0247's)
            gates.append(Gate(lv))
            lv.poll = 0.15
            threading.Thread(target=lv.watch, kwargs={"say": lambda s_: None}, daemon=True).start()
        srv = play.server(hub)
        base = "http://127.0.0.1:%d" % srv.server_address[1]
        port = srv.server_address[1]
        ch = PT.Channel(min(time.time() + WORLDS_LIMITS["honest"], END), alive=lambda: proc is not None and proc.poll() is None)
        hub.page_test = ch
        get = lambda path: _get(port, path)[1]
        aside = lambda: sorted(n for n in os.listdir(worlds) if play.ASIDE.match(n))
        other_art = os.path.join(worlds, OTHER, "art", "briefs", OTHER + ".art")
        other_text = open(other_art, "rb").read()
        page_art = os.path.join(worlds, PAGE, "art", "briefs", PAGE + ".art")
        page_text = open(page_art, "rb").read()

        def until(fn, limit, step=0.1):
            limit = min(limit, max(0.0, ch.deadline - time.time()))
            t0 = time.time()
            while True:
                v = fn()
                if v or time.time() - t0 > limit:
                    return v
                time.sleep(step)

        def settled(lv):
            return until(lambda: lv.settled()[0] is True and not lv.compiling, 120, 0.2)

        def open_page():
            m0 = time.monotonic()
            r_ = ch.do({"do": "open", "url": "/play.html?world=%s&slot=0&w=%d&h=%d" % (PAGE, PT.VIEW[0], PT.VIEW[1])}, 120)
            if not r_.get("ok"):
                raise RuntimeError("the page did not open: %s; the server answered: %s" % (r_.get("error"), ch.answered(m0)))
            return r_

        def reset():
            """the worlds folder as the run began: no imported world, nothing aside, foundry-yard's brief as seeded, no
            route wrapped; then the page opened again"""
            play.validate_info, play.outline = saved[2], saved[3]
            D.durable.HOOK = None
            if open(other_art, "rb").read() != other_text:
                open(other_art, "wb").write(other_text)
            if open(page_art, "rb").read() != page_text:
                open(page_art, "wb").write(page_text)
            for n in hub.names():
                if n not in (OTHER, PAGE):
                    D.durable.remove_tree(os.path.join(worlds, n))
            for n in aside():
                D.durable.remove_tree(os.path.join(worlds, n))
            log = os.path.join(worlds, "IMPORTS.jsonl")
            if os.path.exists(log):
                os.remove(log)
            for lv in hub.worlds.values():
                settled(lv)
            return open_page()

        # ============================================================ the scenarios
        def sc_worlds():
            w = ch.do({"do": "lp", "until": {"worlds_any": True, "panel_state": ["worlds", ["current"]]}}, 60)
            host = {n: hub.inspect(n) for n in hub.names()}
            _c, wj = _get(port, "/worlds.json")
            shown = {x["name"]: x for x in w.get("worlds", [])}
            same = sorted(shown) == sorted(host) and all(shown[n]["head"] == host[n]["head"] and shown[n]["events"] == host[n]["events"]
                                                         and shown[n]["state"] == ("verified" if host[n]["verified"] else "not-verified") for n in host)
            row("worlds: the worlds panel is each world as the host reads it back (Hub.inspect: its ledger replayed to its files), current, "
                "this page's world (not the default) among them", same and w.get("brief") == PAGE and PAGE != hub.default
                and [x["world"] for x in wj.get("worlds", [])] == sorted(host),
                "the panel %s; the host %s; the page shows %s" % ({n: (x["state"], x["events"], x["head"][:8]) for n, x in shown.items()},
                                                                  {n: (h["verified"], h["events"], h["head"][:8]) for n, h in host.items()}, w.get("brief")))
            # another world changed by hand: not verified, then verified again once its brief is put back, each read by
            # Refresh's own read (the page counts them: the 10 s read does not count)
            f0 = ((w.get("panels") or {}).get("worlds") or {}).get("forced", 0)
            with open(other_art, "ab") as fh:
                fh.write(b"# a hand edit in another world\n")
            ch.do({"do": "lp_press", "what": "wrefresh"}, 30)
            a = ch.do({"do": "lp", "until": {"forced_gt": f0}}, 60)
            f1 = ((a.get("panels") or {}).get("worlds") or {}).get("forced", f0)
            open(other_art, "wb").write(other_text)
            ch.do({"do": "lp_press", "what": "wrefresh"}, 30)
            b = ch.do({"do": "lp", "until": {"forced_gt": f1}}, 60)
            ra = next((x for x in a.get("worlds", []) if x["name"] == OTHER), {})
            rb = next((x for x in b.get("worlds", []) if x["name"] == OTHER), {})
            row("worlds: another world changed by hand reads not verified (UNLOGGED-CHANGE), its brief put back verified again, each read by Refresh",
                ra.get("code") == "UNLOGGED-CHANGE" and "not verified" in ra.get("text", "") and rb.get("state") == "verified",
                "changed: %r; put back: %s" % (ra.get("text", a.get("error", ""))[:100], rb.get("state", b.get("error", ""))))
            # the collapse: the panel folds to a strip; a control inside cannot be pressed (not shown); it opens again
            t1 = ch.do({"do": "lp_press", "what": "toggle"}, 30)
            c1 = ch.do({"do": "lp"}, 30)
            inside = ch.do({"do": "lp_press", "what": "wrefresh"}, 30)
            ch.do({"do": "lp_press", "what": "toggle"}, 30)
            c2 = ch.do({"do": "lp"}, 30)
            # this world's files refused by the loop: the panel's mark moves at once (it holds the files' compile, not only the
            # head served), so its row is never shown current as verified over them; the periodic read held off so that only
            # the mark can ask
            # the periodic read held off, and its key settled by one read Refresh makes, so that only the mark can ask
            s0 = ch.do({"do": "lp", "set_every": 1e12, "until": {"world_state": [PAGE, "verified"], "panel_state": ["worlds", ["current"]]}}, 60)
            ch.do({"do": "lp_press", "what": "wrefresh"}, 30)
            ch.do({"do": "lp", "until": {"forced_gt": ((s0.get("panels") or {}).get("worlds") or {}).get("forced", 0), "panel_state": ["worlds", ["current"]]}}, 60)
            open(page_art, "wb").write(page_text + b"bogus_statement x\n")
            x = ch.do({"do": "lp", "until": {"rev_refused": True}}, 90)
            me = next((r_ for r_ in x.get("worlds", []) if r_["name"] == PAGE), {})
            pst = ((x.get("panels") or {}).get("worlds") or {}).get("state")
            at_once = bool(x.get("worlds")) and not (pst == "current" and me.get("state") == "verified")
            y = z = {"error": "not waited for: the row failed at the refusal"}
            if at_once:
                y = ch.do({"do": "lp", "until": {"world_state": [PAGE, "not-verified"], "panel_state": ["worlds", ["current"]]}}, 60)
            me2 = next((r_ for r_ in y.get("worlds", []) if r_["name"] == PAGE), {})
            open(page_art, "wb").write(page_text)
            if at_once:
                z = ch.do({"do": "lp", "until": {"world_state": [PAGE, "verified"], "panel_state": ["worlds", ["current"]]}}, 90)
            ch.do({"do": "lp", "set_every": 10000}, 30)
            row("worlds: this world's files refused by the loop — the moment the page sees the refusal its worlds panel is stale or shows this world "
                "not verified, never current over verified; then not verified (FILES-REFUSED), current; the files put back, verified again",
                at_once and me2.get("code") == "FILES-REFUSED" and not z.get("error"), "at the refusal: the panel %s, the row %s; then %s %s; put back: %s" % (
                    pst, me.get("state", x.get("error", "")), me2.get("state"), me2.get("code", y.get("error", "")), "verified" if not z.get("error") else z.get("error")))
            row("worlds: the left panel collapses to a strip (its controls not shown, a press refused) and opens again",
                t1.get("pressed") == "pressed" and c1.get("collapsed") and c1.get("columns", "").startswith("28px") and "not shown" in inside.get("error", "")
                and not c2.get("collapsed") and c2.get("columns", "").startswith("214px"),
                "collapsed %s (%s); a press inside: %r; open %s (%s)" % (c1.get("collapsed"), c1.get("columns", "")[:20], inside.get("error", inside.get("pressed")),
                                                                       not c2.get("collapsed"), c2.get("columns", "")[:20]))

        def sc_outline():
            o = ch.do({"do": "lp", "until": {"outline_any": True, "panel_state": ["outline", ["current"]]}}, 60)
            lv = hub.worlds[PAGE]
            _c, oj = _get(port, "/outline.json?world=%s&slot=0" % PAGE)
            host_ids = [x["id"] for rg in oj.get("regions", []) for kd in rg["kinds"] for x in kd["objects"]]
            S = play.scene_of(lv.slot(0))
            rule = studio_refs.objects(S)
            row("worlds: the outline is the host's (GET /outline.json, by the host's object rule over the scene slot 0 serves), current, its header "
                "naming the world, the source and the scene", o.get("outline") == host_ids and sorted(host_ids) == sorted(rule) and oj.get("sha") == lv.slot(0)["sha"]
                and PAGE in o.get("outline_head", "") and lv.slot(0)["sha"][:12] in o.get("outline_head", ""),
                "%d objects in the page, %d by the rule; %r" % (len(o.get("outline", [])), len(rule), o.get("outline_head", "")[:80]))
            term = host_ids[len(host_ids) // 2].split(":")[0] if host_ids else "x"
            want = [x["id"] for rg in oj.get("regions", []) for kd in rg["kinds"] for x in kd["objects"] if term in x["id"].lower() or term in x["address"].lower()]
            s1 = ch.do({"do": "lp_search", "text": term}, 30)
            ch.do({"do": "lp_search", "text": ""}, 30)
            pick = want[0] if want else ""
            ch.do({"do": "lp_press", "what": "object", "name": pick}, 30)
            sel = ch.do({"do": "lp", "until": {"sel": pick, "info": True}}, 30)
            row("worlds: the outline's search keeps the objects whose name or address holds the words; an object pressed is selected and the "
                "inspector reads the host's account of it (GET /object.json)", s1.get("shown") == want and bool(want) and sel.get("sel") == pick
                and (sel.get("info") or {}).get("piece") == pick and (sel.get("info") or {}).get("world") == PAGE,
                "%r: %d shown of %d; selected %s, the inspector %s" % (term, len(s1.get("shown", [])), len(host_ids), sel.get("sel", sel.get("error", "")), sel.get("info")))

        def sc_import():
            i = ch.do({"do": "lp", "until": {"importable_any": True}}, 60)
            _c, ij = _get(port, "/importable.json")
            names = [b["name"] for b in ij.get("briefs", [])]
            row("worlds: the importable briefs are the host's (GET /importable.json): the source's briefs that are no world here, the source by its label",
                i.get("importable") == names == ["harbor-day", "plaza-night"] and ij.get("source_label") == WORLDS_LABEL and WORLDS_LABEL in (i.get("panels", {}).get("import") or {}).get("text", ""),
                "the page %s; the host %s" % (i.get("importable"), names))
            # the owner's case 6: an import that fails partway (the host stops it at its second file)
            before = {n: tree_bytes(os.path.join(worlds, n)) for n in hub.names()}
            names0 = hub.names()

            def boom(name):
                if name == "import:file-2":
                    raise RuntimeError("planted: the import stopped at its second file")
            D.durable.HOOK = boom
            try:
                ch.do({"do": "lp_press", "what": "stage", "name": "harbor-day"}, 30)
                f = ch.do({"do": "lp", "until": {"said_code": True}}, 60)
            finally:
                D.durable.HOOK = None
            row("worlds: case 6, an import that fails partway — the page says IMPORT-FAILED with the source and the name; no staging by a listing "
                "of the worlds folder; the worlds listed as before, each byte for byte",
                "IMPORT-FAILED" in f.get("said", "") and WORLDS_LABEL in f.get("said", "") and "harbor-day" in f.get("said", "") and not aside()
                and hub.names() == names0 and all(tree_bytes(os.path.join(worlds, n)) == b for n, b in before.items()),
                "the page: %r; aside %s; listed %s" % (f.get("said", f.get("error", ""))[:140], aside(), hub.names()))
            # stage, then commit: the record the page shows is the host's; after the commit the world is listed, verified, its
            # ledger started at import; the page stays where it is and offers Open
            page_before = tree_bytes(os.path.join(worlds, PAGE))
            ch.do({"do": "lp_press", "what": "stage", "name": "harbor-day"}, 30)
            s = ch.do({"do": "lp", "until": {"staged": True}}, 120)
            st = s.get("staged") or {}
            rec_path = os.path.join(worlds, st.get("staging", "") or "-", "IMPORTED.json")
            rec_sha = play.sha256(open(rec_path, "rb").read()) if os.path.isfile(rec_path) else ""
            rec = json.loads(open(rec_path, "rb").read()) if rec_path and os.path.isfile(rec_path) else {}
            listed_while = "harbor-day" in hub.names()
            ch.do({"do": "lp_press", "what": "commit"}, 30)
            c = ch.do({"do": "lp", "until": {"committed": True}}, 120)
            ch.do({"do": "lp_press", "what": "wrefresh"}, 30)
            v = ch.do({"do": "lp", "until": {"world_state": ["harbor-day", "verified"]}}, 120)
            hrow = next((x for x in v.get("worlds", []) if x["name"] == "harbor-day"), {})
            insp = hub.inspect("harbor-day") if "harbor-day" in hub.names() else {}
            log = [json.loads(ln) for ln in open(os.path.join(worlds, "IMPORTS.jsonl"), "rb").read().splitlines()] if os.path.exists(os.path.join(worlds, "IMPORTS.jsonl")) else []
            row("worlds: a stage and a commit through the page — the staged record it shows is the host's (sha256), not listed while staged; committed, "
                "harbor-day is listed and verified, one event started at import, its line in the imports log; the page stays on its world and offers Open",
                st.get("sha") == rec_sha and bool(rec_sha) and len(rec.get("files", {})) and str(len(rec.get("files", {}))) + " files" in st.get("text", "")
                and not listed_while and c.get("committed") == "harbor-day" and c.get("open_offered") and hrow.get("events") == 1 == insp.get("events")
                and hrow.get("head") == insp.get("head") and "started at import" in hrow.get("text", "") and [x["name"] for x in log] == ["harbor-day"]
                and v.get("brief") == PAGE and v.get("same_doc") is True and v.get("left") == 0 and "world=" + PAGE in v.get("href", "")
                and tree_bytes(os.path.join(worlds, PAGE)) == page_before and not aside() and tree_bytes(src) == src_before,
                "staged %s (sha %s, the host's %s); committed %r; the row %r; log %s" % (st.get("staging"), st.get("sha", "")[:12], rec_sha[:12],
                                                                                        c.get("committed", c.get("error", "")), hrow.get("text", v.get("error", ""))[:90], [x["name"] for x in log]))
            # a refused stage: the source's plaza-night, whose ledger does not verify
            ch.do({"do": "lp_press", "what": "irefresh"}, 30)
            ch.do({"do": "lp", "until": {"importable_any": True}}, 60)
            ch.do({"do": "lp_press", "what": "stage", "name": "plaza-night"}, 30)
            r = ch.do({"do": "lp", "until": {"said_code": True}}, 120)
            row("worlds: a stage refused — plaza-night's ledger does not verify in the copy: the page says IMPORT-LEDGER (UNLOGGED-CHANGE); nothing left",
                "IMPORT-LEDGER" in r.get("said", "") and "UNLOGGED-CHANGE" in r.get("said", "") and not aside() and "plaza-night" not in hub.names(),
                "the page: %r" % r.get("said", r.get("error", ""))[:140])

        def sc_world():
            # the owner's case 7 across two worlds: the host's own answers for the other world, given to this page
            # the other world's scene as the page would print it (its first twelve characters, short()), never this world's
            other_sha = hub.worlds[OTHER].slot(0)["sha"][:12]
            assert not hub.worlds[PAGE].slot(0)["sha"].startswith(other_sha)
            vi, ol = saved[2], saved[3]

            def other_v(live_, k):
                return dict(vi(hub.worlds[OTHER], k), world=OTHER) if live_.brief == PAGE else vi(live_, k)

            def other_o(hub_, q_):
                return ol(hub_, dict(q_, world=OTHER)) if q_.get("world") == PAGE else ol(hub_, q_)
            o0 = ch.do({"do": "lp", "until": {"outline_any": True, "panel_state": ["outline", ["current"]]}}, 60)
            n0 = (o0.get("panels", {}).get("outline") or {}).get("answers", 0)
            play.validate_info, play.outline = other_v, other_o
            try:
                t = ch.do({"do": "tab", "tab": "validation"}, 60)
                ch.do({"do": "lp_press", "what": "toggle"}, 30)
                ch.do({"do": "lp_press", "what": "toggle"}, 30)            # opened again, the panel reads its outline again
                p = ch.do({"do": "lp", "until": {"outline_answers_gt": n0}, "marker": other_sha}, 60)
            finally:
                play.validate_info, play.outline = vi, ol
            n1 = (p.get("panels", {}).get("outline") or {}).get("answers", 0)
            t2 = ch.do({"do": "tab", "tab": "validation"}, 60)
            ch.do({"do": "lp_press", "what": "toggle"}, 30)
            ch.do({"do": "lp_press", "what": "toggle"}, 30)
            p2 = ch.do({"do": "lp", "until": {"outline_answers_gt": n1}}, 60)
            row("worlds: case 7 across two worlds — the host's own answers for %s given to the page of %s: Validation and the outline say refused, nothing "
                "of %s's scene in the page, every data-world %s; given their own again, current" % (OTHER, PAGE, OTHER, PAGE),
                OTHER in t.get("refused", "") and OTHER in (p.get("panels", {}).get("outline") or {}).get("refused", "") and p.get("html_has") is False
                and set(p.get("data_worlds") or []) <= {PAGE} and t2.get("state") == "current" and not t2.get("refused")
                and (p2.get("panels", {}).get("outline") or {}).get("state") == "current" and bool(p2.get("data_worlds")) and set(p2.get("data_worlds")) == {PAGE},
                "validation %r, outline %r; %s's scene in the page %s; data-world %s; then validation %s, outline %s, data-world %s" % (
                    t.get("refused", t.get("error", ""))[:50], (p.get("panels", {}).get("outline") or {}).get("refused", p.get("error", ""))[:50], OTHER,
                    p.get("html_has"), sorted(set(p.get("data_worlds") or [])), t2.get("state"), (p2.get("panels", {}).get("outline") or {}).get("state"),
                    sorted(set(p2.get("data_worlds") or []))))

        RUN = {"worlds": sc_worlds, "outline": sc_outline, "import": sc_import, "world": sc_world}
        if not browser:
            row("worlds: a browser to drive the page (Edge or Chrome; elsewhere Edge, Chrome or Chromium on PATH; --browser EXE)", False, "none found")
            return rows, caught, seen
        proc = PT.launch(browser, base + "/page_test.html", profile, headed, os.path.join(tmp, "browser.log"))
        t_run = time.time()
        for name in WORLDS_SCENARIOS:
            try:
                reset()
                if not alive:
                    alive = [x for x in PT.leftovers(marker) if x == "unknown" or not x.split()[-1].lower().startswith("python")]
                RUN[name]()
            except PT.PageLost as e:
                row("worlds: the scenario %s ran to its end" % name, False, "the page was lost: %s" % e)
                break
            except Exception as e:  # noqa: BLE001 — the self-test says what stopped a scenario, and goes on to the next
                import traceback
                traceback.print_exc()
                row("worlds: the scenario %s ran to its end" % name, False, "%s: %s" % (type(e).__name__, str(e)[:200]))
        seen.append("OBSERVED worlds: the honest run's four scenarios in %.0f s (a software timing)" % (time.time() - t_run))
        js = open(saved[1]["/play.js"][0], "rb").read().decode("utf-8")
        for plant, (scen, want, (old, new)) in WORLDS_PLANTS.items():
            if ch.lost and not (proc is not None and proc.poll() is None):
                caught.append(False)
                print("[FAIL] worlds plant %s caught — NOT RUN: the page was lost (%s)" % (plant, ch.lost), flush=True)
                continue
            if js.count(old) != 1:
                caught.append(False)
                print("[FAIL] worlds plant %s caught — NOT PLANTED: its text occurs %d times in play.js, not once" % (plant, js.count(old)), flush=True)
                continue
            if END - time.time() < 60:
                caught.append(False)
                print("[FAIL] worlds plant %s caught — NOT RUN: the suite's time was spent" % plant, flush=True)
                continue
            planted = os.path.join(tmp, "play-%s.js" % plant)
            open(planted, "wb").write(js.replace(old, new).encode("utf-8"))
            play.FILES["/play.js"] = (planted, saved[1]["/play.js"][1])
            got = []
            mode.update(out=got, say=None, stop=want)
            ch.deadline = min(time.time() + WORLDS_LIMITS["plant"], END)
            if proc is not None and proc.poll() is None:
                ch.lost = ""
            stopped = ""
            try:
                reset()
                RUN[scen]()
            except Stop:
                pass
            except Exception as e:  # noqa: BLE001
                stopped = "%s: %s" % (type(e).__name__, str(e)[:160])
            finally:
                play.FILES["/play.js"] = saved[1]["/play.js"]
                mode.update(out=rows, say=say, stop="")
            mine = [x for x in got if x[0].startswith(want)]
            ok = not stopped and bool(mine) and not mine[0][1] and all(x[1] for x in got[:got.index(mine[0])])
            caught.append(ok)
            print("[%s] worlds plant %s caught — %s" % ("PASS" if ok else "FAIL", plant,
                                                      ("by: " + mine[0][0][:90] + " — " + mine[0][2][:240]) if ok else ("the run stopped: " + stopped) if stopped
                                                      else "NOT CAUGHT: " + ("; ".join("%s %s" % ("PASS" if x[1] else "FAIL", x[0][:60]) for x in got) or "no row")), flush=True)
            if ch.lost and not (proc is not None and proc.poll() is None):
                break
    except Exception as e:  # noqa: BLE001 — the self-test says what stopped it
        import traceback
        traceback.print_exc()
        row("worlds: the self-test ran to its end", False, "%s: %s" % (type(e).__name__, str(e)[:200]))
    finally:
        mode.update(out=rows, say=say, stop="")
        D.durable.HOOK = None
        for g in gates:
            g.remove()
        try:
            if hub is not None and getattr(hub, "page_test", None) is not None:
                hub.page_test.steps.put({"do": "end"})
                time.sleep(1.0)
        except Exception:  # noqa: BLE001
            pass
        if proc is not None:
            left, first, took = PT.end_browser(proc, marker)
            row("worlds: the browser ended, and nothing of it is left (the query that says so found the browser's processes while it ran)",
                not left and bool(alive) and alive != ["unknown"], "while it ran: %d process%s; left: %s" % (
                    len(alive) if alive != ["unknown"] else 0, "" if len(alive) == 1 else "es", left or "nothing"))
            seen.append("OBSERVED worlds: the browser ended in %.1f s%s" % (took, ("; standing at the first look: %s" % first) if first else ""))
        play.ROOT = saved[0]
        play.FILES.clear()
        play.FILES.update(saved[1])
        play.validate_info, play.outline = saved[2], saved[3]
        if hub is not None:
            for lv in list(hub.worlds.values()):
                lv.stopping = True
                if lv.studio:
                    lv.studio.shutdown()
        if srv:
            srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    return rows, caught, seen
