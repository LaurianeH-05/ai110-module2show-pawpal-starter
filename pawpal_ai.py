from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import List, Optional

from pawpal_system import DailyPlan, Task, TaskScheduler, User, Pet


@dataclass
class PlanOutcome:
    tasks: List[Task]
    explanation_steps: List[str]
    warnings: List[str]
    confidence: float
    score: float


class PawPalAgent:
    """A lightweight planning agent for PawPal+.

    The agent evaluates a pet's tasks for a selected day, detects conflicts,
    proposes schedule improvements, and returns a transparent explanation.
    """

    def __init__(self, owner: User, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.scheduler = TaskScheduler(f"{pet.name}Scheduler", pet, owner)
        self.explanation_steps: List[str] = []

    def plan_day(self, for_date: date) -> PlanOutcome:
        self.explanation_steps = []
        tasks = self.scheduler._tasks_for_pet()
        self.explanation_steps.append(f"Loaded {len(tasks)} pet task(s) from the owner store.")

        scheduled = [t for t in tasks if t.scheduled_time and t.scheduled_time.date() == for_date]
        unscheduled = [t for t in tasks if not t.scheduled_time]
        self.explanation_steps.append(
            f"Found {len(scheduled)} scheduled task(s) and {len(unscheduled)} unscheduled task(s) for {for_date.isoformat()}."
        )

        scheduled.sort(key=lambda t: t.scheduled_time)
        conflicts = self.scheduler.detect_conflicts()
        if conflicts:
            self.explanation_steps.append(
                f"Detected {len(conflicts)} overlapping task pair(s); these should be rescheduled to avoid missed care."
            )
        else:
            self.explanation_steps.append("No overlapping tasks were detected for this pet.")

        warnings = self.scheduler.detect_simultaneous_tasks()
        if warnings:
            self.explanation_steps.append("Found exact-time scheduling warnings across pets.")
        else:
            self.explanation_steps.append("No simultaneous cross-pet scheduling issues detected.")

        proposed_plan = list(scheduled)
        if unscheduled:
            self.explanation_steps.append("Attempting to place unscheduled tasks into available daily gaps.")
            allocated, unplaced = self._allocate_unscheduled_tasks(for_date, scheduled, unscheduled)
            proposed_plan.extend(allocated)
            if allocated:
                self.explanation_steps.append(
                    f"Assigned {len(allocated)} unscheduled task(s) into free time blocks for today."
                )
            if unplaced:
                self.explanation_steps.append(
                    f"Could not place {len(unplaced)} unscheduled task(s) today due to time constraints: {', '.join(t.name for t in unplaced)}."
                )
        else:
            self.explanation_steps.append("No unscheduled tasks to place today.")

        proposed_plan.sort(key=lambda x: (x.scheduled_time is None, x.scheduled_time or datetime.max))
        score, confidence = self._score_plan(proposed_plan, conflicts)
        self.explanation_steps.append(
            f"Generated final plan with score {score:.2f} and confidence {confidence:.2f}."
        )

        return PlanOutcome(
            tasks=proposed_plan,
            explanation_steps=self.explanation_steps,
            warnings=warnings,
            confidence=confidence,
            score=score,
        )

    def _allocate_unscheduled_tasks(
        self,
        for_date: date,
        scheduled: List[Task],
        unscheduled: List[Task],
    ) -> tuple[List[Task], List[Task]]:
        day_start = datetime.combine(for_date, time(hour=8, minute=0))
        day_end = datetime.combine(for_date, time(hour=20, minute=0))

        windows = []
        if scheduled:
            current_start = day_start
            for t in scheduled:
                if t.scheduled_time is None:
                    continue
                if t.scheduled_time > current_start:
                    windows.append((current_start, t.scheduled_time))
                task_end = t.scheduled_time + timedelta(minutes=t.duration_minutes or 30)
                current_start = max(current_start, task_end)
            if current_start < day_end:
                windows.append((current_start, day_end))
        else:
            windows.append((day_start, day_end))

        unscheduled_sorted = sorted(unscheduled, key=lambda t: (t.priority, t.name.lower()))
        allocated: List[Task] = []
        unplaced: List[Task] = []

        for task in unscheduled_sorted:
            duration = timedelta(minutes=task.duration_minutes or 30)
            placed = False
            for index, (start, end) in enumerate(windows):
                if end - start >= duration:
                    proposed_time = start
                    allocated.append(
                        Task(
                            name=task.name,
                            description=task.description,
                            scheduled_time=proposed_time,
                            duration_minutes=task.duration_minutes,
                            priority=task.priority,
                            recurrence=task.recurrence,
                            pet_id=task.pet_id,
                            owner_id=task.owner_id,
                        )
                    )
                    self.explanation_steps.append(
                        f"Proposed '{task.name}' at {proposed_time.strftime('%H:%M')} because it fits a {int((end - start).total_seconds() / 60)}-minute gap."
                    )
                    next_start = proposed_time + duration + timedelta(minutes=5)
                    windows[index] = (next_start, end) if next_start < end else (end, end)
                    placed = True
                    break
            if not placed:
                unplaced.append(task)
        return allocated, unplaced

    def _score_plan(self, tasks: List[Task], conflicts: List[tuple[Task, Task]]) -> tuple[float, float]:
        if not tasks:
            return 0.0, 0.0

        priority_score = sum(max(0, 3 - (t.priority or 1)) for t in tasks)
        conflict_penalty = len(conflicts) * 2
        task_count = len(tasks)
        score = max(0.0, min(10.0, priority_score / max(1, task_count) - conflict_penalty * 0.5 + 5.0))
        confidence = max(0.0, min(1.0, (score / 10.0) - (len(conflicts) * 0.05)))
        return score, confidence
