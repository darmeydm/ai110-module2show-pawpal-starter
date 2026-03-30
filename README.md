# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a busy pet owner plan daily care tasks across multiple pets — taking into account time budgets, priorities, time slots, recurrence, and scheduling conflicts.

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

---

## Features

### Core scheduling
- **Greedy priority scheduler** — `Scheduler.generate_schedule()` fits as many due tasks as possible into the available time budget, sorted high → medium → low priority. Completed tasks and tasks not due today are automatically excluded.
- **Sort by time** — `Scheduler.sort_by_time()` returns tasks ordered by their `"HH:MM"` start time using `sorted()` with a lambda key. Tasks with no time set fall to the end. The daily plan reads like a real timeline.
- **Slot-aware sorting** — `sort_tasks()` uses a secondary sort key (morning → afternoon → evening → any) so tasks in the same priority tier are ordered naturally through the day.

### Filtering
- **Filter by pet** — `filter_by_pet(name)` returns every task belonging to a specific pet, useful for per-pet workload views.
- **Filter by status** — `filter_by_status(completed)` surfaces all pending or all finished tasks without touching the main schedule.

### Recurrence
- **Daily and weekly auto-recurrence** — `Scheduler.mark_task_complete(task)` marks a task done and automatically creates the next occurrence using Python's `timedelta`. The new task is registered on both the pet and the scheduler with `next_due_date` set — no manual re-entry needed. `"as needed"` tasks do not auto-recur.

### Conflict detection
- **Same-time conflict warnings** — `warn_time_conflicts()` groups pending tasks by exact start time (`"HH:MM"`) and returns a plain-English warning string for every clash. Displayed as `st.warning` banners in the UI so the pet owner can't miss them.
- **Slot overload detection** — `detect_conflicts()` also flags time slots (morning / afternoon / evening) that are assigned more than one task, surfacing softer scheduling pressure even when exact times aren't set.

### Advanced: Next available slot (Agent Mode feature)
- **`Scheduler.find_next_available_slot(duration, start_from, end_by)`** — an interval gap-search algorithm that walks the existing timed tasks on the schedule and returns the earliest open window that fits a new task without creating a conflict.

  **How it works (step by step):**
  1. Convert `start_from` and `end_by` to integer minutes-since-midnight.
  2. Collect all pending tasks that have a `time` field set; convert each to a `(start, end)` interval in minutes and sort by start.
  3. Walk the sorted intervals with a `cursor` beginning at `start_from`. For each interval, check whether the gap *before* it is wide enough for `duration_minutes`. If yes, return `cursor` as the suggested start time.
  4. After all intervals, check whether the remaining window before `end_by` fits the task.
  5. Return `None` if no slot is found — never crashes or returns a conflicting time.

  This is an O(n log n) algorithm (dominated by the sort). It is strictly better than the greedy scheduler for tasks that need a *specific* open window rather than just fitting somewhere in a total time budget.

---

## Agent Mode — how this feature was built

The `find_next_available_slot` method was developed using **VS Code Copilot Agent Mode** with the following workflow:

1. **Problem framing prompt** — opened Agent Mode and asked: *"I have a `Scheduler` class with a list of `Task` objects, each with an optional `time` field in HH:MM format and a `duration_minutes` int. Write a method `find_next_available_slot(duration_minutes, start_from, end_by)` that returns the earliest open time window with no conflicts. Use an interval gap-search approach."*

2. **Agent's first pass** — Agent Mode read `#file:pawpal_system.py` to understand the existing `Task` and `Scheduler` dataclasses, then generated a complete method including the `to_minutes` / `to_hhmm` helpers and the sorted-interval walk.

3. **Architectural review** — I reviewed the generated code and made two changes the agent didn't anticipate:
   - Added `try/except ValueError` around `to_minutes()` inside the loop to skip tasks with malformed time strings (e.g. `"8:30"` instead of `"08:30"`) rather than crashing.
   - Confirmed the `cursor = max(cursor, e)` pattern handles overlapping intervals correctly — if two tasks overlap, `cursor` advances to the furthest end, preventing the algorithm from suggesting a slot inside the second task.

4. **UI integration prompt** — followed up with: *"Now add a Streamlit section in `#file:app.py` that lets the user enter a duration, start_from, and end_by, calls `find_next_available_slot`, and displays the result alongside a table of existing timed tasks for context."*

5. **What I kept vs. changed** — Agent Mode's UI suggestion used `st.write` for the result. I replaced it with `st.success` / `st.warning` to match the visual language of the rest of the app. I also added the computed end-time display (`start + duration`) so the user sees a complete time window, not just a start time.

**Key takeaway from Agent Mode:** Agent Mode is most effective when you give it a concrete algorithmic goal and a file reference (`#file:`). It handled the boilerplate (helpers, loop skeleton, edge-case comments) quickly. The human work was verifying correctness of the gap logic and deciding how it integrates with the existing design — neither of which the agent can do alone.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

---

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

---

## UML Class Diagram

See [uml_final.md](uml_final.md) for the final Mermaid.js class diagram and a summary of design changes from the initial UML.

---

## Testing PawPal+

### Run the test suite

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Area | Description |
|---|---|
| **Sorting correctness** | Verifies tasks are ordered high → medium → low priority, and that `sort_by_time()` returns tasks in chronological HH:MM order with untimed tasks placed last. |
| **Recurrence logic** | Confirms that completing a `daily` task creates a new task due tomorrow, a `weekly` task creates one due in 7 days, an `as needed` task produces no recurrence, and tasks without a pet assigned do not crash. |
| **Conflict detection** | Checks that two pending tasks at the same start time trigger a warning, that completed tasks are excluded from conflict checks, and that tasks with no time set never produce false positives. |
| **Edge cases** | A pet with zero tasks does not crash the scheduler; a single task whose duration exceeds the available time budget is excluded from the generated plan. |

### Confidence level

★★★★☆ (4 / 5)

All 15 tests pass. Core scheduling, recurrence, and conflict-detection paths are covered with both happy-path and edge-case scenarios. The one gap is overlapping-duration detection — `warn_time_conflicts` currently catches only exact same-start-time clashes, not tasks whose time windows overlap — which is noted in `reflection.md`.

---

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
