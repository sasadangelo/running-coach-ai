# Paces and Heart Rate: Method

Shared reference for the `training-plan` skill (setting and revising paces) and the `running-coach` skill (judging sessions against them). It holds the **rules**. The athlete's current **numbers** live in one place only:

- `training-plan.md`, section "Ritmi e FC di Riferimento": the current pace table and HR zones.
- `.claude/training-zones.yaml`: HR max, resting HR average, threshold HR, threshold pace.
- `health-log/threshold.md`, `health-log/vo2max.md`, `health-log/heart-rate-zones.md`: history and estimates.
- `vdot-tables.md` (next to this file): VDOT tables (A1 equivalent race times, A2 training paces).

Never copy the numbers into a skill file: they would drift apart.

> **Reference values, not prescriptions.** VDOT tables give a starting point. What guides the paces is always the athlete's feedback (RPE, how the session felt, symptoms) and the real data of their own training (paces held, HR at those paces, how they recovered). When the table and the athlete disagree, the athlete wins: adjust the paces and note why in the plan.

## 1. Pace categories

Names in Italian are the ones used in `training-plan.md` and in chat.

| Category | Italian name | Use | Pace source (VDOT table A2) |
|---|---|---|---|
| Easy, recovery | **Corsa facile / recupero** | Easy runs, recovery days, warm-up and cool-down | Slower half of the E band |
| Easy, long | **Lungo** | Long run | Faster half of the E band, governed by HR |
| Marathon / steady | **Medio / ritmo maratona** | Steady segments, HM/marathon specific work | M |
| Threshold, continuous | **Tempo continuo** | Continuous block at threshold | T |
| Threshold, reps | **Tempo a ripetute** | Cruise intervals: threshold reps (1000-2000 m) with short jog recoveries (~1' per 5' of work) | T |
| Interval | **Ripetute medie e lunghe** | VO2max reps (800, 1000, 1200 m and longer) | I |
| Repetition | **Ripetute brevi** | Speed and economy reps (200, 400 m) | R |

Rep length depends on the athlete's speed, not only on the distance:
- **Interval** reps last **3-5 minutes** at I pace. A distance that takes longer than 5' at I pace is not done as an Interval (it becomes threshold work): for a slower runner a 1600 m rep is a threshold rep, not an Interval.
- **Repetition** reps last **up to ~2 minutes** at R pace (a 400 m slightly over 2' is fine), with full recovery (walking allowed).

## 2. Where paces come from

Pick the case that fits the athlete. When several sources exist, the priority is: **threshold test or all-out race > estimate from recorded sessions > target time.**

### a. Beginner, no reliable data
- Sessions by **time**, not distance or pace: at least **30 minutes** of continuous movement.
- Run at a **conversational pace** (talk test: full sentences without gasping). When running is no longer possible at that pace, walk, then run again. Progression = less walking, then the same 30' all running, then longer.
- **No HR targets** at this stage: a beginner's HR is unstable (it jumps with small pace changes, heat, nerves), so it would mislead more than help. No pace targets either.
- The distance-based interval rule of the `training-plan` skill does not apply here: there are no intervals yet.
- Once the athlete runs 30' continuously, schedule a first benchmark (a 3-5 km time trial or a local race, run all-out but evenly) to get a VDOT and move to case b.

### a2. Returning after a break of 3-4 weeks or more
- Even an experienced runner starts with **2 weeks of easy running only**: sessions of at least **30 minutes**, at conversational pace, walking when needed, no quality work (no reps, no Tempo, no strides).
- Purpose: get back to continuous running, and give tendons, fascia and calves time to adapt (they adapt more slowly than the heart and lungs).
- Then set paces as in case b or c. A race from before the break gives a ceiling, not the current level.

### b. Experienced runner with a recent race
- Take a race run **all-out** in the last ~6-8 weeks, on the athlete's own watch (GPS distance and run time; the official time is only a note).
- Find the VDOT in table A1 (interpolate between rows) and read the paces from table A2. The VDOT formula is also `vdot()` in `.claude/skills/garmin-sync/scripts/calculate_threshold.py`.
- An old race (months ago, or after a break) gives a ceiling, not the current level: start a VDOT point or two lower and confirm with a threshold test.

### c. Runs regularly, recorded sessions but no recent race
- Sync the sessions with the `garmin-sync` skill.
- Estimate threshold pace from steady efforts near threshold HR (`calculate_threshold.py` does this on Tempo sessions), then find the VDOT whose T pace matches and take the other paces from that row.
- Mark these paces as **provisional** and confirm them in the first weeks with a threshold test (2 km or 20' continuous at threshold HR).

### Rules for all cases
- **The target time never sets paces.** It is only a realism check: compare it with table A1 at the current VDOT (or `training-plan/scripts/calculate_paces.py`).
- **A race run below maximum gives a floor value.** Its VDOT underestimates fitness: check it against the HR. If at threshold HR the athlete ran faster than the formula's T pace, the HR evidence wins.
- **Never lower paces on a formula alone.** Lower them only for real reasons (illness, long break, repeated failures to hold a pace at normal HR).
- Calibrate to the athlete: the VDOT row is only the starting point. Move a band when the athlete's feedback and own data (reps, Tempo, HR, recovery) consistently show it, and write the reason in the plan.

## 3. Heart rate

### Zones
- Karvonen (% of HR reserve) on HR max and resting HR from `.claude/training-zones.yaml`; computed by `.claude/scripts/calculate_hr_zones.py`.
- **Resting HR** is updated at every sync: mean of the last 7 days, excluding nights without the watch (with no sleep data the daily value is a daytime minimum).
- **HR max and threshold HR** change only when the athlete confirms them. Never raise them from a single spike: an isolated spike is a strap/wrist artefact or a symptom to ask about.
- Threshold HR is checked at races run hard: average HR from minute 10 to the end (Friel).

### What governs each session
| Session | Governed by | HR role |
|---|---|---|
| Easy / recovery | **HR** (ceiling at the top of Z2 or lower, as the plan says) | If HR rises, slow down; pace is only a reference |
| Long run | **HR** (target and ceiling in the plan) | Same; walking is allowed if needed to stay under the ceiling |
| Medio | Pace | HR as a check |
| Tempo continuo / a ripetute | **Pace** | HR ceiling near threshold HR; if exceeded before the last part, ease off a few seconds |
| Interval | Pace | HR mostly reached late in the rep; used for recovery (start the next rep when HR has come down) |
| Repetition | Pace | HR is not useful during a rep shorter than ~2' |

### Reading HR data
- Note which device is reliable for which session (chest strap or wrist) in the plan, and judge HR accordingly.
- Heat, humidity, evening runs, stress, poor sleep and illness raise HR by a few beats at the same pace: say so, do not treat it as lost fitness.
- Aerobic decoupling, Efficiency Factor and the other `health-log` metrics are trends: decide on several sessions, not on one.

## 4. Session limits

Each session must respect the **time limit** and the **share of weekly volume** for its type: whichever comes first. The share counts only the quality kilometres (reps or the continuous block, not warm-up, cool-down or recoveries); for the long run, the whole run.

| Type | Time limit | Absolute distance limit | Share of weekly volume (5+ runs/week) | Single rep |
|---|---|---|---|---|
| Long / easy | 2h30 | 29 km | 25% | - |
| Threshold | 60' of total T work (reps); a classic continuous Tempo is ~20' at precise T pace, longer only in race preparation | - | 10% | - |
| Interval | 30' of work (recoveries excluded) | 10 km | 8% | max 5' |
| Repetition | - | 8 km | 5% | max ~2' |

The weekly shares assume 5-7 runs a week. With fewer runs each session is a larger share of the week, so the shares are scaled:

| Runs/week | Long | Threshold | Interval | Repetition |
|---|---|---|---|---|
| 5+ | 25% | 10% | 8% | 5% |
| 4 | 35% | 15% | 12% | 8% |
| 3 | 45-50% | 20% | 16% | 10% |

Time limits, absolute limits and single-rep limits do not scale. When a session would exceed a limit, cut the session (fewer reps, shorter block), never raise the limit. Weekly volume grows by ~5-10% a week with a recovery week every 3-4.

## 5. When paces and zones change

- **Paces rise** only with new evidence better than the current anchor: a threshold test, or a race run all-out whose VDOT beats the current one. A +1 VDOT step not sooner than 4-6 weeks after the last one, unless a race proves more.
- **Paces stay** after a race run below maximum (floor value) or a single bad session.
- **Zones** change every sync with resting HR; HR max and threshold HR only with athlete confirmation (section 3).
- **Readiness**: when resting HR is above its 7-day range (or above the plan's threshold) or HRV is low, the quality session is shortened or replaced by an easy run. The exact thresholds are in the plan, next to the session.

## 6. How the running coach uses this

- Compare each session with the governing measure from section 3 (HR for easy and long, pace for Tempo, Interval, Repetition).
- Explain deviations with context (heat, evening, stress, terrain, device) before calling them a problem.
- After a race or test, apply section 5: say whether the paces change, and why, citing the evidence (VDOT, HR at threshold, Tempo estimates).
- Flag sessions in the plan that break section 4.
