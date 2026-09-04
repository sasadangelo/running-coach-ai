#!/usr/bin/env python3
"""
Sync training activities from Garmin Connect and write a training-log/week-N.md
file with a per-activity section for each run, including lap-by-lap detail.

Requires:
    pip install -r ../requirements.txt

Credentials (env vars, or a .env file in the current directory):
    GARMIN_EMAIL
    GARMIN_PASSWORD
    GARMINTOKENS   (optional, defaults to ~/.garmin-running-coach-tokens - cached
                    session tokens so you don't need to log in / re-do MFA every sync)

Usage:
    python3 garmin_sync.py --week 3 --days 7
    python3 garmin_sync.py --week 3 --start-date 2024-01-15 --end-date 2024-01-21
    python3 garmin_sync.py --week 3 --unit km
"""

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from garminconnect import Garmin
except ImportError:
    print(
        "Missing dependency 'garminconnect'. Install with:\n"
        "    pip install -r skills/garmin-sync/requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)

METERS_PER_MILE = 1609.344
METERS_PER_FOOT = 0.3048

# Garmin activityType.typeKey -> display name used in the markdown output
ACTIVITY_TYPE_LABELS = {
    "running": "Run",
    "trail_running": "Run",
    "treadmill_running": "Run",
    "track_running": "Run",
    "cycling": "Ride",
    "road_biking": "Ride",
    "mountain_biking": "Ride",
    "indoor_cycling": "Ride",
    "lap_swimming": "Swim",
    "open_water_swimming": "Swim",
    "strength_training": "Strength",
    "hiking": "Hike",
    "walking": "Walk",
}

RUNNING_TYPE_KEYS = {
    "running",
    "trail_running",
    "treadmill_running",
    "track_running",
}

# Below this distance, a separate "Run" activity is almost always a stray
# start/stop blip (e.g. a watch accidentally started/stopped a few meters in)
# rather than a real training bout, so it's noise in the weekly log.
DEFAULT_MIN_ACTIVITY_DISTANCE_KM = 0.8

WALK_SPEED_THRESHOLD_M_S = 1.96  # ~8:30/km - below this a sample counts as walking


def login(email: str, password: str, token_dir: str) -> Garmin:
    """Log in to Garmin Connect, reusing a cached session token if available."""
    client = Garmin(email=email, password=password)
    client.login(tokenstore=token_dir)
    return client


def activity_label(activity: dict) -> str:
    type_key = (activity.get("activityType") or {}).get("typeKey", "")
    return ACTIVITY_TYPE_LABELS.get(type_key, type_key.replace("_", " ").title() or "Other")


def is_running_activity(activity: dict) -> bool:
    type_key = (activity.get("activityType") or {}).get("typeKey", "")
    return type_key in RUNNING_TYPE_KEYS


def is_noise_activity(activity: dict, min_distance_km: float) -> bool:
    distance_km = (activity.get("distance", 0.0) or 0.0) / 1000.0
    return distance_km < min_distance_km


def compute_run_walk_split(client: Garmin, activity_id: int) -> tuple[float, float] | tuple[None, None]:
    """
    Estimate time spent running vs walking within an activity from
    second-by-second speed samples. Garmin doesn't expose a simple
    "run time" / "walk time" field on the activity summary, so this fetches
    full activity detail (like runanalyze's GarminSyncService does for
    HR/speed) and classifies each sample against WALK_SPEED_THRESHOLD_M_S.

    Returns (run_seconds, walk_seconds), or (None, None) if detail samples
    aren't available for this activity.
    """
    try:
        details = client.get_activity_details(activity_id)
    except Exception as exc:  # noqa: BLE001 - soft warning, don't abort the sync
        print(f"  warning: could not fetch details for run/walk split on activity {activity_id}: {exc}", file=sys.stderr)
        return None, None

    descriptors = details.get("metricDescriptors", []) if isinstance(details, dict) else []
    speed_index = None
    duration_index = None
    for descriptor in descriptors:
        key = descriptor.get("key")
        idx = descriptor.get("metricsIndex")
        if key == "directSpeed":
            speed_index = idx
        elif key == "sumDuration":
            duration_index = idx

    if speed_index is None or duration_index is None:
        return None, None

    entries = details.get("activityDetailMetrics", []) if isinstance(details, dict) else []
    prev_ts = None
    run_seconds = 0.0
    walk_seconds = 0.0
    for entry in entries:
        values = entry.get("metrics", [])
        if speed_index >= len(values) or duration_index >= len(values):
            continue
        ts = values[duration_index]
        speed = values[speed_index]
        if ts is None or speed is None:
            continue
        if prev_ts is not None:
            dt = ts - prev_ts
            if dt > 0:
                if speed >= WALK_SPEED_THRESHOLD_M_S:
                    run_seconds += dt
                else:
                    walk_seconds += dt
        prev_ts = ts

    return run_seconds, walk_seconds


def meters_to_distance(meters: float, unit: str) -> float:
    return meters / METERS_PER_MILE if unit == "mi" else meters / 1000.0


def distance_unit_label(unit: str) -> str:
    return "mi" if unit == "mi" else "km"


def meters_to_elevation(meters: float, unit: str) -> float:
    return meters / METERS_PER_FOOT if unit == "mi" else meters


def elevation_unit_label(unit: str) -> str:
    return "ft" if unit == "mi" else "m"


def format_duration(seconds: float) -> str:
    seconds = int(round(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:d}:{minutes:02d}:{secs:02d}"


def format_pace(speed_m_s: float, unit: str) -> str:
    """Pace as MM:SS per mile/km. Returns 'N/A' for zero/near-zero speed."""
    if not speed_m_s or speed_m_s <= 0.05:
        return "N/A"
    distance_per_unit_m = METERS_PER_MILE if unit == "mi" else 1000.0
    seconds_per_unit = distance_per_unit_m / speed_m_s
    minutes, secs = divmod(int(round(seconds_per_unit)), 60)
    return f"{minutes}:{secs:02d}"


def fetch_laps(client: Garmin, activity_id: int) -> list:
    """
    Fetch lap/split data for an activity. Returns a list of dicts with
    distance_m, duration_s, avg_speed_m_s, avg_hr, elevation_gain_m -
    or an empty list if splits aren't available.

    Note: the exact shape of Garmin's splits response can vary by activity
    type; this defensively pulls from `lapDTOs` and falls back gracefully.
    """
    try:
        raw = client.get_activity_splits(activity_id)
    except Exception as exc:  # noqa: BLE001 - surface as a soft warning, don't abort the sync
        print(f"  warning: could not fetch laps for activity {activity_id}: {exc}", file=sys.stderr)
        return []

    lap_entries = raw.get("lapDTOs", []) if isinstance(raw, dict) else []
    laps = []
    for entry in lap_entries:
        laps.append(
            {
                "distance_m": entry.get("distance", 0.0) or 0.0,
                "duration_s": entry.get("movingDuration") or entry.get("duration", 0.0) or 0.0,
                "avg_speed_m_s": entry.get("averageSpeed", 0.0) or 0.0,
                "avg_hr": entry.get("averageHR"),
                "elevation_gain_m": entry.get("elevationGain", 0.0) or 0.0,
            }
        )
    return laps


def sanitize_note(text: str) -> str:
    """Collapse a free-text note to a single line."""
    return text.replace("\n", " ").replace("\r", " ").strip()


def format_markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    """Render a markdown table with columns padded to line up in raw text, not just when rendered."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def format_row(cells: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)) + " |"

    lines = [format_row(headers), "|-" + "-|-".join("-" * w for w in widths) + "-|"]
    lines.extend(format_row(row) for row in rows)
    return lines


def build_activity_section(activity: dict, laps: list, run_walk_split: tuple, unit: str) -> str:
    name = activity.get("activityName", "Untitled Activity")
    start_time = (activity.get("startTimeLocal") or "").replace("T", " ")
    label = activity_label(activity)

    distance = meters_to_distance(activity.get("distance", 0.0) or 0.0, unit)
    duration_s = activity.get("movingDuration") or activity.get("duration", 0.0) or 0.0
    speed = activity.get("averageSpeed", 0.0) or 0.0
    elevation = meters_to_elevation(activity.get("elevationGain", 0.0) or 0.0, unit)
    avg_hr = activity.get("averageHR")
    max_hr = activity.get("maxHR")
    run_s, walk_s = run_walk_split
    note = sanitize_note(activity.get("description") or "")

    lines = [
        f"### {start_time} - {name}",
        "",
        f"**Type**: {label}",
        f"**Distance**: {distance:.2f} {distance_unit_label(unit)}",
        f"**Duration**: {format_duration(duration_s)}",
        f"**Pace**: {format_pace(speed, unit)}/{distance_unit_label(unit)}",
        f"**Run time**: {format_duration(run_s) if run_s is not None else 'N/A'}",
        f"**Walk time**: {format_duration(walk_s) if walk_s is not None else 'N/A'}",
        f"**Elevation**: {elevation:.0f} {elevation_unit_label(unit)}",
    ]
    if avg_hr:
        hr_line = f"**Heart Rate**: {avg_hr:.0f} bpm"
        if max_hr:
            hr_line += f" (max: {max_hr:.0f})"
        lines.append(hr_line)
    if note:
        lines.append(f"**Note**: {note}")
    lines.append("")

    if laps:
        lines.append("#### Lap Details")
        lines.append("")
        rows = []
        for i, lap in enumerate(laps, 1):
            lap_distance = meters_to_distance(lap["distance_m"], unit)
            lap_pace = format_pace(lap["avg_speed_m_s"], unit)
            lap_hr = f"{lap['avg_hr']:.0f}" if lap["avg_hr"] else "N/A"
            lap_elevation = meters_to_elevation(lap["elevation_gain_m"], unit)
            rows.append(
                [
                    str(i),
                    f"{lap_distance:.2f} {distance_unit_label(unit)}",
                    format_duration(lap["duration_s"]),
                    f"{lap_pace}/{distance_unit_label(unit)}",
                    lap_hr,
                    f"{lap_elevation:.0f} {elevation_unit_label(unit)}",
                ]
            )
        lines.extend(format_markdown_table(["Lap", "Distance", "Time", "Pace", "HR", "Elevation"], rows))
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def build_markdown(activities: list, start: date, end: date, unit: str) -> str:
    total_distance_m = 0.0
    total_duration_s = 0.0
    total_elevation_m = 0.0
    total_run_s = 0.0
    total_walk_s = 0.0

    for activity, _laps, (run_s, walk_s) in activities:
        total_distance_m += activity.get("distance", 0.0) or 0.0
        total_duration_s += activity.get("movingDuration") or activity.get("duration", 0.0) or 0.0
        total_elevation_m += activity.get("elevationGain", 0.0) or 0.0
        total_run_s += run_s or 0.0
        total_walk_s += walk_s or 0.0

    lines = [
        f"# Training Log: {start.isoformat()} to {end.isoformat()}",
        "",
        "## Week Summary",
        "",
        "### Overall Totals",
        f"- **Total Activities**: {len(activities)}",
        f"- **Total Distance**: {meters_to_distance(total_distance_m, unit):.2f} {distance_unit_label(unit)}",
        f"- **Total Time**: {format_duration(total_duration_s)}",
        f"- **Total Elevation**: {meters_to_elevation(total_elevation_m, unit):.0f} {elevation_unit_label(unit)}",
        "",
        "### Running Totals",
        f"- **Total Run Time**: {format_duration(total_run_s)}",
        f"- **Total Walk Time**: {format_duration(total_walk_s)}",
        "",
        "## Activities",
        "",
    ]

    for activity, laps, run_walk_split in activities:
        lines.extend(build_activity_section(activity, laps, run_walk_split, unit).splitlines())

    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="Sync a week of Garmin Connect activities into training-log/week-N.md")
    parser.add_argument("--week", type=int, required=True, help="Training week number, used for the output filename")
    parser.add_argument("--start-date", type=str, help="YYYY-MM-DD (defaults to --days before --end-date)")
    parser.add_argument("--end-date", type=str, help="YYYY-MM-DD (defaults to today)")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days if --start-date is omitted (default: 7)")
    parser.add_argument("--unit", choices=["mi", "km"], default="mi", help="Distance/pace/elevation unit (default: mi)")
    parser.add_argument("--output-dir", type=str, default="training-log", help="Directory to write week-N.md into")
    parser.add_argument(
        "--min-distance-km",
        type=float,
        default=DEFAULT_MIN_ACTIVITY_DISTANCE_KM,
        help=f"Drop 'Run' activities shorter than this (stray start/stop blips, not real sessions). "
        f"Default: {DEFAULT_MIN_ACTIVITY_DISTANCE_KM}km. Use 0 to keep everything.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if load_dotenv:
        load_dotenv()

    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        print("Set GARMIN_EMAIL and GARMIN_PASSWORD (env vars or a .env file) before running this script.", file=sys.stderr)
        sys.exit(1)
    token_dir = os.path.expanduser(os.getenv("GARMINTOKENS") or "~/.garmin-running-coach-tokens")

    end = date.fromisoformat(args.end_date) if args.end_date else date.today()
    start = date.fromisoformat(args.start_date) if args.start_date else end - timedelta(days=args.days)

    print(f"Logging in to Garmin Connect as {email}...")
    client = login(email, password, token_dir)

    print(f"Fetching activities from {start.isoformat()} to {end.isoformat()}...")
    activities = client.get_activities_by_date(startdate=start.isoformat(), enddate=end.isoformat())
    activities = [activity for activity in activities if is_running_activity(activity)]
    noise = [a for a in activities if is_noise_activity(a, args.min_distance_km)]
    activities = [a for a in activities if not is_noise_activity(a, args.min_distance_km)]
    if noise:
        print(f"Ignoring {len(noise)} activities under {args.min_distance_km}km (stray start/stop blips):")
        for activity in noise:
            distance_km = (activity.get("distance", 0.0) or 0.0) / 1000.0
            print(f"  - {activity.get('startTimeLocal')} '{activity.get('activityName')}' ({distance_km:.2f}km)")
    print(f"Found {len(activities)} running activities.")

    enriched_activities = []
    for activity in activities:
        laps = fetch_laps(client, activity["activityId"])
        if len(laps) <= 1:
            # A single lap just means "the whole activity", nothing to break down
            laps = []
        else:
            print(f"  found {len(laps)} laps for '{activity.get('activityName')}'")
        print(f"  computing run/walk split for '{activity.get('activityName')}'...")
        run_walk_split = compute_run_walk_split(client, activity["activityId"])
        enriched_activities.append((activity, laps, run_walk_split))

    # Most recent first, to match the training-log convention used elsewhere in this project
    enriched_activities.sort(key=lambda item: item[0].get("startTimeLocal", ""), reverse=True)

    markdown = build_markdown(enriched_activities, start, end, args.unit)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"week-{args.week}.md"
    output_path.write_text(markdown)

    print(f"\nWrote {output_path} ({len(enriched_activities)} activities)")


if __name__ == "__main__":
    main()
