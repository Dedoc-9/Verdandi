// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// kernel/main.rs — the kernel's command line: a scene in, two witnesses out; the bench off-gate.
//
//     rustc -O kernel/main.rs -o build/kernel
//     kernel scene.bin                                           # URDRMNTI bytes
//     kernel --level L.lvl --tiles T.tiles --camera 34,28,W      # composed from the studio's files
//     kernel ... --bench 200 --warm 20                           # off-gate: p50/p95/p99/max us per phase
//     kernel ... --breakdown 300 --warm 30                        # off-gate (GAUNTLET-0): render split strips/frame/emit + the two witness hashes
//     kernel ... --fast                                           # GAUNTLET-1: DDA emit + collapse baseline vs frozen — fast_equal / collapse_equal, region divide-work (frozen/collapse/DDA), first-diff taxonomy
//     kernel ... --fast-bench 300 --warm 30                        # off-gate (GAUNTLET-1c): frozen / collapse / DDA emit timed on one apparatus (all three must reproduce the witness)
//     kernel ... --emit-breakdown 300 --warm 30                     # off-gate (RE-BREAKDOWN-1): Court A structure + Court B ablation probes (addr/lookup/full/emit), probe VERIFY == emit
//     kernel ... --write-scene out.bin                           # the composed URDRMNTI bytes, for a record
//     kernel ... --hud                                           # HUD-0: the overlay drawn, three more lines
//     kernel ... --hud --write-png out.ppm                       # the composite as a binary PPM (P6), off-gate
//
// Prints `frame <sha256>`, `pixels <sha256>`, `selfcheck OK|DIVERGED` (the picture computed twice); with --hud
// also `hud_overlay <sha256>` (the overlay's own bytes), `hud <sha256>` (the composite picture) and
// `hud_region inside=N outside=M` (pixels the overlay changed inside and outside its declared region); with
// --bench the per-phase percentiles and the host line. Renderer time only: no window, no present, no input —
// never an input-to-photon number.

#[allow(dead_code)]
#[path = "mantle.rs"]
mod mantle;
#[allow(dead_code)]
#[path = "formats.rs"]
mod formats;
#[allow(dead_code)]
#[path = "hud.rs"]
mod hud;
#[allow(dead_code)]
#[path = "fast.rs"]
mod fast;

use std::env;
use std::fs;
use std::hint::black_box;
use std::process::exit;
use std::time::Instant;

use mantle::{frame_digest, hex, parse_scene, picture, sha256, Refusal, Strip, H, W};

fn refuse(msg: &str) -> ! {
    eprintln!("KERNEL-REFUSE: {}", msg);
    exit(2)
}

fn read(path: &str) -> Vec<u8> {
    fs::read(path).unwrap_or_else(|e| refuse(&format!("cannot read {}: {}", path, e)))
}

fn percentiles(mut xs: Vec<u128>) -> (u128, u128, u128, u128) {
    xs.sort_unstable();
    let n = xs.len();
    let at = |p: f64| xs[(((n as f64) * p).ceil() as usize).saturating_sub(1).min(n - 1)];
    (at(0.50), at(0.95), at(0.99), xs[n - 1])
}

fn host_line() -> String {
    let mut cpu = String::from("unknown");
    if let Ok(txt) = fs::read_to_string("/proc/cpuinfo") {
        for ln in txt.lines() {
            if ln.starts_with("model name") {
                if let Some(v) = ln.split(':').nth(1) {
                    cpu = v.trim().to_string();
                    break;
                }
            }
        }
    } else if let Ok(v) = env::var("PROCESSOR_IDENTIFIER") {
        cpu = v;
    }
    format!("host os={} arch={} cpu=\"{}\"", env::consts::OS, env::consts::ARCH, cpu)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let usage = "usage: kernel <scene.bin> | --level L --tiles T --camera x,z,F  [--bench N] [--warm M] [--write-scene OUT]";
    let mut scene_path: Option<String> = None;
    let (mut level, mut tiles, mut camera): (Option<String>, Option<String>, Option<String>) = (None, None, None);
    let mut bench = 0usize;
    let mut breakdown = 0usize;
    let mut warm = 10usize;
    let mut write_scene: Option<String> = None;
    let mut want_hud = false;
    let mut want_fast = false;
    let mut fast_bench = 0usize;
    let mut emit_bd = 0usize;
    let mut want_struct = false;
    let mut write_ppm: Option<String> = None;
    let mut i = 1;
    while i < args.len() {
        let next = |i: usize| -> String {
            args.get(i + 1).cloned().unwrap_or_else(|| refuse(&format!("{} needs a value", args[i])))
        };
        match args[i].as_str() {
            "--level" => { level = Some(next(i)); i += 2; }
            "--tiles" => { tiles = Some(next(i)); i += 2; }
            "--camera" => { camera = Some(next(i)); i += 2; }
            "--bench" => { bench = next(i).parse().unwrap_or_else(|_| refuse("--bench needs a count")); i += 2; }
            "--breakdown" => { breakdown = next(i).parse().unwrap_or_else(|_| refuse("--breakdown needs a count")); i += 2; }
            "--warm" => { warm = next(i).parse().unwrap_or_else(|_| refuse("--warm needs a count")); i += 2; }
            "--write-scene" => { write_scene = Some(next(i)); i += 2; }
            "--hud" => { want_hud = true; i += 1; }
            "--fast" => { want_fast = true; i += 1; }
            "--fast-bench" => { fast_bench = next(i).parse().unwrap_or_else(|_| refuse("--fast-bench needs a count")); i += 2; }
            "--emit-breakdown" => { emit_bd = next(i).parse().unwrap_or_else(|_| refuse("--emit-breakdown needs a count")); i += 2; }
            "--emit-structure" => { want_struct = true; i += 1; }
            "--write-png" => { write_ppm = Some(next(i)); i += 2; }
            a if a.starts_with("--") => refuse(&format!("unknown argument {}", a)),
            _ => { scene_path = Some(args[i].clone()); i += 1; }
        }
    }
    let data: Vec<u8> = match (scene_path, level, tiles, camera) {
        (Some(p), None, None, None) => read(&p),
        (None, Some(l), Some(t), Some(c)) => {
            let lvl = formats::parse_level(&read(&l)).unwrap_or_else(|Refusal(m)| refuse(&m));
            let til = formats::parse_tiles(&read(&t)).unwrap_or_else(|Refusal(m)| refuse(&m));
            let cam = formats::parse_camera(&c).unwrap_or_else(|Refusal(m)| refuse(&m));
            formats::compose(&lvl, cam, &til)
        }
        _ => refuse(usage),
    };
    if let Some(out) = &write_scene {
        fs::write(out, &data).unwrap_or_else(|e| refuse(&format!("cannot write {}: {}", out, e)));
    }
    let scene = parse_scene(&data).unwrap_or_else(|Refusal(m)| refuse(&m));

    // the witnesses, twice (determinism is the selfcheck)
    let first = picture(&scene);
    let fd = first.frame_digest();
    let ps = first.pixel_sha256();
    let second = picture(&scene);
    let same = second.frame_digest() == fd && second.pixel_sha256() == ps;
    println!("frame {}", fd);
    println!("pixels {}", ps);
    println!("selfcheck {}", if same { "OK" } else { "DIVERGED" });

    if want_hud {
        // HUD-0: the overlay drawn into a copy of the picture; the index frame is never touched
        let mut composite = first.pixels.clone();
        hud::overlay(&scene, &first.strips, &mut composite);
        let ov = hex(&sha256(&hud::overlay_bytes(&scene, &first.strips)));
        let hs = hex(&sha256(&composite));
        let (inside, outside) = hud::region_audit(&scene, &first.pixels, &composite);
        println!("hud_overlay {}", ov);
        println!("hud {}", hs);
        println!("hud_region inside={} outside={}", inside, outside);
        if let Some(path) = &write_ppm {
            let mut ppm = format!("P6\n{} {}\n255\n", W, H).into_bytes();
            ppm.extend_from_slice(&composite);
            fs::write(path, &ppm).unwrap_or_else(|e| refuse(&format!("cannot write {}: {}", path, e)));
        }
    } else if let Some(path) = &write_ppm {
        let mut ppm = format!("P6\n{} {}\n255\n", W, H).into_bytes();
        ppm.extend_from_slice(&first.pixels);
        fs::write(path, &ppm).unwrap_or_else(|e| refuse(&format!("cannot write {}: {}", path, e)));
    }

    if bench > 0 {
        // warm-up excluded; each sample is one full frame: traversal+strip+floor (frame) then the texel pass (pixels)
        let mut strips: Vec<Strip> = Vec::with_capacity(W);
        let mut buf = vec![0u8; W * H];
        let mut rgb = vec![0u8; W * H * 3];
        let mut t_frame: Vec<u128> = Vec::with_capacity(bench);
        let mut t_pix: Vec<u128> = Vec::with_capacity(bench);
        let mut t_tot: Vec<u128> = Vec::with_capacity(bench);
        for k in 0..(warm + bench) {
            let t0 = Instant::now();
            scene.strips(&mut strips);
            scene.frame(&strips, &mut buf);
            let t1 = Instant::now();
            scene.emit(&strips, &buf, &mut rgb);
            let t2 = Instant::now();
            if k >= warm {
                t_frame.push((t1 - t0).as_micros());
                t_pix.push((t2 - t1).as_micros());
                t_tot.push((t2 - t0).as_micros());
            }
        }
        // the bench rendered the same thing it witnessed
        let same_after = frame_digest(&buf) == fd && hex(&sha256(&rgb)) == ps;
        let (a, b, c, d) = percentiles(t_frame);
        println!("bench_frame_us p50={} p95={} p99={} max={}", a, b, c, d);
        let (a, b, c, d) = percentiles(t_pix);
        println!("bench_pixels_us p50={} p95={} p99={} max={}", a, b, c, d);
        let (a, b, c, d) = percentiles(t_tot);
        println!("bench_total_us p50={} p95={} p99={} max={}", a, b, c, d);
        println!("bench_samples {} warmup {} same_witnesses {}", bench, warm, if same_after { "OK" } else { "DIVERGED" });
        println!("{}", host_line());
    }
    if want_fast {
        // GAUNTLET-1: the sibling emit renders the SAME frozen strips + frame; its bytes must equal the frozen
        // emit's, or it is not an accepted renderer. The frame (buf) is read-only, so frame_digest cannot move.
        let mut rgb_fast = vec![0u8; W * H * 3]; // GAUNTLET-1c: fast::emit is now the row-major floor DDA
        fast::emit(&scene, &first.strips, &first.frame, &mut rgb_fast);
        let fps = hex(&sha256(&rgb_fast));
        let firstdiff = rgb_fast.iter().zip(first.pixels.iter()).position(|(a, b)| a != b);
        println!("fast_pixels {}", fps);
        println!("fast_frame {}", fd); // fast never writes buf; the frame is the frozen one, echoed for the record
        println!("fast_equal {}", if firstdiff.is_none() && fps == ps { "OK" } else { "DIFFER" });
        // GAUNTLET-1b's collapse, retained as the performance baseline, must ALSO stay byte-identical to frozen
        let mut rgb_collapse = vec![0u8; W * H * 3];
        fast::emit_collapse(&scene, &first.strips, &first.frame, &mut rgb_collapse);
        let cps = hex(&sha256(&rgb_collapse));
        println!("collapse_pixels {}", cps);
        println!("collapse_equal {}", if cps == ps { "OK" } else { "DIFFER" });
        // the deterministic region measure: the divide-work per region, which named GAUNTLET-1b's target
        let (wall_tex, floor_tex, table_px) = fast::region_divides(&first.strips, &first.frame);
        let (wall_work, floor_work) = (wall_tex, 4 * floor_tex);
        let dominant = if floor_work >= wall_work { "floor" } else { "wall" };
        println!("fast_region wall_tex={} floor_tex={} table_px={}", wall_tex, floor_tex, table_px);
        println!("fast_divwork wall={} floor={} dominant={}", wall_work, floor_work, dominant);
        // GAUNTLET-1b (the collapse, now emit_collapse): ONE div_euclid per coordinate (2/floor px) vs the frozen 4.
        let floor_work_fast = 2 * floor_tex;
        let dominant_fast = if floor_work_fast >= wall_tex { "floor" } else { "wall" };
        let floor_saved = floor_work - floor_work_fast;
        println!("fast_optwork wall={} floor={} dominant={} floor_saved={}", wall_tex, floor_work_fast, dominant_fast, floor_saved);
        // GAUNTLET-1c (the DDA, now fast::emit): the floor's perspective divide is per-ROW, not per-pixel — a bounded
        // ~5 div_euclid/rem_euclid per floor row (the two step constants, the constant-axis texel, the row's starting
        // q/rem) against the collapse's 2 per floor pixel. A structural claim read off fast.rs, NOT a wall-clock; the
        // speed is gauntlet1c.py's separate host court. dda_div = 5*floor_rows, collapse_div = 2*floor_px.
        let rows = fast::floor_rows(&first.strips);
        let dda_div = 5 * rows;
        let collapse_div = 2 * floor_tex;
        println!("fast_ddawork floor_px={} floor_rows={} dda_div={} collapse_div={}", floor_tex, rows, dda_div, collapse_div);
        // the failure taxonomy: first differing pixel, its coordinate, region, index and channels
        if let Some(bi) = firstdiff {
            let p = bi / 3;
            let (c, r) = (p % W, p / W);
            let s = &first.strips[c];
            let region = if (r as i64) < s.top { "ceiling" } else if (r as i64) <= s.bot { "wall" } else { "floor" };
            let idx = first.frame[p];
            let o = p * 3;
            eprintln!(
                "GAUNTLET1-DIFFER: first differing byte {} at pixel ({}, {}) region {} idx {} face {} tn {} td {}: frozen [{},{},{}] fast [{},{},{}]",
                bi, c, r, region, idx, s.face, s.tn, s.td,
                first.pixels[o], first.pixels[o + 1], first.pixels[o + 2], rgb_fast[o], rgb_fast[o + 1], rgb_fast[o + 2]);
            exit(3);
        }
    }
    if fast_bench > 0 {
        // The same-apparatus emit comparison — the frozen `mantle` emit, the GAUNTLET-1b collapse baseline, and the
        // GAUNTLET-1c DDA candidate (`fast::emit`), timed back to back over the SAME frozen strips + frame (all are
        // pure functions of them; none writes buf, so frame_digest cannot move). ALL THREE must reproduce the frozen
        // pixel witness or no number is printed. These are EMIT-level deltas ONLY: never the whole render, and never
        // cross-compared to GAUNTLET-0's instrumented render absolute (a different apparatus) — the locked GAUNTLET-1
        // rule. The comparison is left to the reader (verify/gauntlet1c.py): 1c is judged against the collapse, 1b's
        // baseline, not against frozen. Three percentile lines as data.
        let mut rgb_frozen = vec![0u8; W * H * 3];
        let mut rgb_fast = vec![0u8; W * H * 3];
        let mut rgb_collapse = vec![0u8; W * H * 3];
        let mut t_frozen: Vec<u128> = Vec::with_capacity(fast_bench);
        let mut t_fast: Vec<u128> = Vec::with_capacity(fast_bench);
        let mut t_collapse: Vec<u128> = Vec::with_capacity(fast_bench);
        for k in 0..(warm + fast_bench) {
            let a0 = Instant::now();
            scene.emit(&first.strips, &first.frame, &mut rgb_frozen);
            let a1 = Instant::now();
            fast::emit_collapse(&scene, &first.strips, &first.frame, &mut rgb_collapse);
            let a2 = Instant::now();
            fast::emit(&scene, &first.strips, &first.frame, &mut rgb_fast);
            let a3 = Instant::now();
            if k >= warm {
                t_frozen.push((a1 - a0).as_micros());
                t_collapse.push((a2 - a1).as_micros());
                t_fast.push((a3 - a2).as_micros());
            }
        }
        // guard: all three emits reproduced the frozen witness, so the deltas timed the certified render every way
        let same_after =
            hex(&sha256(&rgb_frozen)) == ps && hex(&sha256(&rgb_fast)) == ps && hex(&sha256(&rgb_collapse)) == ps;
        if !same_after {
            refuse("the fast-bench emits did not all reproduce the frozen pixel witness; no number is printed");
        }
        let (a, b, c, d) = percentiles(t_frozen);
        println!("fastbench_frozen_us p50={} p95={} p99={} max={}", a, b, c, d);
        let (a, b, c, d) = percentiles(t_collapse);
        println!("fastbench_collapse_us p50={} p95={} p99={} max={}", a, b, c, d);
        let (a, b, c, d) = percentiles(t_fast);
        println!("fastbench_fast_us p50={} p95={} p99={} max={}", a, b, c, d);
        println!("fastbench_samples {} warmup {} same_witnesses OK", fast_bench, warm);
        println!("{}", host_line());
    }
    if emit_bd > 0 || want_struct {
        // RE-BREAKDOWN-1: Court A (deterministic structure, wall-clock-free) always; Court B (host ablation) only with
        // --emit-breakdown N. The probes are fenced measurement apparatus, never renderers (see kernel/fast.rs::probe);
        // production emit calls none. Court A — what work exists, off the frozen frame:
        let st = fast::structure(&scene, &first.strips, &first.frame);
        println!(
            "emitbd_struct wall_tex={} floor_tex={} divides={} tile_reads={} map_reads={} ws_floor={} ws_wall={}",
            st.wall_tex, st.floor_tex, st.divides, st.tile_reads, st.map_reads, st.ws_floor, st.ws_wall
        );
        let local_permille = if st.floor_adj > 0 { st.floor_local * 1000 / st.floor_adj } else { 0 };
        println!("emitbd_locality floor_adj={} floor_local={} local_permille={}", st.floor_adj, st.floor_local, local_permille);
        println!("emitbd_writes writes={} writes_once={}", st.writes, if st.writes_once { "OK" } else { "NO" });
        // Faithfulness / negative control (deterministic, gate-checkable): the probe's VERIFY path is byte-identical
        // to emit (hence the frozen oracle), so the ablated probes are a demonstrable SUBSET of the certified path,
        // auditable rather than merely asserted.
        let mut rgb_emit = vec![0u8; W * H * 3];
        fast::emit(&scene, &first.strips, &first.frame, &mut rgb_emit);
        let mut rgb_verify = vec![0u8; W * H * 3];
        fast::probe::emit_probe::<{ fast::probe::VERIFY }>(&scene, &first.strips, &first.frame, &mut rgb_verify);
        let verify_ok = rgb_verify == rgb_emit && hex(&sha256(&rgb_verify)) == ps;
        println!("emitbd_verify {}", if verify_ok { "OK" } else { "DIFFER" });
        if !verify_ok || !st.writes_once {
            refuse("emit-breakdown: the probe VERIFY path is not the certified emit, or write coverage is not exactly once");
        }
        if emit_bd > 0 {
            // Court B — the ablation ladder timed against emit on ONE apparatus. Deltas are INCREMENTAL wall-clock
            // attribution under controlled ablation (LOOKUP−ADDR ~ tile fetch, FULL−LOOKUP ~ map/assembly), NOT
            // hardware-resource costs; FULL vs emit is the negative control (FULL carries a small black_box anchor
            // tax). Never cross-compared to GAUNTLET-0's instrumented render absolute.
            let mut a = vec![0u8; W * H * 3];
            let mut l = vec![0u8; W * H * 3];
            let mut f = vec![0u8; W * H * 3];
            let mut e = vec![0u8; W * H * 3];
            let mut t_addr: Vec<u128> = Vec::with_capacity(emit_bd);
            let mut t_lookup: Vec<u128> = Vec::with_capacity(emit_bd);
            let mut t_full: Vec<u128> = Vec::with_capacity(emit_bd);
            let mut t_emit: Vec<u128> = Vec::with_capacity(emit_bd);
            for kk in 0..(warm + emit_bd) {
                let a0 = Instant::now();
                fast::probe::emit_probe::<{ fast::probe::ADDR }>(&scene, &first.strips, &first.frame, &mut a);
                let a1 = Instant::now();
                fast::probe::emit_probe::<{ fast::probe::LOOKUP }>(&scene, &first.strips, &first.frame, &mut l);
                let a2 = Instant::now();
                fast::probe::emit_probe::<{ fast::probe::FULL }>(&scene, &first.strips, &first.frame, &mut f);
                let a3 = Instant::now();
                fast::emit(&scene, &first.strips, &first.frame, &mut e);
                let a4 = Instant::now();
                black_box(&a);
                black_box(&l);
                black_box(&f);
                if kk >= warm {
                    t_addr.push((a1 - a0).as_micros());
                    t_lookup.push((a2 - a1).as_micros());
                    t_full.push((a3 - a2).as_micros());
                    t_emit.push((a4 - a3).as_micros());
                }
            }
            if hex(&sha256(&e)) != ps {
                refuse("emit-breakdown: the timed emit did not reproduce the frozen witness; no number is printed");
            }
            let pl = |name: &str, xs: Vec<u128>| {
                let (a, b, c, d) = percentiles(xs);
                println!("emitbd_{}_us p50={} p95={} p99={} max={}", name, a, b, c, d);
            };
            pl("addr", t_addr);
            pl("lookup", t_lookup);
            pl("full", t_full);
            pl("emit", t_emit);
            println!("emitbd_samples {} warmup {} same_witnesses OK", emit_bd, warm);
            println!("{}", host_line());
        }
    }
    if breakdown > 0 {
        // GAUNTLET-0: the render decomposed at the kernel's pub-phase boundaries — strips (traversal), frame
        // (walls + floor cast), emit (texel pass) — plus the two WITNESS hashes (frame_digest, pixel_sha),
        // which the --bench total excludes and an interactive render never pays. mantle.rs is not touched: this
        // only times the existing calls. Host-CPU-specific; finer than frame() (floor vs walls) needs a sibling
        // renderer, which is GAUNTLET-1's differential fast path.
        let mut strips: Vec<Strip> = Vec::with_capacity(W);
        let mut buf = vec![0u8; W * H];
        let mut rgb = vec![0u8; W * H * 3];
        let mut t_strips: Vec<u128> = Vec::with_capacity(breakdown);
        let mut t_frame: Vec<u128> = Vec::with_capacity(breakdown);
        let mut t_emit: Vec<u128> = Vec::with_capacity(breakdown);
        let mut t_fd: Vec<u128> = Vec::with_capacity(breakdown);
        let mut t_ps: Vec<u128> = Vec::with_capacity(breakdown);
        let mut t_render: Vec<u128> = Vec::with_capacity(breakdown);
        for k in 0..(warm + breakdown) {
            let a0 = Instant::now();
            scene.strips(&mut strips);
            let a1 = Instant::now();
            scene.frame(&strips, &mut buf);
            let a2 = Instant::now();
            scene.emit(&strips, &buf, &mut rgb);
            let a3 = Instant::now();
            let fdx = frame_digest(&buf);
            let a4 = Instant::now();
            let psx = hex(&sha256(&rgb));
            let a5 = Instant::now();
            // guard: the phases reproduced the frozen witnesses, so the breakdown timed the certified render
            if fdx != fd || psx != ps {
                refuse("the breakdown rendered something other than the witnessed picture");
            }
            if k >= warm {
                t_strips.push((a1 - a0).as_micros());
                t_frame.push((a2 - a1).as_micros());
                t_emit.push((a3 - a2).as_micros());
                t_fd.push((a4 - a3).as_micros());
                t_ps.push((a5 - a4).as_micros());
                t_render.push((a3 - a0).as_micros()); // render = strips + frame + emit (the --bench total; excludes hashes)
            }
        }
        let render_p99 = { let (_, _, c, _) = percentiles(t_render.clone()); c };
        let line = |name: &str, xs: Vec<u128>| {
            let (a, b, c, d) = percentiles(xs);
            let share = if render_p99 > 0 { c * 1000 / render_p99 } else { 0 }; // p99 share of the render, permille
            println!("breakdown_{}_us p50={} p95={} p99={} max={} render_permille={}", name, a, b, c, d, share);
        };
        line("strips", t_strips);
        line("frame", t_frame);
        line("emit", t_emit);
        line("framedigest", t_fd);
        line("pixelsha", t_ps);
        {
            let (a, b, c, d) = percentiles(t_render);
            println!("breakdown_render_us p50={} p95={} p99={} max={}", a, b, c, d);
        }
        println!("breakdown_samples {} warmup {} same_witnesses OK", breakdown, warm);
        println!("{}", host_line());
    }
    if !same {
        exit(1);
    }
}
