# PawPal+ Project Reflection

## 1. System Design

### Core actions
- Add and manage pets
- Add, edit, reschedule, complete, and cancel tasks
- Build and explain a daily care plan

### Main objects
- `User`: central owner record and task store
- `Pet`: lightweight pet profile
- `Task`: task data with scheduling, duration, priority, and recurrence
- `TaskScheduler`: pet-specific task filtering, conflict detection, and calendar operations
- `DailyPlan`: ephemeral plan generation for a date
- `PawPalAgent`: AI-style planner that proposes schedule placements and reasoning steps

### Design changes during this extension
Yes. I added an agent component after the initial scheduler design to make the system more responsible and explainable.

Key changes:
- Added `PawPalAgent` to evaluate daily task plans, detect issues, and propose placements for unscheduled tasks.
- Kept `User.tasks_by_id` as the single source of truth for tasks across pets and scheduler views.
- Added a confidence score and explicit reasoning steps for every generated schedule.
- Added a reliability harness separate from the pytest suite so the system can validate end-to-end behavior.

These changes made the system easier to reason about and more transparent for users.

## 2. Scheduling Logic and Tradeoffs

### Constraints considered
- Scheduled task times and durations
- Task priority
- Recurrence behavior for daily or weekly tasks
- Overlapping task conflicts
- Simultaneous scheduling warnings across pets

I chose to prioritize correctness and explainability over a fully optimized scheduler. The agent uses a fixed daily window and gap-filling strategy, which makes it easier to verify and understand.

### Tradeoffs
- Simplicity vs. flexibility: The planner assumes an 08:00–20:00 planning window and does not support arbitrary availability or pet-specific time preferences yet.
- Deterministic rules vs. learning: The system is rule-based, which is more predictable but less adaptive than a learned model.
- Proposal mode vs. automatic scheduling: Unscheduled tasks are proposed into gaps for the user to review rather than hidden automatic scheduling.

These tradeoffs are reasonable for a demo-grade applied AI system because they keep outputs reliable and explainable.

## 3. AI Collaboration

### How AI was used
I used Copilot and Copilot Chat to help identify edge cases, draft tests, and suggest possible schedule evaluation strategies.

### Good vs. bad suggestions
- Helpful: AI suggested strong unit tests around conflict detection and recurrence handling, which made it easier to validate planner behavior.
- Flawed: AI initially suggested a global mutable task list approach, which I rejected because it would have introduced inconsistent state across components.

I verified AI-assisted suggestions by writing tests and running the suite before accepting changes.

## 4. Testing and Reliability

### What was tested
- Task sorting by time
- Recurrence expansion when completing recurring tasks
- Conflict detection for overlapping tasks
- Simultaneous scheduling warnings across pets
- AI planner proposal and task insertion for unscheduled tasks
- Confidence score normalization

### Reliability harness
The repository now includes `reliability_harness.py`, which runs a small suite of checks and prints a pass/fail summary. This is a lightweight evaluation layer beyond unit tests.

## 5. Reflection

### What went well
- The planning agent added meaningful AI behavior without overcomplicating the system.
- Transparent reasoning and confidence scoring improved trustworthiness.
- The reliability harness made it easier to validate end-to-end behavior quickly.

### What I would improve next
- Add persistence so tasks survive app restarts
- Support pet-specific availability and preferred care windows
- Improve the planner to handle multi-pet coordination and shared resources

### Key takeaway
A strong applied AI system is not just the model or planner; it is the combination of logic, explanation, guardrails, and testing that makes the behavior trustworthy.
