# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""savegame — the durable serialization of the earned canonical components: persist stores state (URDRSAV1).

THE ELEVENTH GAME-LAYER VERTICAL SLICE, and D24 §3's PERSISTENCE rung (chain role "persist"). It gets its
own module name and glyph on purpose: `persist.py` (URDRLAT5) is the MMO Stage-H rollback-window checkpoint,
its public contract bound to `storecost`/`horizon` and the N-actor glide model, so it is NOT reusable as a
game-state API. What IS reused is the tree's UNIVERSAL content-addressing vocabulary — `SHA-256(MAGIC |
content) = identity`, a trailing-digest verify, reconstruct-or-refuse — a discipline ~25 modules share, not
`persist.py`'s property. This module imports no `persist.py` and inherits none of the URDRLAT5 model.

PERSIST STORES CANONICAL STATE; REPLAY DERIVES IT. The advertised "serialize/restore/re-bind a run
bit-identically" must not quietly become "replay the actions": `actionlog` records OPAQUE tokens, including
actions with different RNG-consumption behaviour (a `move` command does not advance the stream at all), so
folding the log does NOT reproduce the run's RNG state in general. Therefore every canonical component is
serialized INDEPENDENTLY and reconstructed DIRECTLY — never by replaying the log. Re-deriving state from the
action history is `replay`'s rung (10), across this boundary, not this one's.

THE SNAPSHOT (the currently-earned canonical components, each independently recoverable):
    seed                     the generative root
    depth                    with `seed`, REGENERATES the level via `gamegen.generate` (no cells stored)
    pos                      the entity position; RECONSTRUCTS the entity via `entity.at(pos)`
    (n, R_n)                 the RNG stream; RECONSTRUCTS via `rngstream.Stream(n, R_n)` — stored DIRECTLY
    actionlog entries        the ordered action history; RECONSTRUCTS via `actionlog.from_actions`

THIS IS NOT THE ASSEMBLED CANONICAL STATE. The record is a DURABLE SERIALIZATION of currently-earned
components, not the canonical `D_n`. Assembling seed + world + entity + RNG + history into one canonical-state
identity is `statecanon`'s rung (11), later; this rung stores the parts and earns no assembled digest.

THE RECORD (canonical, length-framed, big-endian — no ambiguous concatenation of native encodings). The
components' native serializations are variable-length and delimiter-based (`entity`'s `|pos:x,y`, `rngstream`'s
`|n:..|r:..`, opaque log tokens), so composition without ambiguity requires explicit length framing:
    record = MAGIC(8) | seed(8) | depth(8) | pos_x(8, signed) | pos_y(8, signed) | n(8) | R_n(32)
           | log_count(4) | (len(4) | token)*log_count
           | level_digest(32) | entity_digest(32) | stream_digest(32) | actionlog_digest(32)   # check-block
           | SHA-256(preceding)(32)
The trailing digest is integrity check AND content address (its hex is the filename a durable store WOULD
use); the check-block binds each recoverable input to its component's OWN identity authority.

TWO-LAYER INTEGRITY. `restore` verifies the trailing digest first (`SHA-256(buf[:-32]) == buf[-32:]`), so
every single-byte flip and every truncation refuses typed SAVEGAME-REFUSE before anything is reconstructed.
Then it RECONSTRUCTS usable typed state — regenerates the level, rebuilds the entity, stream and log — and
requires each reconstructed component's digest to EQUAL the check-block, so a validly re-sealed record whose
seed (or pos, or stream, or a token) was altered to a different component still refuses. Restoration produces
objects, never mere digest equality.

A PURE BYTES LAW. Serialize and restore are deterministic functions of bytes; there is NO filesystem here.
Actual disk I/O (digest-named files) is a DECLARED application discipline, not part of the certification law,
exactly as `persist.py` treats its store medium as a demonstration līmes — nondeterministic I/O has no place
inside a byte-identical gate.

GRADE (honest, D5). MEASURED: over a corpus of snapshots the record round-trips BIT-FOR-BIT, restore yields
usable typed state whose component digests match, the level is REGENERATED (the record carries no cells and
its size is independent of level dimensions), and length framing round-trips even a token that mimics a
component encoding. ESTABLISHED: persist is not replay (the stream is restored directly, and a log that folds
to a different stream still restores the stored stream); every single-byte flip and truncation refuses; a
re-sealed wrong-component record refuses per-component; malformed inputs refuse typed SAVEGAME-REFUSE; the
module imports no `persist.py` and mints no new identity mechanism. DECLARED: that the snapshot is the earned
components (seed, depth, pos, (n,R_n), actionlog) and NOT the assembled canonical `D_n`, and that disk I/O,
`statecanon`'s assembled identity, replay-based reconstruction, multi-entity rosters and manifests/windows are
LATER rungs'. does_not_show: the assembled canonical-state identity (statecanon's); that a restored run is
reachable or winnable; wall-clock or crash-atomicity of any actual write; and nothing about the MMO rollback
window, whose `persist.py` this module does not touch."""
import hashlib
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in __import__("sys").path:
    __import__("sys").path.insert(0, _HERE)
import gamegen as _G                                                      # noqa: E402  (regenerate the level)
import entity as _E                                                      # noqa: E402  (reconstruct the entity)
import rngstream as _R                                                   # noqa: E402  (reconstruct the stream)
import actionlog as _A                                                   # noqa: E402  (reconstruct the log)

MAGIC = b"URDRSAV1"

LAYER = "CORE"
D24_ANSWER = "affects canonical game state — the durable serialization of the earned canonical components"
ALLOWED_IMPORTS = ("hashlib", "os", "gamegen", "entity", "rngstream", "actionlog")

DIGEST_BYTES = 32
_U64 = 1 << 64
#: fixed prefix width before the framed log: MAGIC + seed + depth + pos_x + pos_y + n + R_n + log_count
_PREFIX = len(MAGIC) + 8 + 8 + 8 + 8 + 8 + DIGEST_BYTES + 4
_CHECKBLOCK = 4 * DIGEST_BYTES                                           # level, entity, stream, actionlog


class SavegameError(Exception):
    def __init__(self, message):
        super().__init__(f"SAVEGAME-REFUSE: {message}")
        self.code = "SAVEGAME-REFUSE"


def _u64(v, what):
    if not (type(v) is int and 0 <= v < _U64):
        raise SavegameError(f"{what} must be an int in 0..2^64-1, got {v!r}")
    return v.to_bytes(8, "big")


def _s64(v, what):
    if not (type(v) is int and -(1 << 63) <= v < (1 << 63)):
        raise SavegameError(f"{what} must be a signed 64-bit int, got {v!r}")
    return v.to_bytes(8, "big", signed=True)


def _is_pos(v):
    return (isinstance(v, tuple) and len(v) == 2
            and type(v[0]) is int and type(v[1]) is int)      # bool excluded


def serialize(seed, depth, pos, stream, log):
    """The canonical durable record of the earned components. Each is validated and reconstructed to derive
    its own identity for the check-block; a malformed component refuses typed SAVEGAME-REFUSE. The level is
    NOT stored — only `(seed, depth)`, from which it regenerates."""
    seed_b, depth_b = _u64(seed, "seed"), _u64(depth, "depth")
    if not _is_pos(pos):
        raise SavegameError(f"pos must be an (int, int), got {pos!r}")
    if not isinstance(stream, _R.Stream):
        raise SavegameError(f"stream must be an rngstream.Stream, got {type(stream).__name__}")
    try:
        _A.entries(log)                                      # validates the log is a tuple of byte tokens
    except _A.ActionlogError as exc:
        raise SavegameError(f"log is not a valid actionlog: {exc}")
    # component identities, each from its OWN authority
    try:
        level = _G.generate(seed, depth)
    except Exception as exc:
        raise SavegameError(f"(seed, depth) does not generate a level: {exc}")
    lvl_dig = bytes.fromhex(_G.level_digest(level))
    ent_dig = bytes.fromhex(_E.entity_digest(_E.at(pos)))
    str_dig = bytes.fromhex(_R.stream_digest(stream))
    log_dig = bytes.fromhex(_A.digest(log))

    body = bytearray(MAGIC)
    body += seed_b + depth_b
    body += _s64(pos[0], "pos_x") + _s64(pos[1], "pos_y")
    body += stream.n.to_bytes(8, "big") + stream.r
    ents = _A.entries(log)
    body += len(ents).to_bytes(4, "big")
    for e in ents:
        body += len(e).to_bytes(4, "big") + e
    body += lvl_dig + ent_dig + str_dig + log_dig
    return bytes(body) + hashlib.sha256(bytes(body)).digest()


def _verified(buf):
    """Type, minimum length, magic, and the digest law — the tree's content-addressing verify, reconstruct-
    or-refuse. Returns the buffer as bytes or a typed SAVEGAME-REFUSE."""
    if not (type(buf) is bytes or type(buf) is bytearray):
        raise SavegameError("a record must be bytes")
    buf = bytes(buf)
    floor = _PREFIX + _CHECKBLOCK + DIGEST_BYTES
    if len(buf) < floor:
        raise SavegameError(f"buffer of {len(buf)} bytes is shorter than the {floor}-byte minimum")
    if buf[:len(MAGIC)] != MAGIC:
        raise SavegameError("bad magic — not a URDRSAV1 record")
    if hashlib.sha256(buf[:-DIGEST_BYTES]).digest() != buf[-DIGEST_BYTES:]:
        raise SavegameError("digest mismatch — tampered, truncated, or corrupted; refused, not repaired")
    return buf


def address(buf):
    """The content address (the trailing digest hex) of a VERIFIED record — the filename a durable store
    would use. No address for corrupt bytes."""
    return _verified(buf)[-DIGEST_BYTES:].hex()


def restore(buf):
    """The inverse of `serialize`: reconstruct usable TYPED state — `(seed, depth, level, entity, stream,
    log)` — BIT-FOR-BIT, or a typed SAVEGAME-REFUSE. Verifies the envelope digest first (every flip and
    truncation refuses), then reconstructs each component and requires its digest to EQUAL the check-block."""
    buf = _verified(buf)
    off = len(MAGIC)
    seed = int.from_bytes(buf[off:off + 8], "big"); off += 8
    depth = int.from_bytes(buf[off:off + 8], "big"); off += 8
    px = int.from_bytes(buf[off:off + 8], "big", signed=True); off += 8
    py = int.from_bytes(buf[off:off + 8], "big", signed=True); off += 8
    n = int.from_bytes(buf[off:off + 8], "big"); off += 8
    r = buf[off:off + DIGEST_BYTES]; off += DIGEST_BYTES
    count = int.from_bytes(buf[off:off + 4], "big"); off += 4
    ents = []
    for _ in range(count):
        if off + 4 > len(buf) - _CHECKBLOCK - DIGEST_BYTES:
            raise SavegameError("framed log overruns the record — malformed length prefix")
        ln = int.from_bytes(buf[off:off + 4], "big"); off += 4
        if off + ln > len(buf) - _CHECKBLOCK - DIGEST_BYTES:
            raise SavegameError("framed token overruns the record — malformed length prefix")
        ents.append(buf[off:off + ln]); off += ln
    # the check-block must sit exactly where the framed log ends
    if off != len(buf) - _CHECKBLOCK - DIGEST_BYTES:
        raise SavegameError("log framing does not reach the check-block — malformed record")
    exp_lvl = buf[off:off + DIGEST_BYTES].hex(); off += DIGEST_BYTES
    exp_ent = buf[off:off + DIGEST_BYTES].hex(); off += DIGEST_BYTES
    exp_str = buf[off:off + DIGEST_BYTES].hex(); off += DIGEST_BYTES
    exp_log = buf[off:off + DIGEST_BYTES].hex(); off += DIGEST_BYTES

    # RECONSTRUCT usable typed state, then VERIFY each against its OWN identity authority
    try:
        level = _G.generate(seed, depth)
    except Exception as exc:
        raise SavegameError(f"(seed, depth) does not regenerate a level: {exc}")
    if _G.level_digest(level) != exp_lvl:
        raise SavegameError("regenerated level digest does not match the check-block")
    try:
        ent = _E.at((px, py))
    except _E.EntityError as exc:
        raise SavegameError(f"position does not reconstruct an entity: {exc}")
    if _E.entity_digest(ent) != exp_ent:
        raise SavegameError("reconstructed entity digest does not match the check-block")
    try:
        stream = _R.Stream(n, r)
    except _R.RngError as exc:
        raise SavegameError(f"(n, R_n) does not reconstruct a stream: {exc}")
    if _R.stream_digest(stream) != exp_str:
        raise SavegameError("reconstructed stream digest does not match the check-block")
    log = _A.from_actions(tuple(ents))
    if _A.digest(log) != exp_log:
        raise SavegameError("reconstructed actionlog digest does not match the check-block")
    return (seed, depth, level, ent, stream, log)


# ---- the laws / falsifiers ------------------------------------------------------------------------------
def _snap(seed, depth, pos, tokens, stream_tokens):
    """A corpus snapshot: a level from (seed, depth), a position, an actionlog from `tokens`, and a stream
    advanced by `stream_tokens` from the run's root — note the log and the stream are INDEPENDENT."""
    stream = _R.apply(_R.root(seed), stream_tokens)
    log = _A.from_actions(tokens)
    return seed, depth, pos, stream, log


def a_snapshot_round_trips(seed, depth, pos, tokens, stream_tokens):
    """MEASURED: serialize -> restore -> re-serialize is BIT-IDENTICAL, and the restored components carry the
    same identities."""
    s, d, p, st, lg = _snap(seed, depth, pos, tokens, stream_tokens)
    rec = serialize(s, d, p, st, lg)
    seed2, depth2, level2, ent2, stream2, log2 = restore(rec)
    re = serialize(seed2, depth2, ent2.get("pos"), stream2, log2)
    return (re == rec
            and _G.level_digest(level2) == _G.level_digest(_G.generate(s, d))
            and ent2.get("pos") == p
            and stream2 == st
            and _A.entries(log2) == _A.entries(lg))


def restore_yields_usable_typed_state(seed, depth, pos, tokens, stream_tokens):
    """The re-bind seam: restore returns TYPED objects (a Level, an Entity, a Stream, a log), not mere digest
    equality — each usable and matching its source."""
    s, d, p, st, lg = _snap(seed, depth, pos, tokens, stream_tokens)
    _s, _d, level, ent, stream, log = restore(serialize(s, d, p, st, lg))
    return (isinstance(level, _G.Level) and isinstance(ent, _E.Entity)
            and isinstance(stream, _R.Stream) and isinstance(log, tuple)
            and ent.get("pos") == p and stream == st and _A.entries(log) == _A.entries(lg))


def persist_is_not_replay(seed, depth, pos):
    """The rung boundary: the stream is restored DIRECTLY from (n, R_n), never by folding the log. Built so
    the stored stream DIFFERS from folding the log; restore returns the STORED stream, proving no replay."""
    log = _A.from_actions(("N", "loot:x", "S"))          # includes a non-advancing move token
    stored = _R.apply(_R.root(seed), ("loot:only",))     # a DIFFERENT stream than folding the log
    folded = _R.apply(_R.root(seed), _A.entries(log))
    _s, _d, _lvl, _ent, stream, _lg = restore(serialize(seed, depth, pos, stored, log))
    return (stream == stored and stream != folded
            and _R.stream_digest(stream) != _R.stream_digest(folded))


def the_level_is_regenerated_not_stored(seed, depth, pos, tokens, stream_tokens):
    """The record carries no level cells: its size is `_PREFIX + framed-log + check-block + digest`,
    independent of the level's dimensions — the level regenerates from (seed, depth)."""
    s, d, p, st, lg = _snap(seed, depth, pos, tokens, stream_tokens)
    rec = serialize(s, d, p, st, lg)
    framed = sum(4 + len(e) for e in _A.entries(lg))
    expected = _PREFIX + framed + _CHECKBLOCK + DIGEST_BYTES
    return len(rec) == expected


def length_framing_is_unambiguous(seed, depth, pos):
    """A token that MIMICS a component encoding (delimiters and all) round-trips exactly — framing is by
    length, never by delimiter, so no concatenation ambiguity."""
    tricky = (b"|n:5|r:deadbeef", b"URDRSAV1", b"", b"\x00\x04\x00\x00", b"loot:" + b"x" * 40)
    log = _A.from_actions(tricky)
    st = _R.root(seed)
    _s, _d, _lvl, _ent, _stream, log2 = restore(serialize(seed, depth, pos, st, log))
    return _A.entries(log2) == tricky


def every_single_byte_flip_refuses(seed, depth, pos):
    """EXHAUSTIVE corruption: every single-byte flip of a real record refuses typed — caught by the envelope
    digest before any reconstruction."""
    rec = serialize(seed, depth, pos, _R.root(seed), _A.from_actions(("a", "b")))
    for i in range(len(rec)):
        bad = bytearray(rec); bad[i] ^= 0xFF
        try:
            restore(bytes(bad)); return False
        except SavegameError:
            pass
    return True


def every_truncation_refuses(seed, depth, pos):
    """Every truncation of a real record refuses typed."""
    rec = serialize(seed, depth, pos, _R.root(seed), _A.from_actions(("a", "b")))
    for cut in range(len(rec)):                              # 0..len-1, all shorter than the record
        try:
            restore(rec[:cut]); return False
        except SavegameError:
            pass
    return True


def a_resealed_wrong_component_refuses(seed, depth, pos):
    """A validly RE-SEALED record whose stored component identity was altered refuses per-component: flip one
    byte of each check-block digest in turn, re-seal the envelope, and require a typed refusal every time."""
    rec = serialize(seed, depth, pos, _R.root(seed), _A.from_actions(("a",)))
    body = bytearray(rec[:-DIGEST_BYTES])
    base = len(body) - _CHECKBLOCK
    caught = 0
    for k in range(4):                                       # level, entity, stream, actionlog digests
        b2 = bytearray(body); b2[base + k * DIGEST_BYTES] ^= 0xFF
        resealed = bytes(b2) + hashlib.sha256(bytes(b2)).digest()
        try:
            restore(resealed)
        except SavegameError:
            caught += 1
    return caught == 4


def refuse_is_total(seed=0, depth=1, pos=(3, 4)):
    """(serialize inputs, restore inputs): each malformed component and each malformed record refuses typed
    SAVEGAME-REFUSE."""
    st, lg = _R.root(seed), _A.from_actions(("a",))
    s_ref = 0
    bad_calls = (
        (-1, depth, pos, st, lg), (seed, -1, pos, st, lg), (seed, depth, (0.0, 0), st, lg),
        (seed, depth, pos, "stream", lg), (seed, depth, pos, st, "log"), (seed, depth, (0,), st, lg),
    )
    for args in bad_calls:
        try:
            serialize(*args)
        except SavegameError as exc:
            s_ref += exc.code == "SAVEGAME-REFUSE"
    r_ref = 0
    for bad in (None, 0, b"short", b"X" * 400):
        try:
            restore(bad)
        except SavegameError as exc:
            r_ref += exc.code == "SAVEGAME-REFUSE"
    return s_ref == len(bad_calls), r_ref == 4


def does_not_import_persist_or_mint_identity():
    """REJECTS the MMO model and a second identity mechanism, read off this module's AST: it imports no
    `persist` (nor `storecost`/`horizon`), its declared substrate is exactly `ALLOWED_IMPORTS`, and its ONLY
    hashlib call is the tree's `sha256` content-addressing (no bespoke chain)."""
    import ast
    with open(_os.path.join(_HERE, "savegame.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    top = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            top.add((node.module or "").split(".")[0])
    reaches = {n.attr for n in ast.walk(tree)
               if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
               and n.value.id == "hashlib"}
    return (top == set(ALLOWED_IMPORTS)
            and not ({"persist", "storecost", "horizon"} & top)
            and reaches <= {"sha256"})


def is_not_the_assembled_canonical_state():
    """The user's nuance, made a law: this rung serializes the earned COMPONENTS, it does not mint the
    assembled canonical `D_n`. The module exposes no such assembled-identity API — that is `statecanon`'s."""
    return not any(hasattr(__import__("savegame"), nm)
                   for nm in ("canonical_state", "d_n", "statecanon", "assembled_digest"))


# ---- scenes ---------------------------------------------------------------------------------------------
#: The corpus: `gamegen` seeds/depths, arbitrary positions (savegame does not police traversability — that is
#: `move`'s), independent action logs and streams (opaque tokens; the log is NOT the stream's preimage).
CORPUS = (
    (0, 1, (3, 4), ("N", "S"), ("loot:x",)),
    (1, 2, (0, 0), (), ("v0", "loot:y")),
    (12345, 3, (7, 2), ("loot:a", "N", "loot:b"), ("loot:a", "loot:b")),
    (0xDEADBEEF, 5, (-1, 9), (b"raw", "N", b"|n:1|r:00"), ("v0",)),
)
SCENES = ("snapshot", "laws")


def _snap_row(seed, depth, pos, tokens, stream_tokens):
    s, d, p, st, lg = _snap(seed, depth, pos, tokens, stream_tokens)
    rec = serialize(s, d, p, st, lg)
    return "%d,%d,%d,%d,n%d=%d:%s" % (seed, depth, pos[0], pos[1], len(_A.entries(lg)),
                                      len(rec), address(rec)[:16])


def scene_case(name):
    if name == "snapshot":
        return "|".join(_snap_row(*c) for c in CORPUS)
    if name == "laws":
        return ("roundtrip=%s|typed=%s|notreplay=%s|regen=%s|framing=%s|flip=%s|trunc=%s|reseal=%s|"
                "refuse=%s|noimport=%s|notcanon=%s") % (
            tuple(a_snapshot_round_trips(*c) for c in CORPUS),
            tuple(restore_yields_usable_typed_state(*c) for c in CORPUS),
            persist_is_not_replay(0, 1, (3, 4)),
            tuple(the_level_is_regenerated_not_stored(*c) for c in CORPUS),
            length_framing_is_unambiguous(0, 1, (2, 2)),
            every_single_byte_flip_refuses(0, 1, (3, 4)),
            every_truncation_refuses(0, 1, (3, 4)),
            a_resealed_wrong_component_refuses(0, 1, (3, 4)),
            refuse_is_total(),
            does_not_import_persist_or_mint_identity(),
            is_not_the_assembled_canonical_state())
    raise SavegameError(f"no scene named {name!r}")


def scene_result(name):
    return hashlib.sha256(MAGIC + b"|" + name.encode() + b"|"
                          + scene_case(name).encode()).hexdigest()


def savegame_digest():
    return hashlib.sha256(MAGIC + b"|" + "|".join(scene_result(n)
                                                  for n in SCENES).encode()).hexdigest()


def golden(name):
    with open(_os.path.join(_HERE, "conformance_savegame.txt"), encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                nm, dig = ln.split()
                if nm == name:
                    return dig
    raise SavegameError(f"no golden named {name!r}")


def emitted_matches_pinned():
    return (all(scene_result(n) == golden(n) for n in SCENES)
            and savegame_digest() == golden("savegame"))


def an_unpinned_name_refuses():
    try:
        golden("not-a-scene")
    except SavegameError as exc:
        return exc.code == "SAVEGAME-REFUSE"
    return False


def main():
    print("SAVEGAME — the durable serialization of the earned canonical components (URDRSAV1)")
    print("layer %s: %s | imports %s" % (LAYER, D24_ANSWER, ALLOWED_IMPORTS))
    print("chain role: persist (§3); NOT persist.py/URDRLAT5 (the MMO rollback-window arc)")
    print()
    s, d, p = 0xDEADBEEF, 3, (3, 4)
    st = _R.apply(_R.root(s), ("loot:x", "loot:y"))
    lg = _A.from_actions(("N", "loot:x", "S", "loot:y"))
    rec = serialize(s, d, p, st, lg)
    print("record bytes:", len(rec), " address:", address(rec)[:16])
    seed2, depth2, level2, ent2, stream2, log2 = restore(rec)
    print("restored typed state:", type(level2).__name__, type(ent2).__name__,
          type(stream2).__name__, "log[%d]" % len(_A.entries(log2)))
    print()
    print("round-trips bit-identical      :", a_snapshot_round_trips(*CORPUS[0]))
    print("restore yields typed state     :", restore_yields_usable_typed_state(*CORPUS[0]))
    print("persist is NOT replay          :", persist_is_not_replay(0, 1, (3, 4)))
    print("level regenerated, not stored  :", the_level_is_regenerated_not_stored(*CORPUS[0]))
    print("length framing unambiguous     :", length_framing_is_unambiguous(0, 1, (2, 2)))
    print("every byte flip refuses        :", every_single_byte_flip_refuses(0, 1, (3, 4)))
    print("every truncation refuses       :", every_truncation_refuses(0, 1, (3, 4)))
    print("resealed wrong-component refuses:", a_resealed_wrong_component_refuses(0, 1, (3, 4)))
    print("imports no persist, one identity:", does_not_import_persist_or_mint_identity())
    print("not the assembled canonical D_n :", is_not_the_assembled_canonical_state())
    print("refuse total (serialize, restore):", refuse_is_total())
    print()
    for n in SCENES:
        print(n, scene_result(n))
    print("savegame", savegame_digest())
    print()
    print("does_not_show: the assembled canonical-state identity (statecanon's); that a restored run is")
    print("winnable; wall-clock or crash-atomicity of any real write; and nothing about the MMO rollback")
    print("window, whose persist.py this module does not touch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
