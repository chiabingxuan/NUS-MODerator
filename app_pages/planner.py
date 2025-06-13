from moderator.config import IBLOCS_SEM_NUM
from moderator.planner.course_plan_checker import CoursePlanChecker
from moderator.planner.save_plan_to_db import insert_valid_plan_into_db
from moderator.utils.helpers import get_formatted_user_enrollments_from_db
import streamlit as st
import time


# Callable to update default selection for a selectbox, when its selection is changed
def change_default_selection(checker: CoursePlanChecker, acad_year: str, sem_num: int) -> None:
    # Get the edited list of selected modules
    selectbox_key = f"mod_selection_{acad_year}_{sem_num}"
    edited_selection = st.session_state[selectbox_key]

    # Update default selection for that selectbox
    checker.set_default_selection_for_term(acad_year=acad_year, sem_num=sem_num, new_default_selection=edited_selection)

    # Get the list of sem_nums after the sem_num corresponding to the edited selectbox, for that same AY
    sem_nums_in_that_ay = sorted(list(checker.course_default_selections[acad_year].keys()))
    subsequent_sem_nums_in_that_ay = sem_nums_in_that_ay[sem_nums_in_that_ay.index(sem_num) + 1:]

    # Get the list of AYs after the AY corresponding to the edited selectbox
    subsequent_ays = checker.ays_for_user[checker.ays_for_user.index(acad_year) + 1:]
    
    # Remove modules in the edited selection, from the subsequent semesters in that same AY
    for subsequent_sem_num in subsequent_sem_nums_in_that_ay:
        checker.remove_edited_selection_from_subsequent_selections(
            edited_selection=edited_selection,
            subsequent_selection_acad_year=acad_year,
            subsequent_selection_sem_num=subsequent_sem_num
        )
    
    # Remove modules in the edited selection, from subsequent AYs
    for subsequent_ay in subsequent_ays:
        for subsequent_sem_num in checker.course_default_selections[subsequent_ay].keys():
            checker.remove_edited_selection_from_subsequent_selections(
                edited_selection=edited_selection,
                subsequent_selection_acad_year=subsequent_ay,
                subsequent_selection_sem_num=subsequent_sem_num
            )

    # If there are modules that are year-long in the edited selection,
    # ensure that they are consistent across the terms in that AY
    for sem_num_in_ay in sem_nums_in_that_ay:
        if sem_num_in_ay != sem_num:
            # Only need to ensure consistency for the other semesters
            # Update default selection for the other semester, ensuring consistency in terms of year-long modules
            checker.ensure_year_long_consistency(
                acad_year=acad_year,
                edited_sem_num=sem_num,
                edited_selection=edited_selection,
                target_sem_num=sem_num_in_ay
            )
            

def display_planner_tabs(checker: CoursePlanChecker) -> tuple[dict[str, dict[int, list[str]]], float]:
    # Get AYs to consider for this user, starting from IBLOCs term
    ays_for_user = checker.ays_for_user
    ibloc_ay, matriculation_ay = ays_for_user[0], ays_for_user[1]      # User can take IBLOCs the AY before he / she matriculates

    # Create planner tabs for these AYs
    planner_tab_names = ays_for_user.copy()
    planner_tab_names[0] = "iBLOCs"       # Format the name of the IBLOCs tab
    planner_tabs = st.tabs(planner_tab_names)

    # Display planner for each AY
    is_y1s1_for_user = False
    for acad_year, planner_tab in zip(ays_for_user, planner_tabs):
        with planner_tab:
            # Update flag for whether or not this iteration corresponds to Y1S1
            if acad_year == matriculation_ay:
                is_y1s1_for_user = True
            
            is_first_sem_of_ay = True

            # Add a multi-module selection field for each term in the AY
            # Semester info is a list of lists in the form (sem_num, sem_name, min_mcs)
            for sem_num, sem_name, sem_min_mcs in checker._sem_info:
                # If this is an IBLOC AY, only need to consider one term (ie. sem_num = 3 aka Special Term 1)
                if acad_year == ibloc_ay and sem_num != IBLOCS_SEM_NUM:
                    continue

                # Add divider to split the selection fields
                if not is_first_sem_of_ay:
                    st.divider()

                # Get the list of module names to be offered to user
                module_name_choices = checker.get_list_of_mod_choices_for_term(
                    acad_year=acad_year,
                    sem_num=sem_num
                )

                # Get the default selection for this term's selectbox, based on previous responses of user
                default_selection_for_term = checker.get_default_selection_for_term_during_check(
                    acad_year=acad_year,
                    sem_num=sem_num
                )

                # Get user's selection of modules
                selected_module_names = st.multiselect(
                    label=sem_name,
                    options=module_name_choices,
                    placeholder="Add courses",
                    default=default_selection_for_term,
                    on_change=change_default_selection,
                    args=(checker, acad_year, sem_num),
                    key=f"mod_selection_{acad_year}_{sem_num}"
                )

                # Check user's module selection for the new term, based on his / her current plan, and get the validation results
                # Result comprises of: 
                # - Type of Streamlit display message that the user will receive
                # - The message content
                # This will also update the checker, based on the results of the check
                message_type, message, selected_total_mcs = checker.handle_user_selection_for_term(
                    selected_module_names=selected_module_names,
                    acad_year=acad_year,
                    sem_num=sem_num,
                    sem_min_mcs=sem_min_mcs,
                    is_y1s1_for_user=is_y1s1_for_user
                )

                # Display total number of MCs for the selection
                st.markdown(f"**Total MCs**: {selected_total_mcs}")
                
                # Display results of validation
                message_function = {
                    "success": st.success,
                    "warning": st.warning,
                    "error": st.error
                }
                message_function[message_type](message)

                is_y1s1_for_user = False
                is_first_sem_of_ay = False

    return checker.plan, checker.total_mcs_taken
    

@st.dialog("This will overwrite your profile's existing course plan (if any). Are you sure you want to proceed?")
def confirm_saving_of_plan(conn: st.connections.SQLConnection, username: str, plan: dict[str, dict[int, list[str]]]) -> None:
    # Add button to confirm saving of plan
    confirm_button = st.button("Yes")
    
    # Add button to cancel saving of plan
    cancel_button = st.button("No")

    if confirm_button:
        # Add plan to database
        insert_valid_plan_into_db(conn=conn, username=username, plan=plan)

        # Get formatted plan from database
        formatted_plan = get_formatted_user_enrollments_from_db(conn=conn, username=username)

        # Update user with this updated and formatted plan
        user.user_enrollments = formatted_plan
        
        st.success("Course plan has been saved!")
        time.sleep(1)
        st.rerun()

    if cancel_button:
        # If cancellation is triggered, use a rerun to close the dialog
        st.rerun()
            

# Retrieve connection from session state
conn = st.session_state["conn"]

# Get user saved in session state
user = st.session_state["user"]

# Initialise course plan checker if it does not exist. Otherwise, reset existing checker
if "course_plan_checker" not in st.session_state:
    st.session_state["course_plan_checker"] = CoursePlanChecker(
        conn=conn,
        user=user,
        list_of_ays=st.session_state["list_of_ays"]
    )

else:
    st.session_state["course_plan_checker"].reset()

# Display header and introduction
st.header("Course Planner")
st.markdown(
    """
    **Note**:
    - You can only plan for courses up until the current AY.
    - We are unable to retrieve prerequisite information for AY2022-2023 - for this, data from AY2023-2024 is used instead.
    - This planner does not take preclusions into account.
    - Before saving a course plan to your profile, please make sure that you have fulfilled all prerequisite requirements.
    """
)

# Display buttons to update data
with st.container(border=True):
    plan, total_mcs_taken = display_planner_tabs(checker=st.session_state["course_plan_checker"])

st.divider()

# Display confirmed MCs cleared by user
st.markdown("### Summary")
st.markdown(f"**Total MCs cleared**: {total_mcs_taken}")
st.markdown(f"**Total MCs required for graduation**: {st.session_state["course_plan_checker"].min_mcs_to_grad}")

# Functionality to add plan to user records, if the plan is valid
if plan is None:
    # Plan is invalid
    st.markdown("Your course plan is incomplete. Please complete it so that you can save it to your profile.")

else:
    # Plan is complete and valid
    st.markdown("Your course plan is complete! Click the button below to save it to your profile.")
    
    # Allow user to save his / her plan and add it to the database
    if st.button("Save Plan"):
        confirm_saving_of_plan(conn=conn, username=user.username, plan=plan)
