import streamlit as st
from pawpal_system import DailyPlan, TaskScheduler, User, Pet, Task
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

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=1440, value=20)
with col3:
    priority_str = st.selectbox("Priority", ["high", "medium", "low"], index=1)

date_col, time_col, recur_col = st.columns([1, 1, 1])
with date_col:
    scheduled_date = st.date_input("Scheduled date", value=date.today())
with time_col:
    scheduled_time = st.time_input("Scheduled time", value=dtime(hour=9, minute=0))
with recur_col:
    recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly"], index=0)

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
                scheduled_dt = datetime.combine(scheduled_date, scheduled_time)
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
        # get sorted tasks for the pet
        sorted_tasks = scheduler.sort_by_time()

        if not sorted_tasks:
            st.info("No tasks scheduled for this pet. Add tasks to see a plan.")
        else:
            st.success(f"{len(sorted_tasks)} task(s) found for {selected_pet.name} — shown in chronological order.")

            # Explain the schedule in plain language
            scheduled_only = [t for t in sorted_tasks if t.scheduled_time]
            if scheduled_only:
                earliest = min(s.scheduled_time for s in scheduled_only)
                latest = max(s.scheduled_time + (timedelta(minutes=s.duration_minutes) if s.duration_minutes else timedelta(minutes=30)) for s in scheduled_only)
                total_minutes = sum((t.duration_minutes if t.duration_minutes else 30) for t in scheduled_only)
                gaps = []
                scheduled_only_sorted = sorted(scheduled_only, key=lambda x: x.scheduled_time)
                for i in range(len(scheduled_only_sorted) - 1):
                    end_i = scheduled_only_sorted[i].scheduled_time + (timedelta(minutes=scheduled_only_sorted[i].duration_minutes) if scheduled_only_sorted[i].duration_minutes else timedelta(minutes=30))
                    start_j = scheduled_only_sorted[i+1].scheduled_time
                    gap = (start_j - end_i).total_seconds() / 60
                    if gap > 0:
                        gaps.append(int(gap))

                explanation = f"Schedule covers {len(scheduled_only)} scheduled task(s) from {earliest.strftime('%Y-%m-%d %H:%M')} to {latest.strftime('%Y-%m-%d %H:%M')}, totaling ~{total_minutes} minutes."
                if gaps:
                    explanation += f" Gaps between tasks (minutes): {', '.join(str(g) for g in gaps)}."
                st.info(explanation)

            # Show each task with actions (Complete / Edit / Reschedule / Cancel)
            for t in sorted_tasks:
                title_time = t.scheduled_time.strftime("%Y-%m-%d %H:%M") if t.scheduled_time else "(no time)"
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

                    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
                    # Complete button
                    if c1.button("Complete", key=f"complete_{t.id}"):
                        try:
                            scheduler.mark_task_complete(t.id)
                            st.success(f"Marked '{t.name}' complete. If recurring, next occurrence has been scheduled.")
                        except Exception as e:
                            st.error(str(e))

                    # Edit button — toggles an inline edit form
                    edit_key = f"edit_{t.id}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False

                    if c2.button("Edit", key=f"edit_btn_{t.id}"):
                        st.session_state[edit_key] = True

                    if st.session_state.get(edit_key):
                        new_name = st.text_input("Name", value=t.name, key=f"edit_name_{t.id}")
                        new_duration = st.number_input("Duration (minutes)", min_value=1, max_value=1440, value=t.duration_minutes or 30, key=f"edit_dur_{t.id}")
                        pr_map = {0: "high", 1: "medium", 2: "low"}
                        rev_map = {v: k for k, v in pr_map.items()}
                        cur_pr = pr_map.get(t.priority, "medium")
                        new_pr_str = st.selectbox("Priority", ["high", "medium", "low"], index=["high", "medium", "low"].index(cur_pr), key=f"edit_pr_{t.id}")
                        new_recur = st.selectbox("Recurrence", ["none", "daily", "weekly"], index=["none", "daily", "weekly"].index(t.recurrence if t.recurrence else "none"), key=f"edit_recur_{t.id}")
                        nd_date = st.date_input("Scheduled date", value=t.scheduled_time.date() if t.scheduled_time else date.today(), key=f"edit_date_{t.id}")
                        nd_time = st.time_input("Scheduled time", value=t.scheduled_time.time() if t.scheduled_time else dtime(hour=9), key=f"edit_time_{t.id}")
                        if st.button("Apply edit", key=f"apply_edit_{t.id}"):
                            try:
                                new_dt = datetime.combine(nd_date, nd_time)
                                owner.edit_task(t.id, name=new_name, scheduled_time=new_dt, duration_minutes=int(new_duration), priority=rev_map.get(new_pr_str, 1), recurrence=(None if new_recur == "none" else new_recur))
                                st.success(f"Updated '{new_name}'.")
                                st.session_state[edit_key] = False
                            except Exception as e:
                                st.error(str(e))

                    # Reschedule flow using session_state flag
                    res_key = f"reschedule_{t.id}"
                    if res_key not in st.session_state:
                        st.session_state[res_key] = False

                    if c3.button("Reschedule", key=f"res_btn_{t.id}"):
                        st.session_state[res_key] = True

                    if st.session_state.get(res_key):
                        # show date/time pickers and apply button
                        new_date = st.date_input("New date", value=t.scheduled_time.date() if t.scheduled_time else date.today(), key=f"res_date_{t.id}")
                        new_time = st.time_input("New time", value=t.scheduled_time.time() if t.scheduled_time else dtime(hour=9), key=f"res_time_{t.id}")
                        if st.button("Apply reschedule", key=f"apply_res_{t.id}"):
                            new_dt = datetime.combine(new_date, new_time)
                            try:
                                scheduler.reschedule_task(t.id, new_dt)
                                st.success(f"Rescheduled '{t.name}' to {new_dt}.")
                                st.session_state[res_key] = False
                            except Exception as e:
                                st.error(str(e))

                    # Cancel (delete) flow with confirmation
                    confirm_key = f"confirm_cancel_{t.id}"
                    if confirm_key not in st.session_state:
                        st.session_state[confirm_key] = False

                    if c4.button("Cancel", key=f"cancel_{t.id}"):
                        st.session_state[confirm_key] = True

                    if st.session_state.get(confirm_key):
                        st.warning(f"Are you sure you want to delete '{t.name}'? This action cannot be undone.")
                        c_yes, c_no = st.columns([1, 1])
                        if c_yes.button("Yes, delete", key=f"yes_del_{t.id}"):
                            try:
                                scheduler.cancel_task(t.id)
                                st.success(f"Deleted '{t.name}'.")
                                st.session_state[confirm_key] = False
                            except Exception as e:
                                st.error(str(e))
                        if c_no.button("No, keep", key=f"no_del_{t.id}"):
                            st.info("Deletion cancelled.")
                            st.session_state[confirm_key] = False

            # show conflicts (overlaps)
            conflicts = scheduler.detect_conflicts()
            if conflicts:
                # stronger, attention-grabbing conflict banner
                st.error(f"⚠️ {len(conflicts)} scheduling conflict(s) detected — please resolve these to avoid missed care.")
                # show concise conflict pairs in a table with action buttons to suggest a fix
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
                st.markdown(
                    "**Suggested quick fixes:** Use the Reschedule action on one of the conflicting tasks below, or click the suggested resolution button to automatically move the later task just after the earlier task."
                )
                # provide auto-resolve suggestions
                for a, b in conflicts:
                    # suggest moving task b after a
                    a_duration = timedelta(minutes=a.duration_minutes) if a.duration_minutes else timedelta(minutes=30)
                    suggested = a.scheduled_time + a_duration + timedelta(minutes=5)
                    if st.button(f"Resolve: move '{b.name}' after '{a.name}'", key=f"resolve_{a.id}_{b.id}"):
                        try:
                            scheduler.reschedule_task(b.id, suggested)
                            st.success(f"Moved '{b.name}' to {suggested} to resolve conflict with '{a.name}'.")
                        except Exception as e:
                            st.error(str(e))

            # show simultaneous scheduling warnings across owner's tasks
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
