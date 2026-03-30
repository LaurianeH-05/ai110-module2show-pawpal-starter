import sys
import os
from datetime import datetime

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
