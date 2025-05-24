from moderator.config import NUM_OF_YEARS_TO_GRAD, MAX_MCS_FIRST_SEM, MIN_MCS_TO_GRAD
from moderator.helpers.utils import get_formatted_user_enrollments_from_db, get_semester_info
from moderator.planner.mod_selection import check_module_selection_for_term, convert_plan_to_frozenset_format, get_credit_internships, get_module_infos, get_terms_offered_for_module, get_list_of_mod_choices_for_term, get_total_mcs_for_term, insert_valid_plan_into_db
import streamlit as st
import time


# If a default selection is edited, make sure to remove these modules from subsequent default selections
# This ensures default selections never include module names from earlier default selections
def remove_edited_selection_from_subsequent_selections(edited_selection: list[str], subsequent_selection: list[str]) -> list[str]:
    for module_name in edited_selection:
        if module_name in subsequent_selection:
            subsequent_selection.remove(module_name)


# If a default selection is edited, we want to ensure that the AY is consistent, with regards to year-long modules
# For another term in that AY (chosen by us), get the new selection for that term such that this consistency is maintained
def ensure_year_long_consistency(conn: st.connections.SQLConnection, acad_year: str, edited_sem_num: int, edited_selection: list[str], target_sem_num: int, target_selection: list[str], module_infos: dict[str, dict[str, float | bool]]) -> None:
    # Get the year-long module names in the selectbox edited, each mapped to the terms that it is offered
    year_long_module_names_in_edited_selection = dict()
    for edited_module_name in edited_selection:
        edited_module_code = edited_module_name.split()[0]
        edited_module_is_year_long = module_infos[edited_module_code]["is_year_long"]
        if edited_module_is_year_long:
            # Get the sem_nums in which this year-long module is being offered, for this AY
            terms_offered = get_terms_offered_for_module(conn=conn, module_code=edited_module_code, acad_year=acad_year)
            
            # Update mapping
            year_long_module_names_in_edited_selection[edited_module_name] = terms_offered

    # Get new list of module names for the target selection
    new_target_selection = list()
    for target_module_name in target_selection:
        target_module_code = target_module_name.split()[0]
        target_module_is_year_long = module_infos[target_module_code]["is_year_long"]
        if target_module_is_year_long:
            # Get the sem_nums in which this year-long module is being offered, for this AY
            target_module_terms_offered = get_terms_offered_for_module(conn=conn, module_code=target_module_code, acad_year=acad_year)

            if edited_sem_num in target_module_terms_offered and target_module_name not in year_long_module_names_in_edited_selection:
                # Year-long module in target selection is also offered in the term corresponding to the edited selection,
                # but it is not in the edited selection. Must remove it from target selection
                continue

        # Module should still stay in the target selection
        new_target_selection.append(target_module_name)

    # Add new year-long modules from the edited selection into the target selection,
    # if these modules are also offered in the term corresponding to the target selection
    for year_long_module_name, year_long_module_terms_offered in year_long_module_names_in_edited_selection.items():
        if year_long_module_name not in new_target_selection and target_sem_num in year_long_module_terms_offered:
            new_target_selection.append(year_long_module_name)

    return new_target_selection


# Callable to update default selection for a selectbox, when its selection is changed
def change_default_selection(conn: st.connections.SQLConnection, acad_year: str, sem_num: int, ays_for_user: list[str], module_infos: dict[str, dict[str, float | bool]]) -> None:
    # Get the edited list of selected modules
    selectbox_key = f"mod_selection_{acad_year}_{sem_num}"
    edited_selection = st.session_state[selectbox_key]

    # Update default selection for that selectbox
    st.session_state["course_default_selections"][acad_year][sem_num] = edited_selection

    # Get the list of sem_nums after the sem_num corresponding to the edited selectbox, for that same AY
    sem_nums_in_that_ay = sorted(list(st.session_state["course_default_selections"][acad_year].keys()))
    subsequent_sem_nums_in_that_ay = sem_nums_in_that_ay[sem_nums_in_that_ay.index(sem_num) + 1:]

    # Get the list of AYs after the AY corresponding to the edited selectbox
    subsequent_ays = ays_for_user[ays_for_user.index(acad_year) + 1:]
    
    # Remove modules in the edited selection, from the subsequent semesters in that same AY
    for subsequent_sem_num in subsequent_sem_nums_in_that_ay:
        subsequent_selection = st.session_state["course_default_selections"][acad_year][subsequent_sem_num]
        remove_edited_selection_from_subsequent_selections(edited_selection=edited_selection, subsequent_selection=subsequent_selection)
    
    # Remove modules in the edited selection, from subsequent AYs
    for subsequent_ay in subsequent_ays:
        for subsequent_sem_num, subsequent_selection in st.session_state["course_default_selections"][subsequent_ay].items():
            remove_edited_selection_from_subsequent_selections(edited_selection=edited_selection, subsequent_selection=subsequent_selection)

    # If there are modules that are year-long in the edited selection, ensure that they are consistent across the terms in that AY
    for sem_num_in_ay in sem_nums_in_that_ay:
        if sem_num_in_ay != sem_num:
            # Only need to ensure consistency for the other semesters
            # Get default selection for the other semester
            target_selection = st.session_state["course_default_selections"][acad_year][sem_num_in_ay]

            # Get new default selection for the other semester, ensuring consistency in terms of year-long modules
            new_target_selection = ensure_year_long_consistency(conn=conn, acad_year=acad_year, edited_sem_num=sem_num, edited_selection=edited_selection, target_sem_num=sem_num_in_ay, target_selection=target_selection, module_infos=module_infos)

            # Update target selection
            st.session_state["course_default_selections"][acad_year][sem_num_in_ay] = new_target_selection


def handle_user_selection_for_term(selected_module_codes: list[str], plan: dict[str, dict[int, list[str]]] | None, acad_year: str, selected_total_mcs: float, outstanding_mc_balance: float, sem_min_mcs: float, sem_max_mcs: float, credit_internships: set[str]) -> tuple[str, str]:
    # Check if plan is already invalid from previous terms
    if plan is None:
        message_type = "error"
        message = "Course selections for previous terms are already invalid. Please review."
        return message_type, message

    # Check if user's selection is valid
    # Get course plan with the user's new selection, in frozenset format
    plan_with_new_selection_frozenset = convert_plan_to_frozenset_format(plan=plan) + (frozenset(selected_module_codes),)
    
    if plan_with_new_selection_frozenset in st.session_state["course_plans_checked"]:
        # If course plan (with the user's new selection) has already been checked before,
        # simply get the result from the session state
        # Result comprises of: 
        # - Type of Streamlit display message that the user will receive
        # - The message content
        message_type = st.session_state["course_plans_checked"][plan_with_new_selection_frozenset]["message_type"]
        message = st.session_state["course_plans_checked"][plan_with_new_selection_frozenset]["message"]

    else:
        # Check whether or not the new selection is valid
        result = check_module_selection_for_term(
            acad_year=acad_year,
            selected_module_codes=selected_module_codes,
            selected_total_mcs=selected_total_mcs,
            outstanding_mc_balance=outstanding_mc_balance,
            sem_min_mcs=sem_min_mcs,
            sem_max_mcs=sem_max_mcs,
            credit_internships=credit_internships,
            current_plan=plan
        )

        message_type = result["type"]
        message = result["message"]

        # Add course plan with the new selection (frozenset format) to session state for memoisation
        st.session_state["course_plans_checked"][plan_with_new_selection_frozenset] = {
            "message_type": message_type,
            "message": message
        }

    return message_type, message


def display_planner_tabs(conn: st.connections.SQLConnection) -> tuple[dict[str, dict[int, list[str]]], float]:
    # Get the AYs during which the user will be studying (capped off by current AY)
    first_ay = st.session_state["user_details"]["matriculation_ay"]
    first_ay_index = st.session_state["list_of_ays"].index(first_ay)
    ays_for_user = st.session_state["list_of_ays"][first_ay_index: first_ay_index + NUM_OF_YEARS_TO_GRAD]

    # Get module info required for planner
    module_infos = get_module_infos(conn=conn)

    # Get semester info (list) in the form (sem_num, sem_name, min_mcs)
    sem_info = get_semester_info(conn=conn)

    # Get list of credit-bearing internships
    credit_internships = get_credit_internships(conn=conn)

    # Initialise default selections for selectboxes (memorise user's choices) in session state
    # Structure: Keys are AYs. Values are themselves dictionaries, with keys = sem_num and 
    # values = list of default module names for that semester's selectbox
    if "course_default_selections" not in st.session_state:
        st.session_state["course_default_selections"] = {ay: {sem_num: list() for sem_num, _, _ in sem_info} for ay in ays_for_user}

    # Will keep track of the plan, building it iteratively from scratch, based on the user's selections for each term
    # Structure: Keys are AYs. Values are themselves dictionaries, with keys = sem_num and values = list of module codes for that term
    # NOTE: If this is None, it means the plan has already become invalid somewhere along the line
    plan = dict()

    # Track total number of MCs taken
    total_mcs_taken = 0.0

    # Create planner tabs for these AYs
    planner_tabs = st.tabs(ays_for_user)

    # Display planner for each AY
    is_first_sem_for_user = True
    for acad_year, planner_tab in zip(ays_for_user, planner_tabs):
        with planner_tab:
            is_first_sem_of_ay = True

            # Add a multi-module selection field for each term in the AY
            for sem_num, sem_name, sem_min_mcs in sem_info:
                # Add divider to split the selection fields
                if not is_first_sem_of_ay:
                    st.divider()

                # Get remaining MCs to clear (before current selection)
                outstanding_mc_balance = MIN_MCS_TO_GRAD - total_mcs_taken

                # If plan is already invalid, set default options for selectbox to an empty list
                if plan is None:
                    st.session_state["course_default_selections"][acad_year][sem_num] = list()

                # Get the list of module names to be offered to user
                module_name_choices = get_list_of_mod_choices_for_term(
                    conn=conn,
                    acad_year=acad_year,
                    sem_num=sem_num,
                    current_plan=plan,
                    module_infos=module_infos
                )

                # Get user's selection of modules
                selected_module_names = st.multiselect(
                    label=sem_name,
                    options=module_name_choices,
                    placeholder="Add courses",
                    default=st.session_state["course_default_selections"][acad_year][sem_num],
                    on_change=change_default_selection,
                    args=(conn, acad_year, sem_num, ays_for_user, module_infos),
                    key=f"mod_selection_{acad_year}_{sem_num}"
                )
                selected_module_codes = [module_name.split()[0] for module_name in selected_module_names]

                # Get total number of MCs for the selection
                selected_total_mcs = get_total_mcs_for_term(
                    conn=conn,
                    module_infos=module_infos,
                    module_codes_for_term=selected_module_codes,
                    acad_year=acad_year
                )
                st.markdown(f"**Total MCs**: {selected_total_mcs}")

                # If this is user's first semester, there is a limit to how many MCs he / she can take
                if is_first_sem_for_user:
                    sem_max_mcs = MAX_MCS_FIRST_SEM
                
                else:
                    sem_max_mcs = None

                # Check user's module selection for the new term, based on his / her current plan, and get the validation results
                # Result comprises of: 
                # - Type of Streamlit display message that the user will receive
                # - The message content
                message_type, message = handle_user_selection_for_term(
                    selected_module_codes=selected_module_codes,
                    plan=plan,
                    acad_year=acad_year,
                    selected_total_mcs=selected_total_mcs,
                    outstanding_mc_balance=outstanding_mc_balance,
                    sem_min_mcs=sem_min_mcs,
                    sem_max_mcs=sem_max_mcs,
                    credit_internships=credit_internships
                )
                
                # Display results of validation
                message_function = {
                    "success": st.success,
                    "warning": st.warning,
                    "error": st.error
                }
                message_function[message_type](message)

                # Update plan based on validation results
                if message_type == "success" or message_type == "warning":
                    # Allow user to proceed - update the plan
                    if acad_year not in plan:
                        plan[acad_year] = dict()

                    plan[acad_year][sem_num] = selected_module_codes

                    # Update total number of MCs taken
                    total_mcs_taken += selected_total_mcs

                    # Update default selection for this selectbox
                    st.session_state["course_default_selections"][acad_year][sem_num] = selected_module_names
                
                else:
                    # Plan is invalid - set it to None
                    plan = None

                    # Update default selection for this selectbox
                    st.session_state["course_default_selections"][acad_year][sem_num] = list()

                is_first_sem_for_user = False
                is_first_sem_of_ay = False

    return plan, total_mcs_taken
    

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

        # Update session state with this updated and formatted plan
        st.session_state["user_details"]["user_enrollments"] = formatted_plan
        
        st.success("Course plan has been saved!")
        time.sleep(1)
        st.rerun()

    if cancel_button:
        # If cancellation is triggered, use a rerun to close the dialog
        st.rerun()
            

# Initialise connection
conn = st.connection("nus_moderator", type="sql")

# Initialise dictionary of plans that have already been checked for their validity
# Format of course plan (keys): Tuple of frozensets, one frozenset per term representing the set of module codes
# taken that term. Frozensets are in chronological order of terms
# Values of dictionary: A dictionary consisting of the type of Streamlit display message that the user will receive, alongside the message content
if "course_plans_checked" not in st.session_state:
    st.session_state["course_plans_checked"] = dict()

# User is registered
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
    plan, total_mcs_taken = display_planner_tabs(conn=conn)

st.divider()

# Display confirmed MCs cleared by user
st.markdown("### Summary")
st.markdown(f"**Total MCs cleared**: {total_mcs_taken}")
st.markdown(f"**Total MCs required for graduation**: {MIN_MCS_TO_GRAD}")

# Functionality to add plan to user records, if the plan is valid
username = st.session_state["user_details"]["username"]
if plan is None:
    # Plan is invalid
    st.markdown("Your course plan is incomplete. Please complete it so that you can save it to your profile.")

else:
    # Plan is complete and valid
    st.markdown("Your course plan is complete! Click the button below to save it to your profile.")
    
    # Allow user to save his / her plan and add it to the database
    if st.button("Save Plan"):
        confirm_saving_of_plan(conn=conn, username=username, plan=plan)
