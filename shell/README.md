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

What a shell number is and is not: frame → composited is software-reachable; input transport, the present
wait beyond composition, and the panel are not (they need capture hardware). No number from this folder is an
input-to-photon claim.
