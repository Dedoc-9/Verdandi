# evidence/

**Actual run outputs only.** No file here is written by hand, pre-declared, or edited to show a desired result; every
file is produced by executing the gate. Treat the contents as a record of *that run on that host*, nothing more
(MEASURED, not ESTABLISHED; not independently reproduced by the owner).

| committed file | produced by | contents |
|---|---|---|
| `latest.json` | `run_gate.py` | run command, interpreter/platform, env, frozen-ecs sha256, per-gate verdicts, totals, exit status, and the sha256 of every package source file (the authoritative, structured evidence) |
| `latest.txt` | snapshot of `run_gate.py`'s transcript | the full console transcript of the gate run |
| `plants.txt` | snapshot of `verify_plants.py`'s output | the validity check: each planted defect and the FAIL count it produced (every plant must BITE) |

**Note on the transcripts.** The repository's `.gitignore` excludes `*.log`, so the scripts' own local outputs
`latest.log` / `plants.log` are not committed; the committed `latest.txt` / `plants.txt` are the frozen snapshot of the
final run. `latest.json` (the structured evidence) is committed directly and carries the per-gate verdicts and the
source hashes, so it is the authoritative record; the `.txt` transcripts are the human-readable companion.

Regenerate and re-snapshot:

```bash
PYTHONHASHSEED=0 PYTHONUTF8=1 python p1-oracle/run_gate.py
PYTHONHASHSEED=0 PYTHONUTF8=1 python p1-oracle/verify_plants.py > p1-oracle/evidence/plants.log 2>&1
cp p1-oracle/evidence/latest.log p1-oracle/evidence/latest.txt
cp p1-oracle/evidence/plants.log p1-oracle/evidence/plants.txt
```

A gate run exits 0 iff there are zero FAILs. `BLOCKED` rows (D4-2 effects-root, below-boundary anchor, D8 trust) are
not passes and do not fail the run; they record what this milestone cannot verify. Each `latest.json` records the
sha256 of every committed source file, so you can confirm the run corresponds to the exact files
(`git show HEAD:p1-oracle/oracle/decoder.py | sha256sum` against `source_sha256["oracle/decoder.py"]`).
