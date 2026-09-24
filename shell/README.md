<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# `shell/` — the window

Contract: own the window, the input pump and the presentation of the kernel's framebuffer; contain no kernel
logic and no mirror of the authority; be replaceable. The shell blits pixels the kernel produced and hashes
what it blitted, so a picture that reached the screen without passing through the kernel is a detectable
fault, not a feature.

Ratified shape for SHELL-0: hand-rolled Win32 through `extern "system"` declarations — window, `StretchDIBits`,
message pump, `DwmGetCompositionTimingInfo` as the frame → composited ruler — zero crates, std-only like the
kernel, Windows-only and declared so. Native controls are the chrome (menu, text editor, inspector list);
the viewport and HUD are the kernel's frame. A cross-platform shell is a later, separate shell. The old
project's lesson stands here: its eight interactive pages each carried an untested JavaScript mirror of the
Python authority; this shell carries none.

| File | What it is |
|---|---|
| `present.rs` | the platform-agnostic core: render a scene to the composite, `to_blit`/`from_blit` (24-bit BGR top-down, a bijection), `blit_witness`, `blit_roundtrip_ok` — the blit-hash law |
| `main.rs` | `shell witness` / `shell selfcheck` (headless, the law); `shell run` (Windows: the window; elsewhere: `SHELL-NO-WINDOW`) |
| `win32.rs` | cfg-gated to Windows: the hand-rolled window, `StretchDIBits`, `DwmGetCompositionTimingInfo`; guards every present with the blit witness; writes the raw present record |
| `attest/present-<host>.json` | the host's `frame-ready → composited` record, sealed by `../verify/seal_present.py` under RECORD-0's envelope |

SHELL-0a landed the blit-hash law (`../verify/pins/shell-1.json`; rows `shell-*`): the shell shows the kernel's
composite and hands the OS exactly its bytes, and a byte corrupted between the kernel and the blit is detectable
— the defence WORKSHOP-0 named as out of its reach. The window and the number are the host's (SHELL-0,
preregistered).

What a shell number is and is not: frame → composited is software-reachable; input transport, the present
wait beyond composition, and the panel are not (they need capture hardware). No number from this folder is an
input-to-photon claim.
