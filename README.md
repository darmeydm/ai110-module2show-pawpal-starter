# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

The scheduler has been extended beyond basic greedy time-filling with four algorithmic improvements:

**Sort by time** — `Scheduler.sort_by_time()` returns tasks ordered by their `"HH:MM"` start time using `sorted()` with a lambda key. Tasks with no time set fall to the end. This makes the daily plan read like a real timeline instead of a priority dump.

**Filter by pet or status** — `filter_by_pet(name)` and `filter_by_status(completed)` let you query the task list without touching the schedule. Useful for showing only one pet's workload or surfacing everything still pending.

**Recurring task automation** — `Scheduler.mark_task_complete(task)` marks a task done and, for `"daily"` or `"weekly"` tasks, automatically creates the next occurrence using Python's `timedelta`. The new task is registered on both the pet and the scheduler with a `next_due_date` set — no manual re-entry needed. `"as needed"` tasks do not auto-recur.

**Time conflict detection** — `warn_time_conflicts()` groups pending tasks by exact start time and returns a plain-English warning string for every clash. It never raises an exception — if there are no conflicts the list is empty. Note: it detects same start-time collisions only, not overlapping durations (see `reflection.md` section 2b for the reasoning).

---

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
