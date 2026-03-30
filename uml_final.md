# PawPal+ — Final UML Class Diagram

```mermaid
classDiagram
    class Pet {
        +str name
        +str species
        +int age
        +List~Task~ tasks
        +get_info() str
    }

    class Task {
        +str title
        +int duration_minutes
        +str priority
        +str frequency
        +bool completed
        +Pet pet
        +str time_slot
        +str time
        +str last_completed_date
        +str next_due_date
        +is_high_priority() bool
        +is_due_today() bool
        +mark_complete() None
        +__str__() str
    }

    class Owner {
        +str name
        +List~Pet~ pets
        +add_pet(pet: Pet) None
        +get_all_tasks() List~Task~
        +__str__() str
    }

    class Scheduler {
        +Owner owner
        +List~Task~ tasks
        +int available_minutes
        +PRIORITY_ORDER dict
        +SLOT_ORDER dict
        +add_task(task: Task) None
        +mark_task_complete(task: Task) Task
        +sort_tasks() None
        +sort_by_time() List~Task~
        +filter_by_pet(pet_name: str) List~Task~
        +filter_by_status(completed: bool) List~Task~
        +warn_time_conflicts() List~str~
        +detect_conflicts() dict
        +generate_schedule() ScheduledPlan
        +explain_plan() None
    }

    class ScheduledPlan {
        +str date
        +List~Task~ tasks
        +int total_time
        +add_task(task: Task) None
        +display() None
    }

    Owner "1" --> "*" Pet : owns
    Pet "1" --> "*" Task : has
    Task "*" --> "0..1" Pet : assigned to
    Scheduler "1" --> "1" Owner : manages
    Scheduler "1" --> "*" Task : schedules
    Scheduler ..> ScheduledPlan : creates
    ScheduledPlan "1" --> "*" Task : contains
```

## Key relationships vs. initial design

| Change | Reason |
|---|---|
| `Task` gained `pet`, `time_slot`, `time`, `frequency`, `last_completed_date`, `next_due_date` | Needed for recurrence logic, timeline ordering, and conflict detection |
| `Scheduler` gained `sort_by_time()`, `filter_by_pet()`, `filter_by_status()`, `warn_time_conflicts()`, `detect_conflicts()`, `mark_task_complete()` | Phase 3 algorithmic improvements |
| `Task` gained `is_due_today()` and `mark_complete()` | Recurrence logic required task-level awareness of its own schedule |
| `Scheduler` now holds `PRIORITY_ORDER` and `SLOT_ORDER` dicts | Centralised sort keys rather than inline magic numbers |
