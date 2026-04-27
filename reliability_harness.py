from datetime import datetime, date, timedelta

from pawpal_system import User, Pet, Task, TaskScheduler
from pawpal_ai import PawPalAgent


def run_reliability_checks() -> dict:
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "checks": [],
    }

    owner = User("TestOwner")
    pet = Pet(name="Buddy", type="Dog")
    owner.log_pet(pet)
    scheduler = TaskScheduler("BuddyScheduler", pet, owner)

    today = date.today()
    base_time = datetime.combine(today, datetime.min.time()).replace(hour=8)

    task_a = Task(name="Morning walk", scheduled_time=base_time, duration_minutes=30, priority=0, pet_id=pet.id, owner_id=owner.id)
    task_b = Task(name="Grooming", scheduled_time=base_time + timedelta(minutes=20), duration_minutes=30, priority=1, pet_id=pet.id, owner_id=owner.id)
    task_c = Task(name="Play time", duration_minutes=20, priority=1, pet_id=pet.id, owner_id=owner.id)

    scheduler.schedule_task(task_a)
    scheduler.schedule_task(task_b)
    scheduler.schedule_task(task_c)

    from pawpal_ai import PawPalAgent

    agent = PawPalAgent(owner, pet)
    outcome = agent.plan_day(today)

    checks = [
        (
            "conflict_detection",
            len(scheduler.detect_conflicts()) > 0,
            "Conflict detector should flag overlapping tasks.",
        ),
        (
            "agent_planning",
            len(outcome.tasks) >= 2,
            "Agent should include scheduled tasks and propose times for unscheduled tasks when possible.",
        ),
        (
            "plan_order",
            all(
                outcome.tasks[i].scheduled_time <= outcome.tasks[i + 1].scheduled_time
                for i in range(len(outcome.tasks) - 1)
                if outcome.tasks[i].scheduled_time and outcome.tasks[i + 1].scheduled_time
            ),
            "Plan tasks must be returned in chronological order.",
        ),
        (
            "confidence_range",
            0.0 <= outcome.confidence <= 1.0,
            "Confidence should be a normalized value between 0 and 1.",
        ),
    ]

    for check_id, passed, message in checks:
        summary["total"] += 1
        if passed:
            summary["passed"] += 1
            summary["checks"].append({"id": check_id, "status": "passed", "message": message})
        else:
            summary["failed"] += 1
            summary["checks"].append({"id": check_id, "status": "failed", "message": message})

    return summary


if __name__ == "__main__":
    results = run_reliability_checks()
    print("PawPal+ Reliability Harness")
    print(f"Passed {results['passed']} of {results['total']} checks.")
    for check in results["checks"]:
        print(f"- {check['id']}: {check['status']} - {check['message']}")
    if results["failed"] == 0:
        print("All reliability checks passed.")
    else:
        print("Some checks failed. Review the harness output and fix the issues.")
