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

use crate::fast;
use crate::formats::{compose, parse_level, parse_tiles, Camera};
use crate::hud;
use crate::mantle::{frame_digest, hex, parse_scene, sha256, Refusal, Scene, H, W};

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
    // GAUNTLET-2 LOCKED: the production render goes through the accepted threaded fast path (emit_threaded at T=8),
    // byte-identical to the frozen mantle::picture (gauntlet2-lock). The geometry (strips, frame) is mantle's, the
    // oracle's, unchanged; only the pixel pass is the parallel emit, so the ~3x render headroom reaches the present.
    let (strips, frame, viewport) = fast::render(&scene);
    let digest = frame_digest(&frame);
    let pixels = hex(&sha256(&viewport));
    let mut composite = viewport;
    hud::overlay(&scene, &strips, &mut composite);
    let composite_sha = hex(&sha256(&composite));
    Ok(Composed { composite, frame_digest: digest, pixels, composite_sha })
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

/// Parse level + tiles + camera into the kernel's scene, refusing (typed) exactly as `compose_frame` does. Used by
/// LATENCY-1R to prepare each sealed frame's scene OUTSIDE its clock, so the timed interval holds render work only.
pub fn scene_of(level_bytes: &[u8], tiles_bytes: &[u8], cam: Camera) -> Result<Scene, Refusal> {
    let level = parse_level(level_bytes)?;
    let tiles = parse_tiles(tiles_bytes)?;
    parse_scene(&compose(&level, cam, &tiles))
}

/// LATENCY-1R's two arms. They differ ONLY in the pixel pass over mantle's frozen strips + frame:
///   Production   — `fast::render`: `emit_threaded` at `PROD_THREADS = 8`, the path `compose_frame` renders through;
///   SingleThread — the LOCKED single-thread `fast::emit`, GAUNTLET-2's reference.
/// Both draw the same HUD overlay and return (index frame, composite) and nothing else: no digest is computed here,
/// so a clock around this call times rendering, never witness hashing. `compose_frame` stays the production entry.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Arm {
    Production,
    SingleThread,
}

pub fn arm_composite(scene: &Scene, arm: Arm) -> (Vec<u8>, Vec<u8>) {
    let (strips, frame, mut composite) = match arm {
        Arm::Production => fast::render(scene),
        Arm::SingleThread => {
            let mut strips = Vec::with_capacity(W);
            scene.strips(&mut strips);
            let mut frame = vec![0u8; W * H];
            scene.frame(&strips, &mut frame);
            let floor = fast::blocked_floor(&scene.floor);
            let mut pixels = vec![0u8; W * H * 3];
            fast::emit(scene, &strips, &frame, &mut pixels, &floor);
            (strips, frame, pixels)
        }
    };
    hud::overlay(scene, &strips, &mut composite);
    (frame, composite)
}

/// FRAME-SPLIT-0's phase marks: the court records one timestamp per phase boundary.
pub trait Marks {
    fn mark(&mut self);
}

/// FRAME-SPLIT-0's instrumented mirror of `arm_composite`: the SAME statement sequence per arm, with one mark after
/// each phase — strips, frame (its buffer allocated inside the phase), the floor swizzle, the pixel pass (its buffer
/// allocated inside the phase; Production = `emit_threaded` at `PROD_THREADS`, the calls `fast::render` makes, in its
/// order; SingleThread = `fast::emit`), and the HUD. The gate proves its output byte-identical to `arm_composite` and
/// its call order equal to `fast::render`'s; the court's uninstrumented cells call `arm_composite` itself, so the
/// whole-frame envelope is the real production path and the mirror's cost difference is measured, never assumed.
pub fn arm_composite_marked<M: Marks>(scene: &Scene, arm: Arm, m: &mut M) -> (Vec<u8>, Vec<u8>) {
    let mut strips = Vec::with_capacity(W);
    scene.strips(&mut strips);
    m.mark(); // strips
    let mut frame = vec![0u8; W * H];
    scene.frame(&strips, &mut frame);
    m.mark(); // frame
    let floor = fast::blocked_floor(&scene.floor);
    m.mark(); // floor swizzle
    let mut pixels = vec![0u8; W * H * 3];
    match arm {
        Arm::Production => fast::emit_threaded(scene, &strips, &frame, &mut pixels, &floor, fast::PROD_THREADS),
        Arm::SingleThread => fast::emit(scene, &strips, &frame, &mut pixels, &floor),
    }
    m.mark(); // pixel pass
    hud::overlay(scene, &strips, &mut pixels);
    m.mark(); // HUD
    (frame, pixels)
}

/// ALLOC-REUSE-0: `to_blit` into a caller-owned buffer (the same transform, no allocation): B, G, R per pixel. Its
/// lines carry no per-channel comments so that `to_blit`'s own `// R` line stays the one anchor the blit-law plants
/// mutate (rows `shell-blit-plant`, `shell-playback-blit-law`).
pub fn to_blit_into(rgb: &[u8], out: &mut [u8]) {
    let n = W * H;
    for i in 0..n {
        out[i * 3] = rgb[i * 3 + 2];
        out[i * 3 + 1] = rgb[i * 3 + 1];
        out[i * 3 + 2] = rgb[i * 3];
    }
}

/// ALLOC-REUSE-0's persistent buffers: the strips, the index frame, the pixels (which become the composite) and the
/// BGR blit buffer, allocated once and overwritten every frame. The floor swizzle's buffer is not among them: it is
/// `fast::blocked_floor`'s own, and `fast.rs` is untouched, so it stays freshly allocated in both variants.
pub struct ReuseBufs {
    pub strips: Vec<crate::mantle::Strip>,
    pub frame: Vec<u8>,
    pub pixels: Vec<u8>,
    pub bgr: Vec<u8>,
}

impl ReuseBufs {
    pub fn new() -> ReuseBufs {
        ReuseBufs { strips: Vec::with_capacity(W), frame: vec![0u8; W * H], pixels: vec![0u8; W * H * 3], bgr: vec![0u8; W * H * 3] }
    }
}

/// ALLOC-REUSE-0's reuse variant of `arm_composite_marked` (production arm): the same calls in the same order with the
/// same five marks, writing into `b` instead of fresh buffers. `Scene::strips` clears its vector, `Scene::frame` writes
/// every index and the pixel pass writes every pixel exactly once, so no stale byte can survive; the court checks every
/// composite byte for byte regardless. The composite is left in `b.pixels`.
pub fn arm_composite_reuse_marked<M: Marks>(scene: &Scene, b: &mut ReuseBufs, m: &mut M) {
    scene.strips(&mut b.strips);
    m.mark(); // strips
    scene.frame(&b.strips, &mut b.frame);
    m.mark(); // frame
    let floor = fast::blocked_floor(&scene.floor);
    m.mark(); // floor swizzle
    fast::emit_threaded(scene, &b.strips, &b.frame, &mut b.pixels, &floor, fast::PROD_THREADS);
    m.mark(); // pixel pass
    hud::overlay(scene, &b.strips, &mut b.pixels);
    m.mark(); // HUD
}

/// ALLOC-REUSE-1: the render-loop entry, a persistent-buffer renderer for any loop that renders once per presented
/// frame. It makes `fast::render`'s calls in `fast::render`'s order (the strips, the index frame, the floor swizzle, the
/// threaded pixel pass at `PROD_THREADS`) and then the HUD overlay, into four buffers it allocates once in `new()` and
/// overwrites on every render; `blit()` is `to_blit`'s transform into its own BGR buffer. Only the floor swizzle, which
/// is `fast::blocked_floor`'s own small buffer (fast.rs is untouched), is still allocated per render.
///
/// ADOPTED (ALLOC-REUSE-1 LOCK): ALLOC-REUSE-1 read PERFORMANCE PASS on a run and on its confirmation, so this is the
/// production entry for in-loop rendering. A loop that renders once per presented frame renders through it; the
/// fresh render entries stay at their pinned reference sites (row `allocreuse1-lock`). The fresh path (`compose_frame`,
/// `arm_composite`, `fast::render`, `to_blit`) stays the frozen reference and differential oracle and is never
/// rewritten. No shipped window renders per frame yet: `run` renders once, and `playback-window` pre-renders frames
/// that must own their buffers. The adoption is the contract a future live loop enters, not a change to either.
pub struct LoopRenderer {
    pub(crate) b: ReuseBufs,
    renders: u64,
}

impl LoopRenderer {
    pub fn new() -> LoopRenderer {
        LoopRenderer { b: ReuseBufs::new(), renders: 0 }
    }

    /// The viewport: the strips, the index frame, the floor swizzle and the threaded pixel pass, in `fast::render`'s
    /// order, into the persistent buffers. The pixels hold the viewport (no HUD yet).
    pub fn viewport(&mut self, scene: &Scene) -> &[u8] {
        scene.strips(&mut self.b.strips);
        scene.frame(&self.b.strips, &mut self.b.frame);
        let floor = fast::blocked_floor(&scene.floor);
        fast::emit_threaded(scene, &self.b.strips, &self.b.frame, &mut self.b.pixels, &floor, fast::PROD_THREADS);
        self.renders += 1;
        &self.b.pixels
    }

    /// The HUD overlay onto the viewport just rendered: the pixels become the composite.
    pub fn overlay(&mut self, scene: &Scene) -> &[u8] {
        hud::overlay(scene, &self.b.strips, &mut self.b.pixels);
        &self.b.pixels
    }

    /// The production entry: the viewport, then the HUD. Its composite is `arm_composite(scene, Arm::Production)`'s.
    pub fn render(&mut self, scene: &Scene) -> &[u8] {
        self.viewport(scene);
        self.overlay(scene)
    }

    /// The exact bytes the GDI blit receives, written into the persistent BGR buffer (`to_blit`'s transform).
    pub fn blit(&mut self) -> &[u8] {
        to_blit_into(&self.b.pixels, &mut self.b.bgr);
        &self.b.bgr
    }

    pub fn composite(&self) -> &[u8] {
        &self.b.pixels
    }

    pub fn index_frame(&self) -> &[u8] {
        &self.b.frame
    }

    pub fn bgr(&self) -> &[u8] {
        &self.b.bgr
    }

    pub fn renders(&self) -> u64 {
        self.renders
    }

    /// Each persistent buffer's address and capacity. Equal before and after a render iff no buffer was replaced.
    /// Addresses are process-local: they are compared, never recorded.
    pub fn identity(&self) -> [(usize, usize); 4] {
        [
            (self.b.strips.as_ptr() as usize, self.b.strips.capacity()),
            (self.b.frame.as_ptr() as usize, self.b.frame.capacity()),
            (self.b.pixels.as_ptr() as usize, self.b.pixels.capacity()),
            (self.b.bgr.as_ptr() as usize, self.b.bgr.capacity()),
        ]
    }
}
