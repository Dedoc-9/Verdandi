# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
r"""savedform.py — READER-COURT-0: the Python reader of the saved form, written apart from the Rust one.

Everything the tree saves and reads back is in one bounded language: what the tree's registered writers are
permitted to emit, and nothing wider. kernel/savedform.rs is its reader in the programs. This is its reader for the
Python tools (the sealer, the two session sealers, the envelope), and the gate holds the two against each other.
There is no `json.load` or `json.loads` underneath, and no fallback to one: a file this reader refuses is refused.

    a DOCUMENT    one object followed by exactly one LF; nothing before the object, nothing after the LF
    a PAYLOAD     one object and nothing else (a journal record's)
    between tokens   spaces and LFs only
    an object     no name twice; it may be empty
    depth         at most 7 objects and arrays open at once, the root object the first; a string, an integer,
                  true, false or null opens no level
    an integer    "0", or an optional "-" and a digit 1-9 followed by digits, within signed 64 bits
    a string      well-formed UTF-8, raw from U+0020 up except the quote and the backslash; \" \\ \b \f \n \r \t;
                  \u00XX in lower-case hex for the other characters below U+0020 and for nothing else

The verdict on any bytes is a typed value (dict, list, str, int, True, False, None), or `Refused(code, offset)`.
The offset is the first byte at which the input stops being the beginning of any document (or payload) of the
language, or its length if it ended where one could still continue. It is a property of the language and the bytes.

    READER-TRUNCATED  READER-TRAILING  READER-DEPTH  READER-DUPLICATE  READER-STRING  READER-NUMBER  READER-STRUCTURE

    python verify/savedform.py FILE [--payload]     # print the verdict on a file
    python verify/savedform.py --splice MANIFEST    # the court's splices, as `shell form-splice --manifest` takes them

The second form is the court's: each line of MANIFEST is "document|payload <TAB> FILE <TAB> SCRIPT <TAB> OUT", each
line of SCRIPT is "<offset> <bytes removed> <hex inserted or ->", and the same line of OUT is this reader's verdict
on FILE with that splice applied. Every mutant is read from its first byte by the function a sealer calls.
"""
from __future__ import annotations

import hashlib
import re
import sys

DEPTH_MAX = 7
INT_MIN, INT_MAX = -(1 << 63), (1 << 63) - 1

_GAP = re.compile(rb"[ \n]*")
# a run of string bytes that need no thought: ASCII from 0x20 up, except the quote and the backslash
_PLAIN = re.compile(rb"[\x20\x21\x23-\x5b\x5d-\x7f]*")
# the two common tokens, read whole when nothing in them needs thought. A string of plain ASCII with its quotes; an
# integer of at most 18 digits (always in range, and never "-0") that nothing number-like follows. Anything else takes the exact
# path below, which is also the only path that refuses.
_STR_PLAIN = re.compile(rb'"([\x20\x21\x23-\x5b\x5d-\x7f]*)"')
_INT_PLAIN = re.compile(rb"(?:0|-?[1-9][0-9]{0,17})(?![0-9.eE+\-])")
_SHORT = {0x22: 0x22, 0x5C: 0x5C, 0x62: 0x08, 0x66: 0x0C, 0x6E: 0x0A, 0x72: 0x0D, 0x74: 0x09}
# after "\u": two zeros, then 0 or 1, then one lower-case hex digit
_U = (b"0", b"0", b"01", b"0123456789abcdef")
_HAS_SHORT = frozenset((0x08, 0x09, 0x0A, 0x0C, 0x0D))
_C = (0x80, 0xBF)
_WORDS = {0x74: (b"true", True), 0x66: (b"false", False), 0x6E: (b"null", None)}

REFUSALS = 0   # how many times this module has refused, in this process (the gate reads it)


class Refused(Exception):
    """Bytes that are not of the saved form: what was being read, and where they stopped being a beginning of it."""

    def __init__(self, code: str, offset: int):
        global REFUSALS
        REFUSALS += 1
        Exception.__init__(self, "%s %d" % (code, offset))
        self.code, self.offset = code, offset

    def line(self) -> str:
        return "%s %d" % (self.code, self.offset)


def _continuation(c: int):
    """The ranges the bytes after a lead byte must lie in, or None for a byte that cannot lead."""
    if 0xC2 <= c <= 0xDF:
        return (_C,)
    if c == 0xE0:
        return ((0xA0, 0xBF), _C)
    if c == 0xED:
        return ((0x80, 0x9F), _C)
    if 0xE1 <= c <= 0xEF:
        return (_C, _C)
    if c == 0xF0:
        return ((0x90, 0xBF), _C, _C)
    if 0xF1 <= c <= 0xF3:
        return (_C, _C, _C)
    if c == 0xF4:
        return ((0x80, 0x8F), _C, _C)
    return None


def _read(b: bytes, payload: bool):
    n = len(b)

    def stop(code, i):
        raise Refused("READER-TRUNCATED" if i >= n else code, min(i, n))

    def gap(i):
        return _GAP.match(b, i).end()

    def string(i):
        # b[i] is the opening quote; returns (text, index after the closing quote)
        parts = []
        j = i + 1
        while True:
            k = _PLAIN.match(b, j).end()
            if k > j:
                parts.append(b[j:k])
                j = k
            if j >= n:
                stop("", j)
            c = b[j]
            if c == 0x22:
                return b"".join(parts).decode("utf-8"), j + 1
            if c == 0x5C:
                if j + 1 >= n:
                    stop("", j + 1)
                e = b[j + 1]
                if e in _SHORT:
                    parts.append(bytes((_SHORT[e],)))
                    j += 2
                    continue
                if e != 0x75:
                    stop("READER-STRING", j + 1)
                for k, want in enumerate(_U, 2):
                    if j + k >= n:
                        stop("", j + k)
                    if b[j + k] not in want:
                        stop("READER-STRING", j + k)
                v = int(b[j + 4:j + 6], 16)
                if v in _HAS_SHORT:
                    stop("READER-STRING", j + 5)
                parts.append(bytes((v,)))
                j += 6
                continue
            if c < 0x20:
                stop("READER-STRING", j)
            need = _continuation(c)
            if need is None:
                stop("READER-STRING", j)
            for k, (lo, hi) in enumerate(need, 1):
                if j + k >= n:
                    stop("", j + k)
                if not lo <= b[j + k] <= hi:
                    stop("READER-STRING", j + k)
            parts.append(b[j:j + 1 + len(need)])
            j += 1 + len(need)

    def number(i):
        j = i
        neg = b[j] == 0x2D
        if neg:
            j += 1
            if j >= n:
                stop("", j)
            if not 0x31 <= b[j] <= 0x39:      # "-0" and "-x" are not integers of the language
                stop("READER-NUMBER", j)
        v = 0
        if b[j] == 0x30:
            j += 1
        else:
            while j < n and 0x30 <= b[j] <= 0x39:
                v = v * 10 + (b[j] - 0x30)
                if (neg and v > -INT_MIN) or (not neg and v > INT_MAX):
                    stop("READER-NUMBER", j)   # the digit that takes it out of range
                j += 1
        if j < n and (0x30 <= b[j] <= 0x39 or b[j] in b".eE+-"):
            stop("READER-NUMBER", j)
        return (-v if neg else v), j

    def value(i, depth):
        if i >= n:
            stop("", i)
        c = b[i]
        if c == 0x22:
            m = _STR_PLAIN.match(b, i)
            return (m.group(1).decode("ascii"), m.end()) if m else string(i)
        if c == 0x2D or 0x30 <= c <= 0x39:
            m = _INT_PLAIN.match(b, i)
            return (int(m.group()), m.end()) if m else number(i)
        if c == 0x7B:
            if depth >= DEPTH_MAX:
                stop("READER-DEPTH", i)
            obj = {}
            i = gap(i + 1)
            if i < n and b[i] == 0x7D:
                return obj, i + 1
            while True:
                if i >= n:
                    stop("", i)
                if b[i] != 0x22:
                    stop("READER-STRUCTURE", i)
                m = _STR_PLAIN.match(b, i)
                name, i = (m.group(1).decode("ascii"), m.end()) if m else string(i)
                if name in obj:
                    stop("READER-DUPLICATE", i - 1)
                i = gap(i)
                if i >= n:
                    stop("", i)
                if b[i] != 0x3A:
                    stop("READER-STRUCTURE", i)
                obj[name], i = value(gap(i + 1), depth + 1)
                i = gap(i)
                if i >= n:
                    stop("", i)
                if b[i] == 0x2C:
                    i = gap(i + 1)
                    continue
                if b[i] == 0x7D:
                    return obj, i + 1
                stop("READER-STRUCTURE", i)
        if c == 0x5B:
            if depth >= DEPTH_MAX:
                stop("READER-DEPTH", i)
            arr = []
            i = gap(i + 1)
            if i < n and b[i] == 0x5D:
                return arr, i + 1
            while True:
                v, i = value(i, depth + 1)
                arr.append(v)
                i = gap(i)
                if i >= n:
                    stop("", i)
                if b[i] == 0x2C:
                    i = gap(i + 1)
                    continue
                if b[i] == 0x5D:
                    return arr, i + 1
                stop("READER-STRUCTURE", i)
        if c in _WORDS:
            word, val = _WORDS[c]
            for k in range(1, len(word)):
                if i + k >= n:
                    stop("", i + k)
                if b[i + k] != word[k]:
                    stop("READER-STRUCTURE", i + k)
            return val, i + len(word)
        stop("READER-STRUCTURE", i)

    if n == 0:
        stop("", 0)
    if b[0] != 0x7B:
        stop("READER-STRUCTURE", 0)
    root, i = value(0, 0)
    if payload:
        if i != n:
            raise Refused("READER-TRAILING", i)
        return root
    if i >= n:
        stop("", i)
    if b[i] != 0x0A:
        raise Refused("READER-TRAILING", i)
    if i + 1 != n:
        raise Refused("READER-TRAILING", i + 1)
    return root


def read_document(b: bytes):
    """The typed value of a document (one object, then exactly one LF), or Refused."""
    return _read(bytes(b), False)


def read_payload(b: bytes):
    """The typed value of a payload (one object and nothing else), or Refused."""
    return _read(bytes(b), True)


def read_file(path: str):
    """The typed value of the document in a file, or Refused. The file is read as bytes: nothing is decoded first."""
    with open(path, "rb") as fh:
        return read_document(fh.read())


def canonical_sha256(value) -> str:
    """The sha256 of a typed value's RECORD-0 canonical JSON: how two accepted inputs are compared. Writing, not
    reading: the json module renders the value and never parses anything here."""
    import json
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
                          .encode("utf-8")).hexdigest()


def verdict(b: bytes, payload: bool = False) -> str:
    """One line: "A <sha256 of the typed value's canonical JSON>" or "R <CODE> <offset>"."""
    try:
        v = _read(bytes(b), payload)
    except Refused as r:
        return "R " + r.line()
    return "A " + canonical_sha256(v)


def splice(manifest: str) -> tuple[int, int]:
    """Run a manifest of splices (see the module docstring); returns (files, mutants)."""
    files = mutants = 0
    with open(manifest, encoding="utf-8") as fh:
        entries = [ln.split("\t") for ln in fh.read().split("\n") if ln]
    for kind, path, script, out in entries:
        if kind not in ("document", "payload"):
            raise ValueError("manifest: %r is neither document nor payload" % kind)
        with open(path, "rb") as fh:
            base = fh.read()
        lines = []
        with open(script, encoding="ascii") as fh:
            for ln in fh.read().split("\n"):
                if not ln:
                    continue
                at, cut, ins = ln.split(" ")
                at, cut = int(at), int(cut)
                lines.append(verdict(base[:at] + (b"" if ins == "-" else bytes.fromhex(ins)) + base[at + cut:], kind == "payload"))
        with open(out, "w", encoding="ascii", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        files += 1
        mutants += len(lines)
    return files, mutants


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--splice":
        print("spliced %d files %d mutants" % splice(sys.argv[2]))
        sys.exit(0)
    args = [a for a in sys.argv[1:] if a != "--payload"]
    if len(args) != 1:
        print("usage: python verify/savedform.py FILE [--payload]")
        sys.exit(2)
    with open(args[0], "rb") as fh:
        print(verdict(fh.read(), "--payload" in sys.argv[1:]))
