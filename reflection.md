# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

At the start, I defined three core user actions:

1. Add a pet by entering name, species, and age.
2. Schedule a walk by selecting a pet and time.
3. View today’s tasks across all pets.

From there, I modeled the system around these objects:

Pet
- attributes: `name`, `species`, `age`
- methods: `get_info()`

Owner
- attributes: `name`, `pets` (list)
- methods: `add_pet()`

Task
- attributes: `title`, `duration_minutes`, `priority` (`low`/`medium`/`high`)
- methods: `is_high_priority()`

Scheduler
- attributes: `owner`, `tasks` (list), `available_minutes`
- methods: `add_task()`, `generate_schedule()`, `explain_plan()`

ScheduledPlan
- attributes: `tasks` (ordered), `total_time`, `date`
- methods: `display()`

**b. Design changes**

As implementation progressed, I made several important adjustments:

1. Added `pet` to `Task` so each task is tied to a specific pet.
2. Updated `generate_schedule()` to explicitly return a `ScheduledPlan`.
3. Added `sort_tasks()` so scheduling logic is more modular and readable.
4. Made `ScheduledPlan.total_time` update automatically when tasks are added.
5. Extended `Task` with `time_slot`, `time`, `frequency`, `last_completed_date`, and `next_due_date` to support recurrence and timeline features.
6. Expanded `Scheduler` with `sort_by_time`, `filter_by_pet`, `filter_by_status`, `warn_time_conflicts`, `detect_conflicts`, and `mark_task_complete` to support Phase 3 algorithmic improvements.

In short, the original design was a good baseline, but the scheduler grew significantly once real usage scenarios were implemented.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler evaluates constraints in this order:

1. **Time budget (hard constraint):** a task is only scheduled if it fits in remaining minutes.
2. **Priority:** when time is limited, `high` tasks are considered before `medium`, then `low`.
3. **Recurrence/due date:** tasks that are not due today are skipped.

`time_slot` (`morning`, `afternoon`, `evening`) is treated as a secondary ordering signal, not a strict scheduling rule.

**b. Tradeoffs**

`warn_time_conflicts()` currently flags only tasks with the exact same start time. It does **not** detect overlap by duration (for example, `07:00` for 30 minutes vs `07:15` for 10 minutes).

I kept this tradeoff intentionally:

1. **Lower complexity:** exact-time grouping is simpler than pairwise overlap checks.
2. **Data realism:** many tasks are untimed (`time = ""`), so a strict overlap engine would imply precision the data does not always support.

A future improvement would be interval-based checks using `(start, end)` and overlap logic.

---

## 3. AI Collaboration

**a. How I used AI**

I used AI across design, implementation, and debugging:

- **Design:** brainstormed classes and relationships for owners, pets, tasks, and scheduling.
- **Implementation:** used suggestions for `generate_schedule` structure and recurrence handling with `timedelta`.
- **Debugging:** diagnosed false positives in conflict warnings and added missing guards.

The most useful prompts were specific and constrained (for example, asking about one method and one failing test).

**b. Judgment and verification**

For `detect_conflicts`, AI suggested a full overlap-check algorithm using interval comparisons. I chose not to adopt it yet because:

1. Optional time fields mean overlap analysis can look complete while still missing many real cases.
2. The added complexity did not match the current project scope.

I treated AI output as proposals, not final decisions: review, validate, and keep only what fits user needs and current architecture.

Keeping separate chat sessions by phase also helped. Design conversations stayed focused on modeling, while implementation/debug sessions stayed focused on code behavior.

**Summary — lead architect mindset**

The key lesson is that AI is a strong collaborator, but architecture decisions still require human judgment. The best outcomes came from understanding each suggestion before accepting it.

---

## 4. Testing and Verification

**a. What I tested**

- **Sorting behavior:** validated priority order and chronological `HH:MM` ordering (with untimed tasks last).
- **Recurrence behavior:** verified daily and weekly task regeneration, plus no recurrence for `as needed` tasks.
- **Conflict behavior:** confirmed same-time conflict detection, exclusion of completed tasks, and safe handling of untimed tasks.
- **Edge cases:** confirmed scheduler behavior with no tasks and with tasks that exceed the daily budget.

**b. Confidence**

★★★★☆ (4/5)

I’m confident in core scheduling, recurrence, and conflict detection paths. Remaining improvements:

- Add duration-overlap conflict detection.
- Expand multi-pet edge-case coverage (simultaneous tasks, nonexistent pet filters, etc.).

---

## 5. Reflection

**a. What went well**

Recurrence was the strongest part of implementation. Using `dataclasses.replace()` kept follow-up task creation concise, consistent, and easy to test.

**b. What I would improve**

Time handling needs stronger validation and normalization. A free-form string can lead to inconsistent behavior if formatting differs. In a next iteration, I would normalize inputs or store time as a typed object.

I would also expose a “mark complete” interaction in the Streamlit UI so backend recurrence features are fully usable from the app.

**c. Key takeaway**

Designing classes is only the first step. The harder part is designing how data moves between those classes through real workflows. `ScheduledPlan` became more important as features grew, showing that system value comes from relationships and flow, not just object definitions.
