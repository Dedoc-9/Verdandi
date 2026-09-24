# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""envelope.py — RECORD-0: the envelope every record Verðandi mints is written in, and the firewall it is read through.

A fork of `witness_core.Artifact` (Dedoc-9/executable-epistemics) for a repository whose records are written by
two languages and read by one gate. The rules, kept:

    a record is  { name, version, claim_class, provenance, validity_scope, forbidden_interpretations, data,
                   reading, chain_hash }
    claim_class          one of measured | established | declared | predicted
    validity_scope       a dict with a non-empty `certifies` (what this record vouches for, and for what inputs)
    forbidden_interpretations   a non-empty list of readings the record must not be given
    data                 the measurement — and NO VERDICT-SHAPED KEY anywhere inside it (scanned recursively);
                         a comparison against a budget is two numbers in data and a sentence in `reading`
    chain_hash           sha256 of the canonical JSON of the seven required fields; `reading` stays outside it

Canonical JSON (the Rust twin in workshop/edit.rs writes the same bytes): UTF-8; object keys sorted by code
point; no whitespace; integers only; strings escaped as \\" \\\\ \\n \\r \\t \\b \\f and \\u00xx (lowercase) for other
control characters, everything else raw. Two writers, one gate: `records-twins` proves they agree.
"""
from __future__ import annotations

import hashlib
import json

CLAIM_CLASSES = ("measured", "established", "declared", "predicted")
REQUIRED = ("name", "version", "claim_class", "provenance", "validity_scope", "forbidden_interpretations", "data")
# witness_core's set, extended for a gate that prints PASS/FAIL and must never see them stored as data
VERDICT_KEYS = frozenset({"verdict", "valid", "passed", "healthy", "anomaly", "correct", "legal", "safe", "approved",
                          "score_is_good", "ok", "pass", "fail", "failed", "status", "within", "over"})


class EnvelopeViolation(Exception):
    pass


def canonical(value) -> str:
    """The canonical text of a JSON value (see the module docstring)."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def chain_hash(record: dict) -> str:
    return hashlib.sha256(canonical({k: record[k] for k in REQUIRED}).encode("utf-8")).hexdigest()


def _scan(node, path: str):
    if isinstance(node, dict):
        for k, v in node.items():
            if str(k).lower() in VERDICT_KEYS:
                raise EnvelopeViolation(f"verdict_field:{path}.{k}")
            _scan(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _scan(v, f"{path}[{i}]")
    elif isinstance(node, float):
        raise EnvelopeViolation(f"float:{path}")


def validate(record: dict) -> None:
    """Raise EnvelopeViolation with a reason, or return None."""
    for k in REQUIRED:
        if k not in record or record[k] in (None, "", [], {}):
            raise EnvelopeViolation(f"missing_or_empty:{k}")
    if record["claim_class"] not in CLAIM_CLASSES:
        raise EnvelopeViolation(f"claim_class:{record['claim_class']}")
    if not isinstance(record["validity_scope"], dict) or not record["validity_scope"].get("certifies"):
        raise EnvelopeViolation("validity_scope.certifies required")
    if not isinstance(record["forbidden_interpretations"], list) or not all(isinstance(x, str) and x for x in record["forbidden_interpretations"]):
        raise EnvelopeViolation("forbidden_interpretations must be a non-empty list of strings")
    if not isinstance(record["version"], int):
        raise EnvelopeViolation("version must be an integer")
    _scan(record["data"], "data")
    if "chain_hash" not in record:
        raise EnvelopeViolation("missing:chain_hash")
    if record["chain_hash"] != chain_hash(record):
        raise EnvelopeViolation("chain_hash does not match the required fields")


def seal(name: str, version: int, claim_class: str, provenance: dict, validity_scope: dict,
         forbidden_interpretations: list, data: dict, reading: str) -> dict:
    """Build a record, validate it, and seal its chain hash."""
    rec = {"name": name, "version": version, "claim_class": claim_class, "provenance": provenance,
           "validity_scope": validity_scope, "forbidden_interpretations": list(forbidden_interpretations),
           "data": data, "reading": reading}
    rec["chain_hash"] = chain_hash(rec)
    validate(rec)
    return rec


def write(path: str, rec: dict) -> None:
    validate(rec)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def read(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        rec = json.load(fh)
    validate(rec)
    return rec
