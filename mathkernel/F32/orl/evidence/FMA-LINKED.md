# Fused multiply-add instructions in the linked test programs (2026-11-14)

Paths are relative to `mkf/orl/`. Run on the local Windows host; clang 22.1.8, target x86_64-pc-windows-msvc, static C
runtime (libcmt / libucrt), llvm-objdump of the same LLVM. The originals in `gen/` and `wd/cache/` were read, never
written.

## Statement checked

> The linked test programs `gen/sweep.exe` and `gen/sweep2.exe` contain a few fused multiply-add instructions, all
> inside C runtime library code and none in the functions that compute the results under test; the object files
> compiled from `sweep.c` and `sweep2.c` alone contain none.

Result: **holds as far as the checks below reach** (MEASURED for the counts and their locations; ARGUED for
reachability; limits in the last section).

## Counts (MEASURED)

Instructions whose mnemonic matches `vfmadd* / vfmsub* / vfnmadd* / vfnmsub*` in `llvm-objdump -d`:

| file | sha256 (first 16) | instructions disassembled | vfmadd | vfmsub | vfnmadd | vfnmsub | total |
|---|---|---|---|---|---|---|---|
| `gen/sweep.exe` (original) | 6ed70f8f6d803d53 | 35246 | 8 | 1 | 0 | 0 | **9** |
| `gen/sweep2.exe` (original) | ef9d229ae44cc401 | 34024 | 14 | 1 | 0 | 0 | **15** |
| `evidence/fma/sweep.exe` (rebuilt, with map) | 6474e46338058864 | 35246 | 8 | 1 | 0 | 0 | 9 |
| `evidence/fma/sweep2.exe` (rebuilt, with map) | 36ef449b8cc888b8 | 34024 | 14 | 1 | 0 | 0 | 15 |
| `gen/sweep.o`, `evidence/fma/sweep.o` | f0b2a515…, d7ca1208… | | 0 | 0 | 0 | 0 | **0** |
| `gen/sweep2.o`, `evidence/fma/sweep2.o` | 4074024c…, 3bf311d5… | | 0 | 0 | 0 | 0 | **0** |
| `wd/cache/c99-60e5e095c4d1301f156b2ee5.exe` (Orlog, exp32, C99) | 72f48f8c553fe515 | 26487 | 0 | 0 | 0 | 0 | **0** |
| `wd/cache/rust-a44fe97bfe25f50e67f7d04c.exe` (Orlog, exp32, Rust) | 29cff71a7b4a8ae9 | 171041 | 0 | 0 | 0 | 0 | **0** |

The rebuilt programs are not byte-identical to the originals (the file hashes differ; a linked PE carries a
timestamp), but their code is: the full `llvm-objdump -d` listing, raw bytes included, of each original equals that of
its rebuild (sha256 of the listing without its two header lines: sweep `3d6fd33b…`, sweep2 `274207be…`, the same for
original and rebuild). The same holds for the object files with their relocations (`-d -r`: sweep `9885cfa2…`, sweep2
`4cb7cced…`). So the map of a rebuild names the addresses of the original.

For the two Orlog programs no map exists and none was made (they were not rebuilt): the count is all that is reported,
and it is zero, so there is nothing to attribute.

## Where each instruction is (MEASURED, from the linker map)

`sweep.exe`, 9 instructions, all in `libucrt:log10.obj`:

| address | instruction | function (map symbol) |
|---|---|---|
| 14001cf3f, 14001cf48, 14001cf55 | vfmadd213sd | `Llog10_fma3_continue_common` |
| 14001cf62, 14001cf67 | vfmadd231sd | `Llog10_fma3_continue_common` |
| 14001cf7c | vfmsub213sd | `Llog10_fma3_continue_common` |
| 14001cf97 | vfmadd231sd | `Llog10_fma3_continue_common` |
| 14001cfe4, 14001cfed | vfmadd213sd | `Llog10_fma3_near_one` |

`sweep2.exe`, 15 instructions: the same 9 of `log10` (at 14001be4f … 14001befd, same labels), and 6 in
`libucrt:exp.obj`:

| address | instruction | function (map symbol) |
|---|---|---|
| 14000b559 | vfmadd231sd | `Lexp_fma3_y_is_finite` |
| 14000b582, 14000b58b, 14000b594, 14000b59d, 14000b5aa | vfmadd213sd | `Lexp_fma3_y_is_finite` |

These labels are local labels inside the runtime's `log10` (map: `log10`, `libucrt:log10.obj`) and `exp` (`exp`,
`libucrt:exp.obj`). Nothing compiled from `sweep.c` or `sweep2.c` holds one: the program's own object occupies
`main` .. `__local_stdio_scanf_options` (sweep: 140001000..140001ed8) and every FMA address is far outside it, in
objects the map attributes to libucrt.

## Can the code under test reach them? (ARGUED, on measured facts)

Surprise against the statement as first imagined: in `sweep.exe` the FMA code is not `exp`, `sqrt` or `nextafter`
(sweep.c calls no `exp`) but `log10`, pulled in by `printf`.

1. **The code under test calls nothing.** `evidence/fma_undertest.py` copies only the constants, `narrow` and
   `f_sqrt32 / f_rsqrt32 / f_hypot32` (from sweep.c) or `g_exp32` (from sweep2.c) into `fma/undertest_*.c`, compiles
   them with the same options, and reports for each object: undefined symbols `_fltused` only; relocations only to
   floating constants (`__real@…`, `__xmm@…`); **0 call instructions, 0 indirect jumps, 0 FMA instructions**; the
   square roots are 3 inline `sqrtsd`. Code that makes no call and no jump out of itself cannot enter `log10` or `exp`.
2. **Who does enter them.** In the linked programs (`fma_scan.py`, direct call and jump targets):
   - `exp` is called from one site, `main`+0x3ce in `sweep2.exe`; `sweep2.o` has exactly one relocation to `exp`, and
     `sweep2.c` has exactly one call, line 56, `double e = exp(x), el = …` — the comparison side (the reference the
     result is judged against). `g_exp32` itself contains no `exp`.
   - `log10` is called from one site in each program, inside `__acrt_fltout` (`libucrt:cfout.obj`), the runtime's
     conversion of a floating value to decimal for `printf`. The programs' format strings hold only `%s`, `%08x`,
     `%llu`, `%016llx` (no floating conversion), so by the source this path is not taken at all; that it is not taken
     was not measured at run time.
   - The FMA labels themselves are entered only from inside their own function (`Lexp_fma3` → `Lexp_fma3_y_is_finite`;
     `Llog10_fma3_denormal_adjust` / `_continue_common` → the two log10 labels).
3. **Classification.**

| function holding FMA | program | callable from narrow, f_sqrt32, f_rsqrt32, f_hypot32, g_exp32 | reached from |
|---|---|---|---|
| runtime `exp` (FMA3 path) | sweep2.exe | no | comparison side only: the reference `exp(x)` in the sweep loop |
| runtime `log10` (FMA3 path) | sweep.exe, sweep2.exe | no | runtime only: `printf`'s floating conversion (`__acrt_fltout`), which these programs' formats do not use |

The other comparison-side and start-up routines named in the task (`sqrt`, `sqrtf`, `nextafter`, `nextafterf`,
`frexp`, `ldexp`, start-up code) hold no FMA instruction in either program: `sqrt` and `sqrtf` are not linked as
functions at all (neither is an undefined symbol of `sweep.o` / `sweep2.o`; they are inline `sqrtsd` / `sqrtss`).

Note: with `-O2` the functions under test are inlined into `main`, so in the linked program "the function under test"
is a region of `main`, not a symbol. What stands for it is: `main`'s whole object has 0 FMA instructions (table
above), and the under-test source compiled alone has none and calls nothing (item 1).

## Run-time CPU feature check (MEASURED in the disassembly)

Yes. Both runtime functions begin with a test of the runtime's flag `__use_fma3_lib` (`libucrt:fma3_available.obj`)
and take the FMA path only when it is non-zero; otherwise they run the SSE2 path (`Llog10_sse2…`, `Lexp_…`):

```
exp   (sweep2.exe)  14000b2bf: cmpl $0x0, __use_fma3_lib ; 14000b2c6: jne Lexp_fma3   (14000b500)
log10 (sweep2.exe)  14001ba8a: cmpl $0x0, __use_fma3_lib ; 14001ba91: jne Llog10_fma3 (14001bd80)
```

The flag is written only by `__acrt_initialize_fma3`, which executes `cpuid` (three times) and `xgetbv` before
setting it. So the instructions are executed only on a processor (and operating system state) the runtime found to
support FMA3. Whether this host takes the FMA path was not determined and is not recorded here. Consequence for the
exp32 sweep: the reference `exp(x)` may be computed by different instruction sequences on different processors; the
sweep's comparison allows the reference a relative 2^-40 either way, and nothing here measures the runtime `exp`'s
error on either path.

## Commands

From `evidence/fma/` (F = `-O2 -ffp-contract=off -fno-math-errno -D_CRT_SECURE_NO_WARNINGS`; the originals' recorded
build line has no `-D_CRT_SECURE_NO_WARNINGS`, which changes diagnostics only: the code listings are equal, above):

```
clang F -c ../../gen/sweep.c  -o sweep.o          clang F -c ../../gen/sweep2.c -o sweep2.o
clang F ../../gen/sweep.c  -o sweep.exe  -Wl,/map:sweep.map
clang F ../../gen/sweep2.c -o sweep2.exe -Wl,/map:sweep2.map
clang F ../../gen/sweep.c  -o sweep-nomap.exe     clang F ../../gen/sweep2.c -o sweep2-nomap.exe
llvm-objdump -d --no-show-raw-insn FILE | grep -cE '\bvfn?m(add|sub)'       # every file of the first table
llvm-objdump -d ../../gen/sweep.exe | sed 1,2d | sha256sum                  # against the same of sweep.exe; and sweep2
llvm-objdump -d -r ../../gen/sweep.o | sed 1,2d | sha256sum                 # against the same of sweep.o; and sweep2
llvm-nm -u sweep.o sweep2.o
llvm-objdump -d --no-show-raw-insn sweep.exe > sweep.dis                    # and sweep2.dis
python -B ../fma_scan.py sweep.exe sweep.map                                # and sweep2: owner of each instruction, entries
python -B ../fma_undertest.py                                               # the code under test alone
grep -n '14002cb8c' sweep2.dis                                              # the uses of __use_fma3_lib
```

No debug information was added: a map was enough, and it leaves the code as it was.

## What remains unproven

- **Indirect calls are not followed.** The reachability argument uses direct call and jump targets only; the programs
  hold indirect calls (173 `call *` in sweep2.exe, all outside the under-test code, which has none). That no pointer
  leads from the comparison or start-up code into `log10` other than through `__acrt_fltout` is not shown — it would
  not matter to the statement, since the code under test makes no call of any kind.
- **Inlined code is argued, not isolated.** The under-test functions are inlined into `main`; that the inlined copies
  are instruction-for-instruction the stand-alone ones was not compared. What is measured is that `main`'s object has
  no FMA instruction at all.
- **A linear disassembly.** The counts are of what `llvm-objdump -d` decodes, by mnemonic, in executable sections. An
  FMA encoding in bytes it decodes as something else (data in code, a misaligned decode) or reached only by a jump
  into the middle of an instruction would not be counted. The raw bytes were not searched for VEX FMA opcodes.
- **Only these four mnemonic families.** Scalar and packed forms are matched; other fused or contracted operations
  (AVX-512 forms with other names, x87) were not looked for.
- **Not executed.** Nothing here ran the programs under a tracer: that the `log10` path is never taken, and which
  `exp` path this host takes, are read from source and disassembly, not observed.
- **The Orlog programs**: counts only. How they were built, and what their code under test is, were not examined here.
- **Other programs in `gen/`** (`plant_*.exe`, `plant2_unfaithful.exe`) and the other files of `wd/cache/` were not
  scanned.
- The run is on one host with one toolchain; another C runtime version may place FMA code elsewhere.

## Files

`evidence/fma_scan.py`, `evidence/fma_undertest.py`; `evidence/fma/`: `sweep.o`, `sweep2.o`, `sweep.exe`, `sweep2.exe`,
`sweep.map`, `sweep2.map`, `sweep-nomap.exe`, `sweep2-nomap.exe`, `sweep.dis`, `sweep2.dis`, `undertest_sweep.c/.o`,
`undertest_sweep2.c/.o`.
