#!/usr/bin/env python3
"""Sync Garmin daily recovery and sleep metrics into a markdown log."""

import argparse
import math
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
    print("Missing dependency 'garminconnect'. Install the Garmin sync requirements.", file=sys.stderr)
    sys.exit(1)


def login(email: str, password: str, token_dir: str) -> Garmin:
    client = Garmin(email=email, password=password)
    client.login(tokenstore=token_dir)
    return client


def resting_heart_rate(client: Garmin, day: str) -> float | None:
    data = client.get_rhr_day(day) or {}
    metrics_map = (data.get("allMetrics") or {}).get("metricsMap") or {}
    entries = metrics_map.get("WELLNESS_RESTING_HEART_RATE") or []
    for entry in entries:
        if entry.get("calendarDate") == day and entry.get("value") is not None:
            return float(entry["value"])
    return None


def hrv_value(client: Garmin, day: str) -> float | None:
    data = client.get_hrv_data(day) or {}
    value = (data.get("hrvSummary") or {}).get("lastNightAvg")
    return float(value) if value is not None else None


def as_minutes(seconds: object) -> str:
    if seconds is None:
        return "N/A"
    total_minutes = round(float(seconds) / 60)
    return f"{total_minutes // 60}h {total_minutes % 60:02d}m"


def sleep_values(rows: list[dict]) -> dict[str, dict]:
    result = {}
    for row in rows:
        day = row.get("calendarDate")
        if not day:
            continue
        values = row.get("values") or row
        result[day] = {
            "duration": values.get("totalSleepTimeInSeconds") or values.get("sleepTimeSeconds"),
            "deep": values.get("deepTime") or values.get("deepSleepSeconds"),
            "light": values.get("lightTime") or values.get("lightSleepSeconds"),
            "rem": values.get("remTime") or values.get("remSleepSeconds"),
            "awake": values.get("awakeTime") or values.get("awakeSleepSeconds"),
            "score": values.get("sleepScore") or values.get("sleepScoreValue"),
            "score_label": values.get("sleepScoreQuality") or values.get("sleepScoreFeedback"),
        }
    return result


def rolling_stats(values: list[float | None], index: int, window: int = 7) -> tuple[float | None, float | None]:
    available = [value for value in values[max(0, index - window + 1): index + 1] if value is not None]
    if len(available) < 3:
        return None, None
    average = sum(available) / len(available)
    deviation = math.sqrt(sum((value - average) ** 2 for value in available) / len(available))
    return average, deviation


def fmt(value: float | None, digits: int = 0) -> str:
    return "N/A" if value is None else f"{value:.{digits}f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def render(cells: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells)) + " |"

    return [render(headers), "| " + " | ".join("-" * width for width in widths) + " |", *[render(row) for row in rows]]


def build_markdown(rows: list[dict], start: date, end: date) -> str:
    hrv_values = [row["hrv"] for row in rows]
    rhr_values = [row["resting_hr"] for row in rows]
    lines = [
        f"# Daily Health Log: {start.isoformat()} to {end.isoformat()}",
        "",
        "Baseline: rolling 7-day average; acceptable range is average +/- 1 rolling standard deviation.",
        "Ranges are descriptive recovery signals, not medical reference ranges or diagnoses.",
        "",
        "## Recovery",
        "",
    ]
    recovery_rows = []
    for index, row in enumerate(rows):
        rhr_avg, rhr_std = rolling_stats(rhr_values, index)
        hrv_avg, hrv_std = rolling_stats(hrv_values, index)
        rhr_range = "N/A" if rhr_avg is None else f"{rhr_avg - rhr_std:.0f}-{rhr_avg + rhr_std:.0f}"
        hrv_range = "N/A" if hrv_avg is None else f"{hrv_avg - hrv_std:.0f}-{hrv_avg + hrv_std:.0f}"
        sleep = row["sleep"]
        recovery_rows.append([row["date"], f"{fmt(row['resting_hr'])} bpm", f"{rhr_range} bpm", f"{fmt(row['hrv'])} ms", f"{hrv_range} ms"])
    lines.extend(markdown_table(
        ["Date", "Resting HR", "7d acceptable range", "HRV (RMSSD)", "7d acceptable range"],
        recovery_rows,
    ))
    lines.extend([
        "",
        "## Sleep",
        "",
    ])
    sleep_rows = []
    for row in rows:
        sleep = row["sleep"]
        sleep_rows.append([
            row["date"],
            as_minutes(sleep.get("duration")),
            as_minutes(sleep.get("deep")),
            as_minutes(sleep.get("rem")),
            str(sleep.get("score", "N/A")),
        ])
    lines.extend(markdown_table(["Date", "Total sleep", "Deep sleep", "REM sleep", "Score"], sleep_rows))
    lines.extend([
        "",
        "## Interpretation Notes",
        "",
        "- A 7-day rolling baseline smooths day-to-day noise; it is not a clinical threshold.",
        "- Compare trends with sleep, symptoms, training load, and subjective fatigue.",
        "- Missing Garmin values are kept as N/A rather than inferred.",
        "",
    ])
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="Sync Garmin daily recovery and sleep metrics")
    parser.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="YYYY-MM-DD (defaults to today)")
    parser.add_argument("--output", default="health-log/daily-health.md", help="Output markdown path")
    return parser.parse_args()


def main():
    args = parse_args()
    if load_dotenv:
        load_dotenv()
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        print("Set GARMIN_EMAIL and GARMIN_PASSWORD before running this script.", file=sys.stderr)
        return 1

    start = date.fromisoformat(args.start_date)
    end = date.fromisoformat(args.end_date) if args.end_date else date.today()
    if end < start:
        print("--end-date must not be before --start-date", file=sys.stderr)
        return 1

    token_dir = os.path.expanduser(os.getenv("GARMINTOKENS") or "~/.garmin-running-coach-tokens")
    print(f"Fetching Garmin health and sleep data from {start} to {end}...")
    client = login(email, password, token_dir)
    sleep_by_day = sleep_values(client.get_sleep_daily(start.isoformat(), end.isoformat()) or [])
    rows = []
    current = start
    while current <= end:
        day = current.isoformat()
        row = {"date": day, "resting_hr": None, "hrv": None, "sleep": sleep_by_day.get(day, {})}
        try:
            row["resting_hr"] = resting_heart_rate(client, day)
        except Exception as exc:
            print(f"warning: could not fetch resting HR for {day}: {exc}", file=sys.stderr)
        try:
            row["hrv"] = hrv_value(client, day)
        except Exception as exc:
            print(f"warning: could not fetch HRV for {day}: {exc}", file=sys.stderr)
        rows.append(row)
        current += timedelta(days=1)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_markdown(rows, start, end))
    print(f"Wrote {output} ({len(rows)} days)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())