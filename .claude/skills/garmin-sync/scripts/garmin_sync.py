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
    import yaml
except ImportError:
    yaml = None

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

NGP_WINDOW_SECONDS = 30  # rolling-average window before the quartic mean, same convention as TrainingPeaks' NGP/NP

TRAINING_ZONES_CONFIG = ".claude/training-zones.yaml"


def load_threshold_speed_m_s(config_path: str = TRAINING_ZONES_CONFIG) -> float | None:
    """Load threshold pace (pace.threshold_sec_per_km) from training-zones.yaml, as m/s."""
    if yaml is None:
        return None
    path = Path(config_path)
    if not path.exists():
        return None
    try:
        config = yaml.safe_load(path.read_text()) or {}
    except Exception:  # noqa: BLE001 - malformed config shouldn't crash the sync
        return None
    threshold_sec_per_km = ((config.get("pace") or {}).get("threshold_sec_per_km"))
    if not threshold_sec_per_km:
        return None
    return 1000.0 / threshold_sec_per_km


def compute_if(ngp_speed_m_s: float | None, threshold_speed_m_s: float | None) -> float | None:
    """Intensity Factor = NGP speed / threshold speed (TrainingPeaks convention)."""
    if not ngp_speed_m_s or not threshold_speed_m_s:
        return None
    return ngp_speed_m_s / threshold_speed_m_s


def compute_tss(duration_s: float, intensity_factor: float | None) -> float | None:
    """Training Stress Score = duration_hours * IF^2 * 100 (TrainingPeaks convention)."""
    if intensity_factor is None or duration_s <= 0:
        return None
    return (duration_s / 3600.0) * (intensity_factor**2) * 100.0


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


def activity_calories(activity: dict) -> float | None:
    """Return Garmin's activity calorie estimate, handling API field variants."""
    for key in ("activeKilocalories", "activeCalories", "calories", "kilocalories"):
        value = activity.get(key)
        if value is not None:
            return float(value)
    return None


def fetch_activity_details(client: Garmin, activity_id: int) -> dict | None:
    """Fetch full per-second activity detail once, shared by run/walk split and NGP."""
    try:
        return client.get_activity_details(activity_id)
    except Exception as exc:  # noqa: BLE001 - soft warning, don't abort the sync
        print(f"  warning: could not fetch details for activity {activity_id}: {exc}", file=sys.stderr)
        return None


def _metric_index(details: dict, key: str) -> int | None:
    for descriptor in details.get("metricDescriptors", []) if isinstance(details, dict) else []:
        if descriptor.get("key") == key:
            return descriptor.get("metricsIndex")
    return None


def compute_run_walk_split(details: dict | None) -> tuple[float, float] | tuple[None, None]:
    """
    Estimate time spent running vs walking within an activity from
    second-by-second speed samples, classifying each sample against
    WALK_SPEED_THRESHOLD_M_S.

    Returns (run_seconds, walk_seconds), or (None, None) if detail samples
    aren't available for this activity.
    """
    if not details:
        return None, None

    speed_index = _metric_index(details, "directSpeed")
    duration_index = _metric_index(details, "sumDuration")
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


def compute_ngp(details: dict | None) -> float | None:
    """
    Normalized Graded Pace speed (m/s), TrainingPeaks-style: grade-adjusted
    speed (Garmin's own directGradeAdjustedSpeed, already corrected for
    elevation) smoothed over a rolling NGP_WINDOW_SECONDS window, then
    combined via a quartic mean (4th-power average, 4th root) so sustained
    surges count for more than a simple average - the same non-linear
    weighting TrainingPeaks uses for Normalized Power/NGP.

    Intentionally NOT gated on walk fraction: the quartic mean already does
    the right thing with a mix of hard efforts and walked/slow recovery -
    the hard segments dominate the 4th-power sum and the slow ones are
    naturally discounted, which is the whole point of NP/NGP (built for
    exactly this kind of variable-intensity session, e.g. intervals with
    walked recovery). It's least reliable on sessions with only one or two
    isolated brief surges in an otherwise slow/uncertain effort (e.g. the
    free-form pre-plan runs in week 1) - there a single surge can dominate
    the quartic mean more than it represents the session as a whole. Read
    those with more skepticism; they aren't used for coaching decisions
    anyway.

    Assumes 1 Hz samples (Garmin's activity detail stream); falls back to
    None if grade-adjusted speed or duration aren't available.
    """
    if not details:
        return None

    gap_index = _metric_index(details, "directGradeAdjustedSpeed")
    duration_index = _metric_index(details, "sumDuration")
    if gap_index is None or duration_index is None:
        return None

    entries = details.get("activityDetailMetrics", []) if isinstance(details, dict) else []
    series = []
    for entry in entries:
        values = entry.get("metrics", [])
        if max(gap_index, duration_index) >= len(values):
            continue
        ts, gap = values[duration_index], values[gap_index]
        if ts is None or gap is None:
            continue
        series.append((ts, gap))

    if len(series) < NGP_WINDOW_SECONDS:
        return None

    speeds = [gap for _, gap in series]
    window = NGP_WINDOW_SECONDS
    rolling_avgs = []
    running_sum = sum(speeds[:window])
    rolling_avgs.append(running_sum / window)
    for i in range(window, len(speeds)):
        running_sum += speeds[i] - speeds[i - window]
        rolling_avgs.append(running_sum / window)

    quartic_mean = (sum(v**4 for v in rolling_avgs) / len(rolling_avgs)) ** 0.25
    return quartic_mean


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


def build_activity_section(
    activity: dict, laps: list, run_walk_split: tuple, ngp_speed: float | None, threshold_speed_m_s: float | None, unit: str
) -> str:
    name = activity.get("activityName", "Untitled Activity")
    start_time = (activity.get("startTimeLocal") or "").replace("T", " ")
    label = activity_label(activity)

    distance = meters_to_distance(activity.get("distance", 0.0) or 0.0, unit)
    duration_s = activity.get("movingDuration") or activity.get("duration", 0.0) or 0.0
    speed = activity.get("averageSpeed", 0.0) or 0.0
    elevation = meters_to_elevation(activity.get("elevationGain", 0.0) or 0.0, unit)
    calories = activity_calories(activity)
    avg_hr = activity.get("averageHR")
    max_hr = activity.get("maxHR")
    run_s, walk_s = run_walk_split
    note = sanitize_note(activity.get("description") or "")
    intensity_factor = compute_if(ngp_speed, threshold_speed_m_s)
    tss = compute_tss(duration_s, intensity_factor)

    lines = [
        f"### {start_time} - {name}",
        "",
        f"**Type**: {label}",
        f"**Distance**: {distance:.2f} {distance_unit_label(unit)}",
        f"**Duration**: {format_duration(duration_s)}",
        f"**Pace**: {format_pace(speed, unit)}/{distance_unit_label(unit)}",
    ]
    if ngp_speed is not None:
        lines.append(f"**NGP medio**: {format_pace(ngp_speed, unit)}/{distance_unit_label(unit)}")
    if intensity_factor is not None:
        lines.append(f"**IF**: {intensity_factor:.2f}")
    if tss is not None:
        lines.append(f"**TSS**: {tss:.0f}")
    lines += [
        f"**Run time**: {format_duration(run_s) if run_s is not None else 'N/A'}",
        f"**Walk time**: {format_duration(walk_s) if walk_s is not None else 'N/A'}",
        f"**Elevation**: {elevation:.0f} {elevation_unit_label(unit)}",
    ]
    if calories is not None:
        lines.append(f"**Calories**: {calories:.0f} kcal")
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


def build_markdown(activities: list, start: date, end: date, unit: str, threshold_speed_m_s: float | None) -> str:
    total_distance_m = 0.0
    total_duration_s = 0.0
    total_elevation_m = 0.0
    total_calories = 0.0
    activities_with_calories = 0
    total_run_s = 0.0
    total_walk_s = 0.0
    total_tss = 0.0
    activities_with_tss = 0

    for activity, _laps, (run_s, walk_s), ngp_speed in activities:
        total_distance_m += activity.get("distance", 0.0) or 0.0
        activity_duration_s = activity.get("movingDuration") or activity.get("duration", 0.0) or 0.0
        total_duration_s += activity_duration_s
        total_elevation_m += activity.get("elevationGain", 0.0) or 0.0
        calories = activity_calories(activity)
        if calories is not None:
            total_calories += calories
            activities_with_calories += 1
        total_run_s += run_s or 0.0
        total_walk_s += walk_s or 0.0
        tss = compute_tss(activity_duration_s, compute_if(ngp_speed, threshold_speed_m_s))
        if tss is not None:
            total_tss += tss
            activities_with_tss += 1

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
        f"- **Total Calories**: {total_calories:.0f} kcal ({activities_with_calories}/{len(activities)} activities with data)",
    ]
    if activities_with_tss:
        lines.append(f"- **Total TSS**: {total_tss:.0f} ({activities_with_tss}/{len(activities)} activities with a valid NGP/IF)")
    lines += [
        "",
        "### Running Totals",
        f"- **Total Run Time**: {format_duration(total_run_s)}",
        f"- **Total Walk Time**: {format_duration(total_walk_s)}",
        "",
        "## Activities",
        "",
    ]

    for activity, laps, run_walk_split, ngp_speed in activities:
        lines.extend(build_activity_section(activity, laps, run_walk_split, ngp_speed, threshold_speed_m_s, unit).splitlines())

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
        details = fetch_activity_details(client, activity["activityId"])
        print(f"  computing run/walk split for '{activity.get('activityName')}'...")
        run_walk_split = compute_run_walk_split(details)
        ngp_speed = compute_ngp(details)
        enriched_activities.append((activity, laps, run_walk_split, ngp_speed))

    # Most recent first, to match the training-log convention used elsewhere in this project
    enriched_activities.sort(key=lambda item: item[0].get("startTimeLocal", ""), reverse=True)

    threshold_speed_m_s = load_threshold_speed_m_s()
    if threshold_speed_m_s is None:
        print("  note: no pace.threshold_sec_per_km in .claude/training-zones.yaml - skipping IF/TSS", file=sys.stderr)

    markdown = build_markdown(enriched_activities, start, end, args.unit, threshold_speed_m_s)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"week-{args.week}.md"
    output_path.write_text(markdown)

    print(f"\nWrote {output_path} ({len(enriched_activities)} activities)")


if __name__ == "__main__":
    main()
