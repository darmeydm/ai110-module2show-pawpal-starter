from dataclasses import dataclass, field, replace
from typing import List
from datetime import date, datetime, timedelta


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: List["Task"] = field(default_factory=list)

    def get_info(self) -> str:
        """Return a formatted string with the pet's name, species, and age."""
        return f"{self.name} ({self.species}, {self.age} yr{'s' if self.age != 1 else ''} old)"


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str                   # "low", "medium", "high"
    frequency: str = "daily"        # "daily", "weekly", "as needed"
    completed: bool = False
    pet: "Pet" = None
    time_slot: str = "any"          # "morning", "afternoon", "evening", "any"
    time: str = ""                  # scheduled start time in "HH:MM" format, e.g. "08:30"
    last_completed_date: str = ""   # ISO date string, e.g. "2026-03-30"
    next_due_date: str = ""         # ISO date when the next recurrence is due

    def is_high_priority(self) -> bool:
        """Return True if the task's priority is 'high'."""
        return self.priority == "high"

    def is_due_today(self) -> bool:
        """
        Return True if the task should be scheduled today.
        If next_due_date is set, that is the authoritative due date.
        Otherwise falls back to frequency + last_completed_date logic.
        """
        today = date.today()
        if self.next_due_date:
            try:
                return today >= datetime.strptime(self.next_due_date, "%Y-%m-%d").date()
            except ValueError:
                return True
        if not self.last_completed_date:
            return True
        if self.frequency == "daily":
            return self.last_completed_date != str(today)
        if self.frequency == "weekly":
            try:
                last = datetime.strptime(self.last_completed_date, "%Y-%m-%d").date()
            except ValueError:
                return True
            return (today - last).days >= 7
        return True  # "as needed" is always eligible

    def mark_complete(self):
        """Mark the task as completed and record today's date."""
        self.completed = True
        self.last_completed_date = str(date.today())

    def __str__(self) -> str:
        """Return a human-readable summary of the task."""
        status = "done" if self.completed else "pending"
        pet_label = f" [{self.pet.name}]" if self.pet else ""
        slot_label = f" @{self.time_slot}" if self.time_slot != "any" else ""
        return (
            f"[{self.priority.upper()}]{pet_label}{slot_label} {self.title} "
            f"({self.duration_minutes} min, {self.frequency}) — {status}"
        )


class Owner:
    def __init__(self, name: str):
        self.name = name
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet):
        """Add a Pet to this owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all pets owned by this owner."""
        all_tasks: List[Task] = []
        for pet in self.pets:
            if hasattr(pet, "tasks"):
                all_tasks.extend(pet.tasks)
        return all_tasks

    def __str__(self) -> str:
        """Return a string listing the owner's name and all their pets."""
        pet_names = ", ".join(p.name for p in self.pets) if self.pets else "none"
        return f"Owner: {self.name} | Pets: {pet_names}"


class Scheduler:
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
    SLOT_ORDER = {"morning": 0, "afternoon": 1, "evening": 2, "any": 3}

    def __init__(self, owner: Owner, available_minutes: int):
        """
        Initialize the Scheduler with an owner and a daily time budget.

        Args:
            owner: The Owner whose pets' tasks will be scheduled.
            available_minutes: Total minutes available for pet care today.
        """
        self.owner = owner
        self.tasks: List[Task] = []
        self.available_minutes = available_minutes

    def add_task(self, task: Task):
        """Register a task with the scheduler for inclusion in the plan."""
        self.tasks.append(task)

    def mark_task_complete(self, task: Task) -> "Task | None":
        """
        Mark a task complete and, if it recurs, automatically create the next
        occurrence using timedelta and register it on the pet and scheduler.

        Returns the new Task if one was created, otherwise None.
        """
        # Idempotency guard: avoid duplicating recurring follow-up tasks.
        if task.completed:
            return None

        task.mark_complete()

        if task.frequency == "daily":
            next_due = date.today() + timedelta(days=1)
        elif task.frequency == "weekly":
            next_due = date.today() + timedelta(weeks=1)
        else:
            return None  # "as needed" tasks don't auto-recur

        next_task = replace(
            task,
            completed=False,
            last_completed_date="",
            next_due_date=str(next_due),
        )

        if task.pet:
            task.pet.tasks.append(next_task)
        self.tasks.append(next_task)
        return next_task

    def sort_tasks(self):
        """Sort tasks by priority → time slot → duration (shortest first within a tier)."""
        self.tasks.sort(
            key=lambda t: (
                self.PRIORITY_ORDER.get(t.priority, 99),
                self.SLOT_ORDER.get(t.time_slot, 3),
                t.duration_minutes,
            )
        )

    def sort_by_time(self) -> List[Task]:
        """
        Return tasks sorted by their scheduled start time in ascending order.
        Uses sorted() with a lambda key on the 'time' field ("HH:MM" string).
        Tasks without a time set ("") are placed at the end.
        """
        return sorted(
            self.tasks,
            key=lambda t: t.time if t.time else "99:99"
        )

    def filter_by_pet(self, pet_name: str) -> List[Task]:
        """
        Return all registered tasks that belong to a specific pet.

        Args:
            pet_name: The exact name of the pet to filter by (case-sensitive).

        Returns:
            A list of Task objects assigned to that pet, or an empty list if
            no tasks match or the pet name is not found.
        """
        return [t for t in self.tasks if t.pet and t.pet.name == pet_name]

    def filter_by_status(self, completed: bool) -> List[Task]:
        """
        Return all registered tasks matching the given completion state.

        Args:
            completed: Pass True to get finished tasks, False to get pending ones.

        Returns:
            A list of Task objects whose `completed` flag matches the argument.
        """
        return [t for t in self.tasks if t.completed == completed]

    def warn_time_conflicts(self) -> List[str]:
        """
        Lightweight conflict detection: group pending tasks by their exact
        start time ("HH:MM") and return a warning string for every clash.
        Returns an empty list when no conflicts exist — never raises an error.
        """
        time_groups: dict[str, List[Task]] = {}
        for task in self.tasks:
            if task.time and not task.completed:
                time_groups.setdefault(task.time, []).append(task)

        warnings = []
        for time_str, tasks in time_groups.items():
            if len(tasks) > 1:
                names = " and ".join(
                    f"'{t.title}' ({t.pet.name if t.pet else 'no pet'})"
                    for t in tasks
                )
                warnings.append(
                    f"WARNING: Time conflict at {time_str} — {names} are scheduled at the same time."
                )
        return warnings

    def detect_conflicts(self) -> dict:
        """
        Identify two kinds of conflicts:
        - overbooked: tasks that won't fit in available_minutes
        - slot_collisions: multiple tasks sharing the same specific time slot
        """
        plan = self.generate_schedule()
        scheduled_ids = {id(t) for t in plan.tasks}

        overbooked = [t for t in self.tasks if id(t) not in scheduled_ids and not t.completed]

        slot_groups: dict[str, List[Task]] = {}
        for task in self.tasks:
            if task.time_slot != "any" and not task.completed:
                slot_groups.setdefault(task.time_slot, []).append(task)
        slot_collisions = {slot: tasks for slot, tasks in slot_groups.items() if len(tasks) > 1}

        return {"overbooked": overbooked, "slot_collisions": slot_collisions}

    def find_next_available_slot(
        self,
        duration_minutes: int,
        start_from: str = "08:00",
        end_by: str = "20:00",
    ) -> str | None:
        """
        Find the earliest open time window that fits a task of the given duration.

        Algorithm (interval gap-search):
        1. Convert start_from and end_by to integer minutes-since-midnight.
        2. Collect all pending tasks that have a scheduled time, convert each to
           a (start, end) interval in minutes, and sort by start.
        3. Walk the sorted intervals from `start_from`.  After each occupied
           window, check whether the gap before the next window (or end_by) is
           wide enough.  Return the first slot that fits.
        4. If no gap is found inside the day window, return None.

        Args:
            duration_minutes: How many consecutive minutes the new task needs.
            start_from: Earliest acceptable start time as "HH:MM" (default 08:00).
            end_by: Hard deadline — the task must finish by this time (default 20:00).

        Returns:
            A suggested start time as "HH:MM", or None if no slot is available.
        """
        def to_minutes(hhmm: str) -> int:
            h_str, m_str = hhmm.split(":")
            h = int(h_str)
            m = int(m_str)
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError(f"Invalid time value: {hhmm}")
            return h * 60 + m

        def to_hhmm(total_minutes: int) -> str:
            return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"

        day_start = to_minutes(start_from)
        day_end = to_minutes(end_by)
        if day_end <= day_start:
            raise ValueError("end_by must be later than start_from")

        # Build sorted list of (start, end) intervals from timed pending tasks
        intervals: list[tuple[int, int]] = []
        for task in self.tasks:
            if task.time and not task.completed:
                try:
                    s = to_minutes(task.time)
                    e = s + task.duration_minutes
                    intervals.append((s, e))
                except ValueError:
                    continue  # skip malformed time strings
        intervals.sort()

        # Walk gaps between intervals looking for a window >= duration_minutes
        cursor = day_start
        for (s, e) in intervals:
            if s <= cursor:
                # This interval starts before or at our cursor — push cursor past it
                cursor = max(cursor, e)
                continue
            # There is a gap from cursor to s
            if s - cursor >= duration_minutes and cursor + duration_minutes <= day_end:
                return to_hhmm(cursor)
            # Gap was too small — advance past this interval
            cursor = max(cursor, e)

        # Check the remaining window after all intervals
        if cursor + duration_minutes <= day_end:
            return to_hhmm(cursor)

        return None  # no slot found in the day window

    def generate_schedule(self) -> "ScheduledPlan":
        """
        Fit as many due tasks as possible into available_minutes, highest priority first.
        Skips completed tasks and tasks not due today based on their frequency.
        """
        self.sort_tasks()
        plan = ScheduledPlan(date=str(date.today()))
        remaining = self.available_minutes

        for task in self.tasks:
            if task.completed:
                continue
            if not task.is_due_today():
                continue
            if task.duration_minutes <= remaining:
                plan.add_task(task)
                remaining -= task.duration_minutes

        return plan

    def explain_plan(self):
        """
        Print a human-readable summary of today's schedule to the terminal.

        Calls generate_schedule() internally, then reports:
        - Total available time vs. time actually scheduled
        - How many tasks were skipped because their frequency means they aren't due today
        - Which tasks were skipped because they didn't fit in the remaining time budget
        - The full ordered task list via ScheduledPlan.display()
        """
        plan = self.generate_schedule()
        not_due = [t for t in self.tasks if not t.completed and not t.is_due_today()]
        skipped = [t for t in self.tasks if t not in plan.tasks and not t.completed and t.is_due_today()]

        print(f"\n=== PawPal Schedule for {self.owner.name} ===")
        print(f"Available time : {self.available_minutes} min")
        print(f"Scheduled      : {plan.total_time} min across {len(plan.tasks)} task(s)")
        if not_due:
            print(f"Not due today  : {len(not_due)} task(s) skipped by frequency")
        if skipped:
            print(f"Skipped (no time): {len(skipped)} task(s)")
            for t in skipped:
                print(f"  - {t}")
        plan.display()


class ScheduledPlan:
    def __init__(self, date: str):
        """
        Create an empty plan for a specific date.

        Args:
            date: ISO date string (e.g. "2026-03-30") representing the plan day.
        """
        self.date = date
        self.tasks: List[Task] = []
        self.total_time: int = 0

    def add_task(self, task: Task):
        """
        Add a task to the plan and accumulate its duration into total_time.

        Args:
            task: The Task to include in this plan.
        """
        self.tasks.append(task)
        self.total_time += task.duration_minutes

    def display(self):
        """Print all scheduled tasks and the total time to the terminal."""
        print(f"\n--- Plan for {self.date} ({self.total_time} min total) ---")
        if not self.tasks:
            print("  No tasks scheduled.")
            return
        for i, task in enumerate(self.tasks, start=1):
            print(f"  {i}. {task}")
