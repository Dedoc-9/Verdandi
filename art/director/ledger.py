# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director/ledger.py — DIRECTOR-0's intent ledger: one canonical document to a line, each naming the one before.
#
# An event is a canonical document (art/director/intent.py) with
#   protocol "DIRECTOR-0", version "0", seq (an integer string, from 0), prev (the sha256 of the previous line's bytes,
#   64 zeros for the first), kind, and the kind's own fields.
# The file is the events' canonical bytes, each followed by one LF. Nothing is ever rewritten: an event is appended
# or nothing happens. The ledger's head is the sha256 of its last line's bytes (without the LF).

import os

import intent as canon

PROTOCOL, VERSION = "DIRECTOR-0", "0"
ZERO = "0" * 64
KINDS = ("genesis", "evaluate", "refuse_input", "admit", "refuse", "rebase", "approve")


class LedgerError(Exception):
    pass


def read(path):
    """The ledger's events, its lines' bytes and its head. Every line must be a canonical document."""
    if not os.path.exists(path):
        return [], [], ZERO
    raw = open(path, "rb").read()
    if raw and not raw.endswith(b"\n"):
        raise LedgerError("LEDGER-TORN: the last line has no LF")
    lines = raw.split(b"\n")[:-1] if raw else []
    events = []
    for i, ln in enumerate(lines):
        try:
            events.append(canon.loads(ln))
        except canon.IntentError as e:
            raise LedgerError("LEDGER-LINE: line %d is not a canonical document (%s)" % (i + 1, e.code))
    return events, lines, (canon.sha256(lines[-1]) if lines else ZERO)


def append(path, kind, fields):
    """Append one event; returns it. The caller supplies the kind's fields, never seq or prev."""
    if kind not in KINDS:
        raise LedgerError("LEDGER-KIND: %r" % kind)
    events, _lines, head = read(path)
    ev = dict(fields, protocol=PROTOCOL, version=VERSION, seq=str(len(events)), prev=head, kind=kind)
    b = canon.dumps(ev)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "ab") as fh:
        fh.write(b + b"\n")
    return ev


def chain(path):
    """The chain alone: seq from 0, each prev the sha256 of the line before, known protocol, version and kinds."""
    events, lines, head = read(path)
    prev = ZERO
    for i, (ev, ln) in enumerate(zip(events, lines)):
        if ev.get("protocol") != PROTOCOL or ev.get("version") != VERSION:
            raise LedgerError("LEDGER-VERSION: event %d is %s %s" % (i, ev.get("protocol"), ev.get("version")))
        if ev.get("seq") != str(i):
            raise LedgerError("LEDGER-SEQ: event %d says seq %r" % (i, ev.get("seq")))
        if ev.get("prev") != prev:
            raise LedgerError("LEDGER-CHAIN: event %d does not name the line before it" % i)
        if ev.get("kind") not in KINDS or (i == 0) != (ev.get("kind") == "genesis"):
            raise LedgerError("LEDGER-KIND: event %d is %r" % (i, ev.get("kind")))
        prev = canon.sha256(ln)
    return events, head
