"""0259 (G-2): standalone Tier-1 negative vectors. Each malformed input is rejected by its intended LOCAL decoder rule
(decode_value / decode_key / decode_node / parse_collection), with the specific error code — not a downstream
reconstruction failure. Value/key/VTYPE/UTF-8/surrogate are candidate-independent; node framing runs for both
candidates. Accepting neighbours confirm the rejection is specific, not blanket."""
from oracle import decoder as d
from oracle import canonicality as C
from .harness import Cases, reject


def _V(b):
    return d.decode_value(d.Reader(b))


def run():
    c = Cases()

    # --- §1 value, candidate-independent (local: decode_value / encode_value) ---
    c.ok("T1 INT non-minimal -> INT_NONMINIMAL",
         lambda: reject(lambda: _V(bytes([0x01, 0x00]) + d.u64(2) + b"\x00\x05"), code="INT_NONMINIMAL"))
    c.ok("T1 INT negative-zero -> INT_NEGZERO",
         lambda: reject(lambda: _V(bytes([0x01, 0x01]) + d.u64(0)), code="INT_NEGZERO"))
    c.ok("T1 INT bad sign byte -> INT_SIGN",
         lambda: reject(lambda: _V(bytes([0x01, 0x02]) + d.u64(1) + b"\x05"), code="INT_SIGN"))
    c.ok("T1 bad VTYPE -> VTYPE",
         lambda: reject(lambda: _V(bytes([0x09, 0x00]) + d.u64(0)), code="VTYPE"))
    c.ok("T1 STR invalid UTF-8 (decode) -> STR_UTF8",
         lambda: reject(lambda: _V(bytes([0x02]) + d.u64(1) + b"\xff"), code="STR_UTF8"))
    c.ok("T1 STR lone surrogate (encode) -> STR_SURROGATE",
         lambda: reject(lambda: d.encode_value("\ud800"), code="STR_SURROGATE"))
    # accepting neighbours
    def valid_values():
        if _V(bytes([0x01, 0x00]) + d.u64(1) + b"\x05") != 5:
            raise AssertionError("valid int neighbour failed")
        if _V(bytes([0x02]) + d.u64(3) + b"orc") != "orc":
            raise AssertionError("valid str neighbour failed")
    c.ok("T1 valid int/str decode (neighbours)", valid_values)

    # --- §2 keys, candidate-independent (local: decode_key) ---
    c.ok("T1 bad KTYPE -> KTYPE",
         lambda: reject(lambda: d.decode_key(d.Reader(bytes([0x20]) + d.u64(2) + b"e1")), code="KTYPE"))
    c.ok("T1 KTYPE position (comp where eid expected) -> KTYPE_POS",
         lambda: reject(lambda: d.decode_key(d.Reader(bytes([0x11]) + d.u64(2) + b"hp"), expect_kind="eid"), code="KTYPE_POS"))

    # --- §8/§0 node framing, both candidates (local: decode_node) ---
    for cand in ("A", "B"):
        other = "B" if cand == "A" else "A"
        c.ok("T1 wrong candidate domain -> DOMAIN [%s]" % cand,
             lambda cand=cand, other=other: reject(lambda: d.decode_node(d.enc_empty(other), cand), code="DOMAIN"))
        c.ok("T1 wrong VERSION on node -> VERSION [%s]" % cand,
             lambda cand=cand: reject(lambda: d.decode_node(d.dom(cand, "empty") + d.u16(1) + d.u8(0x00), cand), code="VERSION"))
        c.ok("T1 ROOT missing SCALARS -> TRUNCATED (framing) [%s]" % cand,
             lambda cand=cand: reject(lambda: d.decode_node(d.dom(cand, "root") + d.u16(0) + d.u8(0x01)
                                      + (d.u8(0) if cand == "B" else b"") + d.u32(0), cand), code="TRUNCATED"))
        c.ok("T1 SCALARS on non-ROOT (BRANCH) -> TRAILING (framing) [%s]" % cand,
             lambda cand=cand: reject(lambda: d.decode_node(
                 d.enc_branch(cand, 0, {0: d.node_address(d.enc_empty(cand))}) + d.enc_scalars(1, 0, 0), cand), code="TRAILING"))
        c.ok("T1 popcount > children -> TRUNCATED (framing) [%s]" % cand,
             lambda cand=cand: reject(lambda: d.decode_node(
                 d.dom(cand, "branch") + d.u16(0) + d.u8(0x02) + (d.u8(0) if cand == "B" else b"")
                 + d.u32(0b11) + d.node_address(d.enc_empty(cand)), cand), code="TRUNCATED"))
        c.ok("T1 valid EMPTY node parses (neighbour) [%s]" % cand,
             lambda cand=cand: d.decode_node(d.enc_empty(cand), cand))

    # --- §4a container framing, candidate-independent (local: parse_collection) ---
    good = C.serialize_state({"entities": {}, "alloc": 1, "rng": {"seed": 0, "counter": 0}}, "A")
    hdr = len(d.DOM("skuld-state-0"))
    c.ok("T1 container wrong DOM -> STATE_DOM",
         lambda: reject(lambda: C.parse_collection(b"skuld-WRONG--0\x00" + good[hdr:], "A"), code="STATE_DOM"))
    c.ok("T1 container wrong VERSION -> VERSION",
         lambda: reject(lambda: C.parse_collection(d.DOM("skuld-state-0") + d.u16(1) + good[hdr + 2:], "A"), code="VERSION"))
    c.ok("T1 valid container parses (neighbour)",
         lambda: C.parse_collection(good, "A"))

    return c.done()
