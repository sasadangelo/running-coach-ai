---
name: training-plan
description: Create personalized training plans for 5K, 10K, Half Marathon, and Marathon races. Use when the user requests a training plan for any of these distances, wants to prepare for a race, or asks for a structured running program. This skill generates comprehensive markdown training plans that include race goals, training paces, phased progression, and week-by-week workout schedules.
---

# Training Plan Creator

## Overview

This skill creates personalized, evidence-based training plans for 5K, 10K, Half Marathon, and Marathon distances. Plans are delivered as structured markdown documents with clear progression, appropriate training intensities, and race-specific preparation.

## Workflow

### 1. Gather Essential Information

Before creating a plan, collect these key details from the user:

**Required:**
- **Race distance**: 5K, 10K, Half Marathon, or Marathon
- **Race date**: When the race occurs
- **Current weekly mileage**: Average miles/km per week over the last 4 weeks
- **Available training days**: Number of days per week the athlete can train (typically 3-6)

**Recommended:**
- **Target race time**: Goal finish time or pace
- **Recent race results**: Previous race times to establish current fitness level
- **Training background**: Months/years of consistent running
- **Injury history**: Any recurring issues or limitations
- **Other constraints**: Schedule restrictions, terrain access, weather, life stress

**Handling missing information:**
- If target time is not provided, ask about recent race performance or typical training paces
- If training days are unclear, suggest 4-5 days as a reasonable starting point
- If race date creates a very short timeline (< 8 weeks for marathon), flag this concern

### 2. Set Training Paces and HR Targets

**IMPORTANT**: Follow `.claude/skills/running-coach/references/pace-and-hr.md` (from the project root). It defines the pace categories, where paces come from for each kind of athlete, the HR rules and the per-session limits. In short:

- **Beginner, no reliable data**: time-based sessions (at least 30 minutes), run at conversational pace and walk when needed. No HR or pace targets yet. Schedule a first benchmark (3-5 km time trial or race) once the athlete runs 30 minutes continuously.
- **Returning after a break of 3-4 weeks or more**: 2 weeks of easy running only (at least 30 minutes, conversational pace) before any quality work, then as below.
- **Recent race run all-out**: VDOT from the race (watch data: GPS distance and run time), paces from table A2 of `.claude/skills/running-coach/references/vdot-tables.md`.
- **Recorded sessions, no recent race**: sync them with the `garmin-sync` skill, estimate threshold pace (`calculate_threshold.py`), take the VDOT row with that T pace. Paces are provisional until a threshold test confirms them.
- **The target time never sets paces.** Use it only as a realism check against the current VDOT (table A1).
- **VDOT values are a reference, not a prescription.** The athlete's feedback (RPE, how sessions felt, symptoms) and the real data of their training always guide the paces: when they disagree with the table, adjust the paces and note why in the plan.

Ask for the athlete's recent races and whether they have recorded sessions when gathering information (step 1).

**Checking a target time** with `scripts/calculate_paces.py` (relative to this skill's directory):

```bash
python3 scripts/calculate_paces.py --distance <km> --time <HH:MM:SS or MM:SS> --per-km
```

It derives paces from a race time with Riegel's formula. Use it as a cross-check of a target, or for a quick estimate when only a recent race is known; when the VDOT table and the script disagree, the VDOT table wins.

**Where the numbers go**: the pace table and HR zones go only in the "Ritmi e FC di Riferimento" section of `training-plan.md`, and HR max, resting HR, threshold HR and threshold pace in `.claude/training-zones.yaml`. Run `python3 .claude/scripts/calculate_hr_zones.py` after changing the yaml.

### 3. Design the Phased Structure

Read `references/coaches-guide.md` for comprehensive guidance on plan design principles, phase structures, and distance-specific emphases.

**Key sections to reference:**
- Section 1: Core Principles
- Section 2: The "Shape" of a Good Plan (Phases A-E)
- Section 4: Weekly Architecture
- Section 6: Distance-Specific Emphases

**Determine phase durations** based on total plan length and race distance:
- **Foundation/Base**: Build aerobic capacity and durability
- **Build/Development**: Introduce and expand quality workouts
- **Specific/Peak**: Race-specific preparation and intensity
- **Taper**: Reduce fatigue while maintaining sharpness
- **Transition**: (Brief mention for post-race)

**Apply the plan length guidelines** from section 7:
- 8 weeks: Short build, assumes existing base
- 10-12 weeks: Standard for 5K/10K, workable for HM
- 12-16 weeks: Common for HM, minimum for experienced marathoners
- 16-20 weeks: Marathon standard

**Scale appropriately** using section 8 guidelines:
- Adjust volume, workout duration, and recovery based on ability level
- Apply the "minimum effective dose" principle for newer athletes
- Avoid common design errors from section 9

### 4. Structure the Weekly Microcycles

**IMPORTANT**: Follow `references/weekly-structure.md`. It overrides the generic weekly template of the coaches guide. In short:

- **Runs per week follow the volume**: 3 runs up to ~30-35 km/week, a 4th from ~30-35 km, a 5th from ~40-45 km, adapted to the runner.
- **Every run is quality by default**: long run, threshold, reps. Only if the runner does not tolerate it, one becomes an easy run (long + threshold or reps + easy). A 4th or 5th day is easy when the runner already does 3 quality sessions; otherwise it depends on what they tolerate.
- **Session types enter in order**: base easy running → strides → Tempo a ripetute → Tempo continuo → Repetition → Interval (shortest reps first).
- Optional: strength training on the run days or separately.

**Important workout structure rules:**
- ALL interval workouts must be **distance-based** (e.g., "5 x 1 mile", "4 x 800m", "3 x 1km")
- Never use time-based intervals (e.g., "5 x 4 min")
- Every interval workout follows: **warm-up → intervals → cool-down** structure
- Specify distances in miles, meters, or km (e.g., 1.5 miles, 400m, 2km)

**Session limits:** every session must respect the limits in section 4 of `.claude/skills/running-coach/references/pace-and-hr.md` (time, absolute distance, share of weekly volume scaled by runs per week, single-rep length). Check them for each week before finalizing.

**Progressive overload:**
- Increase volume gradually (typically 5-10% per week)
- Follow 3:1 or 2:1 build-to-recovery patterns
- Include planned deload weeks (~15-30% volume reduction)

**Distance-specific emphases** (from section 6):
- **5K**: Focus on VO₂max and speed-endurance
- **10K**: Emphasize threshold work with supporting speed
- **Half Marathon**: Threshold durability and long run progression
- **Marathon**: Volume, marathon pace durability, and fueling practice

### 5. Create Week-by-Week Schedule

For each week of the plan, specify:
- Week number and phase
- Total weekly mileage/volume
- Specific workouts for each training day:
  - Day of week (or Training Day 1, 2, etc.)
  - Workout type (Easy, Threshold, Intervals, Long Run, etc.)
  - Workout details (distance-based, pace, structure)
  - Purpose or focus of the session

**CRITICAL: All interval workouts MUST follow this structure:**
- **Warm-up** (distance + pace)
- **Intervals** (number x distance @ pace, with recovery distance/time)
- **Cool-down** (distance + pace)

**All intervals must be DISTANCE-BASED, not time-based.** Use miles, meters, or kilometers (e.g., "5 x 1 mile", "4 x 800m", "3 x 1km") rather than time-based intervals (e.g., "5 x 4 min").

**Workout description format examples:**
- "Easy 45 min + 6 strides"
- "Threshold: 1 mile easy warm-up, 4 x 1 mile @ T pace (0.25 mile jog recovery), 1 mile easy cool-down"
- "Long Run: 90 min easy"
- "Intervals: 1 mile easy warm-up, 5 x 1 mile @ I pace (0.25 mile jog recovery), 1 mile easy cool-down"
- "Marathon Pace: 1 mile easy warm-up, 2 x 2 miles @ MP (0.5 mile jog recovery), 1 mile easy cool-down"
- "Long Run with quality: 14 miles, last 3 miles @ steady pace (S)"

**Recovery within intervals:**
- Use distance-based recovery: "0.25 mile jog", "0.5 mile jog", "400m jog"
- Or time-based recovery: "2:00 jog", "90 sec jog" (but prefer distance-based)

### 6. Verify Weekly Mileage Using interval_calculator.py

**IMPORTANT**: Before finalizing the weekly mileage totals, use the `interval_calculator.py` script to accurately compute the distance for each interval workout.

**Why this is critical:**
- Manual calculations of workout distances are prone to error
- The script ensures accurate totals including warm-up, intervals, recovery, and cool-down
- This prevents understating or overstating weekly mileage (which can lead to overtraining or undertraining)

**How to use the calculator:**

For each interval workout in your plan, run the calculator with the workout parameters. The script is located at `scripts/interval_calculator.py` (relative to this skill's directory).

```bash
python3 scripts/interval_calculator.py \
  --warmup <distance> \
  --intervals <number> --interval-dist <distance> --interval-pace <pace> \
  --recovery <distance> \
  --cooldown <distance> \
  --easy-pace <pace>
```

**Example:** For "1 mile easy warm-up, 5 x 1 mile @ I pace (0.25 mile jog recovery), 1 mile easy cool-down":

```bash
python3 scripts/interval_calculator.py \
  --warmup 1mi \
  --intervals 5 --interval-dist 1mi --interval-pace 6:15 \
  --recovery 0.25mi \
  --cooldown 1mi \
  --easy-pace 8:00
```

Output:
```
TOTAL DISTANCE: 8.25 mi
TOTAL TIME:     1:01:15
```

**Workflow:**
1. Design your interval workouts following the standard structure
2. Run `interval_calculator.py` for each interval workout to get exact distance
3. Add up all training day distances (easy runs, intervals, long runs) for the week
4. Verify the weekly total matches your intended volume progression
5. Update the "**Total Volume**: X miles/km" for each week with accurate totals

**Note:** For easy runs and long runs without structured intervals, you can estimate distances directly. Only use the calculator for workouts with warm-up, intervals, recovery, and cool-down components. The calculator defaults to miles but can use kilometers with `--unit km`.

### 7. Generate the training-plan.md Output

Create a comprehensive markdown document with the following structure:

```markdown
# Training Plan: [Race Distance] in [Number] Weeks

## Goal Summary
- **Race**: [Race name if provided]
- **Date**: [Race date]
- **Distance**: [5K / 10K / Half Marathon / Marathon]
- **Target Time**: [Goal time]
- **Target Pace**: [Goal pace per mile/km]
- **Training Days**: [X] days per week
- **Plan Duration**: [X] weeks

## Training Paces

Use these paces for workouts throughout the plan:

| Pace Type | Description | Pace Range | Effort (RPE) |
|-----------|-------------|------------|--------------|
| Easy (E) | Recovery and aerobic development | [pace range] | 2-4/10 |
| Steady (S) | Aerobic endurance (marathon/HM) | [pace range] | 4-5/10 |
| Threshold (T) | Comfortably hard, sustainable | [pace range] | 6-7/10 |
| Interval (I) | VO₂max, hard but repeatable | [pace range] | 8-9/10 |
| Repetition (R) | Short, fast reps | [pace range] | Fast/crisp |
| [Race] Pace | Target race effort | [pace range] | Race effort |

**Note**: Adjust paces for terrain, weather, and how you feel. These are guidelines.

## Plan Structure

### Phase 1: [Phase Name] (Weeks X-Y)
**Focus**: [Primary training focus for this phase]
**Volume**: [Typical weekly mileage range]
**Key Sessions**: [Types of workouts emphasized]

### Phase 2: [Phase Name] (Weeks X-Y)
**Focus**: [Primary training focus for this phase]
**Volume**: [Typical weekly mileage range]
**Key Sessions**: [Types of workouts emphasized]

[Continue for all phases...]

## Week-by-Week Training Schedule

### Week 1: [Phase Name]
**Total Volume**: [X] miles/km
**Focus**: [Key focus for this week]

- **Monday**: Rest or cross-training
- **Tuesday**: [Workout details]
- **Wednesday**: [Workout details]
- **Thursday**: [Workout details]
- **Friday**: Rest or easy 30 min
- **Saturday**: [Workout details]
- **Sunday**: [Long run details]

[Continue for all weeks...]

## Important Notes

- **Easy days should feel easy**: [Distance-specific guidance]
- **Fueling**: [If HM or Marathon, include fueling practice guidance]
- **Strength training**: [Brief recommendation]
- **Listen to your body**: [Injury prevention advice]
- **Adjust as needed**: [Flexibility guidance]

```

## Output Guidelines

**Tone**: Clear, supportive, practical. Avoid over-complication.

**Completeness**: Include every week of the plan with specific workouts. Don't abbreviate with "continue similar pattern."

**Flexibility reminders**: Acknowledge that plans may need adjustment. Include notes about when to modify (illness, excessive fatigue, life events).

**Safety**: Include appropriate warnings about injury prevention, gradual progression, and listening to the body.

## References

- **references/weekly-structure.md**: runs per week by volume, which runs are quality, the order in which session types enter the plan. Takes precedence over coaches-guide.md on weekly structure.

- **coaches-guide.md**: Comprehensive framework for training plan design covering principles, phases, intensities, weekly structure, progression models, distance-specific emphases, plan lengths, scaling across abilities, common errors, and a practical recipe for building plans. Reference this extensively when designing the plan structure and selecting workouts.

- **.claude/skills/running-coach/references/pace-and-hr.md** (project root): the method for paces, HR and session limits. Read it before setting or revising any pace.

- **.claude/skills/running-coach/references/vdot-tables.md** (project root): VDOT tables, equivalent race times (A1) and training paces (A2).

- **scripts/calculate_paces.py**: Command-line tool that derives paces from a race time with Riegel's formula. Use it only as a cross-check of a target time (see step 2). Defaults to minute/mile paces (use `--per-km` for minute/km). Run with `--help` flag for usage details.

- **scripts/interval_calculator.py**: Command-line tool for accurately computing workout distances. Located in the skill's scripts directory. Use this to calculate total distance for all interval workouts (warm-up + intervals + recovery + cool-down) to ensure accurate weekly mileage totals. Defaults to miles (use `--unit km` for kilometers). Run with `--help` flag for usage details.
