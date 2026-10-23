"""P-1 decoder: primitives, VALUE/KEY, chunk, the two TYPED hash seams, node encode + Tier-1 decode, resource limits.

Implemented from ENCODING-TABLE-P1.md rev 20 (§0-§4). Node ADDRESSING is production SHA-256 and is a module function
that NEVER takes the key-hash seam (structural seam isolation, G2). Key ROUTING goes through an injectable KeyHasher.
"""
import hashlib

# --- normative v0 constants (pinned here, checked by P1V-constants) --------------------------------------------------
VERSION = 0                      # u16; the "-0" domains are v0
MAX_LEN = 2**32 - 1              # lp lengths and per-field counts
MAX_NODES = 2**32 - 1            # unique nodes by hash (§4a)
MAX_TOTAL = 2**40                # sum of unique node-encoding bytes (§4a)
MAX_HASH_CHUNKS = 52             # chunk 0..51
U64_MAX = 2**64 - 1              # reserved; never a valid index (§5)

CAND_INFIX = {"A": "hamtA", "B": "merkleB"}
NODE_EMPTY, NODE_ROOT, NODE_BRANCH, NODE_LEAF_ENT, NODE_LEAF_COMP, NODE_BUCKET = range(6)  # 0x00..0x05
KTYPE_EID, KTYPE_COMP = 0x10, 0x11
VTYPE_INT, VTYPE_STR = 0x01, 0x02

# --- stable verdict categories (P10); never conflated -----------------------------------------------------------------
MALFORMED = "MALFORMED"          # Tier-1/2 structural
SEMANTIC = "SEMANTIC"            # Tier-3 replay / commitment mismatch
BLOCKED = "BLOCKED"              # D4-2 effects-root, below-boundary anchor; never a pass


class OracleError(Exception):
    """A rejection with a stable category and a specific code."""
    def __init__(self, category, code, msg=""):
        self.category = category
        self.code = code
        super().__init__("%s/%s: %s" % (category, code, msg))


def malformed(code, msg=""):
    return OracleError(MALFORMED, code, msg)


class Limits:
    """Resource limits; production = the normative constants. A reduced instance (3B) changes ONLY the thresholds,
    never field widths or grammar."""
    def __init__(self, max_len=MAX_LEN, max_nodes=MAX_NODES, max_total=MAX_TOTAL):
        self.max_len = max_len
        self.max_nodes = max_nodes
        self.max_total = max_total


PROD_LIMITS = Limits()

# =====================================================================================================================
# The two TYPED hash interfaces (G2). They are different types so a node-address call can never reach the key-hash seam.
# =====================================================================================================================


def node_address(encoding):
    """Production node content address = SHA256(node_encoding). NEVER parameterized by the key-hash seam."""
    return hashlib.sha256(encoding).digest()


def prod_key_hasher(key_bytes):
    """Production key hash H = int.from_bytes(sha256(KEY), 'big') (§2). A KeyHasher is callable: KEY bytes -> 256-bit int."""
    return int.from_bytes(hashlib.sha256(key_bytes).digest(), "big")


class InjectedKeyHasher:
    """Test-only seam (3A): supplies CONTROLLED key-hash outputs for routing fixtures real SHA-256 cannot construct
    (final-bit divergence, full collision). Results are 'injected', never a real SHA-256 outcome. Keys absent from the
    table fall back to production SHA-256 so ordinary routing still works."""
    def __init__(self, table):
        # table: {key_bytes: 256-bit int H}
        self.table = dict(table)
        self.injected = True

    def __call__(self, key_bytes):
        if key_bytes in self.table:
            return self.table[key_bytes]
        return prod_key_hasher(key_bytes)


# =====================================================================================================================
# Primitives
# =====================================================================================================================


def u8(n):
    if not (0 <= n <= 0xFF):
        raise malformed("U8_RANGE", str(n))
    return bytes([n])


def u16(n):
    if not (0 <= n <= 0xFFFF):
        raise malformed("U16_RANGE", str(n))
    return n.to_bytes(2, "big")


def u32(n):
    if not (0 <= n <= 0xFFFFFFFF):
        raise malformed("U32_RANGE", str(n))
    return n.to_bytes(4, "big")


def u64(n):
    if not (0 <= n <= U64_MAX):
        raise malformed("U64_RANGE", str(n))
    return n.to_bytes(8, "big")


def lp(b, limits=PROD_LIMITS):
    if len(b) > limits.max_len:
        raise malformed("LP_TOO_LONG", "%d > max_len %d" % (len(b), limits.max_len))
    return u64(len(b)) + b


def raw32(h):
    if len(h) != 32:
        raise malformed("RAW32_LEN", str(len(h)))
    return h


def DOM(s):
    return s.encode("ascii") + b"\x00"


def dom(cand, name):
    return DOM("skuld-%s-%s-0" % (CAND_INFIX[cand], name))


# =====================================================================================================================
# VALUE (§1) and KEY (§2)
# =====================================================================================================================


def encode_value(v):
    if isinstance(v, bool):                       # bool is an int subclass; refused at the op layer, never here
        raise malformed("VALUE_BOOL", repr(v))
    if isinstance(v, int):
        if v >= 0:
            sign = 0x00
            mag = b"" if v == 0 else v.to_bytes((v.bit_length() + 7) // 8, "big")
        else:
            sign = 0x01
            a = -v
            mag = a.to_bytes((a.bit_length() + 7) // 8, "big")   # non-empty (v<0)
        return bytes([VTYPE_INT, sign]) + lp(mag)
    if isinstance(v, str):
        try:
            body = v.encode("utf-8")                              # utf-8; a lone surrogate cannot be encoded
        except UnicodeEncodeError as e:
            raise malformed("STR_SURROGATE", str(e))             # typed local rejection (0259)
        return bytes([VTYPE_STR]) + lp(body)
    raise malformed("VALUE_TYPE", type(v).__name__)


def encode_key(kind, s):
    kt = KTYPE_EID if kind == "eid" else KTYPE_COMP
    return bytes([kt]) + lp(s.encode("utf-8"))


def chunk(H, d):
    """MSB-first (§2): 51 five-bit chunks (d=0..50), then a 1-bit chunk (d=51)."""
    if d < 0 or d > 51:
        raise malformed("CHUNK_DEPTH", str(d))
    if d <= 50:
        return (H >> (256 - 5 * (d + 1))) & 0x1F
    return H & 0x01


# =====================================================================================================================
# Node ENCODERS (§4). cand in {"A","B"}; B carries u8(level) on ROOT/BRANCH/BUCKET.
# =====================================================================================================================


def enc_empty(cand):
    return dom(cand, "empty") + u16(VERSION) + u8(NODE_EMPTY)


def enc_scalars(alloc, seed, counter):
    return (DOM("skuld-scalars-0") + b"A" + encode_value(alloc)
            + b"S" + encode_value(seed) + b"C" + encode_value(counter))


def _bitmap_children(slot_child):
    """slot_child: dict slot->child_hash(32). Returns (bitmap, concatenated child hashes in ascending slot order)."""
    bitmap = 0
    body = b""
    for slot in sorted(slot_child):
        bitmap |= (1 << slot)
        body += raw32(slot_child[slot])
    return bitmap, body


def enc_root(cand, slot_child, scalars_bytes):
    bitmap, body = _bitmap_children(slot_child)
    out = dom(cand, "root") + u16(VERSION) + u8(NODE_ROOT)
    if cand == "B":
        out += u8(0)                              # level == 0
    out += u32(bitmap) + body + scalars_bytes
    return out


def enc_branch(cand, level, slot_child):
    bitmap, body = _bitmap_children(slot_child)
    out = dom(cand, "branch") + u16(VERSION) + u8(NODE_BRANCH)
    if cand == "B":
        out += u8(level)
    out += u32(bitmap) + body
    return out


def enc_leaf_ent(cand, eid, comp_top_hash):
    return dom(cand, "leafent") + u16(VERSION) + u8(NODE_LEAF_ENT) + encode_key("eid", eid) + raw32(comp_top_hash)


def enc_leaf_comp(cand, comp, value):
    return dom(cand, "leafcomp") + u16(VERSION) + u8(NODE_LEAF_COMP) + encode_key("comp", comp) + encode_value(value)


def enc_bucket(cand, members):
    """members: list of (key_order_bytes, leaf_encoding) already in canonical KEY order."""
    out = dom(cand, "bucket") + u16(VERSION) + u8(NODE_BUCKET)
    if cand == "B":
        out += u8(52)
    out += u32(len(members))
    for _ko, leaf in members:
        out += leaf
    return out


# =====================================================================================================================
# A bounds-checked reader for Tier-1 decode
# =====================================================================================================================


class Reader:
    def __init__(self, buf, limits=PROD_LIMITS):
        self.buf = buf
        self.pos = 0
        self.limits = limits

    def take(self, n):
        if n < 0 or self.pos + n > len(self.buf):
            raise malformed("TRUNCATED", "need %d at %d of %d" % (n, self.pos, len(self.buf)))
        b = self.buf[self.pos:self.pos + n]
        self.pos += n
        return b

    def u8(self):
        return self.take(1)[0]

    def u16(self):
        return int.from_bytes(self.take(2), "big")

    def u32(self):
        return int.from_bytes(self.take(4), "big")

    def u64(self):
        return int.from_bytes(self.take(8), "big")

    def lp(self):
        n = self.u64()
        if n > self.limits.max_len:
            raise malformed("LP_TOO_LONG", "%d > max_len %d" % (n, self.limits.max_len))
        return self.take(n)

    def expect(self, literal, code):
        got = self.take(len(literal))
        if got != literal:
            raise malformed(code, "expected %r got %r" % (literal, got))

    def at_end(self):
        return self.pos == len(self.buf)


def decode_value(r):
    vt = r.u8()
    if vt == VTYPE_INT:
        sign = r.u8()
        mag = r.lp()
        if sign == 0x00:
            if mag and mag[0] == 0x00:
                raise malformed("INT_NONMINIMAL", "leading zero")
            return int.from_bytes(mag, "big")          # b"" -> 0
        if sign == 0x01:
            if not mag:
                raise malformed("INT_NEGZERO", "negative zero")
            if mag[0] == 0x00:
                raise malformed("INT_NONMINIMAL", "leading zero")
            return -int.from_bytes(mag, "big")
        raise malformed("INT_SIGN", hex(sign))
    if vt == VTYPE_STR:
        raw = r.lp()
        try:
            return raw.decode("utf-8")                 # rejects lone surrogates / invalid utf-8
        except UnicodeDecodeError as e:
            raise malformed("STR_UTF8", str(e))
    raise malformed("VTYPE", hex(vt))


def decode_key(r, expect_kind=None):
    kt = r.u8()
    if kt not in (KTYPE_EID, KTYPE_COMP):
        raise malformed("KTYPE", hex(kt))
    if expect_kind == "eid" and kt != KTYPE_EID:
        raise malformed("KTYPE_POS", "expected eid")
    if expect_kind == "comp" and kt != KTYPE_COMP:
        raise malformed("KTYPE_POS", "expected comp")
    raw = r.lp()
    try:
        s = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise malformed("KEY_UTF8", str(e))
    return (kt, s, bytes([kt]) + lp(raw))              # (ktype, string, canonical KEY bytes)


# =====================================================================================================================
# Tier-1 node decode (one node, no descendant resolution). Validates framing/domain/version/type/bitmap/scalars/bucket.
# =====================================================================================================================

_NAME_BY_TYPE = {NODE_EMPTY: "empty", NODE_ROOT: "root", NODE_BRANCH: "branch",
                 NODE_LEAF_ENT: "leafent", NODE_LEAF_COMP: "leafcomp", NODE_BUCKET: "bucket"}


def _match_domain(r, cand):
    """Match one of the six candidate node domains at the cursor; return its name, else reject."""
    for ntype, name in _NAME_BY_TYPE.items():
        d = dom(cand, name)
        if r.buf[r.pos:r.pos + len(d)] == d:
            r.pos += len(d)
            return ntype, name
    raise malformed("DOMAIN", "no skuld-%s-* domain at %d" % (CAND_INFIX[cand], r.pos))


def _read_version(r):
    v = r.u16()
    if v != VERSION:
        raise malformed("VERSION", str(v))


def _read_bitmap_children(r, level):
    bitmap = r.u32()
    if level == 51 and (bitmap & ~0b11):
        raise malformed("BITMAP_HIGH_BITS", "bits above bit1 set at level 51")
    children = []
    for slot in range(32):
        if bitmap & (1 << slot):
            children.append((slot, r.take(32)))        # ascending slot order by construction
    # Tier-1 structural rule (§4a/§8): within a single node, occupied slots reference DISTINCT child hashes.
    # Applies uniformly to ROOT and BRANCH, so a repeated child in a ROOT slot rejects here (DUP_CHILD) rather than
    # downstream as a DUP_KEY consequence. (0258 fix; lawful cross-parent sharing is unaffected.)
    hashes = [h for _s, h in children]
    if len(set(hashes)) != len(hashes):
        raise malformed("DUP_CHILD", "same child hash in two slots of one node")
    return bitmap, children


def _decode_scalars(r):
    r.expect(DOM("skuld-scalars-0"), "SCALARS_DOM")
    out = {}
    for tag, key in ((b"A", "alloc"), (b"S", "seed"), (b"C", "counter")):
        r.expect(tag, "SCALARS_TAG")
        # block D: all three scalars MUST be int VTYPE at Tier-1
        peek = r.buf[r.pos:r.pos + 1]
        if peek != bytes([VTYPE_INT]):
            raise malformed("SCALAR_NOT_INT", "%s vtype %r" % (key, peek))
        out[key] = decode_value(r)
    return out


def read_one_node(r, cand, limits=PROD_LIMITS):
    """Read and Tier-1-validate ONE node from reader r (used both standalone and streamed inside the §4a container).
    Does NOT resolve child hashes (that is Tier-2). Sets _encoding to the exact consumed slice and _address."""
    start = r.pos
    ntype, name = _match_domain(r, cand)
    _read_version(r)
    got_type = r.u8()
    if got_type != ntype:
        raise malformed("NODE_TYPE", "domain %s but type byte %s" % (name, hex(got_type)))

    if ntype == NODE_EMPTY:
        node = {"type": "EMPTY"}

    elif ntype == NODE_ROOT:
        if cand == "B":
            if r.u8() != 0:
                raise malformed("LEVEL_RANGE", "ROOT level must be 0")
        bitmap, children = _read_bitmap_children(r, level=0)
        scalars = _decode_scalars(r)
        node = {"type": "ROOT", "bitmap": bitmap, "children": children, "scalars": scalars}

    elif ntype == NODE_BRANCH:
        level = None
        if cand == "B":
            level = r.u8()
            if not (0 <= level <= 51):
                raise malformed("LEVEL_RANGE", "BRANCH level %d" % level)
        bitmap, children = _read_bitmap_children(r, level if level is not None else -1)
        if bin(bitmap).count("1") < 1:
            raise malformed("BRANCH_EMPTY", "popcount < 1")
        node = {"type": "BRANCH", "level": level, "bitmap": bitmap, "children": children}

    elif ntype == NODE_LEAF_ENT:
        kt, s, kb = decode_key(r, expect_kind="eid")
        comp_top = r.take(32)
        node = {"type": "LEAF_ENT", "eid": s, "key_bytes": kb, "comp_top": comp_top}

    elif ntype == NODE_LEAF_COMP:
        kt, s, kb = decode_key(r, expect_kind="comp")
        value = decode_value(r)
        node = {"type": "LEAF_COMP", "comp": s, "key_bytes": kb, "value": value}

    elif ntype == NODE_BUCKET:
        if cand == "B":
            if r.u8() != 52:
                raise malformed("LEVEL_RANGE", "BUCKET level must be 52")
        count = r.u32()
        if count > limits.max_len:
            raise malformed("BUCKET_COUNT_LIMIT", "%d > max_len" % count)
        if count < 2:
            raise malformed("BUCKET_COUNT", "count %d < 2" % count)
        members = []
        member_types = set()
        for _ in range(count):
            mstart = r.pos
            mtype, mname = _match_domain(r, cand)
            if mtype not in (NODE_LEAF_ENT, NODE_LEAF_COMP):
                raise malformed("BUCKET_MEMBER_TYPE", mname)
            _read_version(r)
            if r.u8() != mtype:
                raise malformed("BUCKET_MEMBER_TYPE", "type byte")
            if mtype == NODE_LEAF_ENT:
                kt, s, kb = decode_key(r, expect_kind="eid")
                r.take(32)
                member_types.add("ENT")
            else:
                kt, s, kb = decode_key(r, expect_kind="comp")
                decode_value(r)
                member_types.add("COMP")
            members.append((kb, r.buf[mstart:r.pos]))
        if len(member_types) != 1:
            raise malformed("BUCKET_MIXED", "mixed leaf types")
        kbs = [kb for kb, _ in members]
        if kbs != sorted(kbs):
            raise malformed("BUCKET_ORDER", "members not in canonical KEY order")
        if len(set(kbs)) != len(kbs):
            raise malformed("BUCKET_DUP_KEY", "duplicate full KEY in bucket")
        node = {"type": "BUCKET", "count": count, "members": members}

    else:  # pragma: no cover
        raise malformed("NODE_TYPE", str(ntype))

    enc = r.buf[start:r.pos]
    node["_encoding"] = enc
    node["_address"] = node_address(enc)
    return node


def decode_node(encoding, cand, limits=PROD_LIMITS, require_end=True):
    """Standalone single-node decode (wraps read_one_node + a trailing-bytes check)."""
    r = Reader(encoding, limits)
    node = read_one_node(r, cand, limits)
    if require_end and not r.at_end():
        raise malformed("TRAILING", "%d trailing bytes" % (len(encoding) - r.pos))
    return node
