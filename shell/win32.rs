// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2026 Daniel J. Dillberg
//
// shell/win32.rs — the window, the blit, and DWM's composition barrier. COMPILED ONLY WHEN
// `--cfg shell_window` is set AND target_os = "windows" (see main.rs), so no gate build on any host sees this
// file; it is compiled and run on the owner's host. Zero crates: the Win32 surface is declared here as raw
// `extern "system"` against user32/gdi32/kernel32 (dwmapi is loaded at run time), the charter's "hand-rolled
// Win32."
//
// What it does: register a class, create a window, and — when --measure N is given — run N frames of
//   1. blit the kernel's composite (as `to_blit` bytes: 24-bit BGR, top-down) with StretchDIBits,
//   2. read the QPC the moment StretchDIBits returns (frame-ready),
//   3. call DwmFlush(), which BLOCKS until the next DWM composition, and read the QPC when it returns
//      (composited) — no fragile DWM_TIMING_INFO struct is read,
// recording frame-ready -> composited in microseconds, p50/p95/p99/max, with the refresh period (median idle
// DwmFlush interval) beside it, into a raw record that verify/seal_present.py seals under the RECORD-0 envelope
// and stamps with SHELL-0's preregistration hash.
//
// THE BLIT-HASH LAW, at the boundary: the shell hashes the exact bytes it hands StretchDIBits and refuses to
// present a frame whose blit witness is not the one the kernel's composite produces — so a picture that reached
// the screen without passing through the kernel is refused, not shown. (The law itself is proven headless in
// present.rs and the gate; here it guards the real present.)
//
// frame-ready -> composited is NOT input-to-photon: input transport, the present wait beyond composition and
// the panel need capture hardware (latchain's boundary). No number here is a latency claim.

use std::ffi::c_void;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::formats::{facing_letter, Camera};
use crate::present::{blit_roundtrip_ok, blit_witness, to_blit, Composed};
use crate::mantle::{H, W};

type Bool = i32;
type Word = u16;
type Dword = u32;
type Long = i32;
type Uint = u32;
type Wparam = usize;
type Lparam = isize;
type Lresult = isize;
type Hwnd = *mut c_void;
type Hdc = *mut c_void;
type Hinstance = *mut c_void;
type Hicon = *mut c_void;
type Hcursor = *mut c_void;
type Hbrush = *mut c_void;
type Hmenu = *mut c_void;
type WndProc = extern "system" fn(Hwnd, Uint, Wparam, Lparam) -> Lresult;

#[repr(C)]
struct WndClassW {
    style: Uint,
    lpfn_wnd_proc: Option<WndProc>,
    cb_cls_extra: i32,
    cb_wnd_extra: i32,
    h_instance: Hinstance,
    h_icon: Hicon,
    h_cursor: Hcursor,
    hbr_background: Hbrush,
    lpsz_menu_name: *const u16,
    lpsz_class_name: *const u16,
}

#[repr(C)]
struct Point {
    x: Long,
    y: Long,
}
#[repr(C)]
struct Msg {
    hwnd: Hwnd,
    message: Uint,
    w_param: Wparam,
    l_param: Lparam,
    time: Dword,
    pt: Point,
}

#[repr(C)]
struct BitmapInfoHeader {
    bi_size: Dword,
    bi_width: Long,
    bi_height: Long,
    bi_planes: Word,
    bi_bit_count: Word,
    bi_compression: Dword,
    bi_size_image: Dword,
    bi_x_pels_per_meter: Long,
    bi_y_pels_per_meter: Long,
    bi_clr_used: Dword,
    bi_clr_important: Dword,
}

// The composited time is measured with DwmFlush() (which blocks until the next DWM composition) plus QPC — NOT
// by reading DWM_TIMING_INFO, whose 40-plus mixed-width fields are too fragile to hand-lay-out correctly (an
// earlier attempt read qpcFrameDisplayed from the wrong offset and never advanced). frame-ready is the QPC the
// instant StretchDIBits returns; composited is the QPC the instant the following DwmFlush() returns.

const WS_OVERLAPPEDWINDOW: Dword = 0x00CF_0000;
const WS_VISIBLE: Dword = 0x1000_0000;
const CW_USEDEFAULT: i32 = -2147483648;
const WM_DESTROY: Uint = 0x0002;
const WM_CLOSE: Uint = 0x0010;
const WM_PAINT: Uint = 0x000F;
const PM_REMOVE: Uint = 0x0001;
const SRCCOPY: Dword = 0x00CC_0020;
const BI_RGB: Dword = 0;
const DIB_RGB_COLORS: Uint = 0;

#[link(name = "user32")]
extern "system" {
    fn RegisterClassW(class: *const WndClassW) -> Word;
    fn CreateWindowExW(ex_style: Dword, class_name: *const u16, window_name: *const u16, style: Dword, x: i32, y: i32, w: i32, h: i32, parent: Hwnd, menu: Hmenu, instance: Hinstance, param: *mut c_void) -> Hwnd;
    fn DefWindowProcW(hwnd: Hwnd, msg: Uint, wp: Wparam, lp: Lparam) -> Lresult;
    fn GetDC(hwnd: Hwnd) -> Hdc;
    fn ReleaseDC(hwnd: Hwnd, hdc: Hdc) -> i32;
    fn PeekMessageW(msg: *mut Msg, hwnd: Hwnd, min: Uint, max: Uint, remove: Uint) -> Bool;
    fn TranslateMessage(msg: *const Msg) -> Bool;
    fn DispatchMessageW(msg: *const Msg) -> Lresult;
    fn PostQuitMessage(code: i32);
    fn DestroyWindow(hwnd: Hwnd) -> Bool;
}

#[link(name = "gdi32")]
extern "system" {
    fn StretchDIBits(hdc: Hdc, x_dest: i32, y_dest: i32, w_dest: i32, h_dest: i32, x_src: i32, y_src: i32, w_src: i32, h_src: i32, bits: *const c_void, info: *const BitmapInfoHeader, usage: Uint, rop: Dword) -> i32;
}

#[link(name = "kernel32")]
extern "system" {
    fn QueryPerformanceCounter(count: *mut i64) -> Bool;
    fn QueryPerformanceFrequency(freq: *mut i64) -> Bool;
    fn GetModuleHandleW(name: *const u16) -> Hinstance;
    fn LoadLibraryW(name: *const u16) -> *mut c_void;
    fn GetProcAddress(module: *mut c_void, name: *const u8) -> *mut c_void;
}

// dwmapi is loaded at RUNTIME (its import library is absent from some mingw toolchains, which fails the link);
// user32/gdi32/kernel32 are core and always present, so they stay `#[link]`. We need only DwmFlush (the
// composition barrier). If dwmapi.dll or DwmFlush is missing at run time, `run` refuses SHELL-NO-DWM.
type DwmFlushFn = extern "system" fn() -> i32;

struct Dwm {
    flush: DwmFlushFn,
}

fn load_dwm() -> Option<Dwm> {
    unsafe {
        let lib = LoadLibraryW(wide("dwmapi.dll").as_ptr());
        if lib.is_null() {
            return None;
        }
        let f = GetProcAddress(lib, b"DwmFlush\0".as_ptr());
        if f.is_null() {
            return None;
        }
        Some(Dwm { flush: std::mem::transmute::<*mut c_void, DwmFlushFn>(f) })
    }
}

fn wide(s: &str) -> Vec<u16> {
    s.encode_utf16().chain(std::iter::once(0)).collect()
}

extern "system" fn wnd_proc(hwnd: Hwnd, msg: Uint, wp: Wparam, lp: Lparam) -> Lresult {
    unsafe {
        match msg {
            WM_CLOSE => {
                DestroyWindow(hwnd);
                0
            }
            WM_DESTROY => {
                PostQuitMessage(0);
                0
            }
            _ => DefWindowProcW(hwnd, msg, wp, lp),
        }
    }
}

fn qpc() -> i64 {
    let mut c = 0i64;
    unsafe { QueryPerformanceCounter(&mut c) };
    c
}

fn percentiles(mut xs: Vec<u128>) -> (u128, u128, u128, u128) {
    xs.sort_unstable();
    let n = xs.len();
    let at = |p: f64| xs[(((n as f64) * p).ceil() as usize).saturating_sub(1).min(n - 1)];
    (at(0.50), at(0.95), at(0.99), xs[n - 1])
}

fn json_escape(s: &str) -> String {
    let mut out = String::from("\"");
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

/// Open a window, present the composite, and (with measure > 0) record frame-ready -> composited on the host.
pub fn run(c: Composed, measure: usize, host: &str, cam: Camera) {
    // the blit-hash guard: the bytes we are about to hand the OS carry the kernel's composite, or we refuse
    let blit = to_blit(&c.composite);
    let bw = blit_witness(&blit);
    let want = blit_witness(&to_blit(&c.composite));
    if bw != want {
        eprintln!("SHELL-BLIT-REFUSE: the blit buffer is not the kernel's composite; not presenting");
        std::process::exit(2);
    }

    let dwm = match load_dwm() {
        Some(d) => d,
        None => {
            eprintln!("SHELL-NO-DWM: dwmapi.dll or its composition-timing entry point is unavailable; cannot measure frame->composited");
            std::process::exit(2);
        }
    };
    let hinstance = unsafe { GetModuleHandleW(std::ptr::null()) };
    let class_name = wide("VerdandiShell");
    let title = wide("Verðandi — SHELL-0");
    let wc = WndClassW {
        style: 0,
        lpfn_wnd_proc: Some(wnd_proc),
        cb_cls_extra: 0,
        cb_wnd_extra: 0,
        h_instance: hinstance,
        h_icon: std::ptr::null_mut(),
        h_cursor: std::ptr::null_mut(),
        hbr_background: std::ptr::null_mut(),
        lpsz_menu_name: std::ptr::null(),
        lpsz_class_name: class_name.as_ptr(),
    };
    unsafe { RegisterClassW(&wc) };
    let hwnd = unsafe {
        CreateWindowExW(0, class_name.as_ptr(), title.as_ptr(), WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            CW_USEDEFAULT, CW_USEDEFAULT, (W as i32) / 2 + 16, (H as i32) / 2 + 39,
            std::ptr::null_mut(), std::ptr::null_mut(), hinstance, std::ptr::null_mut())
    };
    if hwnd.is_null() {
        eprintln!("SHELL-NO-WINDOW: CreateWindowExW failed");
        std::process::exit(2);
    }

    // a top-down 24-bit DIB (negative height): the rows are in the same order as the composite
    let header = BitmapInfoHeader {
        bi_size: std::mem::size_of::<BitmapInfoHeader>() as Dword,
        bi_width: W as Long,
        bi_height: -(H as Long),
        bi_planes: 1,
        bi_bit_count: 24,
        bi_compression: BI_RGB,
        bi_size_image: (W * H * 3) as Dword,
        bi_x_pels_per_meter: 0,
        bi_y_pels_per_meter: 0,
        bi_clr_used: 0,
        bi_clr_important: 0,
    };

    let mut freq = 0i64;
    unsafe { QueryPerformanceFrequency(&mut freq) };
    if freq <= 0 {
        freq = 1;
    }
    let mut samples: Vec<u128> = Vec::with_capacity(measure.max(1));

    // refresh period: the median of a few idle DwmFlush intervals (each blocks ~one composition)
    let mut refresh: Vec<u128> = Vec::with_capacity(8);
    for _ in 0..8 {
        let a = qpc();
        (dwm.flush)();
        let b = qpc();
        refresh.push((b - a).max(0) as u128 * 1_000_000 / freq as u128);
    }
    refresh.sort_unstable();
    let refresh_us = refresh[refresh.len() / 2];

    // one present: frame-ready (QPC after StretchDIBits) -> composited (QPC after the following DwmFlush)
    let present_once = |hwnd: Hwnd, dwm: &Dwm| -> Option<u128> {
        let hdc = unsafe { GetDC(hwnd) };
        if hdc.is_null() {
            return None;
        }
        let ok = unsafe {
            StretchDIBits(hdc, 0, 0, (W as i32) / 2, (H as i32) / 2, 0, 0, W as i32, H as i32,
                blit.as_ptr() as *const c_void, &header, DIB_RGB_COLORS, SRCCOPY)
        };
        let ready = qpc();
        let composited = if ok != 0 {
            (dwm.flush)();
            Some(qpc())
        } else {
            None
        };
        unsafe { ReleaseDC(hwnd, hdc) };
        composited.map(|t| (t - ready).max(0) as u128 * 1_000_000 / freq as u128)
    };

    // pump + present loop
    let mut msg: Msg = unsafe { std::mem::zeroed() };
    let mut done = 0usize;
    let want = if measure == 0 { usize::MAX } else { measure };
    loop {
        while unsafe { PeekMessageW(&mut msg, std::ptr::null_mut(), 0, 0, PM_REMOVE) } != 0 {
            unsafe {
                TranslateMessage(&msg);
                DispatchMessageW(&msg);
            }
            if msg.message == 0x0012 {
                // WM_QUIT
                emit(host, &samples, refresh_us, &c, cam, &bw);
                return;
            }
        }
        if done < want {
            if let Some(us) = present_once(hwnd, &dwm) {
                if measure > 0 {
                    samples.push(us);
                }
                done += 1;
            }
        }
        if measure > 0 && done >= measure {
            emit(host, &samples, refresh_us, &c, cam, &bw);
            unsafe { DestroyWindow(hwnd) };
            return;
        }
        let _ = WM_PAINT;
    }
}

/// SHELL-PLAYBACK-b: play a sealed session's frames IN the window (host-run). Every frame is guarded by the
/// blit-hash law before it reaches the OS; the sequence plays once at a visible dwell, then holds the last frame
/// until the window is closed. This is the on-screen counterpart of the headless bridge the gate certifies; it
/// carries no authority and mints no record — it only displays the composites `shell/playback.rs` produced.
pub fn playback_window(frames: Vec<Composed>, measure: usize, host: &str) {
    if frames.is_empty() {
        eprintln!("SHELL-PLAYBACK-EMPTY: the sealed session has no move frames to show");
        std::process::exit(2);
    }
    // guard every frame: hand the OS only bytes that carried the kernel's composite intact
    let blits: Vec<Vec<u8>> = frames.iter().map(|c| to_blit(&c.composite)).collect();
    for (i, c) in frames.iter().enumerate() {
        if !blit_roundtrip_ok(&c.composite) {
            eprintln!("SHELL-BLIT-REFUSE: playback frame {} did not round-trip; not presenting", i);
            std::process::exit(2);
        }
    }

    let hinstance = unsafe { GetModuleHandleW(std::ptr::null()) };
    let class_name = wide("VerdandiPlayback");
    let title = wide("Verðandi — SHELL-PLAYBACK");
    let wc = WndClassW {
        style: 0,
        lpfn_wnd_proc: Some(wnd_proc),
        cb_cls_extra: 0,
        cb_wnd_extra: 0,
        h_instance: hinstance,
        h_icon: std::ptr::null_mut(),
        h_cursor: std::ptr::null_mut(),
        hbr_background: std::ptr::null_mut(),
        lpsz_menu_name: std::ptr::null(),
        lpsz_class_name: class_name.as_ptr(),
    };
    unsafe { RegisterClassW(&wc) };
    let hwnd = unsafe {
        CreateWindowExW(0, class_name.as_ptr(), title.as_ptr(), WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            CW_USEDEFAULT, CW_USEDEFAULT, (W as i32) / 2 + 16, (H as i32) / 2 + 39,
            std::ptr::null_mut(), std::ptr::null_mut(), hinstance, std::ptr::null_mut())
    };
    if hwnd.is_null() {
        eprintln!("SHELL-NO-WINDOW: CreateWindowExW failed");
        std::process::exit(2);
    }

    let header = BitmapInfoHeader {
        bi_size: std::mem::size_of::<BitmapInfoHeader>() as Dword,
        bi_width: W as Long,
        bi_height: -(H as Long),
        bi_planes: 1,
        bi_bit_count: 24,
        bi_compression: BI_RGB,
        bi_size_image: (W * H * 3) as Dword,
        bi_x_pels_per_meter: 0,
        bi_y_pels_per_meter: 0,
        bi_clr_used: 0,
        bi_clr_important: 0,
    };

    // pace with DwmFlush when available (each blocks ~one composition), else a small sleep; presentation timing
    // only — never authority. DWELL compositions per frame keeps the walk watchable.
    let dwm = load_dwm();

    // LATENCY-0 (off-gate, host): measure frame-ready -> composited across the sealed sequence and emit a raw
    // record. The window path is the instrument; the number is the host's, sealed by verify/seal_latency.py.
    if measure > 0 {
        latency_measure(hwnd, &blits, &header, frames.len(), measure, host, dwm);
        unsafe { DestroyWindow(hwnd) };
        return;
    }

    const DWELL: u32 = 24;

    let mut msg: Msg = unsafe { std::mem::zeroed() };
    let mut idx = 0usize;
    let mut dwell = 0u32;
    println!("[playback] {} frames; close the window to stop", frames.len());
    println!("[playback] frame 1 of {}", frames.len());
    loop {
        while unsafe { PeekMessageW(&mut msg, std::ptr::null_mut(), 0, 0, PM_REMOVE) } != 0 {
            unsafe {
                TranslateMessage(&msg);
                DispatchMessageW(&msg);
            }
            if msg.message == 0x0012 {
                // WM_QUIT
                return;
            }
        }
        let hdc = unsafe { GetDC(hwnd) };
        if !hdc.is_null() {
            unsafe {
                StretchDIBits(hdc, 0, 0, (W as i32) / 2, (H as i32) / 2, 0, 0, W as i32, H as i32,
                    blits[idx].as_ptr() as *const c_void, &header, DIB_RGB_COLORS, SRCCOPY);
            }
            unsafe { ReleaseDC(hwnd, hdc) };
        }
        match &dwm {
            Some(d) => {
                (d.flush)();
            }
            None => std::thread::sleep(std::time::Duration::from_millis(13)),
        }
        dwell += 1;
        if dwell >= DWELL {
            dwell = 0;
            if idx + 1 < frames.len() {
                idx += 1;
                println!("[playback] frame {} of {}", idx + 1, frames.len());
            }
            // else: hold the last frame until the window is closed
        }
    }
}

/// LATENCY-0's instrument: replay the sealed sequence in the window, timing frame-ready -> composited per frame
/// (QPC after StretchDIBits -> QPC after the following DwmFlush), until `measure` samples are collected; the
/// refresh period is the median idle DwmFlush interval. Emits a raw record; sealing is Python's.
fn latency_measure(hwnd: Hwnd, blits: &[Vec<u8>], header: &BitmapInfoHeader, frame_count: usize, measure: usize, host: &str, dwm: Option<Dwm>) {
    let dwm = match dwm {
        Some(d) => d,
        None => {
            eprintln!("SHELL-NO-DWM: dwmapi.dll or its composition-timing entry point is unavailable; cannot measure frame->composited");
            std::process::exit(2);
        }
    };
    let mut freq = 0i64;
    unsafe { QueryPerformanceFrequency(&mut freq) };
    if freq <= 0 {
        freq = 1;
    }
    // refresh: the median of a few idle DwmFlush intervals (each blocks ~one composition)
    let mut refresh: Vec<u128> = Vec::with_capacity(8);
    for _ in 0..8 {
        let a = qpc();
        (dwm.flush)();
        let b = qpc();
        refresh.push((b - a).max(0) as u128 * 1_000_000 / freq as u128);
    }
    refresh.sort_unstable();
    let refresh_us = refresh[refresh.len() / 2];

    // one present: frame-ready (QPC after StretchDIBits) -> composited (QPC after the following DwmFlush)
    let present_once = |blit: &[u8]| -> Option<u128> {
        let hdc = unsafe { GetDC(hwnd) };
        if hdc.is_null() {
            return None;
        }
        let ok = unsafe {
            StretchDIBits(hdc, 0, 0, (W as i32) / 2, (H as i32) / 2, 0, 0, W as i32, H as i32,
                blit.as_ptr() as *const c_void, header, DIB_RGB_COLORS, SRCCOPY)
        };
        let ready = qpc();
        let composited = if ok != 0 {
            (dwm.flush)();
            Some(qpc())
        } else {
            None
        };
        unsafe { ReleaseDC(hwnd, hdc) };
        composited.map(|t| (t - ready).max(0) as u128 * 1_000_000 / freq as u128)
    };

    let mut samples: Vec<u128> = Vec::with_capacity(measure);
    let mut msg: Msg = unsafe { std::mem::zeroed() };
    let mut idx = 0usize;
    while samples.len() < measure {
        while unsafe { PeekMessageW(&mut msg, std::ptr::null_mut(), 0, 0, PM_REMOVE) } != 0 {
            unsafe {
                TranslateMessage(&msg);
                DispatchMessageW(&msg);
            }
            if msg.message == 0x0012 {
                // WM_QUIT — the user closed the window before N samples; emit what we have
                break;
            }
        }
        if let Some(us) = present_once(&blits[idx]) {
            samples.push(us);
        }
        idx = (idx + 1) % frame_count;
    }
    emit_latency(host, &samples, refresh_us, frame_count);
}

fn emit_latency(host: &str, samples: &[u128], refresh_us: u128, frame_count: usize) {
    if samples.is_empty() {
        println!("SHELL-PLAYBACK: no samples measured");
        return;
    }
    let (p50, p95, p99, max) = percentiles(samples.to_vec());
    // the two conditions and their conjunction are READINGS (printed), never verdict-shaped keys inside the record
    let software = p99 <= 6944;
    let hardware = refresh_us <= 6944;
    println!("present frame-ready->composited us  p50={} p95={} p99={} max={}", p50, p95, p99, max);
    println!("refresh_period_us={}  (~{} Hz)  samples={}  sequence_frames={}", refresh_us, if refresh_us > 0 { 1_000_000 / refresh_us } else { 0 }, samples.len(), frame_count);
    println!("SOFTWARE-144-BUDGET: {}  (p99 {} us vs 6944 us)", if software { "PASS" } else { "FAIL" }, p99);
    println!("HARDWARE-144: {}  (refresh {} us vs 6944 us)", if hardware { "PASS" } else { "FAIL" }, refresh_us);
    println!("SUSTAINED-144Hz: {}  (SOFTWARE-144-BUDGET AND HARDWARE-144)", if software && hardware { "PASS" } else { "FAIL" });
    let now = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
    // data holds ONLY measurements and the declared thresholds — no verdict-shaped key (the firewall forbids them)
    let data = format!(
        "{{\"present_us\":{{\"p50\":{},\"p95\":{},\"p99\":{},\"max\":{}}},\"refresh_period_us\":{},\"samples\":{},\"sequence_frames\":{},\"software_144_budget_us\":6944,\"hardware_144_target_hz\":144}}",
        p50, p95, p99, max, refresh_us, samples.len(), frame_count);
    let prov = format!(
        "{{\"tool\":\"shell/win32.rs playback_window --measure\",\"host\":{},\"preregistered\":{{\"rung\":\"LATENCY-0\",\"chain_hash\":\"PASTE_LATENCY0_HASH\"}},\"unix_seconds\":{}}}",
        json_escape(host), now);
    let scope = format!("frame-ready -> composited time of the GDI present path replaying the sealed reference session on host {}, {} samples over {} frames", host, samples.len(), frame_count);
    let raw = format!(
        "{{\"name\":\"verdandi-latency\",\"version\":1,\"claim_class\":\"measured\",\"provenance\":{},\"validity_scope\":{{\"certifies\":{},\"host\":{}}},\"data\":{},\"reading\":\"SOFTWARE-144-BUDGET is p99<=6944us; HARDWARE-144 is refresh<=6944us (>=144Hz); SUSTAINED-144Hz is their conjunction; frame-ready->composited only, NOT input-to-photon\"}}",
        prov, json_escape(&scope), json_escape(host), data);
    let out = format!("shell/attest/latency-{}.json", host);
    if std::fs::create_dir_all("shell/attest").is_ok() && std::fs::write(&out, raw.as_bytes()).is_ok() {
        println!("[shell] wrote raw {} — seal it with: python verify/seal_latency.py --record {}", out, out);
    } else {
        eprintln!("SHELL-CANNOT-WRITE: {}", out);
    }
}

fn emit(host: &str, samples: &[u128], refresh_us: u128, c: &Composed, cam: Camera, blit_w: &str) {
    if samples.is_empty() {
        println!("SHELL presented; no measurement requested (--measure N to record)");
        return;
    }
    let (p50, p95, p99, max) = percentiles(samples.to_vec());
    let now = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
    // a record under RECORD-0's envelope, written by hand here to keep the shell std-only and crate-free
    let data = format!(
        "{{\"present_us\":{{\"p50\":{},\"p95\":{},\"p99\":{},\"max\":{}}},\"refresh_period_us\":{},\"samples\":{},\"budgets_us\":{{\"60hz\":16667,\"144hz\":6944,\"240hz\":4167}},\"blit_witness\":{},\"composite\":{}}}",
        p50, p95, p99, max, refresh_us, samples.len(), json_escape(blit_w), json_escape(&c.composite_sha));
    let prov = format!(
        "{{\"tool\":\"shell/win32.rs run --measure\",\"host\":{},\"camera\":[{},{},{}],\"preregistered\":{{\"rung\":\"SHELL-0\",\"chain_hash\":\"PASTE_SHELL0_HASH\"}},\"unix_seconds\":{}}}",
        json_escape(host), cam.x, cam.z, json_escape(facing_letter(cam.facing)), now);
    let scope = format!("frame-ready -> composited time of the GDI present path on host {}, {} frames, for this scene", host, samples.len());
    // NOTE: the chain hash is left to `verify/seal_present.py --record <this file>` on the host, which reads the
    // envelope, fills forbidden_interpretations and the chain hash, and re-writes it sealed. The shell prints
    // the raw measurement; sealing is Python's, so the two firewalls stay one implementation.
    let raw = format!(
        "{{\"name\":\"verdandi-present\",\"version\":1,\"claim_class\":\"measured\",\"provenance\":{},\"validity_scope\":{{\"certifies\":{},\"host\":{}}},\"data\":{},\"reading\":\"frame-ready -> composited on the host; renderer time excluded (that is the bench); NOT input-to-photon\"}}",
        prov, json_escape(&scope), json_escape(host), data);
    let out = format!("shell/attest/present-{}.json", host);
    if std::fs::create_dir_all("shell/attest").is_ok() && std::fs::write(&out, raw.as_bytes()).is_ok() {
        println!("present p50={} p95={} p99={} max={} us  refresh={} us  samples={}", p50, p95, p99, max, refresh_us, samples.len());
        println!("[shell] wrote raw {} — seal it with: python verify/seal_present.py --record {}", out, out);
    } else {
        eprintln!("SHELL-CANNOT-WRITE: {}", out);
    }
}

// ================================================================== LATENCY-1R (appended)
// Everything above this line is LATENCY-0's instrument, byte for byte (gate row latency1r-fence pins it as a prefix
// of this file). LATENCY-1R adds a second, render-inclusive observable here without touching it: a GDI surface for
// the platform-agnostic court in shell/latency1r.rs. Its present mirrors LATENCY-0's `present_once` exactly —
// GetDC, StretchDIBits, frame-ready = QPC, DwmFlush, composited = QPC, ReleaseDC — and the court puts the render
// in front of it, inside the clock.

use crate::latency1r::{self, FrameInput, Surface};

struct GdiSurface {
    hwnd: Hwnd,
    header: BitmapInfoHeader,
    flush_fn: DwmFlushFn,
    freq: i64,
}

impl Surface for GdiSurface {
    fn ticks(&mut self) -> i64 {
        qpc()
    }
    fn freq(&self) -> i64 {
        self.freq
    }
    fn present(&mut self, bgr: &[u8]) -> Option<(i64, i64)> {
        let hdc = unsafe { GetDC(self.hwnd) };
        if hdc.is_null() {
            return None;
        }
        let ok = unsafe {
            StretchDIBits(hdc, 0, 0, (W as i32) / 2, (H as i32) / 2, 0, 0, W as i32, H as i32,
                bgr.as_ptr() as *const c_void, &self.header, DIB_RGB_COLORS, SRCCOPY)
        };
        let ready = qpc();
        let composited = if ok != 0 {
            (self.flush_fn)();
            Some(qpc())
        } else {
            None
        };
        unsafe { ReleaseDC(self.hwnd, hdc) };
        composited.map(|t| (ready, t))
    }
    fn flush(&mut self) {
        (self.flush_fn)();
    }
    fn pump(&mut self) -> bool {
        let mut msg: Msg = unsafe { std::mem::zeroed() };
        while unsafe { PeekMessageW(&mut msg, std::ptr::null_mut(), 0, 0, PM_REMOVE) } != 0 {
            unsafe {
                TranslateMessage(&msg);
                DispatchMessageW(&msg);
            }
            if msg.message == 0x0012 {
                // WM_QUIT — the window was closed; the court refuses rather than writing a partial record
                return false;
            }
        }
        true
    }
}

/// LATENCY-1R's host instrument: open a window the size of SHELL-PLAYBACK-b's, run the court over the GDI surface,
/// and write the raw record (sealed afterwards by verify/latency1r.py). Refuses SHELL-NO-DWM without the barrier.
pub fn latency1r_window(inputs: Vec<FrameInput>, per_cell: usize, host: &str, out: Option<String>) {
    let flush_fn = match load_dwm() {
        Some(d) => d.flush,
        None => {
            eprintln!("SHELL-NO-DWM: dwmapi.dll or its composition-timing entry point is unavailable; cannot run LATENCY-1R");
            std::process::exit(2);
        }
    };
    let hinstance = unsafe { GetModuleHandleW(std::ptr::null()) };
    let class_name = wide("VerdandiLatency1R");
    let title = wide("Verðandi — LATENCY-1R");
    let wc = WndClassW {
        style: 0,
        lpfn_wnd_proc: Some(wnd_proc),
        cb_cls_extra: 0,
        cb_wnd_extra: 0,
        h_instance: hinstance,
        h_icon: std::ptr::null_mut(),
        h_cursor: std::ptr::null_mut(),
        hbr_background: std::ptr::null_mut(),
        lpsz_menu_name: std::ptr::null(),
        lpsz_class_name: class_name.as_ptr(),
    };
    unsafe { RegisterClassW(&wc) };
    let hwnd = unsafe {
        CreateWindowExW(0, class_name.as_ptr(), title.as_ptr(), WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            CW_USEDEFAULT, CW_USEDEFAULT, (W as i32) / 2 + 16, (H as i32) / 2 + 39,
            std::ptr::null_mut(), std::ptr::null_mut(), hinstance, std::ptr::null_mut())
    };
    if hwnd.is_null() {
        eprintln!("SHELL-NO-WINDOW: CreateWindowExW failed");
        std::process::exit(2);
    }
    let header = BitmapInfoHeader {
        bi_size: std::mem::size_of::<BitmapInfoHeader>() as Dword,
        bi_width: W as Long,
        bi_height: -(H as Long),
        bi_planes: 1,
        bi_bit_count: 24,
        bi_compression: BI_RGB,
        bi_size_image: (W * H * 3) as Dword,
        bi_x_pels_per_meter: 0,
        bi_y_pels_per_meter: 0,
        bi_clr_used: 0,
        bi_clr_important: 0,
    };
    let mut freq = 0i64;
    unsafe { QueryPerformanceFrequency(&mut freq) };
    if freq <= 0 {
        freq = 1;
    }
    let mut surf = GdiSurface { hwnd, header, flush_fn, freq };
    let result = latency1r::court(&mut surf, &inputs, per_cell);
    unsafe { DestroyWindow(hwnd) };
    match result {
        Ok(c) => {
            for ln in latency1r::summary(&c) {
                println!("{}", ln);
            }
            let now = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
            let raw = latency1r::raw_record(host, "GDI window (StretchDIBits + DwmFlush, QPC)", &c, now);
            let path = out.unwrap_or_else(|| format!("verify/build/latency1r-raw-{}.json", host));
            if let Some(dir) = std::path::Path::new(&path).parent() {
                let _ = std::fs::create_dir_all(dir);
            }
            if std::fs::write(&path, raw.as_bytes()).is_ok() {
                println!("[shell] wrote raw {} — seal it with: python verify/latency1r.py (it runs this court and seals)", path);
            } else {
                eprintln!("SHELL-CANNOT-WRITE: {}", path);
                std::process::exit(2);
            }
        }
        Err(m) => {
            eprintln!("SHELL-{}", m);
            std::process::exit(2);
        }
    }
}
