from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date, timedelta
from uuid import uuid4
import threading
import hashlib


def _hash_password(plain: str) -> str:
    """Return a hex SHA-256 hash of the provided password.

    Note: for production use a proper password hashing function (bcrypt, argon2).
    """
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


@dataclass
class Task:
    """Simple Task dataclass used by the scheduler and plans."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    priority: int = 0
    completed: bool = False
    pet_id: Optional[str] = None
    owner_id: Optional[str] = None
    recurrence: Optional[str] = None
    duration_minutes: Optional[int] = None
    reminder_offset: Optional[int] = None

    def mark_complete(self) -> None:
        """Set the task completed flag to True."""
        self.completed = True


@dataclass
class Pet:
    """Lightweight Pet dataclass representing a user's pet."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    type: str = ""
    image_url: Optional[str] = None
    owner_id: Optional[str] = None


class User:
    """User object that owns pets and manages tasks in a central store."""

    def __init__(self, name: str, user_id: Optional[str] = None, password: Optional[str] = None):
        """Create a User with optional password (hashed)."""
        self.name = name
        self.id: str = user_id or str(uuid4())
        self.password_hash: Optional[str] = _hash_password(password) if password else None
        self.pets: Dict[str, Pet] = {}
        self.tasks_by_id: Dict[str, Task] = {}
        self._lock = threading.Lock()

    def log_pet(self, pet: Pet) -> None:
        """Register a pet and set its owner_id."""
        with self._lock:
            pet.owner_id = self.id
            self.pets[pet.id] = pet

    def add_task(self, task: Task) -> None:
        """Add a task to the user's central task store."""
        with self._lock:
            task.owner_id = self.id
            self.tasks_by_id[task.id] = task

    def edit_task(self, task_id: str, **updates) -> None:
        """Update fields on an existing task by id."""
        with self._lock:
            t = self.tasks_by_id.get(task_id)
            if not t:
                raise KeyError(f"task {task_id} not found")
            for k, v in updates.items():
                if hasattr(t, k):
                    setattr(t, k, v)

    def del_task(self, task_id: str) -> None:
        """Remove a task from the user's store by id."""
        with self._lock:
            if task_id in self.tasks_by_id:
                del self.tasks_by_id[task_id]

    def view_pet(self, pet_id: str) -> Optional[Pet]:
        """Return a pet by id or None if it doesn't exist."""
        return self.pets.get(pet_id)


class TaskScheduler:
    """View and manipulate tasks for a single pet (tasks are stored on the owner)."""

    def __init__(self, name: str, pet_info: Pet, task_owner: User):
        """Create a scheduler for a pet backed by the owning user's tasks."""
        self.name = name
        self.pet_info = pet_info
        self.task_owner = task_owner

    def _tasks_for_pet(self) -> List[Task]:
        """Return the list of tasks that belong to this pet."""
        return [t for t in self.task_owner.tasks_by_id.values() if t.pet_id == self.pet_info.id]

    def sort_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Return tasks sorted by their scheduled_time (earlier first).

        If tasks is None, sorts tasks for this pet. Tasks without a scheduled_time
        are placed at the end.

        Note: to sort strings in "HH:MM" format you can use a key like:
            sorted(strings, key=lambda s: int(s.split(':')[0]) * 60 + int(s.split(':')[1]))
        or parse to time objects with datetime.strptime(s, "%H:%M").time().
        """
        tasks = tasks if tasks is not None else self._tasks_for_pet()
        return sorted(tasks, key=lambda t: (t.scheduled_time is None, t.scheduled_time or datetime.max))

    def filter_tasks(self, completed: Optional[bool] = None, pet_name: Optional[str] = None) -> List[Task]:
        """Filter tasks by completion status and/or pet name.

        - completed: if True/False, only return tasks with matching completed flag.
        - pet_name: if provided, returns tasks only for the pet with this name (case-insensitive).
        """
        results = list(self.task_owner.tasks_by_id.values())
        if pet_name is not None:
            # match pet id(s) for the given name (case-insensitive)
            matching_ids = [p.id for p in self.task_owner.pets.values() if p.name.lower() == pet_name.lower()]
            results = [t for t in results if t.pet_id in matching_ids]
        if completed is not None:
            results = [t for t in results if t.completed is completed]
        return results

    def detect_conflicts(self) -> List[Tuple[Task, Task]]:
        """Detect scheduling conflicts among tasks for this pet.

        A conflict is reported when two tasks have overlapping time ranges. If a task
        has no duration_minutes, a default duration of 30 minutes is assumed; if a
        task has no scheduled_time it is ignored for conflict detection.
        Returns a list of tuples (task_a, task_b) that conflict.
        """
        tasks = [t for t in self._tasks_for_pet() if t.scheduled_time]
        # sort by start time
        tasks.sort(key=lambda t: t.scheduled_time)
        conflicts: List[Tuple[Task, Task]] = []
        for i in range(len(tasks)):
            a = tasks[i]
            a_start = a.scheduled_time
            a_duration = timedelta(minutes=a.duration_minutes) if a.duration_minutes else timedelta(minutes=30)
            a_end = a_start + a_duration
            # because tasks are sorted by start time, once a later task's start is
            # at or after a_end we can stop checking further tasks for this 'a'.
            for j in range(i + 1, len(tasks)):
                b = tasks[j]
                b_start = b.scheduled_time
                # no possible overlap with any further tasks
                if b_start >= a_end:
                    break
                b_duration = timedelta(minutes=b.duration_minutes) if b.duration_minutes else timedelta(minutes=30)
                b_end = b_start + b_duration
                # overlap check (keeps behavior correct for unusual durations)
                if a_start < b_end and b_start < a_end:
                    conflicts.append((a, b))
        return conflicts

    def detect_simultaneous_tasks(self) -> List[str]:
        """Detect tasks that are scheduled at the exact same datetime across the owner's tasks.

        Returns a list of human-readable warning strings. This is lightweight and
        intended to warn the user rather than raise exceptions.
        """
        # group tasks by exact scheduled_time
        time_map: Dict[datetime, List[Task]] = {}
        for t in self.task_owner.tasks_by_id.values():
            if t.scheduled_time:
                time_map.setdefault(t.scheduled_time, []).append(t)

        warnings: List[str] = []
        for sched_time, tasks in time_map.items():
            if len(tasks) > 1:
                # collect pet names and task names
                pet_names = []
                for task in tasks:
                    pet = self.task_owner.pets.get(task.pet_id)
                    pet_names.append(pet.name if pet else "(unknown pet)")
                # Build concise warning
                time_str = sched_time.strftime("%Y-%m-%d %H:%M")
                warning = f"{len(tasks)} tasks scheduled at {time_str} for pets: {', '.join(pet_names)}"
                warnings.append(warning)
        return warnings

    def mark_task_complete(self, task_id: str) -> None:
        """Mark a task complete and, if it has a recurrence, create the next occurrence.

        Supported recurrences: "daily", "weekly". The new task is scheduled by
        adding 1 or 7 days to the previous scheduled_time. The newly created task
        will preserve name, description, duration_minutes, priority and recurrence.
        """
        t = self.task_owner.tasks_by_id.get(task_id)
        if not t:
            raise KeyError(f"task {task_id} not found")
        if t.pet_id != self.pet_info.id:
            raise ValueError("task does not belong to this pet")
        # mark complete
        t.mark_complete()
        # handle recurrence
        if t.recurrence:
            freq = t.recurrence.lower()
            if freq in ("daily", "weekly") and t.scheduled_time:
                delta = timedelta(days=1) if freq == "daily" else timedelta(weeks=1)
                new_time = t.scheduled_time + delta
                new_task = Task(
                    name=t.name,
                    description=t.description,
                    scheduled_time=new_time,
                    priority=t.priority,
                    completed=False,
                    pet_id=self.pet_info.id,
                    owner_id=self.task_owner.id,
                    recurrence=t.recurrence,
                    duration_minutes=t.duration_minutes,
                    reminder_offset=t.reminder_offset,
                )
                # schedule the new occurrence
                self.schedule_task(new_task)

    def schedule_task(self, task: Task) -> None:
        """Assign the task to this pet and add it to the owner's store."""
        task.pet_id = self.pet_info.id
        task.owner_id = self.task_owner.id
        self.task_owner.add_task(task)

    def reschedule_task(self, task_id: str, new_time: datetime) -> None:
        """Set a new scheduled_time for a task belonging to this pet."""
        t = self.task_owner.tasks_by_id.get(task_id)
        if not t:
            raise KeyError(f"task {task_id} not found")
        if t.pet_id != self.pet_info.id:
            raise ValueError("task does not belong to this pet")
        t.scheduled_time = new_time

    def cancel_task(self, task_id: str) -> None:
        """Remove a task for this pet from the owner's store."""
        t = self.task_owner.tasks_by_id.get(task_id)
        if not t:
            return
        if t.pet_id != self.pet_info.id:
            raise ValueError("task does not belong to this pet")
        self.task_owner.del_task(task_id)


class DailyPlan:
    """Generate ephemeral daily task plans for a pet from a TaskScheduler."""

    def __init__(self, name: str, pet_info: Pet, task_scheduler: TaskScheduler):
        """Create a daily plan for a pet using the provided scheduler."""
        self.name = name
        self.pet_info = pet_info
        self.task_scheduler = task_scheduler

    def generate_plan(self, for_date: date) -> List[Task]:
        """Return tasks scheduled for the given date for this pet."""
        tasks = self.task_scheduler._tasks_for_pet()
        plan = [t for t in tasks if t.scheduled_time and t.scheduled_time.date() == for_date]
        plan.sort(key=lambda x: (x.priority, x.scheduled_time or datetime.min))
        return plan

    def view_plan(self, for_date: date) -> List[Task]:
        """Return a freshly generated ephemeral plan for the date."""
        return self.generate_plan(for_date)
