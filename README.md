# ProLiant Performance Analyzer — Administration & Licensing POC

A slow server is rarely slow everywhere: one subsystem — the disks, the processor — saturates while the rest of the machine waits on it, and that one subsystem is the bottleneck. In 2001–2003, at HP, the author of this book worked on a web-based performance analyzer for ProLiant servers that detected exactly that, and his part of it was the page that decided what got watched at all: the Administration & Licensing page. From that one page an administrator saw the servers the manager knew about, set each server's monitoring preferences, and licensed servers — because an unlicensed server was not monitored, full stop. This proof of concept is a clean-room simulation of that behaviour: a fictional fleet, a license pool with the same rule the original shipped with (one free license bundled with the servers, more acquired separately), per-server monitoring preferences, a periodic sync of the licensed-server list to the manager, and a bottleneck analysis that only ever sees licensed, opted-in servers.

Chapter 8 of *Ideas That Refused to Die* by Balasubramanian Natarajan (the HP ProLiant Performance Analyzer years, 2001–2003). The original description is the author's blog post: https://pbnsoft.blogspot.com/2010/05/hp-proliant-performance-analyzer-2002.html
**Live demo:** coming with the book's Explore section.

## What's inside

- `src/proliant_analyzer.py` — the simulation. Python 3, standard library only (`random` module, seeded). Discovery, licensing from a pool of 4 (1 free + 3 purchased) for a fleet of 6, monitoring preferences, a periodic sync step, bottleneck analysis, and a built-in verification block that checks the analyzer against the fleet's designed ground truth.
- `docs/` — the documentation folder: the bottleneck rule, the licensing model, the original COM/CIM architecture as described in the post, a run guide, and the honest scope note.
- `media/proliant-analyzer-film.mp4` — a short concept film: an early-2000s operations room, a wall of server gauges with one subsystem climbing into the red while the others idle, and an administrator licensing a server from a single web page.

## Quick start

```bash
python3 src/proliant_analyzer.py
```

Expected result: the fleet is discovered (6 fictional servers), 4 are licensed before the pool runs out, the licensed list is synced to the manager, and the analysis reports DB-02 **disk-bound**, APP-03 **CPU-bound**, and WEB-01 **balanced** — while the two unlicensed servers and the one preference-off server are skipped and never appear in the results. The run ends with a verification block: **7/7 checks passed**, exit code 0. The output is deterministic — run it twice and the numbers match.

## Notes

- Every server, utilization figure, and manager in this repository is **fictional** and generated from seeded profiles for demonstration.
- This is a **clean-room model** of behaviour described in a blog post. It contains no HP software, code, data, screenshots, or proprietary material; the original (a JavaScript page plus a Visual C++ 6.0 ActiveX/COM control talking to Compaq Insight Manager) is described in `docs/how-it-works.md`, not reproduced.
