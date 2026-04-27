import streamlit as st
from pawpal_ai import PawPalAgent
from pawpal_system import TaskScheduler, User, Pet, Task
from datetime import datetime, date, time as dtime, timedelta

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Tasks")
st.caption("Add a task with scheduling details (date/time, duration, recurrence).")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "owner" not in st.session_state:
    # store the Owner/User instance so it persists across interactions
    st.session_state.owner = None

if "show_schedule" not in st.session_state:
    st.session_state.show_schedule = False

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=1440, value=20)
with col3:
    priority_str = st.selectbox("Priority", ["high", "medium", "low"], index=1)

unscheduled = st.checkbox("Unscheduled task (no specific time)", value=False)

date_col, time_col, recur_col = st.columns([1, 1, 1])
with date_col:
    if not unscheduled:
        scheduled_date = st.date_input("Scheduled date", value=date.today())
    else:
        scheduled_date = date.today()
with time_col:
    if not unscheduled:
        scheduled_time = st.time_input("Scheduled time", value=dtime(hour=9, minute=0))
    else:
        scheduled_time = dtime(hour=9, minute=0)
with recur_col:
    recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly"], index=0)

if unscheduled:
    st.info("This task will be saved without a scheduled time and proposed during planning.")

pet_select_col, add_btn_col = st.columns([3, 1])
with pet_select_col:
    # show pet selection if owner exists
    if st.session_state.owner is None or not st.session_state.owner.pets:
        pet_options = []
    else:
        pet_options = list(st.session_state.owner.pets.values())
    pet_names = [p.name for p in pet_options]
    selected_pet_name = st.selectbox("Assign to pet", ["(none)"] + pet_names)

with add_btn_col:
    if st.button("Add task"):
        # map priority string to integer (lower is higher priority for sorting)
        priority_map = {"high": 0, "medium": 1, "low": 2}
        p_val = priority_map.get(priority_str, 1)

        # If no owner exists yet, create one from the owner_name input
        if st.session_state.owner is None:
            st.session_state.owner = User(owner_name)

        owner: User = st.session_state.owner

        if selected_pet_name == "(none)":
            st.warning("No pet selected — please add and select a pet first.")
        else:
            pet_to_use = next((p for p in pet_options if p.name == selected_pet_name), None)
            if not pet_to_use:
                st.error("Selected pet not found. Try reloading the app or re-adding the pet.")
            else:
                # assemble scheduled datetime
                scheduled_dt = None if unscheduled else datetime.combine(scheduled_date, scheduled_time)
                recurrence_val = None if recurrence == "none" else recurrence
                t = Task(
                    name=task_title,
                    description=None,
                    scheduled_time=scheduled_dt,
                    duration_minutes=int(duration),
                    priority=p_val,
                    recurrence=recurrence_val,
                )
                scheduler = TaskScheduler(f"{pet_to_use.name}Scheduler", pet_to_use, owner)
                scheduler.schedule_task(t)
                if unscheduled:
                    st.success(f"Task '{t.name}' saved as unscheduled for pet {pet_to_use.name}.")
                else:
                    st.success(f"Task '{t.name}' scheduled for pet {pet_to_use.name} at {scheduled_dt}.")

if st.session_state.owner:
    owner: User = st.session_state.owner
    if owner.pets:
        st.write("Owner pets:")
        pets_table = [
            {"id": pid, "name": p.name, "type": p.type}
            for pid, p in owner.pets.items()
        ]
        st.table(pets_table)
    else:
        st.info("No pets yet. Add one below.")
else:
    st.info("No owner set. Enter a name above and add a pet to get started.")

st.divider()

st.subheader("Build Schedule")
st.caption("Use the scheduler to view sorted tasks and any warnings (conflicts or simultaneous tasks).")

if st.session_state.owner is None or not st.session_state.owner.pets:
    st.info("No owner or pets found. Add an owner/pet first to build a schedule.")
else:
    owner: User = st.session_state.owner
    pet_options = list(owner.pets.values())
    pet_names = [p.name for p in pet_options]
    selected_pet_name = st.selectbox("Select pet to schedule", pet_names)
    # find selected pet object
    selected_pet = next((p for p in pet_options if p.name == selected_pet_name), pet_options[0])
    scheduler = TaskScheduler(f"{selected_pet.name}Scheduler", selected_pet, owner)

    if st.button("Generate schedule"):
        st.session_state.show_schedule = True

    if st.session_state.show_schedule:
        agent = PawPalAgent(owner, selected_pet)
        outcome = agent.plan_day(date.today())

        if not outcome.tasks:
            st.info("No plan could be generated for this pet today. Add some tasks to see a suggested schedule.")
        else:
            st.success(
                f"Generated a plan for {selected_pet.name} with {len(outcome.tasks)} total task(s)."
            )

            st.info(f"Plan confidence: {outcome.confidence:.2f}  |  Score: {outcome.score:.2f}")

            with st.expander("Plan reasoning steps", expanded=True):
                for step in outcome.explanation_steps:
                    st.write(f"- {step}")

            if outcome.warnings:
                st.error("Warnings detected across pets and tasks:")
                for warning in outcome.warnings:
                    st.warning(warning)

            for t in outcome.tasks:
                title_time = t.scheduled_time.strftime("%Y-%m-%d %H:%M") if t.scheduled_time else "(unscheduled)"
                header = f"{t.name} — {title_time}"
                with st.expander(header, expanded=False):
                    st.write({
                        "Task": t.name,
                        "Scheduled": title_time,
                        "Duration (min)": t.duration_minutes or "",
                        "Priority": t.priority,
                        "Recurrence": t.recurrence or "",
                        "Completed": t.completed,
                    })

            conflicts = scheduler.detect_conflicts()
            if conflicts:
                st.error(
                    f"⚠️ {len(conflicts)} scheduling conflict(s) detected — please resolve these to avoid missed care."
                )
                conflict_rows = []
                for a, b in conflicts:
                    conflict_rows.append(
                        {
                            "task_a": a.name,
                            "a_start": a.scheduled_time.strftime("%Y-%m-%d %H:%M") if a.scheduled_time else "",
                            "task_b": b.name,
                            "b_start": b.scheduled_time.strftime("%Y-%m-%d %H:%M") if b.scheduled_time else "",
                        }
                    )
                st.table(conflict_rows)
                for a, b in conflicts:
                    a_duration = timedelta(minutes=a.duration_minutes) if a.duration_minutes else timedelta(minutes=30)
                    suggested = a.scheduled_time + a_duration + timedelta(minutes=5)
                    if st.button(
                        f"Resolve: move '{b.name}' after '{a.name}'",
                        key=f"resolve_{a.id}_{b.id}",
                    ):
                        try:
                            scheduler.reschedule_task(b.id, suggested)
                            st.success(
                                f"Moved '{b.name}' to {suggested} to resolve conflict with '{a.name}'."
                            )
                            st.session_state.show_schedule = True
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(str(e))

            sim_warnings = scheduler.detect_simultaneous_tasks()
            if sim_warnings:
                for w in sim_warnings:
                    st.warning(w)


## --- Add Pet UI wired to backend ---
st.divider()
st.subheader("Add a Pet")
new_pet_col1, new_pet_col2 = st.columns(2)
with new_pet_col1:
    new_pet_name = st.text_input("New pet name", value="Mochi", key="new_pet_name")
with new_pet_col2:
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"], key="new_pet_species")

if st.button("Add pet"):
    # ensure owner exists
    if st.session_state.owner is None:
        st.session_state.owner = User(owner_name)
    owner: User = st.session_state.owner
    pet = Pet(name=new_pet_name, type=new_pet_species)
    owner.log_pet(pet)
    st.success(f"Added pet {pet.name} (id={pet.id}) for owner {owner.name}.")
    # show updated pet list immediately
    pets_table = [{"id": pid, "name": p.name, "type": p.type} for pid, p in owner.pets.items()]
    st.table(pets_table)
