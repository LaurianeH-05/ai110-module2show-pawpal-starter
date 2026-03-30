# PawPal+ Project Reflection

## 1. System Design


3 core actions:
- Log/add a pet
- Edit/delete/add tasks
- Read/View daily plan

Main Objects:
- User (name, id, password) - logPet, editTask, delTask, addTask, viewPet
- Pet (name, type) - viewImg
- taskScheduler (name, petInfo) - taskList
- dailyPlan (name, petInfo) - generatePlan


**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

I chose User to allow users to interact with the software; the Pet class is essential for the function and purpose of the app. Classes such as taskScheduler and dailyPlan are needed for the core functionalities which include managing a pet's schedule and generating said schedule.
**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
Yes. This iteration focused on clarifying ownership and centralizing task storage to avoid duplicate state and make scheduling deterministic and efficient.

Concrete changes made in this round:

- Added stable unique IDs (UUID4) for `Task` and `Pet` so objects can be serialized and referenced reliably across components.
- Added `owner_id` to `Pet` and `owner_id`/`pet_id` to `Task` to make ownership explicit (tasks belong to a user and may target a specific pet).
- Centralized tasks on the `User` as `tasks_by_id: Dict[str, Task]` instead of keeping copies in `TaskScheduler`. This makes lookups and edits O(1) and avoids inconsistencies between multiple copies of the same task.
- Updated `Task` with optional fields: `recurrence`, `duration_minutes`, and `reminder_offset` to support recurring tasks and reminders.
- Replaced plaintext password storage with a hashed value (`password_hash`) and added a simple hash helper (SHA-256) as a placeholder (note: in production use bcrypt/argon2).
- Introduced a `threading.Lock` in `User` to guard mutations, improving basic thread-safety for concurrent edits.
- Adjusted `TaskScheduler` and `DailyPlan` to read tasks from the user's centralized store (the scheduler filters tasks by `pet_id`), and made daily plans ephemeral by default (generate on-demand).

Why these changes were necessary:

- Ownership clarity: explicit `owner_id` and `pet_id` avoid ambiguity about who is responsible for a task and which pet it targets.
- Single source of truth: centralizing tasks prevents bugs where one component updates a task but another component still holds a stale copy.
- Performance: switching to a dict keyed by id gives O(1) lookups/edits, which matters as task count grows.
- Security & robustness: never storing plaintext passwords and adding a simple lock for thread-safety reduce common security and concurrency pitfalls.

These changes are intentionally minimal and low-risk while preparing the codebase for next steps (persistence, UI wiring, and richer scheduling logic).
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

Simplicity over richness: The scheduler uses straightforward in-memory datamodels and simple recurrence handling (auto-create the next daily/weekly occurrence). That keeps the code simple and easy
to reason about, but it trades off:
Persistence/traceability: created recurring tasks are new Task objects and there's no linkage metadata to the original task (no recurrence-id or series-id), so tracking history or editing the entire series is hard.
Control for the user: the automatic creation is immediate and unconditional — a power user might prefer a configurable behavior (create-on-completion vs. scheduled-expansion vs. using an rrule engine).
Scalability: All scheduling and conflict detection are done in-memory and with basic algorithms; for many tasks and users you might want indexed/queryable storage or interval trees for faster conflict queries.
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
