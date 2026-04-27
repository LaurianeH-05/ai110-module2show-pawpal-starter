from datetime import datetime, date, timedelta

from pawpal_ai import PawPalAgent
from pawpal_system import User, Pet, Task, TaskScheduler


def make_demo_owner() -> User:
    owner = User("Jamie")
    pet = Pet(name="Nova", type="Dog")
    owner.log_pet(pet)

    today = date.today()
    base_time = datetime.combine(today, datetime.min.time()).replace(hour=9)

    tasks = [
        Task(
            name="Morning walk",
            scheduled_time=base_time,
            duration_minutes=30,
            priority=0,
            pet_id=pet.id,
            owner_id=owner.id,
        ),
        Task(
            name="Medication",
            scheduled_time=base_time + timedelta(minutes=15),
            duration_minutes=15,
            priority=0,
            pet_id=pet.id,
            owner_id=owner.id,
        ),
        Task(
            name="Meal prep",
            duration_minutes=20,
            priority=1,
            pet_id=pet.id,
            owner_id=owner.id,
        ),
        Task(
            name="Evening brushing",
            scheduled_time=base_time + timedelta(hours=4),
            duration_minutes=20,
            priority=2,
            pet_id=pet.id,
            owner_id=owner.id,
        ),
    ]

    scheduler = TaskScheduler("NovaScheduler", pet, owner)
    for task in tasks:
        scheduler.schedule_task(task)

    return owner, pet


def print_demo_plan(owner: User, pet: Pet) -> None:
    print(f"Demo schedule for owner={owner.name}, pet={pet.name}\n")
    agent = PawPalAgent(owner, pet)
    outcome = agent.plan_day(date.today())

    print(f"Plan confidence: {outcome.confidence:.2f}")
    print(f"Plan score: {outcome.score:.2f}\n")
    print("Reasoning steps:")
    for step in outcome.explanation_steps:
        print(f"- {step}")

    print("\nPlanned tasks:")
    for task in outcome.tasks:
        scheduled = task.scheduled_time.strftime("%Y-%m-%d %H:%M") if task.scheduled_time else "(unscheduled)"
        print(f"- {task.name}: {scheduled}, duration={task.duration_minutes or 30} min, priority={task.priority}")

    if outcome.warnings:
        print("\nWarnings:")
        for warning in outcome.warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    owner, pet = make_demo_owner()
    print_demo_plan(owner, pet)
