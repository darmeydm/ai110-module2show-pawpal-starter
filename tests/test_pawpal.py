import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from unittest.mock import patch
from pawpal_system import Pet, Task, Owner, Scheduler


def test_mark_complete_changes_status():
    """Calling mark_complete() should set completed to True."""
    task = Task(title="Walk", duration_minutes=20, priority="high")
    assert task.completed == False
    task.mark_complete()
    assert task.completed == True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet's task list should increase the count by 1."""
    pet = Pet(name="Biscuit", species="Dog", age=3)
    assert len(pet.tasks) == 0
    task = Task(title="Feed", duration_minutes=10, priority="medium", pet=pet)
    pet.tasks.append(task)
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_tasks_by_priority():
    """sort_tasks() should order high → medium → low priority."""
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)

    low  = Task(title="Low",  duration_minutes=10, priority="low")
    med  = Task(title="Med",  duration_minutes=10, priority="medium")
    high = Task(title="High", duration_minutes=10, priority="high")

    for t in [low, med, high]:
        scheduler.add_task(t)

    scheduler.sort_tasks()

    assert scheduler.tasks[0].priority == "high"
    assert scheduler.tasks[1].priority == "medium"
    assert scheduler.tasks[2].priority == "low"


def test_sort_by_time_chronological():
    """sort_by_time() should return tasks in ascending HH:MM order."""
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)

    t1 = Task(title="Evening walk", duration_minutes=30, priority="low",  time="18:00")
    t2 = Task(title="Morning meds", duration_minutes=5,  priority="high", time="08:00")
    t3 = Task(title="Afternoon feed",duration_minutes=10, priority="med", time="12:30")

    for t in [t1, t2, t3]:
        scheduler.add_task(t)

    ordered = scheduler.sort_by_time()

    assert ordered[0].time == "08:00"
    assert ordered[1].time == "12:30"
    assert ordered[2].time == "18:00"


def test_sort_by_time_no_time_goes_last():
    """Tasks without a scheduled time should appear after all timed tasks."""
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)

    timed   = Task(title="Timed",   duration_minutes=10, priority="high", time="09:00")
    untimed = Task(title="Untimed", duration_minutes=10, priority="high", time="")

    scheduler.add_task(untimed)
    scheduler.add_task(timed)

    ordered = scheduler.sort_by_time()

    assert ordered[0].title == "Timed"
    assert ordered[1].title == "Untimed"


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_mark_complete_daily_creates_next_task():
    """Completing a daily task should create a follow-up due tomorrow."""
    today = date(2026, 3, 30)
    with patch("pawpal_system.date") as mock_date:
        mock_date.today.return_value = today
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        pet = Pet(name="Biscuit", species="Dog", age=3)
        task = Task(title="Walk", duration_minutes=20, priority="high",
                    frequency="daily", pet=pet)
        pet.tasks.append(task)

        owner = Owner("Alex")
        owner.add_pet(pet)
        scheduler = Scheduler(owner, available_minutes=120)
        scheduler.add_task(task)

        next_task = scheduler.mark_task_complete(task)

        assert next_task is not None
        assert next_task.next_due_date == str(today + timedelta(days=1))
        assert next_task.completed == False
        assert next_task in pet.tasks
        assert next_task in scheduler.tasks


def test_mark_complete_weekly_creates_next_task():
    """Completing a weekly task should create a follow-up due in 7 days."""
    today = date(2026, 3, 30)
    with patch("pawpal_system.date") as mock_date:
        mock_date.today.return_value = today
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

        task = Task(title="Bath", duration_minutes=30, priority="medium",
                    frequency="weekly")
        owner = Owner("Alex")
        scheduler = Scheduler(owner, available_minutes=120)
        scheduler.add_task(task)

        next_task = scheduler.mark_task_complete(task)

        assert next_task is not None
        assert next_task.next_due_date == str(today + timedelta(weeks=1))


def test_mark_complete_as_needed_returns_none():
    """Completing an 'as needed' task should not create a recurrence."""
    task = Task(title="Vet visit", duration_minutes=60, priority="high",
                frequency="as needed")
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)
    scheduler.add_task(task)

    result = scheduler.mark_task_complete(task)

    assert result is None


def test_mark_complete_no_pet_does_not_crash():
    """Completing a recurring task with pet=None should still succeed."""
    task = Task(title="Groom", duration_minutes=20, priority="low",
                frequency="daily", pet=None)
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)
    scheduler.add_task(task)

    next_task = scheduler.mark_task_complete(task)

    assert next_task is not None
    assert next_task in scheduler.tasks


def test_mark_complete_twice_is_idempotent():
    """Completing an already-completed recurring task should not create another follow-up."""
    task = Task(title="Walk", duration_minutes=20, priority="high", frequency="daily")
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)
    scheduler.add_task(task)

    first_next = scheduler.mark_task_complete(task)
    second_next = scheduler.mark_task_complete(task)

    assert first_next is not None
    assert second_next is None
    assert len([t for t in scheduler.tasks if t.title == "Walk"]) == 2


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_warn_time_conflicts_detects_duplicate_times():
    """Two pending tasks at the same time should produce a warning."""
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)

    t1 = Task(title="Feed",  duration_minutes=10, priority="high", time="08:00")
    t2 = Task(title="Meds",  duration_minutes=5,  priority="high", time="08:00")

    scheduler.add_task(t1)
    scheduler.add_task(t2)

    warnings = scheduler.warn_time_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_warn_time_conflicts_no_conflict():
    """Tasks at different times should produce no warnings."""
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)

    t1 = Task(title="Feed",  duration_minutes=10, priority="high", time="08:00")
    t2 = Task(title="Meds",  duration_minutes=5,  priority="high", time="09:00")

    scheduler.add_task(t1)
    scheduler.add_task(t2)

    assert scheduler.warn_time_conflicts() == []


def test_warn_time_conflicts_ignores_completed_tasks():
    """A completed task should not count toward a time conflict."""
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)

    t1 = Task(title="Feed",  duration_minutes=10, priority="high", time="08:00")
    t2 = Task(title="Meds",  duration_minutes=5,  priority="high", time="08:00",
              completed=True)

    scheduler.add_task(t1)
    scheduler.add_task(t2)

    assert scheduler.warn_time_conflicts() == []


def test_warn_time_conflicts_no_tasks_with_time():
    """No timed tasks should produce an empty warnings list."""
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)

    t1 = Task(title="Feed", duration_minutes=10, priority="high", time="")

    scheduler.add_task(t1)

    assert scheduler.warn_time_conflicts() == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_pet_with_no_tasks_does_not_crash_schedule():
    """A pet with no tasks should not cause generate_schedule to error."""
    pet = Pet(name="Ghost", species="Cat", age=2)
    owner = Owner("Alex")
    owner.add_pet(pet)
    scheduler = Scheduler(owner, available_minutes=60)

    plan = scheduler.generate_schedule()

    assert plan.tasks == []
    assert plan.total_time == 0


def test_single_task_exceeds_budget_is_excluded():
    """A task larger than available_minutes should not appear in the plan."""
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=10)

    big_task = Task(title="Long walk", duration_minutes=90, priority="high")
    scheduler.add_task(big_task)

    plan = scheduler.generate_schedule()

    assert big_task not in plan.tasks


def test_is_due_today_invalid_next_due_date_does_not_crash():
    """Invalid next_due_date should fail open and remain schedulable."""
    task = Task(
        title="Walk",
        duration_minutes=20,
        priority="high",
        next_due_date="2026-99-99",
    )
    assert task.is_due_today() is True


def test_is_due_today_invalid_weekly_last_completed_date_does_not_crash():
    """Invalid weekly completion date should fail open and remain schedulable."""
    task = Task(
        title="Brush",
        duration_minutes=10,
        priority="medium",
        frequency="weekly",
        last_completed_date="not-a-date",
    )
    assert task.is_due_today() is True


def test_find_next_available_slot_rejects_out_of_range_times():
    """Out-of-range HH:MM values should raise ValueError."""
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)

    try:
        scheduler.find_next_available_slot(duration_minutes=15, start_from="25:00", end_by="20:00")
        assert False, "Expected ValueError for invalid time"
    except ValueError:
        assert True


def test_find_next_available_slot_requires_end_after_start():
    """end_by must be later than start_from."""
    owner = Owner("Alex")
    scheduler = Scheduler(owner, available_minutes=120)

    try:
        scheduler.find_next_available_slot(duration_minutes=15, start_from="20:00", end_by="20:00")
        assert False, "Expected ValueError for non-increasing window"
    except ValueError:
        assert True
