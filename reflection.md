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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

The `warn_time_conflicts()` method flags tasks that share the exact same start time (`"HH:MM"`) but does **not** check for overlapping durations. For example, a 30-minute task at `07:00` and a 10-minute task at `07:15` would overlap in real life (the first runs until `07:30`) but would not trigger a warning because their start times differ.

This is a reasonable tradeoff for this stage of the project for two reasons:

1. **Simplicity over precision.** Detecting duration overlap requires computing an end time for each task (`start + duration_minutes`) and then checking every pair of tasks against each other — O(n²) comparisons. Exact start-time matching is O(n) and catches the most obvious scheduling mistakes (two tasks literally assigned the same slot).

2. **Data we actually have.** The `time` field is optional and user-supplied. Many tasks in the system have no time set at all. Building a precise overlap detector around incomplete data would produce false confidence. The exact-match approach is honest about what it can check.

A future improvement would be to compute `(start, end)` intervals for tasks that have a `time` set and flag any pair where `start_a < end_b and start_b < end_a`.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
