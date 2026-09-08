---
name: garmin-sync
description: Downloads and syncs training data from Garmin Connect using a local Python script (no MCP server required). Running it with no arguments (e.g. "/garmin-sync") auto-syncs every week missing from training-log/ since the last sync, using a continuous Monday-Sunday weekly cadence independent of the training plan's own week numbering. This is ONE option for importing training data - athletes can also use manual logs, other platforms, or provide data conversationally. Use this skill specifically when the athlete wants to sync from Garmin or when the running-coach indicates Garmin as the chosen data source. Stores activities in the training-log folder as markdown, with a section per activity including lap-by-lap detail and a run/walk time split.
---

# Garmin Training Log Sync

## Overview

This skill downloads training data from Garmin Connect and creates weekly markdown summaries in the `training-log` folder. It uses the `garminconnect` Python library directly (via `scripts/garmin_sync.py`) rather than an MCP server.

Each activity gets its own section with distance, duration, pace, a run/walk time split, heart rate, any Garmin note, and (when the activity has more than one lap) a lap-by-lap table - useful for checking pace consistency across ripetute/tempo reps. The sync also maintains `health-log/daily-health.md` with daily resting heart rate, overnight HRV, and sleep summaries.

There are two ways to run it:
- **Auto-sync (default)**: the athlete just says "/garmin-sync" or "sync my training" with no week number. Syncs every missing/stale week since the last sync automatically - see "Auto-Sync Workflow" below.
- **Single week**: the athlete names a specific week - see "Single-Week Workflow" below.

**Note**: This is a Garmin-specific data import tool. The running coach system also supports:
- Manual training logs - athlete creates markdown files directly
- Conversational input - athlete describes training verbally

## One-Time Setup

Before the first sync, make sure the athlete has:

1. **Installed dependencies**:
   ```bash
   pip install -r .claude/skills/garmin-sync/requirements.txt
   ```

2. **Provided Garmin credentials**, either as environment variables or in a `.env` file in `.claude/skills/garmin-sync/` (copy `.claude/skills/garmin-sync/.env.sample`):
   ```
   GARMIN_EMAIL=their-email@example.com
   GARMIN_PASSWORD=their-password
   ```

If either step hasn't been done, walk the athlete through it before attempting a sync. Never ask the athlete to paste their password into the chat - they should set it via the `.env` file or an exported environment variable themselves.

## Auto-Sync Workflow

Use this when the athlete invokes the skill with no specific week (e.g. "/garmin-sync", "sync my training", "download my missing weeks").

### 1. Confirm setup

Same one-time setup as above (dependencies + credentials) - if either is missing, walk the athlete through it first.

### 2. Run the auto-sync script

```bash
python3 .claude/skills/garmin-sync/scripts/garmin_sync_weeks.py
```

`training-log/week-N.md` numbering is a **continuous log of real calendar weeks** - it is independent of the training plan's own "Settimana N" phase numbering, since the athlete may have started logging before the formal plan began. This script:
1. Looks at the highest-numbered `training-log/week-N.md` and reads its own `# Training Log: START to END` header to find where the log currently ends.
2. Continues forward in fixed 7-day blocks (Monday-Sunday by default - see `--week-start`) from there, one new week number per block, up to and including the block containing today.
3. Re-syncs the last existing week too if today still falls within it, so newly logged activities get picked up.
4. Writes/overwrites `training-log/week-N.md` for every week it (re)syncs via `garmin_sync.py`.
5. Syncs daily health and sleep data from the first existing training-log date through today via `garmin_sync_health.py`.
6. Makes sure `training-plan.md` documents the week-start convention (adds a note near the top if one isn't already there).

**If it errors that training-log is empty and no `--start-date` was given**: this is the very first sync - there's no way to know when the athlete's log should begin. Ask the athlete what calendar date their first training week should start on, then run:
```bash
python3 .claude/skills/garmin-sync/scripts/garmin_sync_weeks.py --start-date YYYY-MM-DD
```
(add `--week-start sunday` if their weeks run Sunday-Saturday instead of Monday-Sunday). After that first run, subsequent `/garmin-sync` calls need no extra arguments - they continue from the last synced week automatically.

### 3. Report the Result

Tell the athlete which week(s) were synced (with date ranges) and, for each, the activity count from the script output. If nothing was pending, say training-log is already up to date. If a week failed (e.g. login/MFA issue), surface the error and stop rather than silently skipping.

## Single-Week Workflow

Use this when the athlete names a specific week to sync.

### 1. Get Week Number from User

Ask the user which training week to sync:

- Prompt: "Which training week would you like to sync? (e.g., 1, 2, 3)"
- Store this number as the week identifier (`--week`)
- The file will be saved as `training-log/week-{n}.md`

### 2. Determine the Date Range

By default the script looks back 7 days from today. If the athlete wants a specific week, ask for start/end dates instead (`--start-date` / `--end-date`, format `YYYY-MM-DD`).

### 3. Run the Sync Script

Run it via Bash from the project root:

```bash
python3 .claude/skills/garmin-sync/scripts/garmin_sync.py --week <n> [--days 7] [--start-date YYYY-MM-DD --end-date YYYY-MM-DD] [--unit mi|km] [--min-distance-km 0.8]
```

The script will:
1. Log in to Garmin Connect (reusing a cached session token after the first login, so no repeated MFA)
2. Fetch all "Run"-type activities in the date range via `get_activities_by_date`
3. Drop stray sub-threshold activities (default under 0.8km - accidental watch start/stop blips, not real sessions); it prints which ones it ignored
4. For each remaining activity, fetch lap splits via `get_activity_splits` (shown only when there's more than one lap) and compute a run/walk time split from second-by-second speed samples via `get_activity_details`
5. Write `training-log/week-{n}.md` with one section per activity plus weekly totals

Daily recovery and sleep data can be synced directly with:
```bash
python3 .claude/skills/garmin-sync/scripts/garmin_sync_health.py --start-date YYYY-MM-DD [--end-date YYYY-MM-DD]
```
It writes `health-log/daily-health.md`. The displayed acceptable ranges are rolling 7-day average +/- 1 rolling standard deviation, requiring at least three observations. They are descriptive wearable-data baselines, not medical thresholds.

**If the script errors on login**: Garmin occasionally requires an MFA code on first login from a new machine; the `garminconnect` library will prompt for it interactively in the terminal. Subsequent runs reuse the cached token in `GARMINTOKENS` (default `~/.garmin-running-coach-tokens`) and won't prompt again. If you see a 401 immediately after "Logging in...", the cached token directory is usually stale or was written by a different tool/library version - delete it (or point `GARMINTOKENS` at a fresh directory) and retry. Don't point `GARMINTOKENS` at a directory shared with another Garmin integration - incompatible cached tokens there cause exactly this kind of confusing failure.

**If dependencies are missing**: the script will tell you to `pip install -r .claude/skills/garmin-sync/requirements.txt`.

### 4. Read the Result

Read `training-log/week-{n}.md` to confirm the sync worked and to hand off into a coaching session if that's what the athlete wants next.

### 5. Provide Summary

After syncing, tell the athlete:
- Week number and date range covered
- Number of activities synced (and how many stray blips were ignored, if any)
- File location (`training-log/week-{n}.md`)
- Any activities that got lap-by-lap detail

## Notes on the run/walk time split

Garmin doesn't expose a simple "time spent running" / "time spent walking" field on the activity summary. `scripts/garmin_sync.py` estimates it from second-by-second speed samples (`get_activity_details`), classifying each sample against `WALK_SPEED_THRESHOLD_M_S` (1.96 m/s, ~8:30/km) - at or above that speed counts as running, below counts as walking. This is a heuristic: a slow jog recovery between reps will register as "walk time" too. Adjust the threshold constant if it's misclassifying for this athlete's paces.

## Notes on laps

Laps are fetched for every activity and shown whenever there's more than one (a single lap just means "the whole activity", nothing to break down). This works whether the laps come from a structured Garmin Connect workout or from the athlete manually pressing lap between reps during a free-form fartlek session - both cases produce multiple `lapDTOs` entries.

## Files

- **scripts/garmin_sync.py**: Standalone script - logs in to Garmin Connect, fetches a week of activities, drops stray blips, pulls lap splits and a run/walk split for each, and writes `training-log/week-{n}.md`. Run with `--help` for all options. No database or external services are used; it depends only on `garminconnect` and `python-dotenv`.
- **scripts/garmin_sync_weeks.py**: Continues `training-log/`'s week numbering forward in fixed 7-day (Monday-Sunday by default) blocks from the last synced week, re-syncing the current in-progress week too, and calls `garmin_sync.py` for each one. Needs `--start-date` only on the very first run (empty training-log). Also documents the week-start convention in `training-plan.md` if missing. Stdlib only - no extra dependencies. Run with `--dry-run` to preview without hitting Garmin, or `--help` for all options.
- **scripts/garmin_sync_health.py**: Fetches daily resting heart rate, overnight HRV, and daily sleep summaries, then writes rolling 7-day baselines to `health-log/daily-health.md`.
- **requirements.txt**: Python dependencies for this skill.
- **.env.sample**: Template for the `GARMIN_EMAIL` / `GARMIN_PASSWORD` / `GARMINTOKENS` environment variables.
