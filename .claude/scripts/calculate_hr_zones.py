#!/usr/bin/env python3
"""Calculate heart-rate training zones from a YAML configuration file."""

import argparse
import math
import re
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_CONFIG = ".claude/training-zones.yaml"
DEFAULT_LOG = "health-log/heart-rate-zones.md"
DEFAULT_WEEK_LOG_DIR = "training-log"
TRAINING_LOG_HEADER = re.compile(r"#\s*Training Log:\s*(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})")


def round_bpm(value: float) -> int:
    """Round a heart rate to the nearest whole beat per minute."""
    return math.floor(value + 0.5)


def load_config(path: Path) -> dict:
    if yaml is None:
        raise ValueError("Missing dependency 'PyYAML'. Install it with: pip install pyyaml")
    try:
        config = yaml.safe_load(path.read_text())
    except FileNotFoundError:
        raise ValueError(f"Configuration file not found: {path}") from None
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from None

    if not isinstance(config, dict):
        raise ValueError("Configuration root must be a mapping")

    if config.get("method") != "karvonen":
        raise ValueError("Only the 'karvonen' method is currently supported")

    heart_rate = config.get("heart_rate") or {}
    max_hr = heart_rate.get("max")
    resting_hr = heart_rate.get("resting_average")
    if not isinstance(max_hr, (int, float)) or not isinstance(resting_hr, (int, float)):
        raise ValueError("heart_rate.max and heart_rate.resting_average must be numbers")
    if not 0 < resting_hr < max_hr:
        raise ValueError("heart_rate.resting_average must be greater than 0 and lower than heart_rate.max")

    zones = config.get("zones")
    if not isinstance(zones, list) or not zones:
        raise ValueError("zones must be a non-empty list")

    previous_max = None
    for zone in zones:
        if not zone.get("name"):
            raise ValueError("Every zone must have a name")
        min_percent = zone.get("min_percent")
        max_percent = zone.get("max_percent")
        if not isinstance(min_percent, (int, float)) or not isinstance(max_percent, (int, float)):
            raise ValueError(f"{zone['name']}: percentages must be numbers")
        if not 0 <= min_percent < max_percent <= 100:
            raise ValueError(f"{zone['name']}: percentages must satisfy 0 <= min < max <= 100")
        if previous_max is not None and min_percent != previous_max:
            raise ValueError("Zone percentage ranges must be contiguous and ordered")
        previous_max = max_percent

    if previous_max != 100:
        raise ValueError("Zone percentage ranges must end at 100%")
    return config


def calculate_zones(config: dict) -> list[dict]:
    max_hr = config["heart_rate"]["max"]
    resting_hr = config["heart_rate"]["resting_average"]
    heart_rate_reserve = max_hr - resting_hr

    results = []
    for zone in config["zones"]:
        lower = resting_hr + heart_rate_reserve * zone["min_percent"] / 100
        upper = resting_hr + heart_rate_reserve * zone["max_percent"] / 100
        results.append({
            "name": zone["name"],
            "min_percent": zone["min_percent"],
            "max_percent": zone["max_percent"],
            "min_bpm": round_bpm(lower),
            "max_bpm": round_bpm(upper),
        })
    return results


def markdown_output(config: dict, zones: list[dict]) -> str:
    max_hr = config["heart_rate"]["max"]
    resting_hr = config["heart_rate"]["resting_average"]
    reserve = max_hr - resting_hr
    lines = [
        "# Heart-Rate Training Zones",
        "",
        f"Method: Karvonen | Max HR: {max_hr} bpm | Resting HR average: {resting_hr} bpm | HR reserve: {reserve} bpm",
        "",
        "| Zone | % HRR | Heart rate |",
        "| --- | ---: | ---: |",
    ]
    for zone in zones:
        lines.append(
            f"| {zone['name']} | {zone['min_percent']:.0f}-{zone['max_percent']:.0f}% | "
            f"{zone['min_bpm']}-{zone['max_bpm']} bpm |"
        )
    lines.append("")
    return "\n".join(lines)


def log_entry(config: dict, zones: list[dict], calculated_on: date) -> str:
    max_hr = config["heart_rate"]["max"]
    resting_hr = config["heart_rate"]["resting_average"]
    reserve = max_hr - resting_hr
    lines = [
        f"## {calculated_on.isoformat()}",
        "",
        f"- **Metodo**: Karvonen",
        f"- **FC max**: {max_hr} bpm",
        f"- **FC riposo media**: {resting_hr} bpm",
        f"- **Riserva cardiaca**: {reserve} bpm",
        "",
        "| Zona | % HRR | FC |",
        "| --- | ---: | ---: |",
    ]
    for zone in zones:
        lines.append(
            f"| {zone['name']} | {zone['min_percent']:.0f}-{zone['max_percent']:.0f}% | "
            f"{zone['min_bpm']}-{zone['max_bpm']} bpm |"
        )
    return "\n".join(lines)


def write_log(path: Path, config: dict, zones: list[dict], calculated_on: date) -> None:
    heading = "# Heart-Rate Zones Log\n\n"
    existing = path.read_text() if path.exists() else heading
    entry = log_entry(config, zones, calculated_on)
    marker = f"## {calculated_on.isoformat()}"
    if marker in existing:
        before, remainder = existing.split(marker, 1)
        next_entry = remainder.find("\n## ")
        after = remainder[next_entry:] if next_entry >= 0 else ""
        existing = before.rstrip() + "\n\n" + entry + after
    else:
        existing = existing.rstrip() + "\n\n" + entry
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(existing.rstrip() + "\n")


def current_week_file(directory: Path, calculated_on: date) -> Path:
    for path in sorted(directory.glob("week-*.md")):
        match = TRAINING_LOG_HEADER.search(path.read_text())
        if not match:
            continue
        start = date.fromisoformat(match.group(1))
        end = date.fromisoformat(match.group(2))
        if start <= calculated_on <= end:
            return path
    raise ValueError(f"Could not find a training log containing {calculated_on.isoformat()}")


def write_week_log(path: Path, config: dict, zones: list[dict], calculated_on: date) -> None:
    section = log_entry(config, zones, calculated_on).replace(f"## {calculated_on.isoformat()}", "## Heart-Rate Zones")
    existing = path.read_text()
    marker = "## Heart-Rate Zones"
    if marker in existing:
        before, remainder = existing.split(marker, 1)
        next_section = remainder.find("\n## ")
        after = remainder[next_section:] if next_section >= 0 else ""
        existing = before.rstrip() + "\n\n" + section + after
    else:
        existing = existing.rstrip() + "\n\n" + section
    path.write_text(existing.rstrip() + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate Karvonen heart-rate training zones from YAML")
    parser.add_argument("--config", type=Path, default=Path(DEFAULT_CONFIG), help=f"YAML configuration file (default: {DEFAULT_CONFIG})")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format (default: markdown)")
    parser.add_argument("--log", type=Path, default=Path(DEFAULT_LOG), help=f"Weekly history file (default: {DEFAULT_LOG})")
    parser.add_argument("--week", type=int, help="Training week number to update (default: week containing today)")
    parser.add_argument("--week-log-dir", type=Path, default=Path(DEFAULT_WEEK_LOG_DIR), help=f"Training log directory (default: {DEFAULT_WEEK_LOG_DIR})")
    parser.add_argument("--no-log", action="store_true", help="Print the calculation without updating the weekly history")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        zones = calculate_zones(config)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        import json

        print(json.dumps({"method": config["method"], "heart_rate": config["heart_rate"], "zones": zones}, indent=2))
    else:
        print(markdown_output(config, zones))
    if not args.no_log:
        calculated_on = date.today()
        write_log(args.log, config, zones, calculated_on)
        week_path = args.week_log_dir / f"week-{args.week}.md" if args.week else current_week_file(args.week_log_dir, calculated_on)
        write_week_log(week_path, config, zones, calculated_on)
        print(f"Logged zones to {args.log} and {week_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
