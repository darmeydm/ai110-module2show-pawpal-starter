from pawpal_system import Owner, Pet, Task, Scheduler

def main():
    # --- Setup ---
    owner = Owner("Shauna")
    dog = Pet(name="Biscuit", species="Dog", age=3)
    cat = Pet(name="Luna", species="Cat", age=5)
    owner.add_pet(dog)
    owner.add_pet(cat)

    # Two tasks intentionally set to the same time to trigger a conflict warning
    walk = Task(
        title="Morning Walk",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet=dog,
        time_slot="morning",
        time="07:00",
    )
    feed_dog = Task(
        title="Feed Biscuit",
        duration_minutes=10,
        priority="high",
        frequency="daily",
        pet=dog,
        time_slot="morning",
        time="07:45",
    )
    feed_cat = Task(
        title="Feed Luna",
        duration_minutes=10,
        priority="high",
        frequency="daily",
        pet=cat,
        time_slot="morning",
        time="07:00",  # same time as walk
    )
    grooming = Task(
        title="Brush Luna",
        duration_minutes=15,
        priority="medium",
        frequency="weekly",
        pet=cat,
        time_slot="evening",
        time="19:30",
    )
    play = Task(
        title="Playtime",
        duration_minutes=20,
        priority="low",
        frequency="daily",
        pet=dog,
        time_slot="afternoon",
        time="14:00",
    )
    vet_call = Task(
        title="Vet Follow-up",
        duration_minutes=45,
        priority="medium",
        frequency="as needed",
        pet=dog,
        time_slot="afternoon",
        time="14:00",  # same time as play
    )

    dog.tasks = [walk, feed_dog, play, vet_call]
    cat.tasks = [feed_cat, grooming]

    scheduler = Scheduler(owner=owner, available_minutes=90)
    for task in owner.get_all_tasks():
        scheduler.add_task(task)

    # --- 1. Show all tasks sorted by time ---
    print("=" * 58)
    print("Tasks sorted by start time:")
    print("=" * 58)
    for t in scheduler.sort_by_time():
        pet_name = t.pet.name if t.pet else "?"
        print(f"  {t.time}  [{t.priority.upper()}]  {t.title:<20} ({pet_name})")

    # --- 2. Conflict detection ---
    print("\n" + "=" * 58)
    print("Conflict check (warn_time_conflicts):")
    print("=" * 58)
    warnings = scheduler.warn_time_conflicts()
    if warnings:
        for w in warnings:
            print(f"  {w}")
    else:
        print("  No time conflicts detected.")

    # --- 3. Build schedule within today's time budget ---
    print("\n" + "=" * 58)
    print("Generated plan (available_minutes=90):")
    print("=" * 58)
    plan = scheduler.generate_schedule()
    if plan.tasks:
        for i, t in enumerate(plan.tasks, start=1):
            pet_name = t.pet.name if t.pet else "?"
            print(f"  {i}. {t.title} ({pet_name}) - {t.duration_minutes} min [{t.priority}]")
        print(f"\n  Total scheduled: {plan.total_time} min")
        print(f"  Time remaining : {scheduler.available_minutes - plan.total_time} min")
    else:
        print("  No tasks fit in the available time window.")


if __name__ == "__main__":
    main()
