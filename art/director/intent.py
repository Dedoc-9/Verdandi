# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/director/intent.py — DIRECTOR-0's canonical byte contract (VERDANDI-CANON 0) and its intent document.
#
# One byte form for every intent and every ledger entry. It is a restricted JSON, defined here exactly; it is not
# RFC 8785 and claims no compatibility with it (RFC 8785 writes non-ASCII as UTF-8 and orders keys by UTF-16 units;
# this form writes ASCII only, and its keys are ASCII, so the two orders agree but the string bytes do not).
#
#   values    objects, arrays, strings and the booleans true and false. No numbers of any kind, no null.
#   integers  written as strings in the fields that declare them: 0 or -?[1-9][0-9]*, at most 19 digits, no -0
#   keys      [a-z][a-z0-9_]*, unique within their object; members in ascending byte order of their keys
#   strings   any Unicode scalar values (no lone surrogates). Escaped as follows, and nothing else is escaped:
#             " as \", \ as \\, U+0008 \b, U+0009 \t, U+000A \n, U+000C \f, U+000D \r; every other code point below
#             U+0020 and every code point above U+007E as \u followed by four lowercase hex digits (above U+FFFF, as
#             a UTF-16 surrogate pair). U+007F is written as \u007f. "/" is not escaped.
#   layout    no whitespace outside strings; ',' between members and elements; ':' between key and value
#   bytes     ASCII. The identity of a document is the sha256 of these bytes.
#
# A document is admitted only in this byte form: bytes that parse but are not their own canonical form are refused
# (INTENT-NONCANONICAL). The conformance vectors (art/director/vectors.json) fix every rule above to bytes.

import hashlib
import json
import re

FORMAT = "VERDANDI-INTENT"
VERSIONS = ("0",)
KEY = re.compile(r"[a-z][a-z0-9_]*\Z")
INTEGER = re.compile(r"(0|-?[1-9][0-9]{0,18})\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class IntentError(Exception):
    """A refusal, with its code: INTENT-<WHAT>."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------------------------------------ writing
def _str(s: str) -> str:
    out = ['"']
    for ch in s:
        o = ord(ch)
        if 0xD800 <= o <= 0xDFFF:
            raise IntentError("INTENT-STRING", "a lone surrogate U+%04X" % o)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\b":
            out.append("\\b")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\f":
            out.append("\\f")
        elif ch == "\r":
            out.append("\\r")
        elif o < 0x20 or o == 0x7F:
            out.append("\\u%04x" % o)
        elif o <= 0x7E:
            out.append(ch)
        elif o <= 0xFFFF:
            out.append("\\u%04x" % o)
        else:
            v = o - 0x10000
            out.append("\\u%04x\\u%04x" % (0xD800 + (v >> 10), 0xDC00 + (v & 0x3FF)))
    out.append('"')
    return "".join(out)


def dumps(v) -> bytes:
    """The canonical bytes of a value of the restricted form."""
    def w(x):
        if x is True:
            return "true"
        if x is False:
            return "false"
        if isinstance(x, str):
            return _str(x)
        if isinstance(x, list):
            return "[" + ",".join(w(e) for e in x) + "]"
        if isinstance(x, dict):
            for k in x:
                if not isinstance(k, str) or not KEY.match(k):
                    raise IntentError("INTENT-KEY", "%r is not a key of [a-z][a-z0-9_]*" % (k,))
            return "{" + ",".join(_str(k) + ":" + w(x[k]) for k in sorted(x)) + "}"
        if x is None:
            raise IntentError("INTENT-NULL", "null is not a value of this form")
        raise IntentError("INTENT-TYPE", "%s is not a value of this form (integers are strings)" % type(x).__name__)
    return w(v).encode("ascii")


# ------------------------------------------------------------------------------------------------ reading
def _no_float(s):
    raise IntentError("INTENT-NUMBER", "a number %s: integers are written as strings, and there are no others" % s)


def _no_const(s):
    raise IntentError("INTENT-NUMBER", "%s is not a value of this form" % s)


def _pairs(pairs):
    seen = set()
    for k, _v in pairs:
        if not KEY.match(k):
            raise IntentError("INTENT-KEY", "%r is not a key of [a-z][a-z0-9_]*" % k)
        if k in seen:
            raise IntentError("INTENT-DUPLICATE-KEY", "the key %r appears twice in one object" % k)
        seen.add(k)
    return dict(pairs)


def loads(b: bytes):
    """A value from bytes that must be its own canonical form. Refusals carry their code."""
    if not isinstance(b, (bytes, bytearray)):
        raise IntentError("INTENT-BYTES", "a document is bytes")
    try:
        text = bytes(b).decode("ascii")
    except UnicodeDecodeError:
        raise IntentError("INTENT-BYTES", "a canonical document is ASCII")
    try:
        v = json.loads(text, object_pairs_hook=_pairs, parse_float=_no_float, parse_int=_no_float, parse_constant=_no_const)
    except IntentError:
        raise
    except ValueError as e:
        raise IntentError("INTENT-NOT-JSON", str(e))

    def walk(x):
        if x is None:
            raise IntentError("INTENT-NULL", "null is not a value of this form")
        if isinstance(x, dict):
            for e in x.values():
                walk(e)
        elif isinstance(x, list):
            for e in x:
                walk(e)
    walk(v)
    if dumps(v) != bytes(b):
        raise IntentError("INTENT-NONCANONICAL", "the bytes parse, but are not their canonical form")
    return v


def integer(s, what):
    if not isinstance(s, str) or not INTEGER.match(s) or s == "-0":
        raise IntentError("INTENT-INTEGER", "%s %r is not an integer string" % (what, s))
    return int(s)


# ------------------------------------------------------------------------------------------------ the intent
REQUIRED = {"format", "version", "brief", "prompt", "candidate", "rationale", "base", "scope", "revision", "layout"}
BASE = {"art_sha256", "world_sha256", "exporter_sha256"}


def head(parts: dict) -> str:
    """The world head a candidate is checked against: the sha256 of the canonical bytes of its three parts."""
    return sha256(dumps({k: parts[k] for k in sorted(BASE)}))


def validate(doc) -> dict:
    """An intent document's fields, checked. VERDANDI-INTENT version 0:

    format     "VERDANDI-INTENT"
    version    "0"; any other is refused, never translated (a translator comes with the first real change)
    brief      the brief's name (art/briefs/<brief>.art)
    prompt     the words the candidate answers
    candidate  a short label for the candidate within its round ("A", "B", ...)
    rationale  one line from the proposer: what it means by the change
    base       {art_sha256, world_sha256, exporter_sha256}: the head it was written against. world_sha256 is the
               graybox world W's canonical sha256: the admitted layout, the map's overlay and the converter
    scope      the addresses it declares it will touch: patterns, at least one
    revision   art revision lines, "= <statement>", "+ <statement>" or "- <key>" (may be empty if layout is not)
    layout     design text lines (VERDANDI-DESIGN 0 statements) for the layout, admitted through the design tool;
               empty for a revision of the look alone
    """
    if not isinstance(doc, dict):
        raise IntentError("INTENT-FIELD", "an intent is an object")
    if doc.get("format") != FORMAT:
        raise IntentError("INTENT-FORMAT", "format is not %r" % FORMAT)
    if doc.get("version") not in VERSIONS:
        raise IntentError("INTENT-VERSION", "version %r is not one this reader knows (%s)" % (doc.get("version"), ", ".join(VERSIONS)))
    missing, extra = REQUIRED - set(doc), set(doc) - REQUIRED
    if missing or extra:
        raise IntentError("INTENT-FIELD", "missing %s; unknown %s" % (sorted(missing) or "none", sorted(extra) or "none"))
    for k in ("brief", "prompt", "candidate", "rationale"):
        if not isinstance(doc[k], str) or not doc[k].strip():
            raise IntentError("INTENT-FIELD", "%s is a non-empty string" % k)
    b = doc["base"]
    if not isinstance(b, dict) or set(b) != BASE:
        raise IntentError("INTENT-FIELD", "base holds exactly %s" % sorted(BASE))
    for k in BASE:
        if not isinstance(b[k], str) or not HEX64.match(b[k]):
            raise IntentError("INTENT-FIELD", "base.%s is 64 lowercase hex digits" % k)
    if not isinstance(doc["scope"], list) or not doc["scope"] or not all(isinstance(p, str) and p for p in doc["scope"]):
        raise IntentError("INTENT-FIELD", "scope is a non-empty list of address patterns")
    if not isinstance(doc["revision"], list) or not isinstance(doc["layout"], list) or not (doc["revision"] or doc["layout"]):
        raise IntentError("INTENT-FIELD", "revision and layout are lists of lines, and not both empty")
    for ln in doc["layout"]:
        if not isinstance(ln, str) or not ln.strip() or "\n" in ln or ln.lstrip().startswith("#") or ln.split()[0] not in ("open", "close", "room", "entrance", "paint"):
            raise IntentError("INTENT-LAYOUT", "%r is not one statement of VERDANDI-DESIGN 0" % (ln,))
    for ln in doc["revision"]:
        if not isinstance(ln, str) or ln[:2] not in ("= ", "+ ", "- ") or "\n" in ln or "#" in ln:
            raise IntentError("INTENT-REVISION", "%r is not '= <statement>', '+ <statement>' or '- <key>' on one line" % (ln,))
    return doc


def load_intent(b: bytes) -> dict:
    return validate(loads(b))
