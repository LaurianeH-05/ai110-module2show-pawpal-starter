import sys
import os
from datetime import datetime, timedelta, date

# ensure project package root is on sys.path so tests can import pawpal_system
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from pawpal_system import User, Pet, Task, TaskScheduler


def test_task_mark_complete():
    t = Task(name="Test Completion")
    assert not t.completed
    t.mark_complete()
    assert t.completed


def test_task_addition_increases_pet_count():
    owner = User("Bob")
    pet = Pet(name="Rex", type="Dog")
    owner.log_pet(pet)
    scheduler = TaskScheduler("RexScheduler", pet, owner)

    initial_count = len(scheduler._tasks_for_pet())
    t = Task(name="Walk", scheduled_time=datetime.now())
    scheduler.schedule_task(t)
    after_count = len(scheduler._tasks_for_pet())

    assert after_count == initial_count + 1


def test_sort_by_time_orders_tasks_chronologically():
    owner = User("Alice")
    pet = Pet(name="Milo", type="Cat")
    owner.log_pet(pet)
    scheduler = TaskScheduler("MiloScheduler", pet, owner)

    now = datetime.now().replace(microsecond=0)
    t1 = Task(name="Breakfast", scheduled_time=now + timedelta(hours=4))
    t2 = Task(name="Walk", scheduled_time=now + timedelta(hours=1))
    t3 = Task(name="Vet", scheduled_time=now + timedelta(hours=2))

    scheduler.schedule_task(t1)
    scheduler.schedule_task(t2)
    scheduler.schedule_task(t3)

    sorted_tasks = scheduler.sort_by_time()
    times = [t.scheduled_time for t in sorted_tasks]
    assert times == sorted(times)


def test_recurrence_creates_next_occurrence_on_complete():
    owner = User("Casey")
    pet = Pet(name="Bella", type="Dog")
    owner.log_pet(pet)
    scheduler = TaskScheduler("BellaScheduler", pet, owner)

    today = datetime.now().replace(microsecond=0)
    daily = Task(name="Feed", scheduled_time=today, recurrence="daily")
    scheduler.schedule_task(daily)

    # mark complete should create next day's task
    scheduler.mark_task_complete(daily.id)

    # original marked complete
    original = owner.tasks_by_id[daily.id]
    assert original.completed is True

    # there should be at least one other task with same name and scheduled_time == today + 1 day
    found = [t for t in owner.tasks_by_id.values() if t.name == "Feed" and t.id != daily.id]
    assert any(t.scheduled_time.date() == (today + timedelta(days=1)).date() for t in found)


def test_detect_conflicts_overlapping_tasks_reported():
    owner = User("Dana")
    pet = Pet(name="Otis", type="Dog")
    owner.log_pet(pet)
    scheduler = TaskScheduler("OtisScheduler", pet, owner)

    base = datetime(2026, 3, 30, 9, 0)
    a = Task(name="A", scheduled_time=base, duration_minutes=60)
    b = Task(name="B", scheduled_time=base + timedelta(minutes=30), duration_minutes=30)
    c = Task(name="C", scheduled_time=base + timedelta(hours=2), duration_minutes=30)

    scheduler.schedule_task(a)
    scheduler.schedule_task(b)
    scheduler.schedule_task(c)

    conflicts = scheduler.detect_conflicts()
    # expect at least one conflict (A overlaps B)
    assert any((x.id == a.id and y.id == b.id) or (x.id == b.id and y.id == a.id) for x, y in conflicts)


def test_detect_simultaneous_tasks_warns_on_exact_same_time():
    owner = User("Evan")
    pet1 = Pet(name="Sam", type="Cat")
    pet2 = Pet(name="Luna", type="Cat")
    owner.log_pet(pet1)
    owner.log_pet(pet2)
    scheduler1 = TaskScheduler("SamScheduler", pet1, owner)
    scheduler2 = TaskScheduler("LunaScheduler", pet2, owner)

    ttime = datetime(2026, 3, 30, 12, 0)
    t1 = Task(name="FeedSam", scheduled_time=ttime)
    t2 = Task(name="FeedLuna", scheduled_time=ttime)

    # schedule tasks for different pets but same owner
    scheduler1.schedule_task(t1)
    scheduler2.schedule_task(t2)

    warnings = scheduler1.detect_simultaneous_tasks()
    assert any("2 tasks scheduled" in w or "tasks scheduled at" in w for w in warnings)


def test_daily_plan_empty_when_no_tasks():
    owner = User("Frank")
    pet = Pet(name="Ghost", type="Dog")
    owner.log_pet(pet)
    scheduler = TaskScheduler("GhostScheduler", pet, owner)
    from pawpal_system import DailyPlan

    plan = DailyPlan("daily", pet, scheduler)
    today = datetime.now().date()
    assert plan.view_plan(today) == []


def test_agent_plans_unscheduled_task_into_free_gap():
    from pawpal_ai import PawPalAgent

    owner = User("Kai")
    pet = Pet(name="Buddy", type="Dog")
    owner.log_pet(pet)
    scheduler = TaskScheduler("BuddyScheduler", pet, owner)

    today = datetime.now().date()
    base = datetime.combine(today, datetime.min.time()).replace(hour=8)
    t1 = Task(name="Walk", scheduled_time=base, duration_minutes=30, priority=0, pet_id=pet.id, owner_id=owner.id)
    t2 = Task(name="Feed", duration_minutes=20, priority=1, pet_id=pet.id, owner_id=owner.id)

    scheduler.schedule_task(t1)
    scheduler.schedule_task(t2)

    agent = PawPalAgent(owner, pet)
    outcome = agent.plan_day(today)

    assert any(t.name == "Feed" and t.scheduled_time is not None for t in outcome.tasks)
    assert outcome.confidence >= 0.0 and outcome.confidence <= 1.0


def test_reliability_harness_reports_all_checks():
    from reliability_harness import run_reliability_checks

    result = run_reliability_checks()
    assert result["total"] == result["passed"]
    assert result["failed"] == 0
