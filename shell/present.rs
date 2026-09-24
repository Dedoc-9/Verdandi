// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/present.rs — the platform-agnostic present core, and the blit-hash law.
//
// The shell owns the window and nothing else; its one correctness duty is that a picture reaching the screen
// passed through the kernel. This file renders a scene to the composite the shell will show (the kernel's
// viewport with the HUD overlay), converts it to the EXACT bytes a GDI blit receives — 24-bit BGR, top-down,
// DWORD-aligned (W = 1920, so 1920*3 = 5760 is a multiple of 4 and no row padding is needed) — and proves that
// conversion is an invertible carrier of the kernel's composite. So:
//
//   the blit-hash law   `from_blit(to_blit(c)) == c`  (the transform is a bijection, its own inverse),
//                       and the shell hands the OS ONLY `to_blit(composite)`, whose sha (`blit_witness`)
//                       therefore determines the composite's sha and back — a byte corrupted between the
//                       kernel and the blit moves the blit witness and breaks the round-trip. Detectable.
//
// No window, no clock, no OS call here; std-only; compiles on any target. `shell/win32.rs` (cfg-gated to
// Windows) is the only file that opens a window and reads DWM's composition clock.

use crate::formats::{compose, parse_level, parse_tiles, Camera};
use crate::hud;
use crate::mantle::{hex, parse_scene, picture, sha256, Refusal, H, W};

pub struct Composed {
    pub composite: Vec<u8>,     // W*H*3 RGB, top-down: the kernel's viewport with the HUD overlay drawn in
    pub frame_digest: String,   // the URDRFB1 index digest (unmoved by the overlay)
    pub pixels: String,         // the viewport pixel sha (Urðr's authority, untouched under the overlay)
    pub composite_sha: String,  // sha256 of the composite RGB bytes
}

/// Render level+tiles+camera to the composite the shell shows. Refuses (typed) exactly as the kernel does.
pub fn compose_frame(level_bytes: &[u8], tiles_bytes: &[u8], cam: Camera) -> Result<Composed, Refusal> {
    let level = parse_level(level_bytes)?;
    let tiles = parse_tiles(tiles_bytes)?;
    let scene = parse_scene(&compose(&level, cam, &tiles))?;
    let pic = picture(&scene);
    let frame_digest = pic.frame_digest();
    let pixels = pic.pixel_sha256();
    let mut composite = pic.pixels.clone();
    hud::overlay(&scene, &pic.strips, &mut composite);
    let composite_sha = hex(&sha256(&composite));
    Ok(Composed { composite, frame_digest, pixels, composite_sha })
}

/// RGB top-down -> BGR top-down: the exact bytes StretchDIBits receives (a 24-bit top-down DIB). Self-inverse.
pub fn to_blit(rgb: &[u8]) -> Vec<u8> {
    let mut out = vec![0u8; rgb.len()];
    let n = W * H;
    for i in 0..n {
        out[i * 3] = rgb[i * 3 + 2]; // B
        out[i * 3 + 1] = rgb[i * 3 + 1]; // G
        out[i * 3 + 2] = rgb[i * 3]; // R
    }
    out
}

/// The inverse of `to_blit` (identical, since a B<->R swap is its own inverse). Named for the law's sake.
pub fn from_blit(blit: &[u8]) -> Vec<u8> {
    to_blit(blit)
}

/// The sha of exactly the bytes the OS blit receives.
pub fn blit_witness(blit: &[u8]) -> String {
    hex(&sha256(blit))
}

/// The law, on one composite: `from_blit(to_blit(c)) == c`. Returns true when the transform carried the
/// kernel's bytes intact. (The plant compiles a `to_blit` that drops a channel; this then returns false.)
pub fn blit_roundtrip_ok(composite: &[u8]) -> bool {
    from_blit(&to_blit(composite)) == composite
}
