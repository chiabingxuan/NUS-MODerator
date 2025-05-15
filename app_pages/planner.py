from moderator.config import NUM_OF_YEARS_TO_GRAD, MAX_MCS_FIRST_SEM, MIN_MCS_TO_GRAD
from moderator.planner.mod_selection import check_module_selection_for_term, get_list_of_mod_choices_for_term, get_semester_info, get_total_mcs_for_term
import streamlit as st


# Callable for button that redirects user to login page
def redirect_to_login() -> None:
    # Remove user details from session state - on rerun, this will trigger the "logged out" state 
    # and bring out the login forms
    st.session_state.pop("user_details")


# Callable to update default selection for a selectbox, when its selection is changed
def change_default_selection(acad_year: str, sem_num: int):
    selectbox_key = f"mod_selection_{acad_year}_{sem_num}"
    st.session_state["course_default_selections"][acad_year][sem_num] = st.session_state[selectbox_key]


def display_planner_tabs(conn: st.connections.SQLConnection) -> float:
    # Get the AYs during which the user will be studying (capped off by current AY)
    first_ay = st.session_state["user_details"]["matriculation_ay"]
    first_ay_index = st.session_state["list_of_ays"].index(first_ay)
    ays_for_user = st.session_state["list_of_ays"][first_ay_index: first_ay_index + NUM_OF_YEARS_TO_GRAD]

    # Get semester info (list) in the form (sem_num, sem_name, min_mcs)
    sem_info = get_semester_info(conn=conn)

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
                module_name_choices = get_list_of_mod_choices_for_term(conn=conn, acad_year=acad_year, sem_num=sem_num, current_plan=plan)

                # Get user's selection of modules
                selected_module_names = st.multiselect(
                    label=sem_name,
                    options=module_name_choices,
                    placeholder="Add courses",
                    default=st.session_state["course_default_selections"][acad_year][sem_num],
                    on_change=change_default_selection,
                    args=(acad_year, sem_num),
                    key=f"mod_selection_{acad_year}_{sem_num}"
                )
                selected_module_codes = [module_name.split()[0] for module_name in selected_module_names]

                # Get total number of MCs for the selection
                selected_total_mcs = get_total_mcs_for_term(conn=conn, module_codes_for_term=selected_module_codes)
                st.markdown(f"**Total MCs**: {selected_total_mcs}")

                # If this is user's first semester, there is a limit to how many MCs he / she can take
                if is_first_sem_for_user:
                    sem_max_mcs = MAX_MCS_FIRST_SEM
                
                else:
                    sem_max_mcs = None

                # Check if user's selection is valid
                result = check_module_selection_for_term(
                    acad_year=acad_year,
                    selected_module_codes=selected_module_codes,
                    selected_total_mcs=selected_total_mcs,
                    outstanding_mc_balance=outstanding_mc_balance,
                    sem_min_mcs=sem_min_mcs,
                    sem_max_mcs=sem_max_mcs,
                    current_plan=plan
                )

                # Display results of validation
                message_function = {
                    "success": st.success,
                    "warning": st.warning,
                    "error": st.error
                }
                message_function[result["type"]](result["message"])

                if result["type"] == "success" or result["type"] == "warning":
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

    return total_mcs_taken
    
    
# Initialise connection
conn = st.connection("nus_moderator", type="sql")

# Verify that user is registered
if st.session_state["user_details"]["username"] is None:
    # User is a guest - no permission to access this page
    with st.container(border=True):
        st.markdown("### Sorry, guests cannot access this feature :(")
        st.markdown("Please log in to access this feature.")
        redirect_to_login_button = st.button("Login", on_click=redirect_to_login)

else:
    # User is registered
    # Display header and introduction
    st.header("Course Planner")
    st.markdown("**Note**: We are unable to retrieve prerequisite information for AY2022-2023 - for this, data from AY2023-2024 is used instead.")
    
    # Display buttons to update data
    with st.container(border=True):
        total_mcs_taken = display_planner_tabs(conn=conn)
    st.divider()

    # Display confirmed MCs cleared by user
    st.markdown("### Summary")
    st.markdown(f"**Total MCs cleared**: {total_mcs_taken}")
    st.markdown(f"**Total MCs required for graduation**: {MIN_MCS_TO_GRAD}")