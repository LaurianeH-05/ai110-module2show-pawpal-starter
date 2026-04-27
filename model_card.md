# PawPal+ Model Card

## Project Summary
PawPal+ is an AI-enhanced pet care planning system built from the Module 2 PawPal project. It uses a lightweight planning agent to analyze tasks, detect conflicts, propose schedule placements, and explain why it made those choices.

## Original Base Project
This work extends the original PawPal+ schedule planner. The base project implemented task management, basic sorting, conflict detection, and recurring task handling for pet care.

## Model Behavior and Responsible Design
The planning agent is rule-based and deterministic. It:
- evaluates existing tasks for a given day
- detects overlapping tasks
- proposes new placements for unscheduled tasks into available time windows
- provides a transparent explanation log for its decisions
- rates confidence based on task coverage and conflict presence

Because it is not a statistical learning model, the main limitation is that it cannot generalize beyond the rules encoded in the planner. It may fail when tasks span more than one day, when timezones are involved, or when multiple pets need shared resources.

## Limitations and Biases
- The planner assumes a fixed daily window (08:00-20:00) and does not handle night schedules.
- Priority is treated as a simple numeric value; there is no learning from user preferences.
- It does not yet optimize for pet-specific routines (for example, morning-only walks or feeding windows).
- Recurrence handling is limited to daily and weekly patterns only.

## Misuse and Guardrails
Potential misuse: the agent could be trusted too much for complex scheduling needs. Guardrails include:
- conflict detection warnings to prevent overlapping care tasks
- an explicit confidence score so users understand the plan's reliability
- a standalone reliability harness to verify planner behavior before deployment

## Testing Summary
A dedicated reliability harness runs checks for:
- conflict detection
- planning order
- unscheduled task handling
- confidence normalization

The repository also includes pytest coverage for task logic, recurrence, sorting, and schedule warnings.

## Collaboration with AI
- Helpful suggestion: AI helped identify the right test cases for conflict detection and recurrence handling.
- Flawed suggestion: an early AI recommendation to store mutable global task lists was rejected in favor of a central `User.tasks_by_id` store.
