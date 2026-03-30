# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Three core actions a user should be able to do:

1. Add a pet — enter basic info like name, species, and age to create a pet profile.
2. Schedule a walk — pick a pet, date, and time to add a walk to the calendar.
3. See today's tasks — view a simple list of everything scheduled for the day across all pets.

Main objects in the system:

Pet
- attributes: name, species, age
- methods: get_info()

Owner
- attributes: name, pets (list)
- methods: add_pet()

Task
- attributes: title, duration_minutes, priority (low/medium/high)
- methods: is_high_priority()

Scheduler
- attributes: owner, tasks (list), available_minutes
- methods: add_task(), generate_schedule(), explain_plan()

ScheduledPlan
- attributes: tasks in order, total time, date
- methods: display()

**b. Design changes**

After reviewing the initial design, a few issues came up:

1. Task needed a pet attribute — without it there's no way to know which pet a task belongs to, making the owner/scheduler connection pointless.
2. generate_schedule() needed to return a ScheduledPlan — the original design had no explicit link between Scheduler and ScheduledPlan.
3. Added a sort_tasks() helper to Scheduler — generate_schedule() was doing too much on its own (filtering, sorting, and building the plan).
4. ScheduledPlan.total_time now updates automatically when tasks are added instead of being set manually.
5. Task gained time_slot, time, frequency, last_completed_date, and next_due_date to support recurrence logic and timeline ordering — none of these were in the initial design because the recurrence feature wasn't scoped until Phase 3.
6. Scheduler gained six new methods (sort_by_time, filter_by_pet, filter_by_status, warn_time_conflicts, detect_conflicts, mark_task_complete) as Phase 3 algorithmic improvements. The initial design underestimated how much the scheduler would grow.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints in order:

1. **Time budget** — the hard constraint. A task is only included in the plan if its duration fits in the remaining minutes. This is the most important constraint because there is a fixed amount of time in a day. A pet owner who is out of time literally cannot do more tasks, no matter the priority.
2. **Priority** — the tiebreaker for which tasks get the remaining time. High-priority tasks (like medication) are scheduled before medium (enrichment) or low (optional grooming). This reflects what actually matters for the pet's wellbeing, not just what the owner feels like doing.
3. **Recurrence / due date** — tasks that are not due today (based on their frequency and last completion date) are skipped entirely. A weekly bath that was just done yesterday should not fill up today's time budget.

Time slot (morning / afternoon / evening) is a secondary sort key within a priority tier, not a hard constraint — a task assigned to "morning" won't be dropped if it ends up running in the afternoon, it's just positioned earlier in the plan.

**b. Tradeoffs**

The `warn_time_conflicts()` method flags tasks that share the exact same start time (`"HH:MM"`) but does **not** check for overlapping durations. For example, a 30-minute task at `07:00` and a 10-minute task at `07:15` would overlap in real life (the first runs until `07:30`) but would not trigger a warning because their start times differ.

This is a reasonable tradeoff for this stage of the project for two reasons:

1. **Simplicity over precision.** Detecting duration overlap requires computing an end time for each task (`start + duration_minutes`) and then checking every pair of tasks against each other — O(n²) comparisons. Exact start-time matching is O(n) and catches the most obvious scheduling mistakes (two tasks literally assigned the same slot).

2. **Data we actually have.** The `time` field is optional and user-supplied. Many tasks in the system have no time set at all. Building a precise overlap detector around incomplete data would produce false confidence. The exact-match approach is honest about what it can check.

A future improvement would be to compute `(start, end)` intervals for tasks that have a `time` set and flag any pair where `start_a < end_b and start_b < end_a`.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI tools across three phases:

- **Design phase** — used Copilot Chat to brainstorm the class structure. I described the scenario ("pet owner, tasks, daily time budget") and asked what classes and relationships made sense. The suggestions aligned closely with what I had sketched on paper, which gave me confidence the design was sound before writing a single line of code.
- **Implementation phase** — used inline completions while writing the `generate_schedule` loop and the `mark_task_complete` recurrence logic. The `timedelta` pattern for computing `next_due_date` came from an AI suggestion that I verified against the Python docs before using.
- **Debugging phase** — when `warn_time_conflicts` was returning false positives on completed tasks, I pasted the method into Copilot Chat and asked "why might this flag tasks that are already done?" The response immediately pointed to the missing `not task.completed` guard, which I added.

The most effective prompt style was **specific and scoped**: "Given this method signature and this test failure, what is wrong?" Open-ended prompts like "make this better" produced generic suggestions that didn't fit the design.

**b. Judgment and verification**

When building `detect_conflicts`, Copilot suggested computing a full overlap check using `(start_time, end_time)` intervals for every task pair. The suggestion was logically correct and produced working code. I rejected it for the simpler exact-match approach for two reasons:

1. The time field is optional — many tasks have `time = ""`. A precise overlap detector built on incomplete data would silently miss real conflicts while appearing comprehensive. That's worse than an honest limited check.
2. The O(n²) approach felt premature for a personal scheduling tool where a user might have 10–15 tasks. I documented the limitation in `reflection.md` instead of over-engineering the solution.

The evaluation process was: read the AI output carefully, ask "does this solve a problem the user actually has with the data they actually provide?", and decide based on that rather than on whether the code was technically impressive.

How did using separate chat sessions for different phases help you stay organized? Keeping design chat separate from implementation chat meant each session had a clear purpose and a short history. The AI's suggestions stayed relevant to the current phase instead of drifting based on earlier decisions. When I started the Phase 3 session fresh, I pasted in the final class structure and asked for algorithmic improvements — the AI could reason cleanly about what to add without being anchored to earlier drafts.

**Summary — being the "lead architect"**

The biggest lesson was that AI is a fast and knowledgeable collaborator, not a decision-maker. Every suggestion I accepted, I accepted because I understood it and it fit the design. Every suggestion I rejected, I rejected because I understood it and it didn't. The places where I got into trouble were the places where I accepted something without fully understanding it first — and then spent extra time debugging why the behavior didn't match my mental model. The tool is most useful when you already have a clear picture of what you're building.

---

## 4. Testing and Verification

**a. What you tested**

- **Sorting correctness** — verified that `generate_schedule` produces tasks in high → medium → low order, and that `sort_by_time` produces chronological HH:MM order with untimed tasks at the end. These tests matter because the sort order is the core output the user sees — a misorder would make the schedule misleading.
- **Recurrence logic** — confirmed that `mark_task_complete` creates a new task due tomorrow for daily tasks, in 7 days for weekly tasks, and nothing for "as needed" tasks. Also verified that a task with no pet assigned does not crash. This was the most complex new behavior in Phase 3 and the most likely to have subtle bugs.
- **Conflict detection** — checked that two pending tasks at the same start time trigger a warning, that completed tasks are excluded, and that tasks with no time set never produce false positives. The false-positive test was important because `warn_time_conflicts` groups by `time` field — empty strings could silently group all untimed tasks together.
- **Edge cases** — a pet with zero tasks doesn't crash the scheduler; a single task whose duration exceeds the budget is excluded from the plan.

**b. Confidence**

★★★★☆ (4 / 5)

All 15 tests pass. I'm confident in the core scheduling, recurrence, and conflict-detection paths. The gap I'd fill next:

- **Duration overlap detection** — as discussed in section 2b, `warn_time_conflicts` only catches exact same-start-time clashes. A test with a 30-minute task at 07:00 and a 10-minute task at 07:15 would pass silently even though they overlap.
- **Multi-pet interaction** — most tests use a single pet. Edge cases where two pets have tasks at the same time, or where `filter_by_pet` is called with a name that doesn't exist, aren't covered.

---

## 5. Reflection

**a. What went well**

The recurrence logic came together cleanly. Using Python's `dataclasses.replace()` to create the next task occurrence — copying all fields from the completed task and only overriding `completed`, `last_completed_date`, and `next_due_date` — was a pattern I hadn't used before. It kept the recurrence code to about 10 lines and made it easy to test because the new task is a predictable copy of the original.

**b. What you would improve**

The `time` field on `Task` is a plain string (`"HH:MM"`) with no validation. A user who types `"8:30"` instead of `"08:30"` will get incorrect sort behavior because string comparison puts `"9:00"` before `"08:30"`. In the next iteration I'd either parse the field into a `datetime.time` object on input, or add a validator in the `Task` dataclass that normalises the format before storing it.

I'd also add a "mark complete" button in the Streamlit UI — `mark_task_complete` exists in the backend but there's no way to trigger it from the app without editing code.

**c. Key takeaway**

The gap between "the class exists in the UML" and "the class does something useful in the app" is bigger than it looks at the design stage. `ScheduledPlan` started as a simple container with `tasks` and `total_time`. By the end it was also the return type of `generate_schedule`, the source of the timeline view in the UI, and the thing `detect_conflicts` compares against to find overbooked tasks. Every method I added to Scheduler touched ScheduledPlan in some way. The lesson: model the data flows between classes, not just the classes themselves, before you write the first line of code.
