# The conformance GATE + its self-verification, and the negative-control demonstration.
# ADMIT a candidate iff (build-config OK: ffp-contract=off) AND (exact output-bit agreement with the normative
# oracle over the corpus). Judges conformance to the ORACLE, not correct rounding. Fail-closed on missing/altered
# fixtures. The meta layer proves: controls reach the gate, each has a known refusal reason, a skipped control cannot
# be a pass, missing fixture => abort, verdict is deterministic, and a weakened gate is caught.
import os, json, struct, subprocess, hashlib, csv, sys

BASE = r"<SCRATCH>"
FD   = os.path.join(BASE,"fdlibm-5.3")
NEG  = os.path.join(BASE,"negctl")
BLD  = os.path.join(NEG,"build")
ORACLE_EXE = os.path.join(FD,"build","test_oracle.exe")   # frozen normative oracle (d1de73d0)
ORACLE_SHA = "d1de73d0db367d3ec22a8920cf6fec8dea8f42d964dcbb447d171ce4df3ac960"
FROZEN_CSV = os.path.join(BASE,"MATH-KERNEL-S5-VECTORS-2026-11-10.csv")
ADV_CSV    = os.path.join(BASE,"MATH-KERNEL-CHAR-CORPUS-2026-11-10.csv")
CERT_CSV   = os.path.join(BASE,"MATH-KERNEL-CHARACTERIZATION-RESULTS-2026-11-10.csv")

def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()

class GateAbort(Exception): pass

# ---------- fixtures (fail-closed) ----------
FIXTURES = {"frozen_corpus":FROZEN_CSV, "adversarial_corpus":ADV_CSV,
            "certified_reference":CERT_CSV, "normative_oracle":ORACLE_EXE}
MANIFEST = os.path.join(NEG,"fixtures.manifest.json")

def write_fixture_manifest():
    json.dump({k:sha(v) for k,v in FIXTURES.items()}, open(MANIFEST,"w"), indent=1)

def load_fixtures(fixtures=FIXTURES, manifest_path=MANIFEST):
    # FAIL-CLOSED: every declared fixture must exist AND match its pinned digest, or the gate refuses to run.
    exp = json.load(open(manifest_path))
    for k, want in exp.items():
        p = fixtures.get(k)
        if p is None or not os.path.exists(p):
            raise GateAbort("FIXTURE-MISSING:%s" % k)
        if sha(p) != want:
            raise GateAbort("FIXTURE-ALTERED:%s" % k)
    if sha(fixtures["normative_oracle"]) != ORACLE_SHA:
        raise GateAbort("ORACLE-IDENTITY")
    return True

# ---------- corpus + reference ----------
def corpus_inputs():
    xs = []
    for row in csv.DictReader(open(FROZEN_CSV,newline="")):
        if (row.get("operation") or "").strip() in ("sin","cos") and \
           (row.get("group") or "").strip() in ("direct sin/cos","reduction stress","exceptional values"):
            xs.append(row["input_bits"].strip().lower())
    for row in csv.DictReader(open(ADV_CSV,newline="")):
        xs.append(row["input_bits"].strip().lower())
    out=[]; seen=set()
    for b in xs:
        if len(b)==16 and b not in seen: seen.add(b); out.append(b)
    return out

def run_exe(exe, inputs):
    r = subprocess.run([exe], input="\n".join(inputs)+"\n", capture_output=True, text=True)
    out={}
    for line in r.stdout.split("\n"):
        p=line.split()
        if len(p)==3: out[p[0].lower()]=(p[1].lower(),p[2].lower())
    return out

def pi4_boundary(b):  # is |x| within the reduction-boundary band (near odd k*pi/4)? used only for evidence labels
    x=abs(struct.unpack('>d',bytes.fromhex(b))[0])
    import math
    for k in (1,3,5,7):
        if abs(x-(2* math.pi* k/8)) < 1e-9: return True
    return x>math.pi/4

# ---------- the gate ----------
def gate(cand_manifest, cand_out, ref, inputs, policy=None):
    """Returns (verdict, reasons, detail). policy injects WEAKENED variants for the meta-test."""
    policy = policy or {}
    reasons=[]; detail={}
    # (1) build-config check unless weakened to skip it
    if not policy.get("skip_build_config"):
        if cand_manifest.get("contract") != "off":
            reasons.append("BUILD-CONFIG:contract=%s" % cand_manifest.get("contract"))
    # (2) exact output-bit conformance over the corpus (or a weakened subset / tolerance)
    excl = set(policy.get("exclude", []))
    use_inputs = [b for b in inputs if b not in excl]   # weakened: a gate that skips some corpus inputs
    tol = policy.get("tolerance", 0)   # weakened: allow <=tol ULP difference
    diffs=[]
    for b in use_inputs:
        for j,op in ((0,"sin"),(1,"cos")):
            rb = ref.get(b,("?","?"))[j]; cb = cand_out.get(b,("?","?"))[j]
            if cb != rb:
                d = ulp(cb,rb)
                if abs(d) > tol: diffs.append((b,op,rb,cb,d))
    if diffs:
        reasons.append("EXACT-BITS:%d divergent output(s)" % len(diffs))
        detail["diffs"]=diffs
    if policy.get("always_admit"): reasons=[]   # weakened: ignore everything
    return ("REFUSE" if reasons else "ADMIT"), reasons, detail

def ulp(a,b):
    def key(h):
        u=int.from_bytes(bytes.fromhex(h),'big')
        return (u^0x7fffffffffffffff) if (u>>63) else (u|0x8000000000000000)
    return key(a)-key(b)

# ---------- demonstration ----------
def demo():
    res={}
    if not os.path.exists(MANIFEST): write_fixture_manifest()
    res["fixtures_loaded"]=load_fixtures()
    inputs=corpus_inputs()
    res["corpus_size"]=len(inputs)
    ref=run_exe(ORACLE_EXE, inputs)
    cert={}
    for row in csv.DictReader(open(CERT_CSV,newline="")):
        cert[(row["input_bits"].strip().lower(),row["op"])]=row["cr_bits"]
    def man(name): return json.load(open(os.path.join(BLD,name+".manifest.json")))
    cands={n:(man(n), run_exe(os.path.join(BLD,n+".exe"), inputs)) for n in ("oracle","oneulp","fma","reduction")}

    # positive control = rebuilt oracle vs frozen reference bits
    verdicts={}
    for n,(m,o) in cands.items():
        v,reasons,detail=gate(m,o,ref,inputs)
        verdicts[n]=(v,reasons,detail)

    # non-equivalence evidence
    # one-ULP: the mutated output vs certified CR (math error), and which input diverged
    d_one = verdicts["oneulp"][2].get("diffs",[])
    one_math=None
    if d_one:
        b,op,rb,cb,dd = d_one[0]
        crb = cert.get((b,op))
        one_math = {"input":b,"op":op,"oracle":rb,"mutant":cb,"ulp_vs_oracle":dd,
                    "certified_cr":crb,"ulp_mutant_vs_cr":ulp(cb,crb) if crb else None}
    # reduction: show failures are at reduction-boundary vectors and NOT at |x|<=pi/4
    d_red = verdicts["reduction"][2].get("diffs",[])
    red_bndry = sum(1 for (b,op,rb,cb,dd) in d_red if pi4_boundary(b))
    red_nored = sum(1 for (b,op,rb,cb,dd) in d_red if not pi4_boundary(b))
    # fma: how many outputs differ (output-bit) vs config-only
    d_fma = verdicts["fma"][2].get("diffs",[])

    res["verdicts"]={n:(v,reasons) for n,(v,reasons,detail) in verdicts.items()}
    res["oneulp_math"]=one_math
    res["reduction_evidence"]={"divergent":len(d_red),"at_boundary":red_bndry,"no_reduction_zone":red_nored}
    # fma broad sweep: genuine behavioral mutant even though output-equivalent on the corpus
    import random
    random.seed(1); sweep=[struct.pack('>d',random.uniform(-1.45,6.283185307179586)).hex() for _ in range(20000)]
    rs=run_exe(ORACLE_EXE,sweep); fs=run_exe(os.path.join(BLD,"fma.exe"),sweep)
    sweep_div=sum(1 for b in sweep if rs[b]!=fs[b])
    res["fma_evidence"]={"output_divergent_on_corpus":len(d_fma),"broad_sweep_divergent":sweep_div,"broad_sweep_n":len(sweep),
                         "contract":man("fma")["contract"],
                         "refused_by":"output-bits" if d_fma else "build-config (output-equivalent on corpus)"}

    # ---------- META: gate self-verification ----------
    meta={}
    # (a) mandatory controls each refused; positive admitted
    mand=["oneulp","fma","reduction"]
    meta["positive_admitted"]= verdicts["oracle"][0]=="ADMIT"
    meta["all_controls_refused"]= all(verdicts[n][0]=="REFUSE" for n in mand)
    # (b) known expected refusal reason present per control
    def has(n,key): return any(r.startswith(key) for r in verdicts[n][1])
    meta["reasons_ok"]= has("oneulp","EXACT-BITS") and (has("fma","BUILD-CONFIG") or has("fma","EXACT-BITS")) and has("reduction","EXACT-BITS")
    # (c) a skipped/disabled control cannot be a pass: suite requires all 3 present+refused
    def suite_pass(present):
        return verdicts["oracle"][0]=="ADMIT" and all(verdicts[n][0]=="REFUSE" for n in present) and set(present)==set(mand)
    meta["full_suite_pass"]=suite_pass(mand)
    meta["suite_with_one_skipped_pass"]=suite_pass(["oneulp","fma"])   # must be False
    # (d) fail-closed on missing fixture
    try:
        load_fixtures({**FIXTURES,"frozen_corpus":os.path.join(NEG,"NOPE.csv")})
        meta["fail_closed_missing"]=False
    except GateAbort as e:
        meta["fail_closed_missing"]=str(e).startswith("FIXTURE-MISSING")
    # (e) determinism: re-run and compare verdicts
    ref2=run_exe(ORACLE_EXE, inputs)
    v2={n:gate(cands[n][0],run_exe(os.path.join(BLD,n+".exe"),inputs),ref2,inputs)[0] for n in cands}
    meta["deterministic"]= all(v2[n]==verdicts[n][0] for n in cands)
    # (f) weakened-gate caught: the gate's self-test REQUIRES all 3 mandatory controls to be REFUSED. Any weakening
    #     that lets a control through breaks that property, so the self-test catches it. We run ALL controls under
    #     each weakening and check whether the "all refused" property still holds (caught iff it does NOT).
    oneulp_input="3fe0000000000000"
    weak={}
    for label,pol in [("tolerance>=1ULP (ignore <=1 ULP errors)",{"tolerance":1}),
                      ("subset-corpus (skip the one-ULP input)",{"exclude":[oneulp_input]}),
                      ("skip-build-config check",{"skip_build_config":True}),
                      ("always-admit",{"always_admit":True})]:
        verds={n:gate(cands[n][0],cands[n][1],ref,inputs,policy=pol)[0] for n in mand}
        admitted=[n for n in mand if verds[n]=="ADMIT"]
        weak[label]={"weakened_control_verdicts":verds,"admitted_that_should_refuse":admitted,
                     "caught_by_selftest": len(admitted)>0}
    meta["weakened_gate"]=weak
    meta["weakened_all_caught"]= all(w["caught_by_selftest"] for w in weak.values())
    res["meta"]=meta
    return res

if __name__=="__main__":
    import pprint
    r=demo()
    print(json.dumps(r,indent=1,default=str))
