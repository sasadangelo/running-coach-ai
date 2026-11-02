#!/usr/bin/env python3
"""
Upload planned running workouts to the Garmin Connect calendar, so the watch
downloads them on its next sync, and remove them once their day has passed.

Every workout this script creates carries MANAGED_MARKER in its description:
cleanup and replace only ever touch those, never workouts made by hand.

Commands:
    push SPEC.json   Remove past managed workouts, then upload and schedule
                     every workout in SPEC. A managed workout already scheduled
                     on the same date is replaced, so re-pushing a revised week
                     never leaves duplicates.
    cleanup          Unschedule and delete managed workouts dated before
                     --before (default today).
    list             Show managed workouts and their scheduled dates.

SPEC format (JSON):
    {
      "workouts": [
        {
          "date": "2026-11-03",
          "name": "S10 Light intervals",
          "description": "optional note shown in Garmin Connect",
          "steps": [
            {"type": "warmup", "distance_m": 500},
            {"repeat": 4, "steps": [
              {"type": "interval", "distance_m": 200, "pace": ["5:10", "5:30"]},
              {"type": "recovery", "time_s": 60}
            ]},
            {"type": "cooldown", "distance_m": 500}
          ]
        }
      ]
    }

Step types: warmup, interval, recovery, rest, cooldown. Each step ends after
exactly one of distance_m, time_s, or "lap": true (lap button). "pace" is an
optional [fast, slow] range in min:sec per km; without it the step has no target.

Requires:
    pip install -r ../requirements.txt

Credentials: same as garmin_sync.py (GARMIN_EMAIL, GARMIN_PASSWORD, GARMINTOKENS).

Usage:
    python3 garmin_workouts.py push week.json [--dry-run]
    python3 garmin_workouts.py cleanup [--before YYYY-MM-DD] [--dry-run]
    python3 garmin_workouts.py list
"""

import argparse
import json
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

MANAGED_MARKER = "[running-coach-ai]"

# How far back and ahead cleanup/replace look in the Garmin calendar
CALENDAR_LOOKBACK_DAYS = 120
CALENDAR_LOOKAHEAD_DAYS = 60

# Used only for the estimated duration of steps without a pace target
DEFAULT_PACE_SEC_PER_KM = 450

STEP_TYPES = {
    "warmup": (1, 1),
    "cooldown": (2, 2),
    "interval": (3, 3),
    "recovery": (4, 4),
    "rest": (5, 5),
}

NO_TARGET = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1}
PACE_TARGET = {"workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone", "displayOrder": 6}

RUNNING_SPORT = {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1}


def login(email: str, password: str, token_dir: str) -> Garmin:
    """Log in to Garmin Connect, reusing a cached session token if available."""
    client = Garmin(email=email, password=password)
    client.login(tokenstore=token_dir)
    return client


def connect() -> Garmin:
    if load_dotenv is not None:
        load_dotenv()
        load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    token_dir = os.path.expanduser(os.environ.get("GARMINTOKENS", "~/.garmin-running-coach-tokens"))
    if not email or not password:
        print("Set GARMIN_EMAIL and GARMIN_PASSWORD (env vars or .env file).", file=sys.stderr)
        sys.exit(1)
    print("Logging in to Garmin Connect...")
    return login(email, password, token_dir)


def parse_pace(text: str) -> int:
    """'5:10' -> 310 seconds per km."""
    minutes, seconds = text.strip().split(":")
    return int(minutes) * 60 + int(seconds)


def format_pace(sec_per_km: float) -> str:
    sec = round(sec_per_km)
    return f"{sec // 60}:{sec % 60:02d}"


class StepBuilder:
    """Turns SPEC steps into Garmin workout step dicts, numbering them in order."""

    def __init__(self) -> None:
        self.order = 0
        self.estimated_s = 0.0

    def build(self, steps: list[dict], multiplier: int = 1) -> list[dict]:
        return [self._build_one(step, multiplier) for step in steps]

    def _build_one(self, step: dict, multiplier: int) -> dict:
        self.order += 1
        if "repeat" in step:
            iterations = int(step["repeat"])
            order = self.order
            return {
                "type": "RepeatGroupDTO",
                "stepOrder": order,
                "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat", "displayOrder": 6},
                "numberOfIterations": iterations,
                "smartRepeat": False,
                "endCondition": {
                    "conditionTypeId": 7,
                    "conditionTypeKey": "iterations",
                    "displayOrder": 7,
                    "displayable": False,
                },
                "endConditionValue": float(iterations),
                "workoutSteps": self.build(step["steps"], multiplier * iterations),
            }

        step_type = step["type"]
        if step_type not in STEP_TYPES:
            raise ValueError(f"unknown step type {step_type!r} (use one of {', '.join(STEP_TYPES)})")
        type_id, type_order = STEP_TYPES[step_type]

        pace = step.get("pace")
        if pace:
            fast, slow = sorted(parse_pace(p) for p in pace)
            target = dict(PACE_TARGET, targetValueOne=1000.0 / slow, targetValueTwo=1000.0 / fast)
            est_pace = (fast + slow) / 2
        else:
            target = dict(NO_TARGET)
            est_pace = DEFAULT_PACE_SEC_PER_KM

        ends = [key for key in ("distance_m", "time_s", "lap") if step.get(key)]
        if len(ends) != 1:
            raise ValueError(f"step {step} needs exactly one of distance_m, time_s, lap")
        if "distance_m" in ends:
            condition = {"conditionTypeId": 3, "conditionTypeKey": "distance", "displayOrder": 3, "displayable": True}
            value = float(step["distance_m"])
            self.estimated_s += multiplier * value / 1000.0 * est_pace
        elif "time_s" in ends:
            condition = {"conditionTypeId": 2, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True}
            value = float(step["time_s"])
            self.estimated_s += multiplier * value
        else:
            condition = {"conditionTypeId": 1, "conditionTypeKey": "lap.button", "displayOrder": 1, "displayable": True}
            value = None

        result = {
            "type": "ExecutableStepDTO",
            "stepOrder": self.order,
            "stepType": {"stepTypeId": type_id, "stepTypeKey": step_type, "displayOrder": type_order},
            "endCondition": condition,
            "targetType": target,
        }
        if value is not None:
            result["endConditionValue"] = value
        if "distance_m" in ends:
            result["preferredEndConditionUnit"] = {"unitKey": "kilometer"}
        if step.get("note"):
            result["description"] = step["note"]
        return result


def build_workout(spec: dict) -> dict:
    builder = StepBuilder()
    steps = builder.build(spec["steps"])
    description = " ".join(filter(None, [spec.get("description", "").strip(), MANAGED_MARKER]))
    return {
        "workoutName": spec["name"],
        "description": description,
        "sportType": RUNNING_SPORT,
        "estimatedDurationInSecs": int(builder.estimated_s),
        "workoutSegments": [{"segmentOrder": 1, "sportType": RUNNING_SPORT, "workoutSteps": steps}],
    }


def describe_steps(steps: list[dict], indent: str = "    ") -> list[str]:
    """Human-readable preview of SPEC steps."""
    lines = []
    for step in steps:
        if "repeat" in step:
            lines.append(f"{indent}{step['repeat']} x:")
            lines.extend(describe_steps(step["steps"], indent + "    "))
            continue
        if step.get("distance_m"):
            amount = f"{step['distance_m'] / 1000:g} km"
        elif step.get("time_s"):
            amount = f"{int(step['time_s']) // 60}:{int(step['time_s']) % 60:02d} min"
        else:
            amount = "until lap button"
        pace = step.get("pace")
        target = f" @ {pace[0]}-{pace[1]}/km" if pace else ""
        lines.append(f"{indent}{step['type']}: {amount}{target}")
    return lines


def managed_workout_ids(client: Garmin) -> set[int]:
    ids = set()
    start = 0
    while True:
        page = client.get_workouts(start=start, limit=100) or []
        for workout in page:
            if MANAGED_MARKER in (workout.get("description") or ""):
                ids.add(int(workout["workoutId"]))
        if len(page) < 100:
            return ids
        start += 100


def scheduled_items(client: Garmin, start: date, end: date) -> list[dict]:
    """Calendar items of type workout between start and end (inclusive)."""
    items = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        calendar = client.get_scheduled_workouts(year, month) or {}
        for item in calendar.get("calendarItems") or []:
            if item.get("itemType") != "workout":
                continue
            item_date = date.fromisoformat(item["date"])
            if start <= item_date <= end:
                items.append(item)
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return items


def managed_schedule(client: Garmin) -> list[dict]:
    """Scheduled managed workouts in the calendar window, sorted by date."""
    managed = managed_workout_ids(client)
    today = date.today()
    items = scheduled_items(
        client,
        today - timedelta(days=CALENDAR_LOOKBACK_DAYS),
        today + timedelta(days=CALENDAR_LOOKAHEAD_DAYS),
    )
    return sorted(
        (item for item in items if int(item.get("workoutId") or 0) in managed),
        key=lambda item: item["date"],
    )


def remove(client: Garmin, items: list[dict], dry_run: bool) -> None:
    """Unschedule items and delete their workout templates."""
    for item in items:
        print(f"  - {item['date']} {item.get('title', '')}")
        if dry_run:
            continue
        client.unschedule_workout(item["id"])
        try:
            client.delete_workout(item["workoutId"])
        except Exception as exc:  # noqa: BLE001 - template may already be gone or shared by another date
            print(f"    (template {item['workoutId']} not deleted: {exc})")


def cleanup(client: Garmin, before: date, dry_run: bool) -> None:
    past = [item for item in managed_schedule(client) if date.fromisoformat(item["date"]) < before]
    if not past:
        print(f"No managed workouts before {before}.")
        return
    print(f"Removing {len(past)} managed workout(s) before {before}{' (dry run)' if dry_run else ''}:")
    remove(client, past, dry_run)


def cmd_push(args: argparse.Namespace) -> None:
    spec = json.loads(Path(args.spec).read_text())
    workouts = spec["workouts"]
    payloads = [(w, build_workout(w)) for w in workouts]

    for workout, payload in payloads:
        minutes = payload["estimatedDurationInSecs"] / 60
        print(f"{workout['date']}  {workout['name']}  (~{minutes:.0f} min)")
        print("\n".join(describe_steps(workout["steps"])))
    if args.dry_run:
        print("\nDry run: nothing sent to Garmin.")
        return

    client = connect()
    cleanup(client, date.today(), dry_run=False)

    dates = {w["date"] for w in workouts}
    replaced = [item for item in managed_schedule(client) if item["date"] in dates]
    if replaced:
        print(f"Replacing {len(replaced)} managed workout(s) already scheduled on those dates:")
        remove(client, replaced, dry_run=False)

    for workout, payload in payloads:
        created = client.upload_workout(payload)
        workout_id = created["workoutId"]
        client.schedule_workout(workout_id, workout["date"])
        print(f"Scheduled {workout['date']} {workout['name']} (workout {workout_id})")
    print("Done: the watch picks them up on its next sync.")


def cmd_cleanup(args: argparse.Namespace) -> None:
    before = date.fromisoformat(args.before) if args.before else date.today()
    cleanup(connect(), before, args.dry_run)


def cmd_list(args: argparse.Namespace) -> None:
    items = managed_schedule(connect())
    if not items:
        print("No managed workouts scheduled.")
        return
    for item in items:
        print(f"{item['date']}  {item.get('title', '')}  (workout {item['workoutId']}, schedule {item['id']})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Push planned workouts to the Garmin Connect calendar.")
    sub = parser.add_subparsers(dest="command", required=True)

    push = sub.add_parser("push", help="upload and schedule the workouts in a SPEC file")
    push.add_argument("spec", help="JSON file with the workouts (see module docstring)")
    push.add_argument("--dry-run", action="store_true", help="print the workouts without contacting Garmin")
    push.set_defaults(func=cmd_push)

    clean = sub.add_parser("cleanup", help="remove managed workouts whose date has passed")
    clean.add_argument("--before", help="remove workouts dated before this day (YYYY-MM-DD, default today)")
    clean.add_argument("--dry-run", action="store_true", help="list what would be removed")
    clean.set_defaults(func=cmd_cleanup)

    show = sub.add_parser("list", help="list managed scheduled workouts")
    show.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
