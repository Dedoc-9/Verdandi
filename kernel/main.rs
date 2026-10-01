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
//     kernel ... --fast                                           # GAUNTLET-1 / LOCALITY-0 LOCK: blocked emit + archived linear emit + collapse baseline vs frozen — fast_equal / linear_equal / collapse_equal, region divide-work, first-diff taxonomy
//     kernel ... --fast-bench 300 --warm 30                        # off-gate (GAUNTLET-1c): frozen / collapse / archived linear DDA emit timed on one apparatus (all three must reproduce the witness)
//     kernel ... --emit-breakdown 300 --warm 30                     # off-gate (RE-BREAKDOWN-1): Court A structure + Court B ablation probes (addr/lookup/full/emit), probe VERIFY == emit
//     kernel ... --locality                                         # LOCALITY-0 differential: both floor layouts byte-identical + bijection + content/format + per-band locality
//     kernel ... --variant blocked --locality-bench 300 --warm 30   # off-gate (LOCALITY-0): process-isolated timing of ONE layout vs the DDA baseline (whole-frame + index tax + per-band)
//     kernel ... --gauntlet2                                         # GAUNTLET-2 correctness court: partition invariance — emit_partitioned over contiguous/adversarial column partitions is byte-identical to frozen (deterministic, no threads)
//     kernel ... --gauntlet2-threads                                 # GAUNTLET-2 threaded byte-identity: emit_threaded (std::thread::scope) byte-identical to frozen at T in {1,2,4,8,16} (deterministic output)
//     kernel ... --gauntlet2-bench 300 --warm 30 --threads 8         # off-gate (GAUNTLET-2): p99 of the threaded emit at an EXPLICIT thread count (byte-identity checked first)
//     kernel ... --render                                            # GAUNTLET-2 LOCKED production render: fast::render (emit_threaded at PROD_THREADS=8) byte-identical to the frozen picture
//     kernel ... --write-scene out.bin                           # the composed URDRMNTI bytes, for a record
//     kernel ... --hud                                           # HUD-0: the overlay drawn, three more lines
//     kernel ... --hud --write-png out.ppm                       # the composite as a binary PPM (P6), off-gate
//     kernel --level L.lvl --tiles T.tiles --at 34,28,123457     # BEARING-0: the REFERENCE bearing kernel at a heading id
//     kernel ... --at x,z,K --bench 200 --warm 20                # off-gate: the reference's per-phase timing (no record)
//     kernel --bearing-table                                     # BEARING-0: the vocabulary's identity (all 360,000 ids)
//     kernel --bearing-triple K                                  # BEARING-0: one id's registered triple
//     kernel --bearing-court FILE [--no-reference] [--threads-set 1,2,8]   # BEARING-FAST-0: the treads vs the reference over a camera list
//     kernel --level L --tiles T --at x,z,K --bearing-bench 200 --warm 20 --tread ref|a|b|ca|cb   # off-gate: one tread's timing
//     kernel --fast-scene scene.bin                              # BEARING-FAST-0: a raw URDRBRGI scene, the reference then tread a (or its refusal)
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
#[allow(dead_code)]
#[path = "vocab.rs"]
mod vocab;
#[allow(dead_code)]
#[path = "bearing.rs"]
mod bearing;
#[allow(dead_code)]
#[path = "bearingfast.rs"]
mod bearingfast;

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

/// BEARING-0: the reference bearing kernel's command line, kept apart from the facing path so nothing above it
/// changes. `--bearing-table` prints the vocabulary's identity over all 360,000 ids; `--bearing-triple K` one id's
/// registered triple; `--at x,z,K` with --level and --tiles renders the bearing camera and prints its triple and its
/// two witnesses, computed twice (the selfcheck); --write-scene, --write-png and the off-gate --bench apply.
#[allow(clippy::too_many_arguments)]
fn bearing_main(level: Option<String>, tiles: Option<String>, at: Option<String>, want_table: bool,
                one: Option<String>, bench: usize, warm: usize, write_scene: Option<String>,
                write_ppm: Option<String>) -> ! {
    let v = vocab::load().unwrap_or_else(|Refusal(m)| refuse(&m));
    if want_table {
        println!("octant {}", vocab::OCTANT_SHA256);
        println!("table {}", v.table_digest());
    }
    if let Some(s) = one {
        let k = vocab::parse_id(&s).unwrap_or_else(|Refusal(m)| refuse(&m));
        let (a, b, c) = v.triple(k).unwrap_or_else(|Refusal(m)| refuse(&m));
        println!("triple {} {},{},{}", k, a, b, c);
    }
    if let Some(s) = at {
        let (l, t) = match (level, tiles) {
            (Some(l), Some(t)) => (l, t),
            _ => refuse("--at needs --level and --tiles"),
        };
        let lvl = formats::parse_level(&read(&l)).unwrap_or_else(|Refusal(m)| refuse(&m));
        let til = formats::parse_tiles(&read(&t)).unwrap_or_else(|Refusal(m)| refuse(&m));
        let cam = vocab::parse_at(&s).unwrap_or_else(|Refusal(m)| refuse(&m));
        let tri = v.triple(cam.k).unwrap_or_else(|Refusal(m)| refuse(&m));
        let data = vocab::compose(&lvl, cam, tri, &til);
        if let Some(out) = &write_scene {
            fs::write(out, &data).unwrap_or_else(|e| refuse(&format!("cannot write {}: {}", out, e)));
        }
        let scene = bearing::parse_scene(&data).unwrap_or_else(|Refusal(m)| refuse(&m));
        let first = bearing::picture(&scene);
        let fd = first.frame_digest();
        let ps = first.pixel_sha256();
        let second = bearing::picture(&scene);
        let same = second.frame_digest() == fd && second.pixel_sha256() == ps;
        println!("triple {},{},{}", tri.0, tri.1, tri.2);
        println!("frame {}", fd);
        println!("pixels {}", ps);
        println!("selfcheck {}", if same { "OK" } else { "DIVERGED" });
        if let Some(path) = &write_ppm {
            let mut ppm = format!("P6\n{} {}\n255\n", W, H).into_bytes();
            ppm.extend_from_slice(&first.pixels);
            fs::write(path, &ppm).unwrap_or_else(|e| refuse(&format!("cannot write {}: {}", path, e)));
        }
        if bench > 0 {
            // off-gate, no record: warm-up excluded; each sample is one full frame, traversal+strip+floor then the texels
            let mut strips: Vec<bearing::Strip> = Vec::with_capacity(W);
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
            let same_after = bearing::frame_digest(&buf) == fd && hex(&sha256(&rgb)) == ps;
            let (a, b, c, d) = percentiles(t_frame);
            println!("bench_frame_us p50={} p95={} p99={} max={}", a, b, c, d);
            let (a, b, c, d) = percentiles(t_pix);
            println!("bench_pixels_us p50={} p95={} p99={} max={}", a, b, c, d);
            let (a, b, c, d) = percentiles(t_tot);
            println!("bench_total_us p50={} p95={} p99={} max={}", a, b, c, d);
            println!("bench_samples {} warmup {} same_witnesses {}", bench, warm, if same_after { "OK" } else { "DIVERGED" });
            println!("{}", host_line());
        }
    }
    exit(0)
}

/// BEARING-FAST-0's treads by name: a (exact stepping), b (a + the blocked floor), ca and cb (a or b in PROD_THREADS
/// row bands).
fn tread_of(name: &str) -> bearingfast::Tread {
    match name {
        "a" => bearingfast::A,
        "b" => bearingfast::B,
        "ca" => bearingfast::Tread { blocked: false, threads: bearingfast::PROD_THREADS },
        "cb" => bearingfast::Tread { blocked: true, threads: bearingfast::PROD_THREADS },
        other => refuse(&format!("no tread named {:?}", other)),
    }
}

const COURT_TREADS: [&str; 4] = ["a", "b", "ca", "cb"];

/// A camera list, one camera per line "LEVEL TILES x z K"; the level and tile files are read once each and every
/// scene is composed when its turn comes.
struct CourtList {
    vocab: vocab::Vocab,
    levels: std::collections::BTreeMap<String, formats::Level>,
    tiles: std::collections::BTreeMap<String, formats::Tiles>,
    cams: Vec<(String, String, vocab::BearingCamera)>,
}

impl CourtList {
    fn read(path: &str) -> CourtList {
        let text = String::from_utf8(read(path)).unwrap_or_else(|_| refuse("the camera list is not text"));
        let mut cl = CourtList {
            vocab: vocab::load().unwrap_or_else(|Refusal(m)| refuse(&m)),
            levels: std::collections::BTreeMap::new(),
            tiles: std::collections::BTreeMap::new(),
            cams: Vec::new(),
        };
        for (n, ln) in text.lines().enumerate() {
            let f: Vec<&str> = ln.split_whitespace().collect();
            if f.is_empty() {
                continue;
            }
            if f.len() != 5 {
                refuse(&format!("camera list line {} is not LEVEL TILES x z K", n + 1));
            }
            if !cl.levels.contains_key(f[0]) {
                cl.levels.insert(f[0].to_string(), formats::parse_level(&read(f[0])).unwrap_or_else(|Refusal(m)| refuse(&m)));
            }
            if !cl.tiles.contains_key(f[1]) {
                cl.tiles.insert(f[1].to_string(), formats::parse_tiles(&read(f[1])).unwrap_or_else(|Refusal(m)| refuse(&m)));
            }
            let cam = vocab::parse_at(&format!("{},{},{}", f[2], f[3], f[4])).unwrap_or_else(|Refusal(m)| refuse(&m));
            cl.cams.push((f[0].to_string(), f[1].to_string(), cam));
        }
        cl
    }
    fn scene(&self, i: usize) -> bearing::Scene {
        let (l, t, cam) = &self.cams[i];
        let tri = self.vocab.triple(cam.k).unwrap_or_else(|Refusal(m)| refuse(&m));
        bearing::parse_scene(&vocab::compose(&self.levels[l], *cam, tri, &self.tiles[t])).unwrap_or_else(|Refusal(m)| refuse(&m))
    }
}

/// BEARING-FAST-0's court: every tread's index frame and picture against the reference's, byte for byte, over a
/// camera list, in this one process. One line per camera: `cam I ref FD PS` then, per tread, `NAME = = 1` when both
/// buffers equal the reference's byte for byte (equal bytes have the reference's digests) or `NAME FD PS 0`.
/// --no-reference (the checked build) renders every tread at every camera and hashes one, rotating: camera I hashes
/// tread I mod n (`NAME FD PS -`, the others `NAME - - -`), so every tread's arithmetic runs everywhere and each is
/// compared by digest on its share. --threads-set replaces the treads with tread C at each listed count, both layouts;
/// --treads a,b,... chooses the treads; --no-digest (the sweep) prints the equality alone, hashing nothing.
fn bearingfast_court(path: &str, no_ref: bool, threads_set: Option<String>, only: Option<String>, no_digest: bool) -> ! {
    let list = CourtList::read(path);
    let chosen: Vec<String> = match only {
        Some(l) => l.split(',').map(|s| s.trim().to_string()).collect(),
        None => COURT_TREADS.iter().map(|s| s.to_string()).collect(),
    };
    let mut names: Vec<String> = chosen.clone();
    let mut treads: Vec<bearingfast::Tread> = chosen.iter().map(|s| tread_of(s)).collect();
    if let Some(ts) = threads_set {
        names.clear();
        treads.clear();
        for t in ts.split(',') {
            let n: usize = t.trim().parse().unwrap_or_else(|_| refuse("--threads-set takes counts"));
            for blocked in [false, true] {
                names.push(format!("{}{}", if blocked { "cb" } else { "ca" }, n));
                treads.push(bearingfast::Tread { blocked, threads: n });
            }
        }
    }
    let mut strips: Vec<bearing::Strip> = Vec::with_capacity(W);
    let mut buf = vec![0u8; W * H];
    let mut rgb = vec![0u8; W * H * 3];
    for i in 0..list.cams.len() {
        let scene = list.scene(i);
        let reference = if no_ref { None } else { Some(bearing::picture(&scene)) };
        let mut line = match &reference {
            Some(_) if no_digest => format!("cam {} ref - -", i),
            Some(p) => format!("cam {} ref {} {}", i, p.frame_digest(), p.pixel_sha256()),
            None => format!("cam {} ref - -", i),
        };
        for (j, t) in treads.iter().enumerate() {
            let floor = bearingfast::prepare(&scene, *t);
            bearingfast::render_into(&scene, *t, &floor, &mut strips, &mut buf, &mut rgb).unwrap_or_else(|Refusal(m)| refuse(&m));
            let cell = match &reference {
                Some(p) if buf == p.frame && rgb == p.pixels => "= = 1".to_string(),
                Some(_) if no_digest => "- - 0".to_string(),
                Some(_) => format!("{} {} 0", bearing::frame_digest(&buf), hex(&sha256(&rgb))),
                None if i % treads.len() == j => format!("{} {} -", bearing::frame_digest(&buf), hex(&sha256(&rgb))),
                None => "- - -".to_string(),
            };
            line.push_str(&format!(" {} {}", names[j], cell));
        }
        println!("{}", line);
    }
    exit(0)
}

/// Off-gate: one tread's whole render (strips, frame and picture) timed in this process, its witnesses checked
/// against the reference's first — a number of the wrong picture is refused.
fn bearingfast_bench(level: Option<String>, tiles: Option<String>, at: Option<String>, n: usize, warm: usize,
                     tread: Option<String>) -> ! {
    let (l, t, a) = match (level, tiles, at) {
        (Some(l), Some(t), Some(a)) => (l, t, a),
        _ => refuse("--bearing-bench needs --level, --tiles and --at"),
    };
    let v = vocab::load().unwrap_or_else(|Refusal(m)| refuse(&m));
    let lvl = formats::parse_level(&read(&l)).unwrap_or_else(|Refusal(m)| refuse(&m));
    let til = formats::parse_tiles(&read(&t)).unwrap_or_else(|Refusal(m)| refuse(&m));
    let cam = vocab::parse_at(&a).unwrap_or_else(|Refusal(m)| refuse(&m));
    let tri = v.triple(cam.k).unwrap_or_else(|Refusal(m)| refuse(&m));
    let scene = bearing::parse_scene(&vocab::compose(&lvl, cam, tri, &til)).unwrap_or_else(|Refusal(m)| refuse(&m));
    let reference = bearing::picture(&scene);
    let name = tread.unwrap_or_else(|| refuse("--bearing-bench needs --tread ref|a|b|ca|cb"));
    let mut strips: Vec<bearing::Strip> = Vec::with_capacity(W);
    let mut buf = vec![0u8; W * H];
    let mut rgb = vec![0u8; W * H * 3];
    let mut times: Vec<u128> = Vec::with_capacity(n);
    if name == "ref" {
        for k in 0..(warm + n) {
            let t0 = Instant::now();
            scene.strips(&mut strips);
            scene.frame(&strips, &mut buf);
            scene.emit(&strips, &buf, &mut rgb);
            let t1 = Instant::now();
            if k >= warm {
                times.push((t1 - t0).as_micros());
            }
        }
    } else {
        let tr = tread_of(&name);
        let floor = bearingfast::prepare(&scene, tr);
        for k in 0..(warm + n) {
            let t0 = Instant::now();
            bearingfast::render_into(&scene, tr, &floor, &mut strips, &mut buf, &mut rgb).unwrap_or_else(|Refusal(m)| refuse(&m));
            let t1 = Instant::now();
            if k >= warm {
                times.push((t1 - t0).as_micros());
            }
        }
    }
    let same = buf == reference.frame && rgb == reference.pixels;
    println!("bench_tread {}", name);
    println!("bench_witness {}", if same { "OK" } else { "DIVERGED" });
    if !same {
        exit(1);
    }
    let (p50, p95, p99, mx) = percentiles(times);
    println!("bench_total_us p50={} p95={} p99={} max={}", p50, p95, p99, mx);
    println!("bench_samples {} warmup {}", n, warm);
    println!("{}", host_line());
    exit(0)
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

/// LOCALITY-0 process-isolated timing for ONE layout (monomorphized, so only this variant's address-generation
/// instructions are hot in this invocation — the Epistemic-Invariance boundary). Times the linear-fetch DDA
/// reference (fast::emit_linear, the archived pre-LOCK baseline) vs the swizzled variant whole-frame (both must
/// reproduce the witness), the whole-frame index-arithmetic tax X (floor ADDR: variant minus linear), and the
/// per-band floor FULL delta (the mid-field shear story). The orchestrator interleaves separate invocations of
/// blocked and morton to cancel thermal drift; with --variant blocked it re-confirms the LOCK (linear vs blocked).
fn locality_bench_variant<const LAYOUT: u8>(
    scene: &mantle::Scene, strips: &[Strip], frame: &[u8], ps: &str, samples: usize, warm: usize, name: &str,
) {
    use fast::locality as loc;
    let floor_sw = loc::swizzle_tile::<LAYOUT>(&scene.floor);
    let floor_lin = scene.floor.clone();
    let bands = loc::floor_bands(strips);
    let mut rgb_dda = vec![0u8; W * H * 3];
    let mut rgb_var = vec![0u8; W * H * 3];
    let mut sink = vec![0u8; W * H * 3];
    let mut t_dda: Vec<u128> = Vec::with_capacity(samples);
    let mut t_var: Vec<u128> = Vec::with_capacity(samples);
    let mut t_xlin: Vec<u128> = Vec::with_capacity(samples);
    let mut t_xvar: Vec<u128> = Vec::with_capacity(samples);
    for k in 0..(warm + samples) {
        let a0 = Instant::now();
        fast::emit_linear(scene, strips, frame, &mut rgb_dda);
        let a1 = Instant::now();
        loc::emit_swizzled::<LAYOUT>(scene, strips, frame, &mut rgb_var, &floor_sw);
        let a2 = Instant::now();
        loc::floor_bench::<{ loc::LINEAR }, { loc::ADDR }>(scene, strips, frame, &mut sink, &floor_lin, 0, H);
        let a3 = Instant::now();
        loc::floor_bench::<LAYOUT, { loc::ADDR }>(scene, strips, frame, &mut sink, &floor_sw, 0, H);
        let a4 = Instant::now();
        black_box(&rgb_dda);
        black_box(&rgb_var);
        black_box(&sink);
        if k >= warm {
            t_dda.push((a1 - a0).as_micros());
            t_var.push((a2 - a1).as_micros());
            t_xlin.push((a3 - a2).as_micros());
            t_xvar.push((a4 - a3).as_micros());
        }
    }
    if hex(&sha256(&rgb_dda)) != ps || hex(&sha256(&rgb_var)) != ps {
        refuse("locality-bench: the DDA baseline or the swizzled variant did not reproduce the frozen witness");
    }
    let pl = |tag: &str, xs: Vec<u128>| {
        let (a, b, c, d) = percentiles(xs);
        println!("locbench_{}_us p50={} p95={} p99={} max={}", tag, a, b, c, d);
    };
    let p99 = |xs: Vec<u128>| {
        let (_, _, c, _) = percentiles(xs);
        c
    };
    pl("dda", t_dda);
    pl(name, t_var);
    println!("locbench_addr_us lin_p99={} var_p99={}", p99(t_xlin), p99(t_xvar));
    // per-band floor FULL: where the memory win (if any) lives across the shear
    for (bi, &(lo, hi)) in bands.iter().enumerate() {
        let bandname = ["near", "mid", "far"][bi];
        let mut td: Vec<u128> = Vec::with_capacity(samples);
        let mut tv: Vec<u128> = Vec::with_capacity(samples);
        for k in 0..(warm + samples) {
            let a0 = Instant::now();
            loc::floor_bench::<{ loc::LINEAR }, { loc::FULL }>(scene, strips, frame, &mut sink, &floor_lin, lo, hi);
            let a1 = Instant::now();
            loc::floor_bench::<LAYOUT, { loc::FULL }>(scene, strips, frame, &mut sink, &floor_sw, lo, hi);
            let a2 = Instant::now();
            black_box(&sink);
            if k >= warm {
                td.push((a1 - a0).as_micros());
                tv.push((a2 - a1).as_micros());
            }
        }
        println!("locband_{}_{} dda_p99={} var_p99={}", name, bandname, p99(td), p99(tv));
    }
    println!("locbench_samples {} warmup {} variant {} same_witnesses OK", samples, warm, name);
    println!("{}", host_line());
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
    let mut want_loc = false;
    let mut loc_variant: Option<String> = None;
    let mut loc_bench = 0usize;
    let mut want_g2 = false;
    let mut want_g2threads = false;
    let mut g2_bench = 0usize;
    let mut n_threads = 1usize;
    let mut want_render = false;
    let mut write_ppm: Option<String> = None;
    let mut at: Option<String> = None;
    let mut want_btable = false;
    let mut btriple: Option<String> = None;
    let mut court: Option<String> = None;
    let mut no_ref = false;
    let mut threads_set: Option<String> = None;
    let mut bbench = 0usize;
    let mut tread: Option<String> = None;
    let mut fast_scene: Option<String> = None;
    let mut court_treads: Option<String> = None;
    let mut no_digest = false;
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
            "--locality" => { want_loc = true; i += 1; }
            "--variant" => { loc_variant = Some(next(i)); i += 2; }
            "--locality-bench" => { loc_bench = next(i).parse().unwrap_or_else(|_| refuse("--locality-bench needs a count")); i += 2; }
            "--gauntlet2" => { want_g2 = true; i += 1; }
            "--gauntlet2-threads" => { want_g2threads = true; i += 1; }
            "--gauntlet2-bench" => { g2_bench = next(i).parse().unwrap_or_else(|_| refuse("--gauntlet2-bench needs a count")); i += 2; }
            "--threads" => { n_threads = next(i).parse().unwrap_or_else(|_| refuse("--threads needs a count")); i += 2; }
            "--render" => { want_render = true; i += 1; }
            "--write-png" => { write_ppm = Some(next(i)); i += 2; }
            "--at" => { at = Some(next(i)); i += 2; }
            "--bearing-table" => { want_btable = true; i += 1; }
            "--bearing-triple" => { btriple = Some(next(i)); i += 2; }
            "--bearing-court" => { court = Some(next(i)); i += 2; }
            "--no-reference" => { no_ref = true; i += 1; }
            "--threads-set" => { threads_set = Some(next(i)); i += 2; }
            "--bearing-bench" => { bbench = next(i).parse().unwrap_or_else(|_| refuse("--bearing-bench needs a count")); i += 2; }
            "--tread" => { tread = Some(next(i)); i += 2; }
            "--fast-scene" => { fast_scene = Some(next(i)); i += 2; }
            "--treads" => { court_treads = Some(next(i)); i += 2; }
            "--no-digest" => { no_digest = true; i += 1; }
            a if a.starts_with("--") => refuse(&format!("unknown argument {}", a)),
            _ => { scene_path = Some(args[i].clone()); i += 1; }
        }
    }
    if let Some(f) = fast_scene {
        // BEARING-FAST-0's envelope probe: a raw URDRBRGI scene, the reference's witnesses, then tread a's or its refusal
        let scene = bearing::parse_scene(&read(&f)).unwrap_or_else(|Refusal(m)| refuse(&m));
        let p = bearing::picture(&scene);
        println!("ref {} {}", p.frame_digest(), p.pixel_sha256());
        let (b, o) = bearingfast::picture(&scene, bearingfast::A).unwrap_or_else(|Refusal(m)| refuse(&m));
        println!("a {} {}", bearing::frame_digest(&b), hex(&sha256(&o)));
        exit(0);
    }
    if court.is_some() || bbench > 0 {
        // BEARING-FAST-0: the court and the off-gate bench stand apart from both other paths
        if scene_path.is_some() || camera.is_some() || want_hud || want_fast || fast_bench > 0 || emit_bd > 0
            || want_struct || want_loc || loc_bench > 0 || want_g2 || want_g2threads || g2_bench > 0 || want_render
            || breakdown > 0 || loc_variant.is_some() || want_btable || btriple.is_some() || bench > 0
            || write_scene.is_some() || write_ppm.is_some() {
            refuse("--bearing-court and --bearing-bench take their own flags only");
        }
        if let Some(f) = court {
            bearingfast_court(&f, no_ref, threads_set, court_treads, no_digest);
        }
        bearingfast_bench(level, tiles, at, bbench, warm, tread);
    }
    if at.is_some() || want_btable || btriple.is_some() {
        // BEARING-0: the reference bearing kernel stands apart; no facing-path flag combines with it
        if scene_path.is_some() || camera.is_some() || want_hud || want_fast || fast_bench > 0 || emit_bd > 0
            || want_struct || want_loc || loc_bench > 0 || want_g2 || want_g2threads || g2_bench > 0 || want_render
            || breakdown > 0 || loc_variant.is_some() {
            refuse("--at, --bearing-table and --bearing-triple take --level, --tiles, --write-scene, --write-png, --bench and --warm only");
        }
        bearing_main(level, tiles, at, want_btable, btriple, bench, warm, write_scene, write_ppm);
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
        // GAUNTLET-1 / LOCALITY-0 LOCK: the sibling emits render the SAME frozen strips + frame; their bytes must
        // equal the frozen emit's, or they are not accepted renderers. The frame (buf) is read-only, so frame_digest
        // cannot move. `emit` is now the LOCKED blocked-layout floor DDA — the floor tile is swizzled ONCE into the
        // blocked execution format here at scene load, then read in the hot path (scene.floor is never touched there).
        let bf = fast::blocked_floor(&scene.floor);
        let mut rgb_fast = vec![0u8; W * H * 3];
        fast::emit(&scene, &first.strips, &first.frame, &mut rgb_fast, &bf);
        let fps = hex(&sha256(&rgb_fast));
        let firstdiff = rgb_fast.iter().zip(first.pixels.iter()).position(|(a, b)| a != b);
        println!("fast_pixels {}", fps);
        println!("fast_frame {}", fd); // fast never writes buf; the frame is the frozen one, echoed for the record
        println!("fast_equal {}", if firstdiff.is_none() && fps == ps { "OK" } else { "DIFFER" });
        // the archived linear-fetch DDA (fast::emit_linear), the immutable reference witness, must ALSO stay
        // byte-identical to frozen — the historical courts and the LOCK's baseline measure against it.
        let mut rgb_linear = vec![0u8; W * H * 3];
        fast::emit_linear(&scene, &first.strips, &first.frame, &mut rgb_linear);
        let lps = hex(&sha256(&rgb_linear));
        println!("linear_pixels {}", lps);
        println!("linear_equal {}", if lps == ps { "OK" } else { "DIFFER" });
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
        // GAUNTLET-1c (the row-major DDA — the LOCKED blocked `fast::emit` and its archived linear form `emit_linear`
        // share the recurrence, only the floor fetch layout differs): the floor's perspective divide is per-ROW, not
        // per-pixel — a bounded ~5 div_euclid/rem_euclid per floor row (the two step constants, the constant-axis
        // texel, the row's starting q/rem) against the collapse's 2 per floor pixel. A structural claim read off
        // fast.rs, NOT a wall-clock; the speed is gauntlet1c.py's separate host court. dda_div = 5*floor_rows.
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
        // GAUNTLET-1c DDA (`fast::emit_linear`, the archived linear-fetch reference — GAUNTLET-1c's own subject,
        // retained byte-identical under the LOCK), timed back to back over the SAME frozen strips + frame (all are
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
            fast::emit_linear(&scene, &first.strips, &first.frame, &mut rgb_fast);
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
        // to the archived linear DDA reference (emit_linear) — RE-BREAKDOWN-1's fixed subject, itself the frozen
        // oracle — so the ablated probes are a demonstrable SUBSET of the certified path, auditable not merely asserted.
        let mut rgb_emit = vec![0u8; W * H * 3];
        fast::emit_linear(&scene, &first.strips, &first.frame, &mut rgb_emit);
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
                fast::emit_linear(&scene, &first.strips, &first.frame, &mut e);
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
    if want_loc {
        // LOCALITY-0 differential (deterministic): both swizzled-floor emits byte-identical to frozen; each swizzle a
        // lossless bijection; the content (canonical order) unmoved while the execution format (swizzled bytes) moves;
        // and the per-band within-cache-line locality of each layout (the shear story). Runs on the current camera.
        use fast::locality as loc;
        let floor = &scene.floor;
        let sw_b = loc::swizzle_tile::<{ loc::BLOCKED }>(floor);
        let sw_m = loc::swizzle_tile::<{ loc::MORTON }>(floor);
        let mut r_b = vec![0u8; W * H * 3];
        loc::emit_swizzled::<{ loc::BLOCKED }>(&scene, &first.strips, &first.frame, &mut r_b, &sw_b);
        let mut r_m = vec![0u8; W * H * 3];
        loc::emit_swizzled::<{ loc::MORTON }>(&scene, &first.strips, &first.frame, &mut r_m, &sw_m);
        let mut r_l = vec![0u8; W * H * 3];
        loc::emit_swizzled::<{ loc::LINEAR }>(&scene, &first.strips, &first.frame, &mut r_l, floor);
        let od = |b: bool| if b { "OK" } else { "DIFFER" };
        // the LINEAR anchor must reproduce the archived linear-fetch DDA reference (fast::emit_linear) exactly
        let dda_ref = { let mut d = vec![0u8; W * H * 3]; fast::emit_linear(&scene, &first.strips, &first.frame, &mut d); d };
        println!("locality_pixels {}", ps);
        println!("locality_equal blocked={} morton={} linear_anchor={}",
                 od(hex(&sha256(&r_b)) == ps), od(hex(&sha256(&r_m)) == ps), od(r_l == dda_ref));
        // bijection: unswizzle(swizzle(tile)) == tile
        println!("locality_bijection blocked={} morton={}",
                 od(loc::unswizzle_tile::<{ loc::BLOCKED }>(&sw_b) == *floor),
                 od(loc::unswizzle_tile::<{ loc::MORTON }>(&sw_m) == *floor));
        // content-provenance vs execution-format: content hash (canonical order) unmoved; raw format bytes moved
        let content = hex(&sha256(floor));
        let content_b = hex(&sha256(&loc::unswizzle_tile::<{ loc::BLOCKED }>(&sw_b)));
        let content_m = hex(&sha256(&loc::unswizzle_tile::<{ loc::MORTON }>(&sw_m)));
        println!("locality_provenance content={} blocked_content_same={} morton_content_same={} blocked_fmt_moved={} morton_fmt_moved={}",
                 &content[..16], content_b == content, content_m == content,
                 hex(&sha256(&sw_b)) != content, hex(&sha256(&sw_m)) != content);
        // NON-VACUOUS bijection + format-move on a synthetic distinct-per-texel tile (the corpus floor is flat, so
        // its round-trip and format-move are trivially true; this exercises the permutation on data where a swizzle
        // bug WOULD show — the real regression guard behind locality0-bijection).
        let mut synth = vec![0u8; 256 * 256 * 3];
        for tj in 0..256usize {
            for ti in 0..256usize {
                for ch in 0..3usize {
                    synth[(tj * 256 + ti) * 3 + ch] = ((tj * 7 + ti * 13 + ch * 5) & 0xFF) as u8;
                }
            }
        }
        let ssb = loc::swizzle_tile::<{ loc::BLOCKED }>(&synth);
        let ssm = loc::swizzle_tile::<{ loc::MORTON }>(&synth);
        println!("locality_synth blocked_roundtrip={} morton_roundtrip={} blocked_fmt_moved={} morton_fmt_moved={}",
                 od(loc::unswizzle_tile::<{ loc::BLOCKED }>(&ssb) == synth),
                 od(loc::unswizzle_tile::<{ loc::MORTON }>(&ssm) == synth),
                 ssb != synth, ssm != synth);
        // NON-VACUOUS emit byte-identity: render the DISTINCT synthetic floor through linear vs blocked vs morton
        // (emit_swizzled takes the floor buffer as a parameter, so no scene mutation) — on flat corpus data every
        // layout trivially agrees; here a mis-indexed fetch would diverge. This is the real Objective-2 guard.
        let mut e_lin = vec![0u8; W * H * 3];
        loc::emit_swizzled::<{ loc::LINEAR }>(&scene, &first.strips, &first.frame, &mut e_lin, &synth);
        let mut e_b = vec![0u8; W * H * 3];
        loc::emit_swizzled::<{ loc::BLOCKED }>(&scene, &first.strips, &first.frame, &mut e_b, &ssb);
        let mut e_m = vec![0u8; W * H * 3];
        loc::emit_swizzled::<{ loc::MORTON }>(&scene, &first.strips, &first.frame, &mut e_m, &ssm);
        println!("locality_synthemit blocked={} morton={}", od(e_b == e_lin), od(e_m == e_lin));
        // per-band deterministic within-cache-line locality (permille), the shear story
        let band_line = |name: &str, bl: [(usize, usize); 3]| {
            let pm = |p: (usize, usize)| if p.0 > 0 { p.1 * 1000 / p.0 } else { 0 };
            println!("locality_bands_{} near={} mid={} far={}", name, pm(bl[0]), pm(bl[1]), pm(bl[2]));
        };
        band_line("linear", loc::band_locality::<{ loc::LINEAR }>(&scene, &first.strips, &first.frame));
        band_line("blocked", loc::band_locality::<{ loc::BLOCKED }>(&scene, &first.strips, &first.frame));
        band_line("morton", loc::band_locality::<{ loc::MORTON }>(&scene, &first.strips, &first.frame));
    }
    if loc_bench > 0 {
        // LOCALITY-0 host timing, process-isolated: this invocation runs exactly ONE variant (chosen by --variant),
        // so only that layout's code is hot. The orchestrator (verify/locality0.py) interleaves blocked and morton
        // invocations to cancel drift and compares their DDA-relative improvements. Never vs GAUNTLET-0's absolute.
        match loc_variant.as_deref() {
            Some("blocked") => locality_bench_variant::<{ fast::locality::BLOCKED }>(&scene, &first.strips, &first.frame, &ps, loc_bench, warm, "blocked"),
            Some("morton") => locality_bench_variant::<{ fast::locality::MORTON }>(&scene, &first.strips, &first.frame, &ps, loc_bench, warm, "morton"),
            Some("linear") => locality_bench_variant::<{ fast::locality::LINEAR }>(&scene, &first.strips, &first.frame, &ps, loc_bench, warm, "linear"),
            _ => refuse("--locality-bench needs --variant blocked|morton|linear"),
        }
    }
    if want_g2 {
        // GAUNTLET-2 correctness court (deterministic, gate-enforced): PARTITION INVARIANCE. The partition-agnostic
        // emit (fast::emit_partitioned) renders any partition of the columns, in any order, byte-identically to the
        // frozen picture — thread count and column partition are EXECUTION parameters, not rendering authority. NO
        // threads, NO host timing, NO promotion here (that is GAUNTLET-2's performance court, off-gate). T is only a
        // harness knob that GENERATES a partition spec; the kernel receives the actual column groups.
        let bf = fast::blocked_floor(&scene.floor);
        // deterministic partition-spec generators, each a partition of 0..W into groups (a Vec<Vec<usize>>)
        fn contiguous(t: usize) -> Vec<Vec<usize>> {
            let (base, extra) = (W / t, W % t);
            let mut g = Vec::new();
            let mut c = 0usize;
            for i in 0..t {
                let len = base + if i < extra { 1 } else { 0 };
                g.push((c..c + len).collect());
                c += len;
            }
            g
        }
        fn strided(t: usize) -> Vec<Vec<usize>> {
            let mut g = vec![Vec::new(); t];
            for c in 0..W {
                g[c % t].push(c);
            }
            g
        }
        fn singles() -> Vec<Vec<usize>> {
            (0..W).map(|c| vec![c]).collect()
        }
        fn reversed_spec(t: usize) -> Vec<Vec<usize>> {
            // a contiguous partition, but the GROUP order reversed AND each group's columns reversed — order must not matter
            let mut g = contiguous(t);
            for grp in g.iter_mut() {
                grp.reverse();
            }
            g.reverse();
            g
        }
        fn permuted(t: usize) -> Vec<Vec<usize>> {
            // a seeded Fisher-Yates shuffle of 0..W (fixed-seed LCG, deterministic), sliced into t groups — each group
            // an arbitrary column set in arbitrary within-group order
            let mut perm: Vec<usize> = (0..W).collect();
            let mut state: u64 = 0x9E3779B97F4A7C15;
            for i in (1..W).rev() {
                state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                let j = ((state >> 33) as usize) % (i + 1);
                perm.swap(i, j);
            }
            let (base, extra) = (W / t, W % t);
            let mut g = Vec::new();
            let mut idx = 0usize;
            for i in 0..t {
                let len = base + if i < extra { 1 } else { 0 };
                g.push(perm[idx..idx + len].to_vec());
                idx += len;
            }
            g
        }
        let specs: Vec<(&str, Vec<Vec<usize>>)> = vec![
            ("contig1", contiguous(1)),
            ("contig2", contiguous(2)),
            ("contig4", contiguous(4)),
            ("contig8", contiguous(8)),
            ("contig16", contiguous(16)),
            ("strided2", strided(2)),
            ("strided8", strided(8)),
            ("reversed8", reversed_spec(8)),
            ("single", singles()),
            ("permuted8", permuted(8)),
        ];
        println!("g2_pixels {}", ps);
        // emit_partitioned over the single whole-frame group must equal the LOCKED blocked emit byte-for-byte (the
        // partition core, at T=1, IS the accepted single-thread emit — no new correctness surface)
        let whole: Vec<usize> = (0..W).collect();
        let mut r_part = vec![0u8; W * H * 3];
        fast::emit_partitioned(&scene, &first.strips, &first.frame, &mut r_part, &bf, &whole);
        let mut r_emit = vec![0u8; W * H * 3];
        fast::emit(&scene, &first.strips, &first.frame, &mut r_emit, &bf);
        println!("g2_vs_emit {}", if r_part == r_emit && hex(&sha256(&r_part)) == ps { "OK" } else { "DIFFER" });
        for (name, groups) in &specs {
            // coverage: every column of 0..W covered exactly once (a true partition)
            let mut cover = vec![0u32; W];
            for grp in groups {
                for &c in grp {
                    if c < W {
                        cover[c] += 1;
                    }
                }
            }
            let cover_ok = cover.iter().all(|&v| v == 1);
            // render into a SENTINEL-filled buffer (a missed column would leave 0xAB, diverging from the frozen sha),
            // processing the groups in the spec's given order
            let mut buf_out = vec![0xABu8; W * H * 3];
            for grp in groups {
                fast::emit_partitioned(&scene, &first.strips, &first.frame, &mut buf_out, &bf, grp);
            }
            let equal_ok = hex(&sha256(&buf_out)) == ps;
            println!("g2_spec {} groups={} cover={} equal={}", name, groups.len(),
                     if cover_ok { "OK" } else { "BAD" }, if equal_ok { "OK" } else { "DIFFER" });
        }
        println!("g2_specs_total {}", specs.len());
    }
    if want_g2threads {
        // GAUNTLET-2 threaded byte-identity (deterministic, gate-enforced): emit_threaded — std::thread::scope, one
        // contiguous column group per thread, disjoint framebuffer writes — reproduces the frozen picture at every
        // thread count. The OUTPUT is deterministic though thread SCHEDULING is not (disjoint per-column writes), so
        // this is a valid gate check; no timing here (that is --gauntlet2-bench, off-gate). Sentinel-init so a missed
        // column would diverge.
        let bf = fast::blocked_floor(&scene.floor);
        for &t in &[1usize, 2, 4, 8, 16] {
            let mut o = vec![0xABu8; W * H * 3];
            fast::emit_threaded(&scene, &first.strips, &first.frame, &mut o, &bf, t);
            println!("g2t_thread {} equal={}", t, if hex(&sha256(&o)) == ps { "OK" } else { "DIFFER" });
        }
        println!("g2t_total 5");
    }
    if want_render {
        // GAUNTLET-2 LOCKED production render: fast::render is the accepted production fast path — mantle's frozen
        // strips + frame geometry, then the pixels via emit_threaded at the production default PROD_THREADS (T=8).
        // Byte-identical to the frozen picture (render_equal): the frame digest and pixel sha both reproduce the
        // witness. T=8 is a production EXECUTION parameter; the correctness court still judges all of {1,2,4,8,16}.
        let (_strips, frame, pixels) = fast::render(&scene);
        let rd = frame_digest(&frame);
        let rp = hex(&sha256(&pixels));
        println!("render_threads {}", fast::PROD_THREADS);
        println!("render_frame {}", rd);
        println!("render_pixels {}", rp);
        println!("render_equal {}", if rp == ps && rd == fd { "OK" } else { "DIFFER" });
    }
    if g2_bench > 0 {
        // GAUNTLET-2 performance court (off-gate, host): time emit_threaded at the EXPLICIT --threads T. Byte-identity
        // is checked FIRST and again after timing — no number is printed if the threaded emit diverged from the frozen
        // witness. p99 is compared (by the orchestrator verify/gauntlet2.py) ONLY against the sealed single-thread
        // baseline, never GAUNTLET-0's absolute, never a refresh-rate claim. One T per invocation for a clean measurement.
        let bf = fast::blocked_floor(&scene.floor);
        let t = n_threads.max(1);
        let mut rgb = vec![0u8; W * H * 3];
        fast::emit_threaded(&scene, &first.strips, &first.frame, &mut rgb, &bf, t);
        if hex(&sha256(&rgb)) != ps {
            refuse("gauntlet2-bench: the threaded emit did not reproduce the frozen witness; no number is printed");
        }
        let mut times: Vec<u128> = Vec::with_capacity(g2_bench);
        for k in 0..(warm + g2_bench) {
            let a0 = Instant::now();
            fast::emit_threaded(&scene, &first.strips, &first.frame, &mut rgb, &bf, t);
            let a1 = Instant::now();
            black_box(&rgb);
            if k >= warm {
                times.push((a1 - a0).as_micros());
            }
        }
        if hex(&sha256(&rgb)) != ps {
            refuse("gauntlet2-bench: the timed threaded emit diverged from the frozen witness; no number is printed");
        }
        let (p50, p95, p99, mx) = percentiles(times);
        println!("g2bench_threads {}", t);
        println!("g2bench_us p50={} p95={} p99={} max={}", p50, p95, p99, mx);
        println!("g2bench_equal OK");
        println!("{}", host_line());
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
