# Athlete Onboarding

Onboarding builds the athlete profile: one written picture of the athlete that every later
session starts from, instead of asking again or guessing.

Run it in the first session (no `athlete-profile.md`), or when the athlete asks to start over.
If the profile exists, don't onboard again: read it, check it is still current (`updated` older
than ~8 weeks, a goal date passed) and ask only about what changed.

## How to run it

- **Pre-fill first.** Before asking anything, read what already exists: Garmin (once connected
  and synced), `nutrition-log/nutrition-profile.json`, `nutrition-log/measurements.md`,
  `storico/`, `long-term-goals.md`. Show the pre-filled values and ask the athlete to
  confirm or correct them, rather than asking again.
- **One section at a time**, in the order below. Wait for the answer before the next section.
  Sections 1-4 come first: the sync in section 4 pre-fills most of the rest.
- **Single source for each fact.** When a value already has a home in the repository (body
  measurements, long-term goals, HR zones, the yearly history), the profile keeps the latest
  value, its date and a link, not a copy.
- **Credentials never go in the profile or in the chat** (see section 3).
- **Constraints, not wishes.** For time, sleep and equipment, ask what can't change (a fixed
  wake time, an office day, no pull-up bar at home): plans must fit those.

## 1. Personal data

- First name and last name
- Date of birth (the age is derived from it, not stored)
- Sex (used by HR, body composition and nutrition formulas)
- Height (cm)
- Weight (kg): the current value; history in section 2
- Job: seated or active, usual stress, known peak periods of the year

## 2. Body measurements

- **Weight**: from Garmin weigh-ins (`get_weigh_ins`, `get_body_composition`) when the athlete
  uses a connected scale, otherwise entered manually.
- **Waist circumference**: manual, in `nutrition-log/measurements.md`.
- Ask how often they want to measure (e.g. weight weekly, waist monthly) and record it.

The profile shows the latest value of each with its date. The history stays in
`nutrition-log/`.

## 3. Devices and platforms

- **Platforms**: which ones the athlete uses. Supported for sync: Garmin Connect.
- **Garmin connection**: follow `.claude/skills/garmin-sync/SKILL.md` (Setup). The athlete puts
  the email and password in `.claude/skills/garmin-sync/.env` themselves; the first login may ask
  for an MFA code in the terminal, then a cached token is reused.
- **Devices**: list them from Garmin (`get_devices`) and confirm with the athlete:
  - the watch (model, whether it has wrist running power);
  - HR sensors: wrist and/or chest strap (model), and **which one for which session type**
    (e.g. strap for intervals, wrist for easy runs). Wrist HR lags in pace changes, so this
    decides how rep and recovery HR are read;
  - whether they wear the watch at night: nights without it have no sleep or HRV, and the
    resting HR is the daytime minimum, so those days are left out of the averages;
  - other: power meter, connected scale.

## 4. First sync: recent first, history later

A long Garmin history takes many calls and a long time. Don't download it all at once:

1. **Recent window first** (~3 months, Monday to Sunday weeks): activities into `training-log/`
   with `garmin_sync_weeks.py --start-date <Monday ~12 weeks ago>`, which also syncs the health
   data (resting HR, HRV, sleep) for the same days. This is enough to set the zones, read the
   current load and start coaching.
2. **History afterwards, newest year first**, in small chunks over later sessions:
   `garmin_sync.py --output-dir storico/<year> ...` one week at a time, never into
   `training-log/`. Find the first activity date first, so the coach knows where the history
   ends. Stop and resume on Garmin errors or rate limits; skip years already present.
3. **One analysis per year** (`storico/analisi-<year>.md`) as each year lands, and the overview
   in `storico/README.md`. Ask the athlete about the gaps and the peaks while the year is fresh.

Tell the athlete what was synced (date ranges, activity counts) and what is still to come.
Earlier apps that are not in Garmin (e.g. phone apps) are noted in the history, not imported.

## 5. Gear

- **Shoes**: read them from Garmin (`get_gear`, `get_gear_stats` for the distance per shoe)
  when the athlete tracks them there; otherwise ask. For each shoe: brand and model, use (easy,
  quality, race, trail), start date, distance so far, and the distance at which the athlete
  wants to retire it.
- Ask whether Garmin assigns a default shoe to activities (`get_gear_defaults`), so the
  distance stays correct without manual work.
- Training places: where they run (park, road, track, trail; flat or hilly), and where they can
  do pace sessions.

Gear tracking with a script is not available yet; until then the profile holds the values read
at onboarding and at each review.

## 6. Running history

A short summary, not the whole archive (details stay in `storico/`):

- since when they run, and with what continuity;
- best results: distance, time, date; watch time and official time when they differ;
- the biggest weekly volume they have handled, and the longest run;
- long breaks and injuries: what, when, recurring or not;
- **recurring patterns**: when in the year the stops tend to start, and why (work peaks,
  darkness, illness, motivation). These are risk windows for future plans;
- methods tried that didn't work for them, and what did;
- other sports, past and present.

Pre-fill from `storico/` when it exists, then ask about the *why* behind the gaps and peaks
(two or three questions are enough). Comparisons with past years match blocks at the same
stage and prior base, not calendar weeks.

## 7. Goals

- **Priority**: health or performance first, in the athlete's own words; it decides every
  conflict later.
- Short term: the next race or goal (name, date, distance, target).
- Long term: link `long-term-goals.md` when it exists, otherwise write the goals there.
- What would make this season a success.

## 8. Availability and life

- Runs per week and which days; days that can't hold a session (office days, family duties).
- Time of day (morning, evening, dark in winter?) and the **maximum time per session** on
  weekdays and at weekends.
- Preferred long-run day, and rest days.
- **Sleep**: fixed wake time (it can't move), usual and target bedtime, what pushes bedtime
  late. The plan protects the nights before key sessions.
- The minimum they can keep in a bad week (e.g. two short easy runs), agreed in advance.

From the answers, agree a **weekly template** (which day is what). Each week it is confirmed
again; a week that was different because of life doesn't change it.

## 9. Health

- Age-related care: from ~50, an unusual HR jump is first asked about (palpitations, irregular
  beat, dizziness, chest discomfort) before calling it a sensor artifact.
- Current pains or niggles, injury and surgery history (what, when, recurring?), anything a
  doctor said to watch.
- Recurring health problems that affect training (e.g. ear, sinus, allergies): route them to
  the matching coach skill (`orl-coach`, `health-coach`).
- How they usually recover after quality sessions (e.g. muscle soreness for days).

## 10. Strength

- Whether they do any now, and whether they want it in the plan. Don't decide for them.
- Setting: gym, home (which equipment), park (bars, benches), and limits (e.g. no door pull-up
  bar at home, done in running shoes outdoors).
- Experience, a simple baseline (e.g. dead hang, push-ups, single-leg squat) and any skill goals
  that motivate them (first pull-up, pistol squat).

## 11. Coaching preferences

- **Feedback rhythm**: after every session, or only in the weekly review.
- **Metrics**: many (as a hobby) or few. Either way, decisions rest only on the decision
  metrics; the rest is trend and curiosity.
- **Progression speed**: how cautious (one variable at a time, at most one "longest ever" a
  week) and how they feel about pushing.
- **Methods**: whether they follow one method or want methods as references, with their own
  data deciding.
- **Watch targets**: how wide a pace range they can actually hold (e.g. at least 20 s/km), and
  whether they follow pace alerts or look at the screen.
- **Race data**: watch (GPS distance, run time) or official results as the reference.
- Naming of activities and workouts, language, and cues that work for them (e.g. for slowing
  down easy runs).

## Profile template

`athlete-profile.md` at the repository root, in the athlete's language, under ~80 lines:

```markdown
# Athlete Profile
updated: YYYY-MM-DD

## Personal data
- Name: First Last
- Born: YYYY-MM-DD · Sex: M/F · Height: 000 cm · Weight: 00.0 kg (YYYY-MM-DD)
- Job: seated / active; peaks: ...

## Body measurements
- Weight 00.0 kg (YYYY-MM-DD, Garmin scale) · Waist 00 cm (YYYY-MM-DD)
- Frequency: weight weekly, waist monthly · History: nutrition-log/measurements.md

## Devices and platforms
- Platforms: Garmin Connect (sync: garmin-sync, credentials in .env)
- Watch: model, wrist power yes/no; worn at night: always / sometimes
- HR: wrist for ...; chest strap (model) for ...
- Sync: training-log from YYYY-MM-DD; history in storico/ YYYY-YYYY (still to sync: ...)

## Gear
| Shoe | Use | Since | km | Retire at |
|---|---|---|---|---|
| Brand Model | easy | YYYY-MM | 000 | 700 |
- Places: ...

## Running history
- Running since YYYY; ...
- Best results: 10K 00:00 (YYYY-MM-DD, watch) ...
- Breaks and injuries: ...
- Recurring patterns / risk windows: ...
- Tried and didn't work: ...

## Goals
- Priority: health first / performance first
- Next: race, date, distance, target
- Long term: long-term-goals.md
- Success this season: ...

## Availability and life
- Days: ... · time of day: ... · max per weekday session: 00 min
- Weekly template: Mon ... · Tue ... · ...
- Sleep: wake HH:MM (fixed), target bed HH:MM
- Minimum week: ...

## Health
- ...

## Strength
- Setting: ... · equipment: ... · baseline: ... · goals: ...

## Coaching preferences
- Feedback: every session · metrics: many, decisions on decision metrics only
- Progression: gradual · methods: references, N=1 decides
- Watch pace range ≥ 20 s/km · race data: watch
```
