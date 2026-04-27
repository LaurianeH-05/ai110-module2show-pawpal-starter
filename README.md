# PawPal+ Applied AI System

## Project Summary
This repository extends the Module 2 PawPal+ pet care planner into a complete applied AI system. PawPal+ now includes a lightweight planning agent that:

- analyzes pet care tasks for a selected day
- detects conflicts and simultaneous scheduling warnings
- proposes schedule placements for unscheduled tasks
- generates a transparent reasoning log
- provides confidence scoring and a reliability harness

## Original Base Project
Original project: **PawPal+ (Module 2 schedule planner)**.

The base project modeled pet care tasks, owners, pets, schedule sorting, recurrence expansion, conflict detection, and Streamlit UI wiring.

## What changed

- Added `pawpal_ai.py` with a rule-based planning agent and explanation pipeline.
- Extended the UI to present plan reasoning, confidence, and schedule suggestions.
- Added support for unscheduled tasks and improved schedule persistence so conflict resolution remains visible.
- Added `reliability_harness.py` to evaluate planner reliability automatically.
- Added a system architecture asset in `assets/system_diagram.mmd`.
- Added a model card describing behavior, limitations, and responsible design.

## Architecture Overview

The system is organized into these main components:

- `User`, `Pet`, `Task`, `TaskScheduler`, `DailyPlan` in `pawpal_system.py`
- `PawPalAgent` in `pawpal_ai.py` to plan and explain daily schedules
- Streamlit UI in `app.py` to add pets/tasks and show schedule recommendations
- `reliability_harness.py` for end-to-end reliability checks

### System diagram

```mermaid
flowchart LR
    Owner[Owner/User]
    Pet[Pet Data]
    TaskStore[Task Store (User.tasks_by_id)]
    Scheduler[TaskScheduler]
    Agent[PawPalAgent Planning]
    Plan[DailyPlan]
    UI[Streamlit UI]
    Harness[Reliability Harness]

    Owner --> Pet
    Owner --> TaskStore
    TaskStore --> Scheduler
    Scheduler --> Agent
    Agent --> Plan
    Plan --> UI
    Agent --> UI
    Harness --> Agent
    Harness --> Scheduler
    Harness --> TaskStore
```

The diagram file is also available at `assets/system_diagram.mmd`.

## Setup

```bash
cd ai110-module2show-pawpal-starter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the app

```bash
cd ai110-module2show-pawpal-starter
streamlit run app.py
```

## Run the demo script

```bash
cd ai110-module2show-pawpal-starter
python demo_script.py
```

## Sample interactions

### 1. Add a pet and build a schedule
- Owner: Jordan
- Pet: Mochi, cat
- Task: Morning walk at 09:00, 20 min, high priority
- Task: Play time at 09:20, 20 min, medium priority

Result: the system warns about overlap and shows a plan confidence score.

### 2. Add an unscheduled task
- Task: Brush fur, 15 min, low priority, no time

Result: the agent proposes a fit in the next available gap and explains the reasoning.

### 3. Mark a recurring task complete
- Task: Daily flea check, 10 min, daily recurrence

Result: the scheduler marks it complete and auto-creates the next occurrence.

## Example demo script output

When you run `python demo_script.py`, the system prints a full plan with reasoning steps. Example output:

```text
Demo schedule for owner=Jamie, pet=Nova

Plan confidence: 0.52
Plan score: 5.75

Reasoning steps:
- Loaded 4 pet task(s) from the owner store.
- Found 3 scheduled task(s) and 1 unscheduled task(s) for 2026-04-26.
- Detected 1 overlapping task pair(s); these should be rescheduled to avoid missed care.
- No simultaneous cross-pet scheduling issues detected.
- Attempting to place unscheduled tasks into available daily gaps.
- Proposed 'Meal prep' at 08:00 because it fits a 60-minute gap.
- Assigned 1 unscheduled task(s) into free time blocks for today.
- Generated final plan with score 5.75 and confidence 0.52.

Planned tasks:
- Meal prep: 2026-04-26 08:00, duration=20 min, priority=1
- Morning walk: 2026-04-26 09:00, duration=30 min, priority=0
- Medication: 2026-04-26 09:15, duration=15 min, priority=0
- Evening brushing: 2026-04-26 13:00, duration=20 min, priority=2
```

## Reliability and testing

Run the automated unit tests:

```bash
cd ai110-module2show-pawpal-starter
python -m pytest
```

Run the reliability harness:

```bash
cd ai110-module2show-pawpal-starter
python reliability_harness.py
```

This harness verifies core behaviors such as:

- conflict detection
- agent planning for unscheduled tasks
- chronological ordering of generated plans
- normalized confidence scoring

## Design decisions

- I chose a rule-based planning agent because it is easy to explain, deterministic, and well-suited to the pet care domain.
- Priority is encoded numerically so the planner can visibly prefer higher-priority tasks and place them earlier.
- I kept persistence simple: all tasks are stored centrally on the `User` object, avoiding duplicated state and stale copies.
- I added explicit reasoning steps and a confidence score so users understand the system's decisions.

## What worked

- The planner correctly detects overlapping tasks and warns users.
- The UI now surfaces agent reasoning and confidence.
- The reliability harness gives an extra layer of validation beyond pytest.

## What I learned

- Even a small planning agent benefits from transparent reasoning steps and confidence metrics.
- Centralizing task ownership makes cross-pet warnings and schedule evaluation easier.
- Testing both core logic and system-level planning helps catch edge cases early.

## Files of note

- `app.py` — Streamlit interface and planner integration
- `pawpal_system.py` — core task, pet, and schedule model
- `pawpal_ai.py` — planner agent and reasoning pipeline
- `reliability_harness.py` — reliability test runner
- `model_card.md` — reflection on model behavior and trustworthiness

## Next steps

- Add persistence so tasks survive app restarts
- Add optional time-window preferences per pet
- Expand the planning agent for multi-pet shared-resource optimization
- Add a Loom video walkthrough linked in the README once recorded

## Demo video guide

Use `video_script.md` for a polished 5-7 minute walkthrough. It outlines what to show:

- project goals and new AI feature
- key files and architecture
- the Streamlit app working end-to-end
- the reliability harness output
- the demo script output
- closing summary and future improvements
