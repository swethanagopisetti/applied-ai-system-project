from __future__ import annotations

import logging
import os

import streamlit as st
import pawpal_system
from datetime import time
from anthropic import APIError
from rag_answer import PetCareAnswer, PetCareAnswerService

_log_level_name = os.getenv("PAWPAL_LOG_LEVEL", "INFO").upper()
_log_level = getattr(logging, _log_level_name, logging.INFO)
logging.basicConfig(
	level=_log_level if isinstance(_log_level, int) else logging.INFO,
	format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Plan pet-care tasks and ask questions about general cat and dog care. Answers are
grounded in PawPal+'s reviewed sources. They are informational only, not veterinary advice.
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

if "owner" not in st.session_state:
    st.session_state["owner"] = pawpal_system.Owner(owner_name)

owner = st.session_state["owner"]
owner.name = owner_name

if not owner.pets:
    owner.add_pet(pawpal_system.Pet(pet_name, species))

pet = owner.pets[0]
pet.name = pet_name
pet.species = species

st.divider()

st.subheader("Ask about pet care")
st.caption(
    "Ask about general grooming, scratching, or exercise. "
    "For health concerns or emergencies, contact a veterinarian."
)
with st.form("pet_care_question"):
    pet_care_question = st.text_input(
        "Your question",
        placeholder="What are some enrichment ideas for my pet?",
    )
    ask_submitted = st.form_submit_button("Ask PawPal+")

if ask_submitted:
    if not pet_care_question.strip():
        st.error("Enter a question before submitting.")
        st.session_state.pop("pet_care_answer", None)
    else:
        species_filter = species if species in {"cat", "dog"} else None
        try:
            st.session_state["pet_care_answer"] = PetCareAnswerService().answer(
                pet_care_question,
                species=species_filter,
            )
        except APIError as error:
            st.session_state.pop("pet_care_answer", None)
            logger.exception("Anthropic request failed while answering a pet-care question.")
            st.error(
                "The answer service is temporarily unavailable. "
                "Please try again later."
            )
        except RuntimeError as error:
            st.session_state.pop("pet_care_answer", None)
            logger.exception("Pet-care answer generation failed.")
            st.error("Could not generate an answer. Please try again.")
        except (OSError, ValueError) as error:
            st.session_state.pop("pet_care_answer", None)
            logger.exception("Could not load or process the pet-care knowledge base.")
            st.error(
                "Could not process the question. Please check the knowledge-base "
                "file and try again."
            )

pet_care_answer: PetCareAnswer | None = st.session_state.get("pet_care_answer")
if pet_care_answer is not None:
    if pet_care_answer.status == "veterinary_referral":
        st.warning(pet_care_answer.answer)
    elif pet_care_answer.status == "insufficient_evidence":
        st.info(pet_care_answer.answer)
    else:
        st.markdown(pet_care_answer.answer)

    if pet_care_answer.status == "answered":
        with st.expander("Optionally add a task based on this guidance"):
            with st.form("answer_based_task"):
                suggested_task_description = st.text_input(
                    "Task description",
                    placeholder="Describe the care task you want to schedule",
                    key="answer_based_task_description",
                )
                suggested_task_time = st.time_input(
                    "Task time",
                    value=time(8, 0),
                    key="answer_based_task_time",
                )
                suggested_task_frequency = st.selectbox(
                    "Frequency",
                    ["daily", "weekly", "once"],
                    key="answer_based_task_frequency",
                )
                add_suggested_task = st.form_submit_button("Add task to schedule")

            if add_suggested_task:
                if not suggested_task_description.strip():
                    st.error("Enter a task description before adding it.")
                else:
                    pet.add_task(
                        pawpal_system.Task(
                            description=suggested_task_description.strip(),
                            time=suggested_task_time,
                            frequency=suggested_task_frequency,
                        )
                    )
                    st.success("Task added to the schedule.")

st.divider()

st.subheader("Schedule a Task")
with st.form("schedule_task"):
    task_description = st.text_input("Task", value="Morning walk")
    task_time = st.time_input("Time", value=time(8, 0))
    frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
    submitted = st.form_submit_button("Schedule task")

if submitted:
    pet.add_task(
        pawpal_system.Task(
            description=task_description,
            time=task_time,
            frequency=frequency,
        )
    )

scheduler = pawpal_system.Scheduler()
conflict_warnings = scheduler.detect_conflicts(owner)
if conflict_warnings:
    st.subheader("Scheduling conflicts")
    for warning in conflict_warnings:
        st.warning(
            f"{warning} Please move one of these tasks to another time.",
            icon="⚠️",
        )
else:
    st.success("No scheduling conflicts detected.")

st.subheader("Current schedule")
pet_options = ["All pets", *(owner_pet.name for owner_pet in owner.pets)]
selected_pet = st.selectbox("Pet", pet_options)
status_options = {"All tasks": None, "To do": False, "Completed": True}
selected_status = st.selectbox("Status", list(status_options))

filtered_tasks = scheduler.filter_tasks(
    owner,
    completed=status_options[selected_status],
    pet_name=None if selected_pet == "All pets" else selected_pet,
)
schedule = scheduler.sort_by_time(filtered_tasks)

if schedule:
    st.table(
        [
            {
                "Pet": next(
                    owner_pet.name
                    for owner_pet in owner.pets
                    if any(pet_task is task for pet_task in owner_pet.tasks)
                ),
                "Time": task.time.strftime("%H:%M"),
                "Task": task.description,
                "Frequency": task.frequency,
                "Completed": task.completed,
            }
            for task in schedule
        ]
    )
    st.caption(f"Showing {len(schedule)} task(s), sorted by scheduled time.")
else:
    if scheduler.get_all_tasks(owner):
        st.info("No tasks match these filters.")
    else:
        st.info("No tasks scheduled yet.")
