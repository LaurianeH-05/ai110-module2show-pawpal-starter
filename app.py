import streamlit as st
from pawpal_system import DailyPlan, TaskScheduler, User, Pet, Task

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
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "owner" not in st.session_state:
    # store the Owner/User instance so it persists across interactions
    st.session_state.owner = None

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    # When adding a task, attempt to schedule it for a selected pet
    # map priority string to integer (lower is higher priority for sorting)
    priority_map = {"high": 0, "medium": 1, "low": 2}
    p_val = priority_map.get(priority, 1)

    # If no owner exists yet, create one from the owner_name input
    if st.session_state.owner is None:
        st.session_state.owner = User(owner_name)

    owner: User = st.session_state.owner

    # choose a pet to schedule the task for (first pet by default)
    pet_options = list(owner.pets.values())
    if not pet_options:
        st.warning("No pets registered yet — please add a pet first.")
    else:
        pet_to_use = pet_options[0]
        # create Task object and schedule via TaskScheduler
        t = Task(name=task_title, description=None, priority=p_val)
        scheduler = TaskScheduler(f"{pet_to_use.name}Scheduler", pet_to_use, owner)
        scheduler.schedule_task(t)
        st.success(f"Task '{t.name}' scheduled for pet {pet_to_use.name}.")

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
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    st.warning(
        "Not implemented yet. Next step: create your scheduling logic (classes/functions) and call it here."
    )
    st.markdown(
        """
Suggested approach:
1. Design your UML (draft).
2. Create class stubs (no logic).
3. Implement scheduling behavior.
4. Connect your scheduler here and display results.
"""
    )


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
