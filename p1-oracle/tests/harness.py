"""Tiny stdlib test harness. Each test module exposes run() -> list of (name, verdict, detail);
verdict in {'PASS','FAIL','BLOCKED'}. 'PASS' for a negative test means the bad input was correctly REJECTED."""
from oracle import decoder as d


def reject(fn, code=None, category=d.MALFORMED):
    """Assert fn() raises an OracleError of the given category (and code, if named). Returns the error on success."""
    try:
        fn()
    except d.OracleError as e:
        if category is not None and e.category != category:
            raise AssertionError("expected %s, got %s/%s" % (category, e.category, e.code))
        if code is not None and e.code != code:
            raise AssertionError("expected code %s, got %s" % (code, e.code))
        return e
    raise AssertionError("expected rejection (%s/%s); nothing raised" % (category, code))


class Cases:
    def __init__(self):
        self.rows = []

    def ok(self, name, fn, detail=""):
        try:
            r = fn()
            self.rows.append((name, "PASS", detail or (r if isinstance(r, str) else "")))
        except Exception as e:  # noqa: BLE001 - a failed assertion/parse is a FAIL row, reported, never hidden
            self.rows.append((name, "FAIL", "%s: %s" % (type(e).__name__, e)))

    def blocked(self, name, detail):
        self.rows.append((name, "BLOCKED", detail))

    def done(self):
        return self.rows
