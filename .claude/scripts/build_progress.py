"""Build progressi.html: per-session-type progress dashboard from training-log/*.md.

Parses every activity in training-log/, classifies it (long, easy, tempo,
intervals, race, strides, warmup), extracts the work blocks from the lap
table and injects the resulting JSON into progress_template.html.

Usage:
    python .claude/scripts/build_progress.py
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "training-log"
TEMPLATE = Path(__file__).with_name("progress_template.html")
OUTPUT = ROOT / "progressi.html"

# Laps faster than this (sec/km) count as work in Tempo sessions.
TEMPO_WORK_MAX_PACE = 6 * 60 + 50
# Laps faster than this (sec/km) count as work in interval sessions.
INTERVAL_WORK_MAX_PACE = 6 * 60 + 30
# Laps of at least this temperature (°C) are flagged as warm.
WARM_TEMP_C = 22


def to_seconds(text: str) -> int:
    """Convert h:mm:ss or m:ss to seconds."""
    parts = [int(p) for p in text.strip().split(":")]
    total = 0
    for part in parts:
        total = total * 60 + part
    return total


def pace_seconds(text: str) -> int | None:
    """Convert '6:42/km' to seconds per km."""
    match = re.match(r"(\d+):(\d+)", text.strip())
    return int(match.group(1)) * 60 + int(match.group(2)) if match else None


def classify(name: str) -> str:
    """Map an activity name to a session type."""
    low = name.lower()
    if "riscaldamento" in low or "shakeout" in low:
        return "warmup"
    if re.search(r"\b5k\b|\b10k\b|gara", low):
        return "race"
    if "allungh" in low:
        return "strides"
    if "tempo" in low:
        return "tempo"
    if re.search(r"\d+\s*x\s*\d+", low):
        return "intervals"
    if "lung" in low:
        return "long"
    return "easy"


def parse_field(block: str, key: str) -> str | None:
    match = re.search(rf"^\*\*{re.escape(key)}\*\*:\s*(.+)$", block, re.M)
    return match.group(1).strip() if match else None


def parse_laps(block: str) -> list[dict[str, Any]]:
    laps = []
    for row in re.findall(r"^\|\s*\d+\s*\|(.+)\|$", block, re.M):
        cells = [c.strip() for c in row.split("|")]
        try:
            dist = float(cells[0].split()[0])
            secs = to_seconds(cells[1])
            hr = int(cells[3]) if cells[3].isdigit() else None
        except (ValueError, IndexError):
            continue
        if dist < 0.05:
            continue
        laps.append({"km": dist, "sec": secs, "pace": round(secs / dist), "hr": hr})
    return laps


def work_blocks(laps: list[dict[str, Any]], max_pace: int) -> list[dict[str, Any]]:
    """Group consecutive fast laps into work blocks (warm-up lap excluded)."""
    blocks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for i, lap in enumerate(laps):
        fast = lap["pace"] <= max_pace and i > 0
        if fast:
            current.append(lap)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    result = []
    for block in blocks:
        km = sum(l["km"] for l in block)
        sec = sum(l["sec"] for l in block)
        hr_laps = [l for l in block if l["hr"]]
        hr = (
            round(sum(l["hr"] * l["sec"] for l in hr_laps) / sum(l["sec"] for l in hr_laps))
            if hr_laps
            else None
        )
        result.append({"km": round(km, 2), "sec": sec, "pace": round(sec / km), "hr": hr})
    return result


def parse_activity(header: str, block: str) -> dict[str, Any] | None:
    match = re.match(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}):\d{2} - (.+)", header)
    if not match:
        return None
    day, clock, name = match.groups()
    distance = parse_field(block, "Distance")
    duration = parse_field(block, "Duration")
    if not distance or not duration:
        return None
    hr_text = parse_field(block, "Heart Rate") or ""
    hr_match = re.match(r"(\d+)", hr_text)
    meteo = parse_field(block, "Meteo") or ""
    temp_match = re.match(r"(-?\d+(?:\.\d+)?)°C", meteo)
    dew_match = re.search(r"rugiada (-?\d+(?:\.\d+)?)°C", meteo)
    rpe_text = parse_field(block, "RPE") or ""
    rpe_match = re.match(r"(\d+)", rpe_text)
    dec_text = parse_field(block, "Decoupling") or ""
    dec_match = re.match(r"(-?\d+(?:\.\d+)?)%", dec_text)
    es_text = parse_field(block, "ES") or ""
    es_match = re.match(r"(\d+(?:\.\d+)?)", es_text)

    def num(key: str) -> float | None:
        value = parse_field(block, key)
        m = re.match(r"(-?\d+(?:\.\d+)?)", value or "")
        return float(m.group(1)) if m else None

    run_time = parse_field(block, "Run time")
    walk_time = parse_field(block, "Walk time")
    laps = parse_laps(block)
    kind = classify(name)
    activity: dict[str, Any] = {
        "date": day,
        "time": clock,
        "name": name.strip(),
        "type": kind,
        "km": float(distance.split()[0]),
        "sec": to_seconds(duration),
        "pace": pace_seconds(parse_field(block, "Pace") or ""),
        "ngp": pace_seconds(parse_field(block, "NGP medio") or ""),
        "hr": int(hr_match.group(1)) if hr_match else None,
        "tss": num("TSS"),
        "rpe": int(rpe_match.group(1)) if rpe_match else None,
        "srpe": num("sRPE"),
        "decoupling": float(dec_match.group(1)) if dec_match else None,
        "es": float(es_match.group(1)) if es_match else None,
        "runSec": to_seconds(run_time) if run_time else None,
        "walkSec": to_seconds(walk_time) if walk_time else None,
        "temp": float(temp_match.group(1)) if temp_match else None,
        "dew": float(dew_match.group(1)) if dew_match else None,
        "note": parse_field(block, "Note") or "",
    }
    if kind == "tempo":
        activity["blocks"] = work_blocks(laps, TEMPO_WORK_MAX_PACE)
    elif kind == "intervals":
        activity["blocks"] = work_blocks(laps, INTERVAL_WORK_MAX_PACE)
    activity["warm"] = activity["temp"] is not None and activity["temp"] >= WARM_TEMP_C
    return activity


def week_start(day: str) -> str:
    d = datetime.strptime(day, "%Y-%m-%d").date()
    return (d - timedelta(days=d.weekday())).isoformat()


def collect() -> list[dict[str, Any]]:
    activities = []
    for path in LOG_DIR.glob("week-*.md"):
        text = path.read_text(encoding="utf-8")
        parts = re.split(r"^### ", text, flags=re.M)[1:]
        for part in parts:
            header, _, body = part.partition("\n")
            activity = parse_activity(header, body)
            if activity:
                activities.append(activity)
    activities.sort(key=lambda a: (a["date"], a["time"]))
    return activities


def weekly(activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    weeks: dict[str, dict[str, Any]] = {}
    for a in activities:
        w = weeks.setdefault(
            week_start(a["date"]),
            {"km": {}, "min": {}, "tss": 0.0, "srpe": 0.0, "runMin": 0.0, "walkMin": 0.0},
        )
        w["km"][a["type"]] = round(w["km"].get(a["type"], 0) + a["km"], 2)
        w["min"][a["type"]] = round(w["min"].get(a["type"], 0) + a["sec"] / 60, 1)
        w["tss"] += a["tss"] or 0
        w["srpe"] += a["srpe"] or 0
        w["runMin"] += (a["runSec"] or a["sec"]) / 60
        w["walkMin"] += (a["walkSec"] or 0) / 60
    result = []
    for start in sorted(weeks):
        w = weeks[start]
        result.append(
            {
                "start": start,
                "km": w["km"],
                "min": w["min"],
                "tss": round(w["tss"]),
                "srpe": round(w["srpe"]),
                "runMin": round(w["runMin"], 1),
                "walkMin": round(w["walkMin"], 1),
            }
        )
    return result


def main() -> None:
    activities = collect()
    data = {
        "generated": date.today().isoformat(),
        "activities": activities,
        "weeks": weekly(activities),
    }
    template = TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(activities)} activities, {len(data['weeks'])} weeks)")


if __name__ == "__main__":
    main()
