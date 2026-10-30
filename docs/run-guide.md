# Run Guide

## Prerequisites

- Python 3.8 or later. Nothing to install — the simulation uses only the standard library (`random`, `sys`).

## Run it

From the repository root:

```bash
python3 src/proliant_analyzer.py
```

The run is deterministic (every server's utilization series comes from a fixed seed), prints five stages plus a verification block, and exits with code **0** when all checks pass.

## Reading the output

```
1) DISCOVERY — fleet reported by Insight Manager:
   WEB-01   web front end
   ...
2) LICENSING — pool: 1 free (bundled with the servers) + 3 purchased = 4 licenses
   WEB-01   licensed (free license)
   ...
   FILE-04  NOT licensed — pool exhausted; acquire more licenses from the licensing site
3) PERIODIC SYNC — licensed-server list communicated to Insight Manager:
   [APP-03, DB-02, MAIL-05, WEB-01]  (4 servers)
4) MONITORING PREFERENCES (set per server on the admin page):
   ...
   MAIL-05  monitoring OFF
5) BOTTLENECK ANALYSIS — monitored servers only:
   DB-02    BOTTLENECK: disk  (cpu 34%  memory 52%  disk 95%  network 27%)
   FILE-04  SKIPPED — unlicensed servers are not monitored
```

- **Stage 2** is the gate being built: watch which license kind each server gets (the free one first), and where the pool runs out.
- **Stage 3** is the sync from the post — the licensed list as the manager receives it. Note MAIL-05 is in it: licensing and monitoring are separate switches.
- **Stage 5** only ever contains licensed, preference-on servers. Skipped servers are named with their reason rather than silently absent — that visibility is part of the design.

## Check the verification by hand

The fleet is seeded with a designed ground truth. Expected outcomes — worth verifying on your first run:

| Check | Expected |
|---|---|
| DB-02 verdict | bottleneck: **disk** (disk mean ~95%, network ~27%) |
| APP-03 verdict | bottleneck: **cpu** (CPU mean ~94%, disk ~24%) |
| WEB-01 verdict | no bottleneck (all means between ~47% and ~58%) |
| FILE-04 in results? | **No** — unlicensed, though disk-bound by design |
| BAK-06 in results? | **No** — unlicensed; the pool ran out before it |
| MAIL-05 in results? | **No** — licensed, but monitoring preference off |
| Synced list | exactly the 4 licensed servers |

Totals: **7/7 checks passed**, exit code 0.

## Adapting the simulation

Everything tunable lives at the top of `src/proliant_analyzer.py`:

- **The fleet** — `FLEET`: add a server dict with a name, role, unique `seed`, a `profile`, and its `designed` ground truth. Profiles are `balanced`, `disk`, and `cpu` (shapes in `PROFILES`: per-subsystem base % and jitter). Add a designed bottleneck server *without* licensing it and the verification pattern extends naturally — it must be skipped, not analyzed.
- **The pool** — `LicensePool(free=1, purchased=3)` in `main()`. Raise `purchased` to 5 and FILE-04 and BAK-06 get licensed and analyzed (FILE-04 will report disk, BAK-06 cpu — and the built-in absence checks will fail, as they should: edit them in `main()` to match your scenario).
- **The rule** — `SATURATED` (90) and `IDLE` (40) are the stated thresholds in `find_bottleneck()`; the window length is `SAMPLES` (24).
- **Preferences** — the `preferences` dict in `main()`; MAIL-05 is the one switched off.

## Watch the film

`media/proliant-analyzer-film.mp4` is a short concept film of the world this chapter came from — an early-2000s operations room, a wall of server gauges with one subsystem climbing into the red while the others idle, and an administrator licensing a server from a single web page.
