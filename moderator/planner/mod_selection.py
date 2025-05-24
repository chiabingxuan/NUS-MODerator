from moderator.helpers.utils import get_semester_name_to_num_mapping
from moderator.sql.credit_internships import GET_CREDIT_INTERNSHIPS_QUERY
from moderator.sql.enrollments import DELETE_USER_ENROLLMENT_STATEMENT, INSERT_NEW_ENROLLMENT_STATEMENT, GET_ENROLLMENTS_OF_USER_QUERY
from moderator.sql.modules import GET_SPECIFIC_TERM_MODULES_QUERY, GET_MODULES_INFO_FOR_PLANNER_QUERY, GET_TERMS_OFFERED_FOR_SPECIFIC_MODULE_QUERY
import re
import requests
import streamlit as st
from sqlalchemy import text


def get_completed_module_codes_from_plan(current_plan: dict[str, dict[int, list[str]]]) -> list[str]:
    completed_module_codes = list()

    for acad_year, acad_year_plan in current_plan.items():
        for sem_num, module_codes in acad_year_plan.items():
            # We have already ensured that there will never be repeated module codes across the terms (except for year-long modules)
            # This is because user will only choose among modules that they have not taken yet
            completed_module_codes.extend(module_codes)

    return completed_module_codes


def get_available_modules_for_term(conn: st.connections.SQLConnection, acad_year: str, sem_num: int) -> list[list[str]]:
    # Query the modules available for the selected term - a list of lists in the form (module_code, module_title)
    available_modules = conn.query(
        GET_SPECIFIC_TERM_MODULES_QUERY,
        params={
            "acad_year": acad_year,
            "sem_num": sem_num
        },
        ttl=3600
    ).values.tolist()

    return available_modules


def get_credit_internships(conn: st.connections.SQLConnection) -> set[str]:
    # Query the modules that are credit-bearing internships
    credit_internships = set(
        conn.query(
            GET_CREDIT_INTERNSHIPS_QUERY,
            ttl=3600
        )["internship_code"]
    )

    return credit_internships


def get_list_of_mod_choices_for_term(conn: st.connections.SQLConnection, acad_year: str, sem_num: int, current_plan: dict[str, dict[int, list[str]]] | None, module_infos: dict[str, dict[str, float | bool]]) -> list[str]:
    # If current plan is None (already invalid), there should be no selections given
    if current_plan is None:
        return list()
    
    # Get previous term's selection of modules
    if not current_plan:
        # If plan is empty (current term is the very first term), set previous term's module selection is empty
        previous_term_ay = None
        previous_term_sem_num = None
        previous_term_module_selection = list()

    else:
        previous_term_ay = sorted(current_plan.keys())[-1]
        previous_term_sem_num = sorted(current_plan[previous_term_ay].keys())[-1]
        previous_term_module_selection = current_plan[previous_term_ay][previous_term_sem_num]

    # Get modules offered for this term in this AY - a list of lists in the form (module_code, module_title)
    available_modules = get_available_modules_for_term(conn=conn, acad_year=acad_year, sem_num=sem_num)

    # Get list of module codes completed already
    completed_module_codes = get_completed_module_codes_from_plan(current_plan=current_plan)

    # Get list of formatted names corresponding to all the remaining modules that have not been taken yet
    module_name_selections = list()
    for module_code, module_title in available_modules:
        if module_code in completed_module_codes:
            # Edge case to handle: Module has been completed already, but...
            # - It is a year-long module
            # - It was taken in the previous term
            # - The previous term is still in the same academic year as this current term
            # Which means this module should still be taken this term
            module_is_year_long = module_infos[module_code]["is_year_long"]
            if not (module_is_year_long and module_code in previous_term_module_selection and previous_term_ay == acad_year):
                # Not the edge case - skip this module as it should not be taken this term
                continue

        formatted_module_name = f"{module_code} {module_title}"
        module_name_selections.append(formatted_module_name)

    return module_name_selections


def get_module_infos(conn: st.connections.SQLConnection) -> dict[str, dict[str, float | bool]]:
    rows_queried = conn.query(
        GET_MODULES_INFO_FOR_PLANNER_QUERY,
        ttl=3600
    ).values.tolist()

    # Maps each module to its number of MCs, and whether or not it is year-long
    module_infos = {
        module_code: {
            "num_mcs": float(num_mcs),
            "is_year_long": is_year_long
        } for module_code, num_mcs, is_year_long in rows_queried
    }

    return module_infos


def get_terms_offered_for_module(conn: st.connections.SQLConnection, module_code: str, acad_year: str) -> list[int]:
    # Query the modules that are credit-bearing internships
    terms_offered = list(
        conn.query(
            GET_TERMS_OFFERED_FOR_SPECIFIC_MODULE_QUERY,
            params={
                "module_code": module_code,
                "acad_year": acad_year
            },
            ttl=3600
        )["sem_num"]
    )

    return terms_offered


def get_total_mcs_for_term(conn: st.connections.SQLConnection, module_infos: dict[str, dict[str, float | bool]], module_codes_for_term: list[str], acad_year: str) -> float:
    total_mcs = 0.0

    # Get number of MCs for each module chosen for the term
    for module_code in module_codes_for_term:
        module_mcs, module_is_year_long = module_infos[module_code]["num_mcs"], module_infos[module_code]["is_year_long"]

        # If module is year-long, number of MCs should be divided equally across each term that it is being taken
        if module_is_year_long:
            num_sems_taken = len(get_terms_offered_for_module(conn=conn, module_code=module_code, acad_year=acad_year))
            module_mcs /= num_sems_taken

        total_mcs += module_mcs

    return total_mcs


def get_prereq_tree(module_code: str, acad_year: str) -> dict | None:
    # NUSMods has no information on prerequisite trees for AY2022-2023. 
    # Use data from AY2023-2024 instead - it's close enough bro
    if acad_year == "2022-2023":
        acad_year = "2023-2024"

    # Use NUSMods API to get detailed information about the specified module, for the chosen academic year
    nusmods_endpoint_url = f"https://api.nusmods.com/v2/{acad_year}/modules/{module_code}.json"
    response = requests.get(url=nusmods_endpoint_url)

    if response.status_code != 200:
        raise Exception("Unsuccessful request to NUSMods API")

    # Successful GET request
    module_info = response.json()

    if "prereqTree" not in module_info:
        # Module has no prerequisites
        return None

    return module_info["prereqTree"]


def check_if_prereqs_satisfied(prereq_tree: dict | str | None, completed_module_codes: list[str]) -> bool:
    if prereq_tree is None:
        # Base case 1: No prerequisites, vacuously true
        return True
    
    if type(prereq_tree) == str:
        # Base case 2: Tree is simply a module - check if it has been taken already
        # Remove grade. The module code obtained might have %, which is a wildcard
        # Eg. CS1010% = Any module starting with CS1010
        module_code_with_wildcard = prereq_tree.split(":")[0]

        # Change any % sign into the correct regex
        module_code_regex = module_code_with_wildcard.replace("%", ".*")

        # Check for at least one match in the list of completed module codes
        for completed_module_code in completed_module_codes:
            if re.search(module_code_regex, completed_module_code):
                return True
        
        return False

    # How the next layer of trees are aggregated (can be "and", "or", "nOf")
    [operation,] = list(prereq_tree.keys())

    if operation == "and":
        # Get list of trees in the layer below
        next_layer_trees = prereq_tree[operation]

        for tree in next_layer_trees:
            # For "and" operation, all the next layer trees must be satisfied
            if not check_if_prereqs_satisfied(prereq_tree=tree, completed_module_codes=completed_module_codes):
                return False
        
        return True

    if operation == "or":
        # Get list of trees in the layer below
        next_layer_trees = prereq_tree[operation]

        for tree in next_layer_trees:
            # For "or" operation, at least one of the next layer trees must be satisfied
            if check_if_prereqs_satisfied(prereq_tree=tree, completed_module_codes=completed_module_codes):
                return True
        
        return False

    # Operation is "nOf" - at least n (minimum number of requirements to be fulfilled)
    # Get n and list of trees in the layer below
    min_num_requirements, next_layer_trees = prereq_tree[operation]

    num_requirements_fulfilled = 0

    for tree in next_layer_trees:
        # For "nOf" operation, at least n of the next layer trees must be satisfied
        if check_if_prereqs_satisfied(prereq_tree=tree, completed_module_codes=completed_module_codes):
            num_requirements_fulfilled += 1

            if num_requirements_fulfilled == min_num_requirements:
                return True
    
    return False


def convert_plan_to_frozenset_format(plan: dict[str, dict[int, list[str]]]) -> tuple[frozenset[str]]:
    # Structure of frozenset format: Tuple of frozensets, one frozenset per term representing the set of module codes
    # taken that term. Frozensets are in chronological order of terms
    frozensets_of_module_codes = list()
    for acad_year, acad_year_plan in plan.items():
        for sem_num, module_codes in acad_year_plan.items():
            module_codes_for_term = frozenset(module_codes)
            frozensets_of_module_codes.append(module_codes_for_term)
    
    return tuple(frozensets_of_module_codes)


def check_module_selection_for_term(acad_year: str, selected_module_codes: list[str], selected_total_mcs: float, outstanding_mc_balance: float, sem_min_mcs: float, sem_max_mcs: float | None, credit_internships: set[str], current_plan: dict[str, dict[int, list[str]]] | None) -> dict[str, bool | str]:
    # Returns a dictionary with keys "type" and "message"
    # "type" will be the type of message to be displayed by Streamlit (success / warning / error)
    result = dict()

    # Check if a credit-bearing internship is being taken
    is_taking_cred_internship = False
    for selected_module_code in selected_module_codes:
        if selected_module_code in credit_internships:
            is_taking_cred_internship = True

    # Check if minimum MC requirement is met. Underloading is only allowed if:
    # - The user, with this selection, meets the graduation requirements, or
    # - The user is taking a credit-bearing internship for the term
    if selected_total_mcs < sem_min_mcs and selected_total_mcs < outstanding_mc_balance and not is_taking_cred_internship:
        result["type"] = "error"
        result["message"] = f"You have not met the minimum requirement of {sem_min_mcs} MCs."
        return result
    
    # Check if maximum MC requirement is met (ie. for first semester)
    if sem_max_mcs is not None and selected_total_mcs > sem_max_mcs:
        result["type"] = "error"
        result["message"] = f"You have exceeded the limit of {sem_max_mcs} MCs."
        return result

    # Get the module codes that have already been taken
    completed_module_codes = get_completed_module_codes_from_plan(current_plan=current_plan)
    
    # Check if prerequisites have already been taken
    # Loop through each module chosen
    module_codes_with_failed_prereqs = list()
    for selected_module_code in selected_module_codes:
        # Get prerequisite tree
        selected_module_prereq_tree = get_prereq_tree(module_code=selected_module_code, acad_year=acad_year)

        # Check if prerequisites have been met, for this module
        if not check_if_prereqs_satisfied(prereq_tree=selected_module_prereq_tree, completed_module_codes=completed_module_codes):
            # Update list of modules whose prerequisites have not been met
            module_codes_with_failed_prereqs.append(selected_module_code)

    if module_codes_with_failed_prereqs:
        # There are some modules whose prerequisites may not have been taken
        # We can only give a warning and not an error, because checking for prerequisites using trees alone
        # would cause users to incorrectly fail the requirements for some modules

        # Eg. DSA1101 prerequisites: (O Level A Math) OR (MA1301) OR (MA1301FC) OR (MA1301X)
        # The tree only shows (MA1301) OR (MA1301FC) OR (MA1301X), omitting non-modular requirements
        # A student that has not taken these modules can still take DSA1101 if he / she has taken A Math,
        # but he / she will still fail the tree requirements. But it would be unfair to flag an error here

        result["type"] = "warning"
        result["message"] = f"You may not have satisfied the prerequisites for the following courses: {', '.join(module_codes_with_failed_prereqs)}. Please verify before proceeding."
        return result
    
    # Selection is valid
    result["type"] = "success"
    result["message"] = "Course selection satisfies the requirements!"
    
    return result


def insert_valid_plan_into_db(conn: st.connections.SQLConnection, username: str, plan: dict[str, dict[int, list[str]]]) -> None:
    # Loop through each AY to get set of new enrollments in the form (acad_year, sem_num, module_code)
    new_enrollments = set()
    for acad_year, acad_year_plan in plan.items():
        # Loop through each semester in the AY
        for sem_num, module_codes in acad_year_plan.items():
            # Update list of new enrollments
            for module_code in module_codes:
                new_enrollments.add((acad_year, sem_num, module_code))
    
    # Get dictionary that maps semester names to semester numbers
    sem_names_to_nums = get_semester_name_to_num_mapping(conn=conn)
    
    # Query existing enrollments
    # List of lists in the form (acad_year, sem_name, module_code, module_title, rating)
    existing_enrollments_rows_queried = conn.query(
        GET_ENROLLMENTS_OF_USER_QUERY,
        params={
            "username": username
        },
        ttl=0
    ).values.tolist()
    
    with conn.session as s:
        # Loop through each existing enrollment
        for acad_year, sem_name, module_code, module_title, rating in existing_enrollments_rows_queried:
            # Get existing enrollment
            sem_num = sem_names_to_nums[sem_name]
            existing_enrollment = (acad_year, sem_num, module_code)

            # Check if existing enrollment is also part of the user's new course plan
            if existing_enrollment not in new_enrollments:
                # Existing enrollment not in new plan - to be deleted
                s.execute(
                    text(DELETE_USER_ENROLLMENT_STATEMENT),
                    params={
                        "username": username,
                        "module_code": module_code,
                        "acad_year": acad_year,
                        "sem_num": sem_num 
                    }
                )

        # Loop through each new enrollment
        for acad_year, sem_num, module_code in new_enrollments:
            s.execute(
                text(INSERT_NEW_ENROLLMENT_STATEMENT),
                params={
                    "username": username,
                    "module_code": module_code,
                    "acad_year": acad_year,
                    "sem_num": sem_num
                }
            )

        s.commit()