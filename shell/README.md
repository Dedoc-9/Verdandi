<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `shell/` — the window

Contract: own the window, the input pump and the presentation of the kernel's framebuffer; contain no kernel
logic and no mirror of the authority; be replaceable. The shell blits pixels the kernel produced and hashes
what it blitted, so a picture that reached the screen without passing through the kernel is a detectable
fault, not a feature.

Ratified shape for SHELL-0: hand-rolled Win32 through `extern "system"` declarations — window, `StretchDIBits`,
message pump, `DwmFlush` as the frame → composited barrier — zero crates, std-only like the
kernel, Windows-only and declared so. Native controls are the chrome (menu, text editor, inspector list);
the viewport and HUD are the kernel's frame. A cross-platform shell is a later, separate shell. The old
project's lesson stands here: its eight interactive pages each carried an untested JavaScript mirror of the
Python authority; this shell carries none.

| File | What it is |
|---|---|
| `present.rs` | the platform-agnostic core: render a scene to the composite, `to_blit`/`from_blit` (24-bit BGR top-down, a bijection), `blit_witness`, `blit_roundtrip_ok` — the blit-hash law |
| `playback.rs` | SHELL-PLAYBACK: `shell playback --session S` consumes a sealed SESSION-WALK, replays it through the present path, and emits the per-move frame digest + blit witness + round-trip; `shell checkpoint --at K` / `shell resume --checkpoint CK` fold in checkpoint/replay equivalence. Re-derives every witness and the head and REFUSES (`DIVERGED`) if the sealed input was tampered; writes no authority (rows `shell-playback-*`) |
| `main.rs` | `shell witness` / `shell selfcheck` (headless, the law); `shell playback` / `checkpoint` / `resume` (headless, SHELL-PLAYBACK); `shell run` (Windows: the window; elsewhere: `SHELL-NO-WINDOW`) |
| `win32.rs` | behind `--cfg shell_window` on Windows: the hand-rolled window, `StretchDIBits`, `DwmFlush` as the composition barrier (frame-ready → composited by QPC); guards every present with the blit witness; writes the raw present record. `playback_window` (SHELL-PLAYBACK-b) plays a sealed session frame-by-frame in the real window, each frame blit-law-guarded; with `--measure N` it is LATENCY-0's instrument (per-frame frame-ready → composited across the sealed sequence → `shell/attest/latency-<host>.json`) — host-run, out of every gate build |
| `attest/present-<host>.json` | the host's `frame-ready → composited` record, sealed by `../verify/seal_present.py` under RECORD-0's envelope |

SHELL-0a landed the blit-hash law (`../verify/pins/shell-1.json`; rows `shell-*`): the shell shows the kernel's
composite and hands the OS exactly its bytes, and a byte corrupted between the kernel and the blit is detectable
— the defence WORKSHOP-0 named as out of its reach. The window and the number are the host's (SHELL-0,
preregistered); the first host record (`attest/present-<host>.json`) measured frame-ready → composited at
p50 ≈ 5.3 ms on a ~74 Hz panel — the compositor-wait baseline, excluding the kernel render, not input-to-photon.

SHELL-PLAYBACK landed the consumer half (rows `shell-playback-*`): the window shows exactly a sealed
SESSION-WALK and nothing else. Playback consumes the sealed session (never an ad-hoc stream), replays it through
the present path, and its composited frame-digest sequence equals the session's per-move witnesses — the crown
witness tying the sealed-authority mechanism to the certified blit law. It writes no authority, refuses a
tampered/reordered/truncated input (`DIVERGED`), and resumes from any certified checkpoint to the same head. The
on-screen window (SHELL-PLAYBACK-b, `shell playback-window`) now ships in `win32.rs` — host-run under
`--cfg shell_window`, it plays a sealed session in the real window; and only after it does LATENCY-0 measure timing.

What a shell number is and is not: frame → composited is software-reachable; input transport, the present
wait beyond composition, and the panel are not (they need capture hardware). No number from this folder is an
input-to-photon claim.
