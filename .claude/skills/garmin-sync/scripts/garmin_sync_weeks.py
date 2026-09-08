#!/usr/bin/env python3
"""
Auto-sync every training week that's missing (or still in progress) in
training-log/.

training-log week numbering is a continuous log of real calendar weeks
(week-1, week-2, week-3, ...) - it is independent of the training plan's own
"Settimana N" phase numbering, since the athlete may have logged weeks
before the formal plan started. Each week is a fixed 7-day block starting
on WEEK_START_WEEKDAY (Monday by default, matching the convention recorded
in training-plan.md).

How it decides what to sync:
  - Reads training-log/week-N.md files to find the highest existing week
    number and its date range (from its own "# Training Log: START to END"
    header).
  - Continues forward in fixed 7-day blocks from there, one per week number,
    until the block containing today.
  - Re-syncs the last existing week too if it's still in progress (today
    falls within it), so newly logged activities get picked up.
  - If training-log is empty, an anchor start date must be given via
    --start-date (there's no way to know when the athlete's log should
    begin otherwise).

Also makes sure training-plan.md documents the week-start convention it
relies on (adds a note if one isn't already there).

Usage:
    python3 garmin_sync_weeks.py
    python3 garmin_sync_weeks.py --start-date 2026-08-24   # only needed the first time
    python3 garmin_sync_weeks.py --dry-run
"""

import argparse
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

WEEK_START_WEEKDAY_NAMES = {"monday": 0, "sunday": 6}
LOG_HEADER_RE = re.compile(r"#\s*Training Log:\s*(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})")
WEEK_FILE_RE = re.compile(r"week-(\d+)\.md$")

WEEK_START_NOTE_MARKER = "Settimane di allenamento"
WEEK_START_NOTES = {
    "monday": "- **Settimane di allenamento**: da lunedì a domenica",
    "sunday": "- **Settimane di allenamento**: da domenica a sabato",
}


def existing_log_range(week_file: Path) -> tuple[date, date] | None:
    if not week_file.exists():
        return None
    m = LOG_HEADER_RE.search(week_file.read_text())
    if not m:
        return None
    return date.fromisoformat(m.group(1)), date.fromisoformat(m.group(2))


def find_existing_weeks(training_log_dir: Path) -> dict[int, tuple[date, date]]:
    weeks = {}
    for path in training_log_dir.glob("week-*.md"):
        m = WEEK_FILE_RE.match(path.name)
        if not m:
            continue
        rng = existing_log_range(path)
        if rng:
            weeks[int(m.group(1))] = rng
    return weeks


def compute_weeks_to_sync(
    existing: dict[int, tuple[date, date]], anchor_start: date | None, today: date
) -> dict[int, tuple[date, date]]:
    pending: dict[int, tuple[date, date]] = {}

    if existing:
        max_week = max(existing)
        last_start, last_end = existing[max_week]
        if last_end >= today:
            pending[max_week] = (last_start, last_end)  # still in progress, refresh it
        cursor_start = last_end + timedelta(days=1)
        next_week_num = max_week + 1
    else:
        if anchor_start is None:
            raise ValueError(
                "training-log is empty and no --start-date was given - "
                "can't tell when the athlete's log should begin."
            )
        cursor_start = anchor_start
        next_week_num = 1

    while cursor_start <= today:
        cursor_end = cursor_start + timedelta(days=6)
        pending[next_week_num] = (cursor_start, cursor_end)
        next_week_num += 1
        cursor_start = cursor_end + timedelta(days=1)

    return pending


def ensure_week_start_documented(plan_path: Path, week_start: str) -> None:
    text = plan_path.read_text()
    if WEEK_START_NOTE_MARKER in text:
        return
    lines = text.splitlines()
    insert_at = 1
    for i, line in enumerate(lines):
        if line.strip().startswith("- **Durata piano**"):
            insert_at = i + 1
            break
    lines.insert(insert_at, WEEK_START_NOTES[week_start])
    plan_path.write_text("\n".join(lines) + "\n")
    print(f"Documented the week-start convention in {plan_path} (it wasn't there yet).")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plan-file", type=str, default="training-plan.md", help="Path to the training plan markdown file")
    parser.add_argument("--training-log-dir", type=str, default="training-log", help="Directory containing week-N.md files")
    parser.add_argument(
        "--week-start", choices=["monday", "sunday"], default="monday",
        help="Weekday each training-log week starts on (default: monday)",
    )
    parser.add_argument(
        "--start-date", type=str, default=None,
        help="YYYY-MM-DD anchor for week 1's start. Only needed the first time, when training-log is empty.",
    )
    parser.add_argument("--unit", choices=["mi", "km"], default="km", help="Distance/pace/elevation unit (default: km)")
    parser.add_argument("--min-distance-km", type=float, default=0.8, help="Passed through to garmin_sync.py")
    parser.add_argument("--dry-run", action="store_true", help="Show which weeks would be synced without calling Garmin")
    parser.add_argument("--skip-health", action="store_true", help="Skip daily HRV, resting HR, and sleep sync")
    return parser.parse_args()


def main():
    args = parse_args()

    plan_path = Path(args.plan_file)
    if plan_path.exists():
        ensure_week_start_documented(plan_path, args.week_start)

    training_log_dir = Path(args.training_log_dir)
    training_log_dir.mkdir(parents=True, exist_ok=True)

    existing = find_existing_weeks(training_log_dir)
    anchor_start = date.fromisoformat(args.start_date) if args.start_date else None
    if anchor_start and anchor_start.weekday() != WEEK_START_WEEKDAY_NAMES[args.week_start]:
        print(
            f"warning: --start-date {anchor_start.isoformat()} is a "
            f"{anchor_start.strftime('%A')}, not a {args.week_start.capitalize()} "
            f"({args.week_start} is the configured week-start day).",
            file=sys.stderr,
        )

    today = date.today()
    try:
        pending = compute_weeks_to_sync(existing, anchor_start, today)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if not pending:
        print("training-log is already up to date - nothing to sync.")
        return

    script_dir = Path(__file__).resolve().parent
    garmin_sync = script_dir / "garmin_sync.py"

    for week_num in sorted(pending):
        start, end = pending[week_num]
        print(f"\n=== Week {week_num}: {start.isoformat()} to {end.isoformat()} ===")
        cmd = [
            sys.executable, str(garmin_sync),
            "--week", str(week_num),
            "--start-date", start.isoformat(),
            "--end-date", end.isoformat(),
            "--unit", args.unit,
            "--output-dir", str(training_log_dir),
            "--min-distance-km", str(args.min_distance_km),
        ]
        if args.dry_run:
            print("  (dry run) " + " ".join(cmd))
            continue
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"garmin_sync.py failed for week {week_num}, stopping.", file=sys.stderr)
            sys.exit(result.returncode)

    if not args.skip_health:
        health_script = script_dir / "garmin_sync_health.py"
        health_start = min(start for start, _end in [*existing.values(), *pending.values()])
        health_end = date.today()
        health_cmd = [
            sys.executable, str(health_script),
            "--start-date", health_start.isoformat(),
            "--end-date", health_end.isoformat(),
        ]
        if args.dry_run:
            print("  (dry run) " + " ".join(health_cmd))
        else:
            result = subprocess.run(health_cmd)
            if result.returncode != 0:
                print("garmin_sync_health.py failed, stopping.", file=sys.stderr)
                sys.exit(result.returncode)

    verb = "Would sync" if args.dry_run else "Synced"
    print(f"\nDone. {verb} {len(pending)} week(s): {', '.join(str(w) for w in sorted(pending))}")


if __name__ == "__main__":
    main()
