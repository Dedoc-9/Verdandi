# Build the positive control + 3 mandatory negative controls as real clang builds, each with a build manifest.
# Frozen originals in fdlibm-5.3/ are READ-ONLY and untouched; mutant sources are new files under negctl/src/.
import os, struct, subprocess, hashlib, json, shutil, math
BASE = r"<SCRATCH>"
FD   = os.path.join(BASE, "fdlibm-5.3")
NEG  = os.path.join(BASE, "negctl")
SRC  = os.path.join(NEG, "src")
BLD  = os.path.join(NEG, "build")
for d in (NEG, SRC, BLD): os.makedirs(d, exist_ok=True)

def sha(p):
    return hashlib.sha256(open(p,'rb').read()).hexdigest()

FROZEN6 = ["s_sin.c","s_cos.c","k_sin.c","k_cos.c","e_rem_pio2.c","k_rem_pio2.c"]
DRIVER  = os.path.join(FD, "test_oracle.c")
FLAGS_OK  = ["-std=c99","-O2","-ffp-contract=off","-fno-fast-math","-D__LITTLE_ENDIAN"]
FLAGS_FMA = ["-std=c99","-O2","-ffp-contract=fast","-mfma","-fno-fast-math","-D__LITTLE_ENDIAN"]  # forbidden contraction ON (hw FMA enabled)
INC = ["-I", FD]

# ---- mutant_oneulp.c: driver that alters ONE selected sin output by +1 ULP (input x=0.5 = 0x3fe0000000000000) ----
drv = open(DRIVER).read()
one = drv.replace(
    "        double s = sin(x);\n        double c = cos(x);",
    "        double s = sin(x);\n        double c = cos(x);\n"
    "        if (in == 0x3fe0000000000000ULL) {   /* ONE-ULP corruption of a selected output */\n"
    "            uint64_t sbb = double_to_bits(s); sbb += 1; s = bits_to_double(sbb);\n"
    "        }")
assert one != drv, "oneulp patch did not apply"
open(os.path.join(SRC,"mutant_oneulp.c"),"w",newline="\n").write(one)

# ---- mutant_rem_pio2.c: e_rem_pio2.c with pio2_1 corrupted by +1 ULP (reduction-constant defect) ----
# pio2_1 (the main high part of pi/2) enters r = t - fn*pio2_1 for EVERY reduced argument (|x|>pi/4), so a 1-ULP
# corruption fails the reduction path broadly while sparing the no-reduction zone |x|<=pi/4. (A 1-ULP change to the
# tiny low part pio2_1t was an equivalent mutant on this corpus - MEASURED, excluded.)
rem = open(os.path.join(FD,"e_rem_pio2.c")).read()
old_pio2_1 = struct.unpack('>d', bytes.fromhex('3ff921fb54400000'))[0]
new_pio2_1 = math.nextafter(old_pio2_1, math.inf)     # +1 ULP -> 0x3ff921fb54400001
new_bits = struct.pack('>d', new_pio2_1).hex()
assert new_bits == '3ff921fb54400001', new_bits
old_line = "pio2_1  =  1.57079632673412561417e+00, /* 0x3FF921FB, 0x54400000 */"
new_line = "pio2_1  =  %r, /* MUTATED +1 ULP from 0x3FF921FB54400000 -> 0x3FF921FB54400001 */" % new_pio2_1
assert old_line in rem, "pio2_1 line not found verbatim"
rem2 = rem.replace(old_line, new_line)
open(os.path.join(SRC,"mutant_rem_pio2.c"),"w",newline="\n").write(rem2)

def build(name, sources, flags, extra_inc=None):
    out = os.path.join(BLD, name + ".exe")
    cmd = ["clang"] + flags + (extra_inc or INC) + sources + ["-o", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    ok = (r.returncode == 0 and os.path.exists(out))
    manifest = {"name": name, "flags": flags,
                "contract": "off" if "-ffp-contract=off" in flags else ("fast" if "-ffp-contract=fast" in flags else "?"),
                "sources": {os.path.basename(s): sha(s) for s in sources},
                "exe_sha256": sha(out) if ok else None,
                "build_returncode": r.returncode, "build_ok": ok}
    json.dump(manifest, open(os.path.join(BLD, name+".manifest.json"),"w"), indent=1)
    return ok, out, manifest, (r.stderr or "")[:300]

frozen_paths = [os.path.join(FD,f) for f in FROZEN6]
builds = {}
# positive control candidate = the normative oracle, rebuilt here; must reproduce d1de73d0 (reproducibility)
builds['oracle']  = build("oracle",  frozen_paths + [DRIVER], FLAGS_OK)
# one-ULP: 6 frozen + mutant driver
builds['oneulp']  = build("oneulp",  frozen_paths + [os.path.join(SRC,"mutant_oneulp.c")], FLAGS_OK)
# FMA: same sources as oracle, contraction ON
builds['fma']     = build("fma",     frozen_paths + [DRIVER], FLAGS_FMA)
# reduction: 5 frozen + mutant e_rem_pio2 + driver
red_sources = [os.path.join(FD,f) for f in FROZEN6 if f!="e_rem_pio2.c"] + [os.path.join(SRC,"mutant_rem_pio2.c"), DRIVER]
builds['reduction'] = build("reduction", red_sources, FLAGS_OK)

# ---- report build identities + reproducibility + reach probe ----
ORACLE_FROZEN = "d1de73d0db367d3ec22a8920cf6fec8dea8f42d964dcbb447d171ce4df3ac960"
for k,(ok,out,man,err) in builds.items():
    print("%-10s build_ok=%s exe=%s" % (k, ok, (man['exe_sha256'] or 'FAIL')[:16]), '' if ok else ('ERR: '+err))
print("positive-control reproduces frozen oracle d1de73d0:",
      builds['oracle'][2]['exe_sha256']==ORACLE_FROZEN)
# reach probe: each exe must RUN and emit a line (not a build error) on a sample input
probe = "3fe0000000000000\n3ff921fb54442d18\n"
print("--- reach probe (each candidate runs & emits output) ---")
for k,(ok,out,man,err) in builds.items():
    if not ok: print(k, "NOT BUILT"); continue
    r = subprocess.run([out], input=probe, capture_output=True, text=True)
    lines = [l for l in r.stdout.split('\n') if l.strip()]
    print("%-10s reached=%s lines=%d first=%s" % (k, len(lines)==2, len(lines), lines[0] if lines else '(none)'))
