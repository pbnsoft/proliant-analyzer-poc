# How It Works

## The workflow

1. **Discovery.** The manager (Compaq Insight Manager in the original) already knows the fleet — it monitors the estate and reports which servers it can see. The simulation prints that fleet: six fictional servers (WEB-01, DB-02, APP-03, FILE-04, MAIL-05, BAK-06).
2. **Licensing.** From the administration page, the administrator licenses servers out of a pool. The rule from the original product: a server **must be licensed to be monitored**, the analyzer came with **one free license** bundled with the purchase of the servers, and additional licenses were acquired separately through a licensing site. The pool here holds 1 free + 3 purchased = 4 licenses for 6 servers, so the pool runs out: FILE-04 and BAK-06 stay unlicensed, and the run says what the admin would do next (acquire more licenses).
3. **Monitoring preferences.** Each server carries a per-server monitoring preference, set on the same page. Licensing makes a server *eligible*; the preference makes it *active*. MAIL-05 is licensed but its preference is off.
4. **Periodic sync.** The administration side does not keep the licensed list to itself — it communicates the list of licensed servers to the manager periodically, and the licensing component syncs with it. The simulation performs one sync and prints the list exactly as the manager receives it.
5. **Bottleneck analysis.** Only servers that are licensed **and** preference-on are analyzed. FILE-04 and BAK-06 are skipped as unlicensed — FILE-04 is disk-bound by design, and the point is that the analyzer cannot say so, because it never sees the server. MAIL-05 is skipped as preference-off. Eligibility is not a footnote in this design; it is the gate, and it is enforced before any data is read.

## The bottleneck rule

The definition used in the original work: *a bottleneck occurs when the performance of one or more subsystems in a server keeps the server from running at its optimal speed.* The analyzer watches four subsystems — CPU, memory, disk, network — over a monitoring window (24 samples here) and applies one stated rule to the mean utilization:

> A subsystem is the **bottleneck** when its mean utilization is **≥ 90%** (sustained saturation) **while at least one other subsystem's mean is ≤ 40%** (the rest of the server is comparatively idle — waiting on the saturated one).

That second clause is what makes it a bottleneck rather than just a busy server: if everything is at 90%, the machine is simply loaded; if one subsystem is pinned while another idles, the pinned one is holding the whole server back, and it is the one to fix or upgrade. The fleet is seeded so the rule can be checked by hand:

| Server | Designed profile | Expected verdict |
|---|---|---|
| WEB-01 | balanced (all subsystems ~47–58%) | no bottleneck |
| DB-02 | disk-bound (disk ~95%, network ~27%) | bottleneck: **disk** |
| APP-03 | CPU-bound (CPU ~94%, disk ~24%) | bottleneck: **cpu** |
| FILE-04 | disk-bound by design | **not analyzed** — unlicensed |
| MAIL-05 | balanced by design | **not analyzed** — preference off |
| BAK-06 | CPU-bound by design | **not analyzed** — unlicensed (pool exhausted) |

The run's verification block asserts each of these outcomes and exits non-zero if any fails.

## The licensing model

- **Pool, not per-server purchase.** Licenses live in a pool the administrator draws from; the free license is consumed first, then purchased ones.
- **One free license.** Bundled with the analyzer as it shipped with the servers — enough to monitor exactly one server before money changes hands. In a six-server fleet that makes licensing a decision, not a default.
- **Exhaustion is visible.** When the pool empties, the page does not silently drop servers; the run names the unlicensed servers and the remedy (acquire more licenses from the licensing site). An admin always knows which servers are dark and why.
- **License ≠ monitoring.** A licensed server whose preference is off is synced to the manager as licensed but contributes no monitoring data until the preference is turned on.

## The original architecture, as described in the post

This simulation models behaviour, in modern Python, that the 2001–2003 original implemented with the era's Windows/COM stack. As the author describes it in his blog post:

- **The page.** The Performance Analyzer pages were JavaScript in the browser; the Administration & Licensing page was where monitoring preferences were set and ProLiant servers were licensed (with a link out to the licensing site to acquire a license key, then apply it to any of the user's servers).
- **The control.** Behind the page sat an administration control written in **Visual C++ 6.0** using **ActiveX, COM, and DCOM**. Its services, in the post's own list: identify the servers monitored by Compaq Insight Manager; communicate with CIM and provide the server list; provide CIM the list of licensed servers together with user preferences; and communicate with the licensing COM component to CIM **periodically** — the sync step this POC reproduces.
- **The test harness.** The team also built a desktop application to unit-test the control, offering the same functionality as the Administration & Licensing web page — an early instance of testing the gate separately from the page that renders it.

## Honest scope note — a model of the gate, not the analyzer product

This repository simulates the *administration and licensing behaviour* and a deliberately simple bottleneck rule over synthetic data. It is not the HP product, contains none of its code or data, and does not reproduce its real analysis (which worked over live subsystem counters from real servers, not seeded profiles). The fleet, the manager, and every number printed are fictional; the model names (subsystems, the 90%/40% thresholds, the pool size) are this POC's stated choices so the described behaviour — license first, preferences respected, licensed list synced, bottleneck = the subsystem holding the others back — can be run and checked. Read it as the chapter's argument in executable form: **in a monitoring system, the administration layer is not paperwork — it decides what is visible, and everything unlicensed is invisible.**
