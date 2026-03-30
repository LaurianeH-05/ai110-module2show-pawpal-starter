from datetime import datetime, date
from pawpal_system import User, Pet, Task, TaskScheduler, DailyPlan


def make_sample_data() -> User:
    owner = User("Alice", password="s3cr3t")

    # create two pets and register them
    dog = Pet(name="Fido", type="Dog")
    cat = Pet(name="Mittens", type="Cat")
    owner.log_pet(dog)
    owner.log_pet(cat)

    # create schedulers
    sched_dog = TaskScheduler("FidoScheduler", dog, owner)
    sched_cat = TaskScheduler("MittensScheduler", cat, owner)

    today = date.today()
    now = datetime.now()

    # three tasks at different times for the two pets
    t1 = Task(name="Morning Walk", scheduled_time=now.replace(hour=8, minute=0, second=0, microsecond=0), priority=1)
    t2 = Task(name="Lunch Feed", scheduled_time=now.replace(hour=12, minute=30, second=0, microsecond=0), priority=2)
    t3 = Task(name="Medication", scheduled_time=now.replace(hour=9, minute=30, second=0, microsecond=0), priority=0)

    # additional tasks created out of chronological order to test sorting
    t4 = Task(name="Evening Brush", scheduled_time=now.replace(hour=19, minute=0, second=0, microsecond=0), priority=3, duration_minutes=15)
    # recurring daily medication for dog to test recurrence handling
    t5 = Task(name="Daily Flea Check", scheduled_time=now.replace(hour=7, minute=30, second=0, microsecond=0), priority=1, recurrence="daily", duration_minutes=10)

    # create a conflicting task at the same time as Morning Walk (same pet)
    t6 = Task(name="Quick Check", scheduled_time=now.replace(hour=8, minute=0, second=0, microsecond=0), priority=2)
    # create a conflicting task at the same time but for the other pet (different pet)
    t7 = Task(name="Neighbor Visit", scheduled_time=now.replace(hour=8, minute=0, second=0, microsecond=0), priority=2)

    # assign tasks to pets via their schedulers (intentionally out of order)
    sched_dog.schedule_task(t2)
    sched_cat.schedule_task(t3)
    sched_dog.schedule_task(t1)
    sched_dog.schedule_task(t4)
    sched_dog.schedule_task(t5)

    # add the conflicting tasks
    sched_dog.schedule_task(t6)
    sched_cat.schedule_task(t7)

    # mark the daily recurring task complete once to demonstrate auto-creation of next occurrence
    sched_dog.mark_task_complete(t5.id)

    return owner


def print_todays_schedule(owner: User) -> None:
    today = date.today()
    print(f"Today's Schedule for {owner.name} ({today.isoformat()}):")
    # for each pet, build a DailyPlan and print tasks
    for pet in owner.pets.values():
        scheduler = TaskScheduler(f"{pet.name}Scheduler", pet, owner)
        plan = DailyPlan(f"{pet.name}Plan", pet, scheduler).generate_plan(today)
        print(f"\n- {pet.name} ({pet.type}):")
        if not plan:
            print("  (no tasks)")
            continue
        for t in plan:
            time_str = t.scheduled_time.strftime("%H:%M") if t.scheduled_time else "(unscheduled)"
            print(f"  • {time_str} — {t.name} (priority={t.priority})")

    # detect any exact-time collisions across all owner's tasks
    if owner.pets:
        any_pet = next(iter(owner.pets.values()))
        global_scheduler = TaskScheduler(f"{any_pet.name}Scheduler", any_pet, owner)
        warnings = global_scheduler.detect_simultaneous_tasks()
        if warnings:
            print("\nConflicts detected:")
            for w in warnings:
                print(f"  ! {w}")


if __name__ == "__main__":
    owner = make_sample_data()
    print_todays_schedule(owner)
