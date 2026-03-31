import streamlit as st
from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A smart daily planner for busy pet owners.")

# ---------------------------------------------------------------------------
# Session-state "vault" — objects persist across reruns until the page closes
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")


def is_valid_hhmm(time_str: str) -> bool:
    """Validate 24-hour HH:MM time format."""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def end_time_from_start(start: str, duration_minutes: int) -> str:
    """Compute end time label from HH:MM start plus duration."""
    if not is_valid_hhmm(start):
        return "Invalid time"
    start_dt = datetime.strptime(start, "%H:%M")
    return (start_dt + timedelta(minutes=duration_minutes)).strftime("%H:%M")


def pet_option_label(index: int, pet: Pet) -> str:
    """Build a unique, human-readable pet label for select boxes."""
    return f"{pet.name} ({pet.species}, {pet.age}y) [#{index + 1}]"

# ---------------------------------------------------------------------------
# Step 1 — Owner
# ---------------------------------------------------------------------------

st.subheader("Owner")
owner_name = st.text_input("Owner name", value=st.session_state.owner.name)
if st.button("Save owner name"):
    st.session_state.owner.name = owner_name
    st.success(f"Owner set to: **{st.session_state.owner.name}**")

# ---------------------------------------------------------------------------
# Step 2 — Add a Pet
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Add a Pet")

col_a, col_b, col_c = st.columns(3)
with col_a:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with col_b:
    new_species = st.selectbox("Species", ["dog", "cat", "other"])
with col_c:
    new_age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)

if st.button("Add pet"):
    new_pet = Pet(name=new_pet_name, species=new_species, age=new_age)
    st.session_state.owner.add_pet(new_pet)
    st.success(f"Added **{new_pet.get_info()}** to {st.session_state.owner.name}'s pets.")

if st.session_state.owner.pets:
    st.write("**Current pets:**")
    for pet in st.session_state.owner.pets:
        st.markdown(f"- {pet.get_info()} — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

# ---------------------------------------------------------------------------
# Step 3 — Add a Task
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Add a Task")

if not st.session_state.owner.pets:
    st.warning("Add a pet first before adding tasks.")
else:
    pet_indices = list(range(len(st.session_state.owner.pets)))
    selected_pet_index = st.selectbox(
        "Assign task to pet",
        pet_indices,
        format_func=lambda i: pet_option_label(i, st.session_state.owner.pets[i]),
    )
    selected_pet = st.session_state.owner.pets[selected_pet_index]

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5, col6 = st.columns(3)
    with col4:
        time_slot = st.selectbox("Time slot", ["any", "morning", "afternoon", "evening"])
    with col5:
        task_time = st.text_input("Start time (HH:MM, optional)", value="", placeholder="e.g. 08:30")
    with col6:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])

    if st.button("Add task"):
        normalized_time = task_time.strip()
        if normalized_time and not is_valid_hhmm(normalized_time):
            st.error("Invalid start time format. Use HH:MM (e.g. 08:30, 14:00).")
        else:
            new_task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                pet=selected_pet,
                time_slot=time_slot,
                time=normalized_time,
                frequency=frequency,
            )
            selected_pet.tasks.append(new_task)
            st.success(f"Task **'{task_title}'** added to {selected_pet.name}.")

    # Show all tasks across all pets
    all_tasks = st.session_state.owner.get_all_tasks()
    if all_tasks:
        st.write("**All tasks (across all pets):**")
        st.table([
            {
                "Pet": t.pet.name,
                "Task": t.title,
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority,
                "Slot": t.time_slot,
                "Time": t.time if t.time else "—",
                "Frequency": t.frequency,
            }
            for t in all_tasks
        ])
    else:
        st.info("No tasks yet. Add one above.")

# ---------------------------------------------------------------------------
# Step 4 — Conflict Detection (runs on demand before generating schedule)
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Conflict Check")
st.caption("Scan for same-time task clashes before building your schedule.")

all_tasks_now = st.session_state.owner.get_all_tasks()

if st.button("Run conflict check"):
    if not all_tasks_now:
        st.info("No tasks to check.")
    else:
        temp_scheduler = Scheduler(
            owner=st.session_state.owner,
            available_minutes=240,
        )
        for t in all_tasks_now:
            temp_scheduler.add_task(t)

        warnings = temp_scheduler.warn_time_conflicts()
        conflicts = temp_scheduler.detect_conflicts()

        if not warnings and not conflicts["slot_collisions"]:
            st.success("No time conflicts found — your schedule looks clean!")
        else:
            for w in warnings:
                # Highlight the conflicting time and task names for the pet owner
                st.warning(
                    f"**Scheduling conflict detected!**\n\n"
                    f"{w}\n\n"
                    f"*Tip: Give each task a different start time, or move one to a different time slot.*"
                )
            for slot, tasks in conflicts["slot_collisions"].items():
                task_list = ", ".join(f"**{t.title}**" for t in tasks)
                st.warning(
                    f"**Slot overload in '{slot}':** {task_list} are all assigned to the same time slot.\n\n"
                    f"*Tip: Spread these across morning / afternoon / evening.*"
                )

# ---------------------------------------------------------------------------
# Step 5 — Generate Schedule
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Build Today's Schedule")

available_minutes = st.slider(
    "Available time today (minutes)", min_value=10, max_value=240, value=60, step=5
)

if st.button("Generate schedule"):
    all_tasks = st.session_state.owner.get_all_tasks()
    if not all_tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner=st.session_state.owner, available_minutes=available_minutes)
        for task in all_tasks:
            scheduler.add_task(task)

        plan = scheduler.generate_schedule()
        not_due_today = [t for t in scheduler.tasks if not t.completed and not t.is_due_today()]
        skipped_due_to_time = [
            t for t in scheduler.tasks
            if t not in plan.tasks and not t.completed and t.is_due_today()
        ]

        # Summary metrics
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Tasks scheduled", len(plan.tasks))
        col_m2.metric("Time used", f"{plan.total_time} min")
        col_m3.metric("Time remaining", f"{available_minutes - plan.total_time} min")

        if plan.tasks:
            st.success(f"Here's {st.session_state.owner.name}'s plan for today:")

            # Timeline view — tasks ordered by start time
            timeline = scheduler.sort_by_time()
            scheduled_ids = {id(t) for t in plan.tasks}
            timeline_scheduled = [t for t in timeline if id(t) in scheduled_ids]

            for i, task in enumerate(timeline_scheduled, start=1):
                badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
                time_label = f" · starts {task.time}" if task.time else ""
                slot_label = f" · {task.time_slot}" if task.time_slot != "any" else ""
                st.markdown(
                    f"**{i}. {badge} {task.title}** ({task.pet.name if task.pet else '—'}) "
                    f"— {task.duration_minutes} min · {task.priority} priority"
                    f"{time_label}{slot_label}"
                )
        else:
            st.warning("No tasks fit in the available time. Try increasing the time budget.")

        if skipped_due_to_time:
            st.info(
                f"{len(skipped_due_to_time)} task(s) were skipped — not enough time remaining. "
                f"Consider increasing available time or reducing task durations."
            )
            with st.expander("Show skipped tasks"):
                for t in skipped_due_to_time:
                    st.markdown(f"- ~~{t.title}~~ ({t.pet.name if t.pet else '—'}, {t.duration_minutes} min)")

        if not_due_today:
            st.info(f"{len(not_due_today)} task(s) are not due today based on frequency settings.")
            with st.expander("Show not-due tasks"):
                for t in not_due_today:
                    st.markdown(f"- {t.title} ({t.pet.name if t.pet else '—'}, {t.frequency})")

        # Conflict warnings alongside the generated schedule
        conflict_warnings = scheduler.warn_time_conflicts()
        if conflict_warnings:
            st.divider()
            st.markdown("**Heads up — conflicts in this schedule:**")
            for w in conflict_warnings:
                st.warning(w)

# ---------------------------------------------------------------------------
# Step 6 — Filter View by Pet
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Filter Tasks by Pet")

all_tasks_filter = st.session_state.owner.get_all_tasks()

if not all_tasks_filter:
    st.info("No tasks yet.")
else:
    pet_indices = list(range(len(st.session_state.owner.pets)))
    filter_pet_index = st.selectbox(
        "Show tasks for",
        pet_indices,
        key="filter_pet_select",
        format_func=lambda i: pet_option_label(i, st.session_state.owner.pets[i]),
    )
    filter_pet_obj = st.session_state.owner.pets[filter_pet_index]

    temp_s = Scheduler(owner=st.session_state.owner, available_minutes=999)
    for t in all_tasks_filter:
        temp_s.add_task(t)

    filtered = [t for t in temp_s.tasks if t.pet is filter_pet_obj]
    pending = temp_s.filter_by_status(completed=False)
    pending_for_pet = [t for t in pending if t.pet is filter_pet_obj]

    if filtered:
        col_f1, col_f2 = st.columns(2)
        col_f1.metric(f"Total tasks for {filter_pet_obj.name}", len(filtered))
        col_f2.metric("Pending", len(pending_for_pet))

        st.table([
            {
                "Task": t.title,
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority,
                "Slot": t.time_slot,
                "Time": t.time if t.time else "—",
                "Status": "✅ done" if t.completed else "⏳ pending",
            }
            for t in filtered
        ])
    else:
        st.info(f"No tasks found for {filter_pet_obj.name}.")

# ---------------------------------------------------------------------------
# Step 7 — Find Next Available Slot
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Find Next Available Slot")
st.caption(
    "Given the tasks already on your schedule (those with a start time set), "
    "find the earliest open window that fits a new task — no manual gap-hunting required."
)

all_tasks_slot = st.session_state.owner.get_all_tasks()

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    slot_duration = st.number_input(
        "Task duration (minutes)", min_value=1, max_value=240, value=30, key="slot_duration"
    )
with col_s2:
    slot_start_from = st.text_input("Earliest start", value="08:00", key="slot_start")
with col_s3:
    slot_end_by = st.text_input("Must finish by", value="20:00", key="slot_end")

if st.button("Find a slot"):
    if not all_tasks_slot:
        st.info("No tasks are on the schedule yet — any time from your window is open.")
        st.success(f"Suggested start: **{slot_start_from}**")
    else:
        slot_scheduler = Scheduler(owner=st.session_state.owner, available_minutes=999)
        for t in all_tasks_slot:
            slot_scheduler.add_task(t)

        try:
            suggestion = slot_scheduler.find_next_available_slot(
                duration_minutes=int(slot_duration),
                start_from=slot_start_from,
                end_by=slot_end_by,
            )
        except ValueError:
            st.error("Invalid time format — use HH:MM (e.g. 08:00, 14:30).")
            suggestion = None

        if suggestion:
            end_time = end_time_from_start(suggestion, int(slot_duration))
            st.success(
                f"First available slot: **{suggestion} – {end_time}** "
                f"({int(slot_duration)} min)"
            )

            # Show how the suggestion fits alongside existing timed tasks
            timed = [t for t in all_tasks_slot if t.time]
            valid_timed = [t for t in timed if is_valid_hhmm(t.time)]
            invalid_timed = [t for t in timed if not is_valid_hhmm(t.time)]

            if invalid_timed:
                st.warning(
                    f"{len(invalid_timed)} timed task(s) were hidden from the context table "
                    "because their start time is not in HH:MM format."
                )

            if valid_timed:
                st.markdown("**Existing timed tasks for context:**")
                st.table([
                    {
                        "Task": t.title,
                        "Pet": t.pet.name if t.pet else "—",
                        "Start": t.time,
                        "Duration": f"{t.duration_minutes} min",
                        "End": end_time_from_start(t.time, t.duration_minutes),
                    }
                    for t in sorted(valid_timed, key=lambda x: x.time)
                ])
        else:
            st.warning(
                f"No {int(slot_duration)}-minute slot available between "
                f"{slot_start_from} and {slot_end_by}. "
                "Try a shorter duration or a wider time window."
            )
