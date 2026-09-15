#!/usr/bin/env python3
"""Compute aerobic (pace:HR) decoupling for a single continuous-effort run.

Decoupling only means something on a sustained, uninterrupted effort long
enough for cardiovascular drift to show above noise (roughly 20+ minutes).
It is not meaningful on interval/rep sessions with recovery breaks.

Usage:
    python3 .claude/skills/garmin-sync/scripts/calculate_decoupling.py --date 2026-09-13 --type resistenza
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from garminconnect import Garmin
except ImportError:
    print("Missing dependency 'garminconnect'. Install the Garmin sync requirements.", file=sys.stderr)
    sys.exit(1)

DEFAULT_OUTPUT = "health-log/aerobic-decoupling.md"
MIN_DURATION_MINUTES = 20
MIN_SPEED_M_S = 0.3  # drop stopped/near-zero samples (traffic lights, etc.)
WALK_SPEED_THRESHOLD_M_S = 1.96  # same threshold as garmin_sync.py's run/walk split (~8:30/km)
MAX_WALK_FRACTION = 0.10  # more than this and it isn't a continuous effort

TYPE_LABELS = {
    "resistenza": "Resistenza aerobica",
    "capacita": "Capacita aerobica",
}


def login(email: str, password: str, token_dir: str) -> Garmin:
    client = Garmin(email=email, password=password)
    client.login(tokenstore=token_dir)
    return client


def find_activity(client: Garmin, day: str, name_contains: str | None) -> dict:
    activities = client.get_activities_by_date(day, day)
    running = [a for a in activities if "running" in (a.get("activityType", {}) or {}).get("typeKey", "").lower()]
    if name_contains:
        running = [a for a in running if name_contains.lower() in (a.get("activityName") or "").lower()]

    if not running:
        raise ValueError(f"No running activity found on {day}" + (f" matching '{name_contains}'" if name_contains else ""))
    if len(running) > 1:
        names = ", ".join(f"{a.get('activityName')} (id {a.get('activityId')})" for a in running)
        raise ValueError(f"Multiple running activities on {day}: {names}. Use --activity-name or --activity-id to disambiguate.")
    return running[0]


def extract_series(client: Garmin, activity_id: int) -> list[tuple[float, float, float]]:
    """Return a list of (elapsed_seconds, heart_rate, speed_m_s) samples."""
    details = client.get_activity_details(activity_id)
    descriptors = details.get("metricDescriptors", [])
    index = {d["key"]: d["metricsIndex"] for d in descriptors}
    for required in ("sumDuration", "directHeartRate", "directSpeed"):
        if required not in index:
            raise ValueError(f"Activity {activity_id} is missing '{required}' in its detail metrics")

    i_dur, i_hr, i_speed = index["sumDuration"], index["directHeartRate"], index["directSpeed"]
    series = []
    for entry in details.get("activityDetailMetrics", []):
        values = entry.get("metrics", [])
        dur, hr, speed = values[i_dur], values[i_hr], values[i_speed]
        if dur is None or hr is None or speed is None or speed < MIN_SPEED_M_S:
            continue
        series.append((dur, hr, speed))
    return series


def compute_decoupling(series: list[tuple[float, float, float]]) -> dict:
    if not series:
        raise ValueError("No usable HR/speed samples in this activity")

    total_duration = series[-1][0]
    if total_duration < MIN_DURATION_MINUTES * 60:
        raise ValueError(
            f"Activity is only {total_duration / 60:.1f} min of continuous effort; "
            f"need at least {MIN_DURATION_MINUTES} min for a reliable decoupling estimate"
        )

    walk_seconds = sum(1 for s in series if s[2] < WALK_SPEED_THRESHOLD_M_S)
    walk_fraction = walk_seconds / len(series)
    if walk_fraction > MAX_WALK_FRACTION:
        raise ValueError(
            f"{walk_fraction * 100:.0f}% of this activity is below running speed ({WALK_SPEED_THRESHOLD_M_S} m/s) - "
            "this looks like an interval session with recovery breaks, not a continuous effort. "
            "Decoupling only applies to sustained, uninterrupted runs (long runs, or a continuous tempo block)."
        )

    half = total_duration / 2
    first_half = [s for s in series if s[0] <= half]
    second_half = [s for s in series if s[0] > half]

    def avg(samples: list[tuple[float, float, float]], idx: int) -> float:
        return sum(s[idx] for s in samples) / len(samples)

    hr1, speed1 = avg(first_half, 1), avg(first_half, 2)
    hr2, speed2 = avg(second_half, 1), avg(second_half, 2)
    ef1 = speed1 / hr1
    ef2 = speed2 / hr2
    decoupling_pct = (ef1 - ef2) / ef1 * 100

    return {
        "total_minutes": total_duration / 60,
        "hr1": hr1, "speed1": speed1, "ef1": ef1,
        "hr2": hr2, "speed2": speed2, "ef2": ef2,
        "decoupling_pct": decoupling_pct,
    }


def pace_str(speed_m_s: float) -> str:
    if speed_m_s <= 0:
        return "N/A"
    min_per_km = 1000 / speed_m_s / 60
    minutes = int(min_per_km)
    seconds = round((min_per_km - minutes) * 60)
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d}/km"


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def render(cells: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)) + " |"

    return [render(headers), "| " + " | ".join("-" * w for w in widths) + " |", *[render(r) for r in rows]]


def update_log(path: Path, day: str, session_type: str, activity_name: str, distance_km: float, result: dict) -> None:
    label = TYPE_LABELS[session_type]
    row = [
        day,
        label,
        activity_name,
        f"{distance_km:.2f} km",
        f"{result['total_minutes']:.1f} min",
        pace_str(result["speed1"]),
        f"{result['hr1']:.0f} bpm",
        pace_str(result["speed2"]),
        f"{result['hr2']:.0f} bpm",
        f"{result['decoupling_pct']:.1f}%",
    ]

    headers = ["Data", "Tipo", "Attivita", "Distanza", "Durata", "Passo 1a meta", "FC 1a meta", "Passo 2a meta", "FC 2a meta", "Decoupling"]

    existing_rows = []
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith("| Data") or line.startswith("| ---") or not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and cells[0] != day:
                existing_rows.append(cells)
            elif cells and cells[0] == day and cells[2] != activity_name:
                # Same day, different activity (rare but possible) - keep both.
                existing_rows.append(cells)

    existing_rows.append(row)
    existing_rows.sort(key=lambda r: r[0])

    lines = [
        "# Aerobic Decoupling Log",
        "",
        "Pace:HR decoupling puro (split a meta tempo, efficiency factor passo/FC in ciascuna meta) su sessioni a sforzo continuo di almeno "
        f"{MIN_DURATION_MINUTES} minuti. Sotto il 5% e considerato buona tenuta aerobica per quel tipo di sforzo; valori piu alti indicano margine di miglioramento, non un problema.",
        "",
        "- **Resistenza aerobica**: decoupling sui lunghi (ritmo facile).",
        "- **Capacita aerobica**: decoupling su un tempo continuo a ritmo soglia/sub-soglia (nessuna sessione di questo tipo nel piano attuale).",
        "",
        *markdown_table(headers, existing_rows),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def parse_args():
    parser = argparse.ArgumentParser(description="Compute aerobic pace:HR decoupling for one continuous run")
    parser.add_argument("--date", required=True, help="YYYY-MM-DD of the activity")
    parser.add_argument("--activity-name", help="Substring to disambiguate if multiple runs happened that day")
    parser.add_argument("--activity-id", type=int, help="Skip lookup and use this Garmin activity ID directly")
    parser.add_argument("--type", choices=["resistenza", "capacita"], default="resistenza", help="Which pillar this session measures (default: resistenza)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help=f"Log file to update (default: {DEFAULT_OUTPUT})")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if load_dotenv:
        load_dotenv()
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        print("Set GARMIN_EMAIL and GARMIN_PASSWORD before running this script.", file=sys.stderr)
        return 1

    token_dir = os.path.expanduser(os.getenv("GARMINTOKENS") or "~/.garmin-running-coach-tokens")
    client = login(email, password, token_dir)

    try:
        if args.activity_id:
            activity = {"activityId": args.activity_id, "activityName": f"id {args.activity_id}", "distance": None}
        else:
            activity = find_activity(client, args.date, args.activity_name)

        series = extract_series(client, activity["activityId"])
        result = compute_decoupling(series)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    distance_km = (activity.get("distance") or 0) / 1000

    print(f"Activity: {activity.get('activityName')} ({args.date})")
    print(f"Duration: {result['total_minutes']:.1f} min | Distance: {distance_km:.2f} km")
    print(f"1st half: {pace_str(result['speed1'])}, {result['hr1']:.0f} bpm")
    print(f"2nd half: {pace_str(result['speed2'])}, {result['hr2']:.0f} bpm")
    print(f"Decoupling: {result['decoupling_pct']:.1f}% ({TYPE_LABELS[args.type]})")

    update_log(Path(args.output), args.date, args.type, activity.get("activityName") or "", distance_km, result)
    print(f"Logged to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
