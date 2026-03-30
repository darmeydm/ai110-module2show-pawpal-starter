from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner("Shauna")
dog = Pet(name="Biscuit", species="Dog", age=3)
cat = Pet(name="Luna", species="Cat", age=5)
owner.add_pet(dog)
owner.add_pet(cat)

# Two tasks intentionally set to the same time to trigger a conflict warning
walk     = Task("Morning Walk", 30, "high",   "daily",  pet=dog, time_slot="morning",   time="07:00")
feed_dog = Task("Feed Biscuit", 10, "high",   "daily",  pet=dog, time_slot="morning",   time="07:45")
feed_cat = Task("Feed Luna",    10, "high",   "daily",  pet=cat, time_slot="morning",   time="07:00")  # ← same time as walk
grooming = Task("Brush Luna",   15, "medium", "weekly", pet=cat, time_slot="evening",   time="19:30")
play     = Task("Playtime",     20, "low",    "daily",  pet=dog, time_slot="afternoon", time="14:00")
vet_call = Task("Vet Follow-up",45, "medium", "as needed", pet=dog, time_slot="afternoon", time="14:00")  # ← same time as play

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
