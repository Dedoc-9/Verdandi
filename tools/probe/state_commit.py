# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# tools/probe/state_commit.py — probe 6, the state-commitment court (DSC-0), outside docs/STUDIO-CONTRACT.md §11's
# five and in their one output form. Off the gate; standard library only; never a gate. It decides one question the
# owner brought on 2026-10-15 with outside documents (a recursive-proof state "dissolving the ledger"; Differential
# State Commitments, a Merkle tree over the grid, "O(k log n) verification instead of O(n) replay", with a threat
# analysis and a draft implementation): should the session's content function become a tree commitment now?
#
#   python tools/probe/state_commit.py [--edits N] [--seed S] [--session-exe PATH]
#
# What it holds. The incumbent: content = sha256(sha256(W) || sha256(M)) over the whole level and tiles bytes, folded
# into the head per edit (workshop/session.rs; the shell keeps an exact memo of the two digests). DSC-0, built here as
# a reference and nothing else: a commitment over the same bytes with
#   leaves bound to their place     cell i: H(00 'C' u32 i | byte); a padding place: H(00 'P' u32 i), never a cell's
#   nodes apart from leaves         H(01 | left | right); a path's sides come from the index, never from the proof
#   a tile class by its generator   a uniform class: H(00 'F' c | r g b); any other: H(00 'T' c | sha256(bytes)); a
#                                   class that is uniform has only the first form (one state, one commitment)
#   the rest of the level           H(00 'R' | sha256(depth, table, maps)): bytes no edit reaches
#   a root bound to its shape       H("VRDNDSC0" | u32 w | u32 rows | u32 tile bytes | cells | tiles | rest)
# A batch is a receipt (one byte form: strictly increasing places, each with its old and new value, no operation that
# changes nothing) and a proof (the siblings the union of its paths needs, in one order, exactly that many). The
# verifier is given the root before, the receipt and the proof, and nothing else; it checks each operation's own law
# (inside the level, the border rock, the alphabet, a class that exists), folds the old values to the root before and
# the new ones to the root after, or refuses with a code.
#
# Kill criteria, written before the first run (the kernel's rate was added to necessity after it, which can only make
# that criterion stricter):
#   KILLED soundness    a forged receipt or proof is not refused with its code (each forge-* case), or the honest
#                       receipt beside them is refused
#   KILLED agreement    at the end of any batch of a seeded session the workshop made edit by edit, the reference's
#                       bytes give a content other than the one the workshop logged there, its final bytes are not the
#                       workshop's replay, an honest receipt is refused, or the root reached by verified receipts is not
#                       the root computed again from the bytes
#   KILLED necessity    at the kernel's largest world (LATTICE 48 x 48, kernel/mantle.rs) the incumbent's content for
#                       one edit, the worse of a cell and a paint at the slower of the two rates below, takes longer
#                       than one 60 Hz frame (16.7 ms) here
# HELD otherwise: the incumbent stands for the kernel's world, and DSC-0 is the content function a larger world's
# format inherits, with the crossover this probe measures. limit-* cases reproduce what a root cannot carry; they
# are not kill criteria. The blocks it counts (SHA-256 compression blocks) are the same on every machine; the times
# are this machine's: incumbent_ms through Python's hashlib, kernel_ms at the rate the workshop's own sha256 shows
# here (its verify's time per edit over the blocks one edit hashes there, the edit's own work included, so a bound
# from above). Nothing here prints the machine.

import hashlib
import json
import os
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import time

from common import Probe, REPO

TILE_BYTES = 256 * 256 * 3
CLASSES = ("wall0", "wall1", "wall2", "wall3", "floor")
ALPHABET = b"#.<>"
LATTICE = 48
FRAME_MS = 1000.0 / 60.0
EXE = ".exe" if os.name == "nt" else ""


class Refused(Exception):
    def __init__(self, code, why):
        Exception.__init__(self, "%s: %s" % (code, why))
        self.code = code


# ------------------------------------------------------------------ hashing, counted
BLOCKS = [0]


def H(data):
    BLOCKS[0] += (len(data) + 9 + 63) // 64
    return hashlib.sha256(data).digest()


def incumbent_content(level, tiles):
    return H(H(level) + H(tiles))


# ------------------------------------------------------------------ the bytes
def split_level(level):
    if level[:8] != b"VRDNLVL1":
        raise Refused("DSC-FORM", "level magic")
    w, rows = struct.unpack_from("<II", level, 8)
    return w, rows, level[16:16 + w * rows], level[16 + w * rows:]


def split_tiles(tiles):
    if tiles[:8] != b"VRDNTIL1" or len(tiles) != 8 + 5 * TILE_BYTES:
        raise Refused("DSC-FORM", "tiles form")
    return [tiles[8 + c * TILE_BYTES:8 + (c + 1) * TILE_BYTES] for c in range(5)]


def fill(rgb):
    return bytes(rgb) * (TILE_BYTES // 3)


def uniform(cls_bytes):
    return cls_bytes[:3] if cls_bytes == cls_bytes[:3] * (TILE_BYTES // 3) else None


# ------------------------------------------------------------------ DSC-0
def cell_leaf(i, v):
    return H(b"\x00C" + struct.pack("<I", i) + bytes([v]))


def pad_leaf(tag, i):
    return H(b"\x00" + tag + struct.pack("<I", i))


def tile_leaf(c, form):
    kind, payload = form
    return H(b"\x00" + kind + bytes([c]) + payload)


def tile_form(c, cls_bytes):
    u = uniform(cls_bytes)
    return (b"F", u) if u is not None else (b"T", hashlib.sha256(cls_bytes).digest())


def node(left, right):
    return H(b"\x01" + left + right)


def depth_of(n):
    d = 0
    while (1 << d) < n:
        d += 1
    return d


def levels_of(leaves, d, pad):
    lv = [list(leaves) + [pad_leaf(pad, i) for i in range(len(leaves), 1 << d)]]
    for _ in range(d):
        prev = lv[-1]
        lv.append([node(prev[j], prev[j + 1]) for j in range(0, len(prev), 2)])
    return lv


def root_of(w, rows, cells_root, tiles_root, rest_leaf):
    return H(b"VRDNDSC0" + struct.pack("<III", w, rows, TILE_BYTES) + cells_root + tiles_root + rest_leaf)


def multiproof(lv, idxs):
    """The siblings the union of the paths of idxs needs, level by level, in increasing place: what fold() reads."""
    out, cur = [], sorted(set(idxs))
    if not cur:
        return [lv[-1][0]]
    for L in range(len(lv) - 1):
        have, nxt = set(cur), []
        for i in cur:
            if (i ^ 1) not in have:
                out.append(lv[L][i ^ 1])
            if not nxt or nxt[-1] != i >> 1:
                nxt.append(i >> 1)
        cur = nxt
    return out


def fold(d, leaves, proof, pos):
    """The root from leaves {place: hash} and the proof's siblings from pos; returns (root, pos after)."""
    if not leaves:
        if pos >= len(proof):
            raise Refused("DSC-PROOF-LENGTH", "a subtree's root is missing")
        return proof[pos], pos + 1
    cur = sorted(leaves.items())
    for _ in range(d):
        have, nxt = dict(cur), {}
        for i, hv in cur:
            if i >> 1 in nxt:
                continue
            if (i ^ 1) in have:
                sib = have[i ^ 1]
            else:
                if pos >= len(proof):
                    raise Refused("DSC-PROOF-LENGTH", "the proof ends before the paths do")
                sib, pos = proof[pos], pos + 1
            nxt[i >> 1] = node(hv, sib) if i % 2 == 0 else node(sib, hv)
        cur = sorted(nxt.items())
    return cur[0][1], pos


class State:
    """The prover: the bytes, and DSC-0's trees over them kept current."""

    def __init__(self, level, tiles):
        self.level, self.tiles = bytearray(level), bytearray(tiles)
        self.w, self.rows, cells, rest = split_level(bytes(level))
        self.n = self.w * self.rows
        self.dc = depth_of(self.n)
        self.cells_lv = levels_of([cell_leaf(i, cells[i]) for i in range(self.n)], self.dc, b"P")
        self.forms = [tile_form(c, b) for c, b in enumerate(split_tiles(bytes(tiles)))]
        self.tiles_lv = levels_of([tile_leaf(c, f) for c, f in enumerate(self.forms)], 3, b"p")
        self.rest_leaf = H(b"\x00R" + hashlib.sha256(rest).digest())

    def root(self):
        return root_of(self.w, self.rows, self.cells_lv[-1][0], self.tiles_lv[-1][0], self.rest_leaf)

    def cell(self, i):
        return self.level[16 + i]

    def _set(self, lv, i, leaf):
        lv[0][i] = leaf
        for L in range(1, len(lv)):
            i >>= 1
            lv[L][i] = node(lv[L - 1][2 * i], lv[L - 1][2 * i + 1])

    def batch(self, ops):
        """The net change of ops [("cell", x, z, byte) | ("tile", c, rgb)], last write winning: (receipt, proof)."""
        cells, tiles = {}, {}
        for op in ops:
            if op[0] == "cell":
                cells[op[2] * self.w + op[1]] = op[3]
            else:
                tiles[op[1]] = bytes(op[2])
        cells = sorted((i, self.cell(i), v) for i, v in cells.items() if self.cell(i) != v)
        tiles = sorted((c, self.forms[c], rgb) for c, rgb in tiles.items() if self.forms[c] != (b"F", rgb))
        receipt = receipt_bytes(self.w, self.rows, cells, tiles)
        return receipt, self.prove(receipt)

    def prove(self, receipt):
        """The proof for a receipt's places against the trees as they stand."""
        _w, _rows, cells, tiles = parse_receipt(receipt)
        return proof_bytes(multiproof(self.cells_lv, [i for i, _o, _n in cells]),
                           multiproof(self.tiles_lv, [c for c, _o, _n in tiles]), self.rest_leaf)

    def apply(self, receipt):
        w, rows, cells, tiles = parse_receipt(receipt)
        for i, _old, new in cells:
            self.level[16 + i] = new
            self._set(self.cells_lv, i, cell_leaf(i, new))
        for c, _old, rgb in tiles:
            self.tiles[8 + c * TILE_BYTES:8 + (c + 1) * TILE_BYTES] = fill(rgb)
            self.forms[c] = (b"F", rgb)
            self._set(self.tiles_lv, c, tile_leaf(c, self.forms[c]))


def receipt_bytes(w, rows, cells, tiles):
    out = bytearray(b"VRDNDSCR0" + struct.pack("<IIH", w, rows, len(cells)))
    for i, old, new in cells:
        out += struct.pack("<IBB", i, old, new)
    out += bytes([len(tiles)])
    for c, (kind, payload), rgb in tiles:
        out += bytes([c]) + kind + payload + bytes(rgb)
    return bytes(out)


def parse_receipt(b):
    """One byte form, read strictly: anything else is refused before any hashing."""
    if b[:9] != b"VRDNDSCR0" or len(b) < 19:
        raise Refused("DSC-FORM", "not a DSC-0 receipt")
    w, rows, nc = struct.unpack_from("<IIH", b, 9)
    p, cells = 19, []
    for _ in range(nc):
        if p + 6 > len(b):
            raise Refused("DSC-FORM", "the receipt ends inside a cell")
        cells.append(struct.unpack_from("<IBB", b, p))
        p += 6
    if p >= len(b):
        raise Refused("DSC-FORM", "the receipt has no tile count")
    nt, p, tiles = b[p], p + 1, []
    for _ in range(nt):
        if p + 2 > len(b) or b[p + 1:p + 2] not in (b"F", b"T"):
            raise Refused("DSC-FORM", "a tile's old form is neither F nor T")
        c, kind = b[p], b[p + 1:p + 2]
        size = 3 if kind == b"F" else 32
        if p + 2 + size + 3 > len(b):
            raise Refused("DSC-FORM", "the receipt ends inside a tile")
        tiles.append((c, (kind, bytes(b[p + 2:p + 2 + size])), bytes(b[p + 2 + size:p + 5 + size])))
        p += 5 + size
    if p != len(b):
        raise Refused("DSC-FORM", "the receipt has trailing bytes")
    return w, rows, cells, tiles


def proof_bytes(cells_proof, tiles_proof, rest_leaf):
    return b"VRDNDSCP0" + struct.pack("<II", len(cells_proof), len(tiles_proof)) + b"".join(cells_proof) + b"".join(tiles_proof) + rest_leaf


def parse_proof(b):
    if b[:9] != b"VRDNDSCP0" or len(b) < 17:
        raise Refused("DSC-FORM", "not a DSC-0 proof")
    nc, nt = struct.unpack_from("<II", b, 9)
    if len(b) != 17 + 32 * (nc + nt + 1):
        raise Refused("DSC-PROOF-LENGTH", "the proof's length is not its counts'")
    hs = [bytes(b[17 + 32 * k:49 + 32 * k]) for k in range(nc + nt + 1)]
    return hs[:nc], hs[nc:nc + nt], hs[-1]


def verify(root_before, receipt, proof):
    """The stateless verifier: the root after, or Refused. It holds no state and reads nothing but its arguments."""
    w, rows, cells, tiles = parse_receipt(receipt)
    if not (0 < w <= 1 << 16 and 0 < rows <= 1 << 16):
        raise Refused("DSC-LAW", "the level's extent")
    if not cells and not tiles:
        raise Refused("DSC-NET", "a receipt that changes nothing")
    n = w * rows
    for k, (i, old, new) in enumerate(cells):
        if k and i <= cells[k - 1][0]:
            raise Refused("DSC-ORDER", "cell places not strictly increasing (a place twice, or out of order)")
        if i >= n:
            raise Refused("DSC-LAW", "cell %d is outside the %dx%d level" % (i, w, rows))
        if old not in ALPHABET or new not in ALPHABET:
            raise Refused("DSC-LAW", "a cell value outside #.<>")
        if old == new:
            raise Refused("DSC-NET", "cell %d does not change" % i)
        x, z = i % w, i // w
        if (x in (0, w - 1) or z in (0, rows - 1)) and new != ord("#"):
            raise Refused("DSC-LAW", "cell (%d, %d) is on the border, which stays rock" % (x, z))
    for k, (c, old, rgb) in enumerate(tiles):
        if k and c <= tiles[k - 1][0]:
            raise Refused("DSC-ORDER", "tile classes not strictly increasing")
        if c >= 5:
            raise Refused("DSC-LAW", "tile class %d does not exist" % c)
        if old == (b"F", rgb):
            raise Refused("DSC-NET", "class %d is already that colour" % c)
    cproof, tproof, rest_leaf = parse_proof(proof)
    dc = depth_of(n)
    roots = []
    for side in (1, 2):   # the old values, then the new, over the same siblings
        cl = {i: cell_leaf(i, old if side == 1 else new) for i, old, new in cells}
        tl = {c: tile_leaf(c, old if side == 1 else (b"F", rgb)) for c, old, rgb in tiles}
        cr, pc = fold(dc, cl, cproof, 0)
        tr, pt = fold(3, tl, tproof, 0)
        if pc != len(cproof) or pt != len(tproof):
            raise Refused("DSC-PROOF-LENGTH", "the proof has siblings no path reads")
        roots.append(root_of(w, rows, cr, tr, rest_leaf))
    if roots[0] != root_before:
        raise Refused("DSC-ROOT", "the old values and the proof do not reach the root before")
    return roots[1]


def verifies(root_before, receipt, proof):
    try:
        verify(root_before, receipt, proof)
        return True
    except Refused:
        return False


def inverse(receipt):
    """The state-captured inverse: each operation's old and new swapped. A paint over a class that was not one colour
    has no inverse here: its old bytes are not in the receipt, only their digest."""
    w, rows, cells, tiles = parse_receipt(receipt)
    if any(old[0] != b"F" for _c, old, _rgb in tiles):
        raise Refused("DSC-INVERSE", "a paint over a textured class: its inverse needs the class's old bytes")
    return receipt_bytes(w, rows, [(i, new, old) for i, old, new in cells], [(c, (b"F", rgb), old[1]) for c, old, rgb in tiles])


def naive_root_after(receipt, proof_paths):
    """A per-path verifier (the hazard): each path folded alone over the siblings recorded before the batch."""
    w, rows, cells, _tiles = parse_receipt(receipt)
    cr = None
    for (i, _old, new), sibs in zip(cells, proof_paths):
        hv = cell_leaf(i, new)
        for L, sib in enumerate(sibs):
            hv = node(hv, sib) if (i >> L) % 2 == 0 else node(sib, hv)
        cr = hv
    return cr


# ------------------------------------------------------------------ the workshop, the authority this court answers to
def session_exe(given, tmp):
    if given:
        return given
    built = os.path.join(REPO, "verify", "build", "session" + EXE)
    if os.path.isfile(built):
        return built
    rustc = shutil.which("rustc")
    if not rustc:
        return None
    out = os.path.join(tmp, "session" + EXE)
    cp = subprocess.run([rustc, "-O", os.path.join(REPO, "workshop", "session.rs"), "-o", out], capture_output=True, text=True)
    return out if cp.returncode == 0 else None


def run(exe, cwd, *args):
    cp = subprocess.run([exe] + list(args), cwd=cwd, capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError("session %s: %s" % (args[0], (cp.stdout + cp.stderr).strip()[-300:]))
    return cp.stdout


def random_ops(rng, w, rows, k):
    ops = []
    for _ in range(k):
        if rng.random() < 0.12:
            ops.append(("tile", rng.randrange(5), (rng.randrange(256), rng.randrange(256), rng.randrange(256))))
        elif rng.random() < 0.1:
            ops.append(("cell", rng.choice((0, w - 1)), rng.randrange(rows), ord("#")))
        else:
            ops.append(("cell", rng.randrange(1, w - 1), rng.randrange(1, rows - 1), rng.choice(ALPHABET)))
    return ops


def spec(op):
    if op[0] == "cell":
        return "cell:%d,%d,%s" % (op[1], op[2], chr(op[3]))
    return "tile:%s,%d,%d,%d" % ((CLASSES[op[1]],) + tuple(op[2]))


# ------------------------------------------------------------------ the court
def median_ms(fn, reps):
    ts = []
    for _ in range(reps):
        t = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t) * 1000.0)
    ts.sort()
    return ts[len(ts) // 2]


def synthetic_level(side, rest):
    """A side x side level of the level's layout: a rock border around floor, the rest of room.lvl after it."""
    row = b"#" + b"." * (side - 2) + b"#"
    return b"VRDNLVL1" + struct.pack("<II", side, side) + b"#" * side + row * (side - 2) + b"#" * side + rest


def agree(p, exe, tmp, tag, tiles_name, level0, rng, edits):
    """A seeded session made by the workshop edit by edit, and the same edits as DSC-0 batches beside it. Returns
    (agreement held, the workshop's verify time per edit in ms, the blocks one of its edits hashes)."""
    d = os.path.join(tmp, tag)
    os.makedirs(d)
    shutil.copy(os.path.join(REPO, "oracle", "levels", "room.lvl"), os.path.join(d, "room.lvl"))
    shutil.copy(os.path.join(REPO, "oracle", "tiles", tiles_name), os.path.join(d, tiles_name))
    tiles0 = open(os.path.join(d, tiles_name), "rb").read()
    run(exe, d, "new", "--level", "room.lvl", "--tiles", tiles_name, "--out", "s.json")
    shutil.copy(os.path.join(d, "s.json"), os.path.join(d, "empty.json"))
    st = State(level0, tiles0)
    w, rows = st.w, st.rows
    ops = random_ops(rng, w, rows, edits)
    batches, k = [], 0
    while k < len(ops):
        n = rng.randrange(1, 6)
        batches.append(ops[k:k + n])
        k += n
    log_at, steps = [], 0
    for bt in batches:
        for op in bt:
            run(exe, d, "commit", "--session", "s.json", "--edit", spec(op))
            steps += 1
        log_at.append(steps)
    log = json.load(open(os.path.join(d, "s.json")))["data"]["log"]
    content_ok, root_ok, refused_honest, receipts, before = True, True, 0, [], []
    for bt, at in zip(batches, log_at):
        rc, pf = st.batch(bt)
        if rc != receipt_bytes(w, rows, [], []):
            try:
                before.append(st.root())
                nxt = verify(st.root(), rc, pf)
                st.apply(rc)
                receipts.append(rc)
                root_ok &= nxt == st.root() == State(bytes(st.level), bytes(st.tiles)).root()
            except Refused:
                refused_honest += 1
                before.pop()
        content_ok &= incumbent_content(bytes(st.level), bytes(st.tiles)).hex() == log[at - 1]["content"]
    run(exe, d, "replay", "--session", "s.json", "--out-level", "final.lvl", "--out-tiles", "final.tiles")
    final_ok = open(os.path.join(d, "final.lvl"), "rb").read() == bytes(st.level) and \
        open(os.path.join(d, "final.tiles"), "rb").read() == bytes(st.tiles)
    verified = "SESSION verify OK" in run(exe, d, "verify", "--session", "s.json")
    p.case("agree-content-%s" % tag, "HELD" if content_ok and final_ok and verified else "BROKEN", edits=steps,
           batches=len(batches), final_bytes_equal=final_ok, workshop_verify=verified)
    p.case("agree-root-%s" % tag, "HELD" if root_ok and refused_honest == 0 else "BROKEN", receipts=len(receipts),
           honest_refused=refused_honest)
    # undo by inverse receipts, newest first, as far as an inverse exists
    undone, inv_ok = 0, True
    for rc in reversed(receipts):
        try:
            iv = inverse(rc)
        except Refused:
            break
        r_now, pf = st.root(), st.prove(iv)
        st.apply(iv)
        try:
            inv_ok &= verify(r_now, iv, pf) == st.root() == before[len(receipts) - 1 - undone]
        except Refused:
            inv_ok = False
        undone += 1
    p.case("agree-inverse-%s" % tag, "HELD" if inv_ok and (undone > 0 or not receipts) else "BROKEN", undone=undone,
           of=len(receipts), stopped_at=("a_paint_over_texture" if undone < len(receipts) else "genesis"))
    # the workshop keeps no memo: each edit of its verify hashes W, M and the content again
    t_full = median_ms(lambda: run(exe, d, "verify", "--session", "s.json"), 5)
    t_empty = median_ms(lambda: run(exe, d, "verify", "--session", "empty.json"), 5)
    BLOCKS[0] = 0
    H(H(bytes(st.level)) + H(bytes(st.tiles)))
    return (content_ok and final_ok and verified and root_ok and refused_honest == 0 and inv_ok,
            max(t_full - t_empty, 0.0) / steps, BLOCKS[0])


def main(argv):
    p = Probe(6, "dsc")
    edits = int(argv[argv.index("--edits") + 1]) if "--edits" in argv else 60
    seed = int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 20261015
    given = argv[argv.index("--session-exe") + 1] if "--session-exe" in argv else None
    level0 = open(os.path.join(REPO, "oracle", "levels", "room.lvl"), "rb").read()
    textured = open(os.path.join(REPO, "oracle", "tiles", "oriented.tiles"), "rb").read()    # no class is one colour
    rng = random.Random(seed)
    killed = []

    # ---- soundness: every forged receipt or proof refused, with its code
    s = State(level0, textured)
    w, rows = s.w, s.rows
    r0 = s.root()
    inner = [i for i in range(s.n) if 0 < i % w < w - 1 and 0 < i // w < rows - 1]
    a = next(i for i in inner[200:] if i % 2 == 0 and i + 1 in inner and 0 < i % rows < rows - 2)
    b2 = a + 1                                            # two cells under one parent: a shared path
    nv = lambda i: ord(".") if s.cell(i) == ord("#") else ord("#")
    good, good_proof = s.batch([("cell", a % w, a // w, nv(a)), ("cell", b2 % w, b2 // w, nv(b2)), ("tile", 4, (9, 9, 9))])
    try:
        honest = verify(r0, good, good_proof)
    except Refused as e:
        honest = e.code
    _, _, gc, gt = parse_receipt(good)
    cp_, tp_, rl_ = parse_proof(good_proof)
    far = next(j for j in reversed(inner) if s.cell(j) == s.cell(a) and (j >> 4) != (a >> 4))
    one = lambda places: proof_bytes(multiproof(s.cells_lv, places), multiproof(s.tiles_lv, []), rl_)
    forged = {
        "forge-old-value": (receipt_bytes(w, rows, [(gc[0][0], gc[0][2], gc[0][1])] + gc[1:], gt), good_proof, "DSC-ROOT"),
        "forge-duplicate": (receipt_bytes(w, rows, [gc[0], gc[0]] + gc[1:], gt), good_proof, "DSC-ORDER"),
        "forge-unsorted": (receipt_bytes(w, rows, list(reversed(gc)), gt), good_proof, "DSC-ORDER"),
        "forge-noop": (receipt_bytes(w, rows, [(gc[0][0], gc[0][1], gc[0][1])] + gc[1:], gt), good_proof, "DSC-NET"),
        "forge-sibling": (good, proof_bytes([bytes([cp_[0][0] ^ 1]) + cp_[0][1:]] + cp_[1:], tp_, rl_), "DSC-ROOT"),
        "forge-extra-hash": (good, proof_bytes(cp_ + [cp_[0]], tp_, rl_), "DSC-PROOF-LENGTH"),
        "forge-missing-hash": (good, proof_bytes(cp_[:-1], tp_, rl_), "DSC-PROOF-LENGTH"),
        "forge-moved-place": (receipt_bytes(w, rows, [(far, gc[0][1], gc[0][2])], []), one([a]), "DSC-ROOT"),
        "forge-padding-place": (receipt_bytes(w, rows, [(s.n + 5, ord("#"), ord("."))], []), one([s.n + 5]), "DSC-LAW"),
        "forge-tile-class": (receipt_bytes(w, rows, [], [(5, (b"F", b"\x00\x00\x00"), b"\x01\x01\x01")]),
                             proof_bytes(multiproof(s.cells_lv, []), multiproof(s.tiles_lv, [5]), rl_), "DSC-LAW"),
        "forge-empty": (receipt_bytes(w, rows, [], []), proof_bytes(multiproof(s.cells_lv, []), multiproof(s.tiles_lv, []), rl_), "DSC-NET"),
        "forge-border": (receipt_bytes(w, rows, [(w, ord("#"), ord("."))], []), one([w]), "DSC-LAW"),
        "forge-alphabet": (receipt_bytes(w, rows, [(gc[0][0], gc[0][1], ord("x"))], []), one([gc[0][0]]), "DSC-LAW"),
        "forge-transposed": (receipt_bytes(rows, w, gc, gt), good_proof, "DSC-ROOT"),
        "forge-tile-old": (receipt_bytes(w, rows, gc, [(4, (b"F", b"\x01\x02\x03"), gt[0][2])]), good_proof, "DSC-ROOT"),
        "forge-trailing": (good + b"\x00", good_proof, "DSC-FORM"),
    }
    sound = True
    for name, (rc, pf, want) in forged.items():
        try:
            verify(r0, rc, pf)
            got = "ACCEPTED"
        except Refused as e:
            got = e.code
        sound &= got == want
        p.case(name, "HELD" if got == want else "BROKEN", want=want, got=got)
    s.apply(good)
    try:
        verify(s.root(), good, good_proof)                # the honest receipt again, after it was applied
        got = "ACCEPTED"
    except Refused as e:
        got = e.code
    sound &= got == "DSC-ROOT"
    p.case("forge-stale-root", "HELD" if got == "DSC-ROOT" else "BROKEN", want="DSC-ROOT", got=got)
    sound &= honest == s.root()
    p.case("honest-accepted", "HELD" if honest == s.root() else "BROKEN", cells=len(gc), tiles=len(gt))
    if not sound:
        killed.append("soundness")

    # ---- limits: what a root cannot carry, reproduced
    back, _bp = s.batch([("cell", a % w, a // w, gc[0][1]), ("cell", b2 % w, b2 // w, gc[1][1])])
    s.apply(back)
    again, again_proof = s.batch([("cell", a % w, a // w, gc[0][2]), ("cell", b2 % w, b2 // w, gc[1][2])])
    try:
        verify(s.root(), again, again_proof)
        accepted = True
    except Refused:
        accepted = False
    same = again == receipt_bytes(w, rows, gc, [])
    p.case("limit-history", "HELD" if same and accepted else "BROKEN", same_receipt=same, verifies_again=accepted,
           meaning="a_root_has_no_history:_the_log's_duplicate_and_anchor_checks_stay")
    try:
        inverse(good)
        inv = "formed"
    except Refused as e:
        inv = e.code
    p.case("limit-inverse-texture", "HELD" if inv == "DSC-INVERSE" else "BROKEN", got=inv,
           meaning="undoing_a_paint_over_texture_needs_its_bytes:_the_log_or_the_base")
    s2 = State(level0, textured)
    rc, _pf = s2.batch([("cell", a % w, a // w, gc[0][2]), ("cell", b2 % w, b2 // w, gc[1][2])])
    paths = [[s2.cells_lv[L][(i >> L) ^ 1] for L in range(s2.dc)] for i, _o, _n in parse_receipt(rc)[2]]
    naive = naive_root_after(rc, paths)
    s2.apply(rc)
    p.case("limit-shared-ancestor", "HELD" if naive != s2.cells_lv[-1][0] else "BROKEN",
           meaning="each_path_folded_alone_over_the_old_siblings_reaches_a_wrong_root:_the_union_proof_is_needed")

    # ---- agreement with the workshop, over a base whose classes are each one colour and over a textured one
    tmp = tempfile.mkdtemp(prefix="dsc-")
    kernel_us_per_block = None
    try:
        exe = session_exe(given, tmp)
        if exe is None:
            p.case("agree-workshop", "SKIPPED", why="no verify/build/session and no rustc")
        else:
            held = True
            for tag, name in (("plain", "identity.tiles"), ("textured", "oriented.tiles")):
                ok, ms_per_edit, blocks = agree(p, exe, tmp, tag, name, level0, rng, edits)
                held &= ok
                if tag == "plain":
                    kernel_us_per_block = ms_per_edit * 1000.0 / blocks
            if not held:
                killed.append("agreement")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---- cost: the incumbent's content for one edit, and DSC-0's verification of it, counted and timed.
    # Beyond 48 x 48 the level's layout is extrapolated (the kernel refuses such a level). DSC-0's verifier is run on a
    # proof of the right shape whose siblings stand for the cells not touched, so no tree of the world is built here.
    # "kernel_ms" is the incumbent's blocks at the rate the workshop's own sha256 showed above (its verify's time per
    # edit, over the blocks one edit hashes there, the edit's own work included: an upper bound on a block's cost).
    rate = lambda blocks: ("%.3f" % (blocks * kernel_us_per_block / 1000.0)) if kernel_us_per_block else "not_measured"
    rest = level0[16 + 48 * 32:]
    rows_out = []
    for side in (LATTICE, 128, 256, 512, 1024, 2048, 4096):
        lvl = synthetic_level(side, rest)
        BLOCKS[0] = 0
        H(H(lvl) + b"\x00" * 32)                         # the memo keeps sha256(M): a cell edit hashes W, then content
        inc_blocks = BLOCKS[0]
        inc_ms = median_ms(lambda: H(H(lvl) + b"\x00" * 32), 9 if side <= 1024 else 3)
        i = side * (side // 2) + side // 2
        rnd = random.Random(side)
        sibs = [bytes(rnd.randrange(256) for _ in range(32)) for _ in range(depth_of(side * side))]
        trs = [bytes(rnd.randrange(256) for _ in range(32)) for _ in range(2)]
        rc = receipt_bytes(side, side, [(i, ord("."), ord("#"))], [])
        pf = proof_bytes(sibs, trs[:1], trs[1])
        r_before = root_of(side, side, fold(depth_of(side * side), {i: cell_leaf(i, ord("."))}, sibs, 0)[0], trs[0], trs[1])
        BLOCKS[0] = 0
        ok = verifies(r_before, rc, pf)
        dsc_blocks = BLOCKS[0]
        dsc_ms = median_ms(lambda: verifies(r_before, rc, pf), 21)
        kern = float(rate(inc_blocks)) if kernel_us_per_block else 0.0
        rows_out.append((side, max(inc_ms, kern)))
        p.case("cost-cell-%d" % side, "HELD" if ok else "BROKEN", incumbent_blocks=inc_blocks, incumbent_ms="%.3f" % inc_ms,
               kernel_ms=rate(inc_blocks), dsc_blocks=dsc_blocks, dsc_ms="%.3f" % dsc_ms)
    tiles0 = open(os.path.join(REPO, "oracle", "tiles", "identity.tiles"), "rb").read()
    BLOCKS[0] = 0
    H(H(tiles0) + b"\x00" * 32)                          # a paint hashes M, then content (the memo keeps sha256(W))
    paint_blocks = BLOCKS[0]
    paint_ms = median_ms(lambda: H(H(tiles0) + b"\x00" * 32), 9)
    st48 = State(synthetic_level(48, rest), tiles0)
    rc, pf = st48.batch([("tile", 4, (1, 2, 3))])
    r_before = st48.root()
    BLOCKS[0] = 0
    ok = verifies(r_before, rc, pf)
    p.case("cost-paint", "HELD" if ok else "BROKEN", incumbent_blocks=paint_blocks, incumbent_ms="%.3f" % paint_ms, kernel_ms=rate(paint_blocks),
           dsc_blocks=BLOCKS[0], dsc_ms="%.3f" % median_ms(lambda: verifies(r_before, rc, pf), 21))
    worst48 = max(rows_out[0][1], paint_ms, float(rate(paint_blocks)) if kernel_us_per_block else 0.0)
    tenth = [r[0] for r in rows_out if r[1] > FRAME_MS / 10]
    whole = [r[0] for r in rows_out if r[1] > FRAME_MS]
    p.case("necessity-48", "HELD" if worst48 <= FRAME_MS else "BROKEN", worst_ms="%.3f" % worst48, frame_ms="%.1f" % FRAME_MS,
           first_side_over_a_tenth_of_a_frame=(tenth[0] if tenth else "none_to_4096"),
           first_side_over_a_frame=(whole[0] if whole else "none_to_4096"))
    if worst48 > FRAME_MS:
        killed.append("necessity")
    return p.verdict(killed=" ".join(killed) if killed else None)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
