# Boundaries — who may read and write what, and where the certified tree ends

The owner's amendment to FPS-GRAYBOX-0 (2026-10-09): *unsafe code is not automatically a contract violation;
unbounded authority across the boundary is.* This file names the boundaries as they stand. It adds no restriction to
the certified tree; it says where that tree's restrictions apply and where they stop.

```text
  ┌──────────────── the certified tree (held by the gate) ────────────────┐
  │ oracle/  kernel/  shell/  workshop/  verify/  design/                 │
  │ the design language ──► shell design-compile ──► shell design (admit) │
  └──────────────────────────────┬───────────────────────────────────────┘
                                 │  read only: a level's bytes (pinned by sha256),
                                 │  a layout read back through the design tool (with its heads)
  ┌──────────────────────────────▼───────────── graybox/ (FPS-GRAYBOX-0) ──┐
  │ level conversion   level.py: D ──► W (canonical) ──► C (collision)     │
  │ runtime shell      serve.py + the browser: window, input, lifecycle    │
  │ simulation         sim.js: moves against C; owns the game's state      │
  │ renderer           render.js: WebGL; draws W and the state; writes none│
  └────────────────────────────────────────────────────────────────────────┘
```

| boundary | its contract | held by |
|---|---|---|
| the certified tree | as the gate holds it, unchanged by the graybox: its rows, its pins (REASON-COURT-0's chain over every Rust source and sealer), its fences and the renderer's and bearing's identities. The design language says walls and floor and colours, and nothing about height, collision or gameplay | the gate (251 rows), at release checkpoints |
| level conversion | the walls and floor are the source's: the layout the design tool admitted, or a level file pinned by its sha256. The overlay adds height, cover and gameplay marks to floor cells only; a statement on rock is refused with its line. W carries every cell's source; C is W's tops and nothing else. No path into the runtime bypasses the converter | `graybox/check.py`: the conformance of W and C to D, by its own reader and search, and seven planted conversion defects refused |
| runtime shell | `serve.py` serves the runtime and the converted map on 127.0.0.1 only, writes nothing to disk, and reads nothing outside `graybox/` but the level file a map pins | its source, 112 lines |
| simulation | the only writer of the game's state. It reads C for movement and W's gameplay marks (spawns, targets, objective, probes, routes), never the render mesh. Fixed tick of 1/120 s; input arrives as one input record a tick, so a recorded sequence replays to the same state hashes on one build | the self-test: probes, routes, gravity, cover, weapon, occlusion, reset, and a replay hashed at every tick |
| renderer | draws W and the state; writes nothing the simulation reads. It may use whatever the platform offers behind its interface — today WebGL in the browser's sandbox — and is never asked whether a wall is there | `sim.js` has no reference to the renderer; `render.js` calls one function of the simulation, `Sim.aim`, which writes nothing; read in review |
| the interface | state flows from the simulation to the renderer only. Anything that would change the game — a click, a key — goes back as an input record of the next tick, through `Sim.step` and nowhere else | `main.js`, read in review |

**What needs review before it is accepted** (his words, kept): a change that expands the verified core's authority,
bypasses the registered conversion path, or alters a declared safety boundary.

**What is not claimed.** That the conversion is correct beyond what `check.py` checks: a source hash is provenance,
not proof of a faithful conversion. That the simulation is bit-for-bit the same across browsers or machines: replay
determinism is shown on one build in one page. That any software timing in the HUD is input-to-photon.
