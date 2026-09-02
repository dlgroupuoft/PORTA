#!/usr/bin/env python3
"""Compute wall-clock runtime for each experiment from its log file."""
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
TS_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]")
PLATFORM_RE = re.compile(r"Platform (\d+)/\d+: (\w+)")


def parse_ts(line: str) -> datetime | None:
    m = TS_RE.match(line)
    return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S") if m else None


def fmt(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}h{m:02d}m{s:02d}s"


def analyse(log: Path) -> None:
    lines = log.read_text().splitlines()
    start_ts = None
    end_ts = None
    markers: list[tuple[str, datetime]] = []  # (platform, ts)
    for line in lines:
        ts = parse_ts(line)
        if ts is None:
            continue
        if start_ts is None and "Experiment Runner" in line:
            start_ts = ts
        pm = PLATFORM_RE.search(line)
        if pm:
            markers.append((pm.group(2), ts))
        if line.rstrip().endswith("Done."):
            end_ts = ts

    if start_ts and end_ts:
        total = (end_ts - start_ts).total_seconds()
        print(f"\n=== {log.parent.parent.name} ({log.name}) ===")
        print(f"start: {start_ts}   end: {end_ts}   total: {fmt(total)}")
        # Per-platform: from Platform-N marker to next marker (or end)
        bounds = [ts for _, ts in markers] + [end_ts]
        print("  per platform:")
        for i, (plat, ts) in enumerate(markers):
            dur = (bounds[i + 1] - ts).total_seconds()
            print(f"    {plat:<10} {fmt(dur)}")
    else:
        print(f"[WARN] could not find bounds in {log}")


def main() -> None:
    totals = []
    for exp in sorted(ROOT.glob("exp*")):
        for log in sorted((exp / "logs").glob("*.log")):
            analyse(log)
            # also collect total for summary
            lines = log.read_text().splitlines()
            start = next((parse_ts(l) for l in lines if parse_ts(l) and "Experiment Runner" in l), None)
            end = next((parse_ts(l) for l in reversed(lines) if parse_ts(l) and l.rstrip().endswith("Done.")), None)
            if start and end:
                totals.append((exp.name, (end - start).total_seconds()))

    print("\n=== SUMMARY ===")
    grand = 0.0
    for name, secs in totals:
        print(f"  {name:<6} {fmt(secs)}")
        grand += secs
    print(f"  {'TOTAL':<6} {fmt(grand)}")


if __name__ == "__main__":
    main()
