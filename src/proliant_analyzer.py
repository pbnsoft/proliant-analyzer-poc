#!/usr/bin/env python3
"""
proliant_analyzer.py — ProLiant Performance Analyzer, administration &
licensing (proof of concept).

A clean-room simulation of the behaviour described in the author's blog post
about his 2001–2003 work at HP: a web-based analyzer that detects hardware
bottlenecks on a fleet of servers, where the administration page is the gate —
a server must be LICENSED before it can be monitored, each server carries a
monitoring preference, and the licensed-server list is synced periodically to
the central manager (Compaq Insight Manager in the original).

Everything here is fictional: the fleet, the utilization series, and the
manager are simulated with seeded random profiles. No HP software, data, or
proprietary material is used — this models the described behaviour only.

Python 3, standard library only (random module).

Usage:
    python3 src/proliant_analyzer.py

Exit code: 0 if every built-in verification check passes, 1 otherwise.
"""

import random
import sys

# ------------------------------------------------------------- the fleet ---
# Fictional servers, as "Insight Manager" discovery would report them.
# "profile" seeds the utilization series; "designed" is the ground truth the
# verification step checks the analyzer against.

SUBSYSTEMS = ["cpu", "memory", "disk", "network"]

FLEET = [
    dict(name="WEB-01",  role="web front end",   seed=1101, profile="balanced",
         designed="none"),
    dict(name="DB-02",   role="database",        seed=2202, profile="disk",
         designed="disk"),
    dict(name="APP-03",  role="application",     seed=3303, profile="cpu",
         designed="cpu"),
    dict(name="FILE-04", role="file shares",     seed=4404, profile="disk",
         designed="disk"),   # would be disk-bound — but it never gets a license
    dict(name="MAIL-05", role="mail relay",      seed=5505, profile="balanced",
         designed="none"),   # licensed, but its monitoring preference is OFF
    dict(name="BAK-06",  role="nightly backup",  seed=6606, profile="cpu",
         designed="cpu"),    # would be CPU-bound — but the license pool runs out
]

# Utilization profile shapes: subsystem -> (base %, jitter ±%)
PROFILES = {
    "balanced": {"cpu": (52, 6), "memory": (58, 5), "disk": (47, 6), "network": (55, 7)},
    "disk":     {"cpu": (34, 5), "memory": (52, 6), "disk": (95, 3), "network": (26, 5)},
    "cpu":      {"cpu": (95, 3), "memory": (31, 5), "disk": (24, 5), "network": (36, 6)},
}

SAMPLES = 24  # one monitoring window: 24 samples per subsystem

# ------------------------------------------------------- bottleneck rule ---
SATURATED = 90.0   # a subsystem at/above this mean is saturated
IDLE = 40.0        # another subsystem at/below this mean is being held back


def find_bottleneck(means):
    """Apply the bottleneck rule to one server's mean utilization.

    The classic signature from the post — "one subsystem keeps the server
    from running at its optimal speed": a subsystem is the bottleneck when
    its sustained (mean) utilization is >= 90% while at least one other
    subsystem sits at <= 40%, i.e. the rest of the server is waiting on it.

    Returns the limiting subsystem name, or None when the load is balanced.
    """
    for sub in SUBSYSTEMS:
        if means[sub] >= SATURATED and any(
            means[other] <= IDLE for other in SUBSYSTEMS if other != sub
        ):
            return sub
    return None


def utilization_series(server):
    """Generate the seeded utilization series for one server.

    Returns {subsystem: [samples]} with values clamped to 1–99%.
    """
    rng = random.Random(server["seed"])
    shape = PROFILES[server["profile"]]
    series = {}
    for sub in SUBSYSTEMS:
        base, jitter = shape[sub]
        series[sub] = [
            max(1.0, min(99.0, base + rng.uniform(-jitter, jitter)))
            for _ in range(SAMPLES)
        ]
    return series


# ------------------------------------------------------------ licensing ----
class LicensePool:
    """The license pool the administration page draws from.

    Per the post: the analyzer came with ONE free license bundled with the
    purchase of the servers; further licenses were acquired separately
    (through a licensing site). A server must hold a license to be monitored.
    """

    def __init__(self, free=1, purchased=3):
        self.free = free
        self.purchased = purchased
        self.assigned = {}  # server name -> "free" | "purchased"

    def available(self):
        used_free = sum(1 for kind in self.assigned.values() if kind == "free")
        used_purchased = len(self.assigned) - used_free
        return (self.free - used_free) + (self.purchased - used_purchased)

    def license_server(self, name):
        """Assign a license to a server. Returns the license kind, or None
        when the pool is exhausted (the admin must acquire more licenses)."""
        if name in self.assigned:
            return self.assigned[name]
        used_free = sum(1 for kind in self.assigned.values() if kind == "free")
        if used_free < self.free:
            kind = "free"
        elif len(self.assigned) - used_free < self.purchased:
            kind = "purchased"
        else:
            return None
        self.assigned[name] = kind
        return kind


class InsightManager:
    """Stand-in for the central manager (CIM in the original).

    Holds the discovered fleet and receives the licensed-server list on each
    periodic sync from the administration component.
    """

    def __init__(self, fleet):
        self.fleet = fleet
        self.licensed_servers = []

    def sync(self, licensed_names):
        """Periodic sync: the administration side communicates the current
        licensed-server list; the manager replaces its copy."""
        self.licensed_servers = sorted(licensed_names)
        return self.licensed_servers


# ------------------------------------------------------------------ run ----
def main():
    out = []
    out.append("=" * 68)
    out.append("PROLIANT PERFORMANCE ANALYZER — ADMINISTRATION & LICENSING (POC)")
    out.append("Fictional fleet, simulated manager, seeded data. Clean-room model.")
    out.append("=" * 68)

    manager = InsightManager(FLEET)
    pool = LicensePool(free=1, purchased=3)

    # (a) Discovery — the fleet as the manager reports it
    out.append("")
    out.append("1) DISCOVERY — fleet reported by Insight Manager:")
    for s in FLEET:
        out.append(f"   {s['name']:<8} {s['role']}")

    # (b) Licensing — one free license bundled, three purchased, pool of 4
    out.append("")
    out.append("2) LICENSING — pool: 1 free (bundled with the servers) "
               "+ 3 purchased = 4 licenses")
    # The administrator licenses the first four servers from the admin page.
    license_plan = ["WEB-01", "DB-02", "APP-03", "MAIL-05", "FILE-04", "BAK-06"]
    for name in license_plan:
        kind = pool.license_server(name)
        if kind:
            out.append(f"   {name:<8} licensed ({kind} license)")
        else:
            out.append(f"   {name:<8} NOT licensed — pool exhausted; "
                       "acquire more licenses from the licensing site")

    # (e) Periodic sync — licensed list communicated to the manager
    out.append("")
    out.append("3) PERIODIC SYNC — licensed-server list communicated to "
               "Insight Manager:")
    synced = manager.sync(pool.assigned.keys())
    out.append(f"   [{', '.join(synced)}]  ({len(synced)} servers)")
    out.append("   Licensing component acknowledged the list: OK")

    # (c) Monitoring preferences — set per server on the administration page
    preferences = {s["name"]: True for s in FLEET}
    preferences["MAIL-05"] = False  # admin turned this one off
    out.append("")
    out.append("4) MONITORING PREFERENCES (set per server on the admin page):")
    for s in FLEET:
        state = "on" if preferences[s["name"]] else "OFF"
        out.append(f"   {s['name']:<8} monitoring {state}")

    # (d) Bottleneck analysis — licensed AND preference-on servers only
    results = {}   # server name -> bottleneck subsystem or None
    out.append("")
    out.append("5) BOTTLENECK ANALYSIS — monitored servers only:")
    for s in FLEET:
        name = s["name"]
        if name not in pool.assigned:
            out.append(f"   {name:<8} SKIPPED — unlicensed servers are not monitored")
            continue
        if not preferences[name]:
            out.append(f"   {name:<8} SKIPPED — monitoring preference is off")
            continue
        series = utilization_series(s)
        means = {sub: sum(vals) / len(vals) for sub, vals in series.items()}
        verdict = find_bottleneck(means)
        results[name] = verdict
        means_txt = "  ".join(f"{sub} {means[sub]:.0f}%" for sub in SUBSYSTEMS)
        if verdict:
            out.append(f"   {name:<8} BOTTLENECK: {verdict}  ({means_txt})")
        else:
            out.append(f"   {name:<8} no bottleneck — load is balanced  ({means_txt})")

    # Verification — the designed ground truth vs the analyzer's verdicts
    out.append("")
    out.append("VERIFICATION")
    out.append("-" * 68)
    checks = []

    def check(label, ok):
        checks.append(ok)
        out.append(f"   [{'PASS' if ok else 'FAIL'}] {label}")

    check("DB-02 reported disk-bound (disk-bound by design)",
          results.get("DB-02") == "disk")
    check("APP-03 reported CPU-bound (CPU-bound by design)",
          results.get("APP-03") == "cpu")
    check("WEB-01 reported no bottleneck (balanced by design)",
          results.get("WEB-01") is None and "WEB-01" in results)
    check("FILE-04 absent from monitoring results (unlicensed)",
          "FILE-04" not in results)
    check("BAK-06 absent from monitoring results (unlicensed, pool exhausted)",
          "BAK-06" not in results)
    check("MAIL-05 absent from monitoring results (preference off)",
          "MAIL-05" not in results)
    check("Synced licensed list matches the pool's assignments",
          synced == sorted(pool.assigned.keys()))

    out.append("-" * 68)
    out.append(f"{sum(checks)}/{len(checks)} checks passed")
    out.append("=" * 68)

    print("\n".join(out))
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
