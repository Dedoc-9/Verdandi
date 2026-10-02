// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/heading.rs — SIM-TICK-0: the frame at a heading, and the reference's recomputation of it.
//
// The session witnesses every frame event (a move, a look) by the digest of the index frame at its camera. This module
// is the only place the shell reaches the bearing kernels:
//
//   witness     at one of the four anchor headings: the facing kernel's frame, exactly as before (present::compose_frame),
//               so a walk that never looks is witnessed as it always was. At any other heading: the bearing camera
//               (x, z, k) composed from the carried vocabulary (kernel/vocab.rs) and rendered ONCE by BEARING-FAST-0's
//               production tread (kernel/bearingfast.rs, tread ca) — the live path. MOUSE-LOOK-0: that one render is
//               made by a Painter the session keeps, into buffers it reuses, and its picture stays readable, so the
//               loop presents the very render the witness came from.
//   reference   the same camera's index frame by the reference kernel (kernel/bearing.rs: its traversal and its frame,
//               the text the tag carries), and nothing of the fast path.
//   certify     a batch of free-heading frames recomputed by the reference across threads; the lowest event whose
//               digest differs (or whose scene the reference refuses) is the answer. A saved session's every
//               free-heading frame goes through here before the file is written (shell/livesession.rs).
//
// Nothing here opens a window, reads a clock or touches a file. The vocabulary is loaded once (its pin checked first,
// fail-closed) and only read after that.

use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Mutex, OnceLock};

use crate::bearing;
use crate::bearingfast;
use crate::formats::{parse_level, parse_tiles, Camera};
use crate::mantle::Refusal;
use crate::vocab;

/// The production tread: BEARING-FAST-0's `ca` — exact stepping (A) on PROD_THREADS row bands (C).
pub const PROD: bearingfast::Tread = bearingfast::Tread { blocked: false, threads: bearingfast::PROD_THREADS };

fn vocabulary() -> Result<&'static vocab::Vocab, String> {
    static VOCAB: OnceLock<Result<vocab::Vocab, String>> = OnceLock::new();
    VOCAB.get_or_init(|| vocab::load().map_err(|Refusal(m)| m)).as_ref().map_err(|m| m.clone())
}

/// The bearing kernel's scene at (x, z, k) over raw level and tiles bytes.
fn scene_at(level_bytes: &[u8], tiles_bytes: &[u8], x: i64, z: i64, k: i64) -> Result<bearing::Scene, String> {
    let level = parse_level(level_bytes).map_err(|Refusal(m)| m)?;
    let tiles = parse_tiles(tiles_bytes).map_err(|Refusal(m)| m)?;
    let triple = vocabulary()?.triple(k).map_err(|Refusal(m)| m)?;
    let data = vocab::compose(&level, vocab::BearingCamera { x, z, k }, triple, &tiles);
    bearing::parse_scene(&data).map_err(|Refusal(m)| m)
}

/// MOUSE-LOOK-0: the session's renderer at a heading, with the buffers it keeps. One render serves the witness and the
/// screen: the index frame is digested, and the picture stays readable until the next free-heading render.
pub struct Painter {
    strips: Vec<bearing::Strip>,
    frame: Vec<u8>,
    pixels: Vec<u8>,
}

impl Painter {
    /// A painter with no buffers yet: they are made at the first free-heading render and reused after.
    pub fn new() -> Painter {
        Painter { strips: Vec::new(), frame: Vec::new(), pixels: Vec::new() }
    }

    /// The frame digest the session witnesses at a camera and heading: the facing kernel's at an anchor (as before;
    /// nothing is kept), the production tread's anywhere else, rendered once into the kept buffers.
    pub fn witness(&mut self, level_bytes: &[u8], tiles_bytes: &[u8], cam: Camera, yaw: i64) -> Result<String, String> {
        if crate::simtick::anchor(yaw).is_some() {
            return crate::present::compose_frame(level_bytes, tiles_bytes, cam).map(|c| c.frame_digest).map_err(|Refusal(m)| m);
        }
        let sc = scene_at(level_bytes, tiles_bytes, cam.x, cam.z, yaw)?;
        if self.frame.is_empty() {
            self.strips = Vec::with_capacity(bearing::W);
            self.frame = vec![0u8; bearing::W * bearing::H];
            self.pixels = vec![0u8; bearing::W * bearing::H * 3];
        }
        let floor = bearingfast::prepare(&sc, PROD);
        bearingfast::render_into(&sc, PROD, &floor, &mut self.strips, &mut self.frame, &mut self.pixels).map_err(|Refusal(m)| m)?;
        Ok(bearing::frame_digest(&self.frame))
    }

    /// The picture (RGB, top-down) of the last free-heading render.
    pub fn pixels(&self) -> &[u8] {
        &self.pixels
    }
}

/// The same frame's digest by the reference kernel alone: its traversal, then its index frame.
pub fn reference(level_bytes: &[u8], tiles_bytes: &[u8], x: i64, z: i64, yaw: i64) -> Result<String, String> {
    let sc = scene_at(level_bytes, tiles_bytes, x, z, yaw)?;
    let mut strips: Vec<bearing::Strip> = Vec::with_capacity(bearing::W);
    let mut frame = vec![0u8; bearing::W * bearing::H];
    sc.strips(&mut strips);
    sc.frame(&strips, &mut frame);
    Ok(bearing::frame_digest(&frame))
}

/// One frame event at a free heading: which event, the W and M it was rendered over, its camera, and the witness the
/// session holds for it.
pub struct FreeFrame {
    pub event: usize,
    pub level: Arc<Vec<u8>>,
    pub tiles: Arc<Vec<u8>>,
    pub x: i64,
    pub z: i64,
    pub yaw: i64,
    pub witness: String,
}

/// How many threads the recomputation runs on: the host's parallelism, at least one.
pub fn threads() -> usize {
    std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1).max(1)
}

/// Recompute each frame with the reference, across `threads` threads. Every frame is recomputed; the lowest event
/// whose digest is not the session's witness (or whose scene the reference refuses) is returned with what happened.
pub fn certify(frames: &[FreeFrame], threads: usize) -> Result<(), (usize, String)> {
    let next = AtomicUsize::new(0);
    let worst: Mutex<Option<(usize, String)>> = Mutex::new(None);
    std::thread::scope(|scope| {
        for _ in 0..threads.max(1).min(frames.len().max(1)) {
            scope.spawn(|| loop {
                let i = next.fetch_add(1, Ordering::SeqCst);
                if i >= frames.len() {
                    break;
                }
                let f = &frames[i];
                let why = match reference(&f.level, &f.tiles, f.x, f.z, f.yaw) {
                    Ok(d) if d == f.witness => continue,
                    Ok(d) => format!("the reference's frame {} is not the session's witness {}", &d[..12], &f.witness[..12.min(f.witness.len())]),
                    Err(m) => format!("the reference refuses the scene: {}", m),
                };
                let mut w = worst.lock().unwrap();
                if w.as_ref().map_or(true, |(e, _)| f.event < *e) {
                    *w = Some((f.event, why));
                }
            });
        }
    });
    match worst.into_inner().unwrap() {
        Some(bad) => Err(bad),
        None => Ok(()),
    }
}
