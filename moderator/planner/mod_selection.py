from moderator.sql.modules import GET_SPECIFIC_TERM_MODULES_QUERY, GET_MODULE_INFO_QUERY
from moderator.sql.semesters import GET_SEMESTERS_QUERY
import numpy as np
import re
import requests
import streamlit as st


def get_semester_info(conn: st.connections.SQLConnection) -> list[list[int | str | np.float64]]:
    # Get list of lists in the form (sem_num, sem_name, min_mcs)
    sem_info = conn.query(GET_SEMESTERS_QUERY, ttl=3600).values.tolist()

    return sem_info


def get_completed_module_codes_from_plan(current_plan: dict[str, dict[int, list[str]]]) -> list[str]:
    completed_module_codes = list()

    for acad_year, acad_year_plan in current_plan.items():
        for sem_num, module_codes in acad_year_plan.items():
            # We have already ensured that there will never be repeated module codes across the terms
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


def get_list_of_mod_choices_for_term(conn: st.connections.SQLConnection, acad_year: str, sem_num: int, current_plan: dict[str, dict[int, list[str]]] | None) -> list[str]:
    # If current plan is None (already invalid), there should be no selections given
    if current_plan is None:
        return list()
    
    # Get modules offered for this term in this AY - a list of lists in the form (module_code, module_title)
    available_modules = get_available_modules_for_term(conn=conn, acad_year=acad_year, sem_num=sem_num)

    # Get list of module codes completed already
    completed_module_codes = get_completed_module_codes_from_plan(current_plan=current_plan)

    # Get list of formatted names corresponding to all the remaining modules that have not been taken yet
    module_name_selections = [f"{module_code} {module_title}" for (module_code, module_title) in available_modules if module_code not in completed_module_codes]

    return module_name_selections


def get_total_mcs_for_term(conn: st.connections.SQLConnection, module_codes_for_term: list[str]) -> float:
    total_mcs = 0.0

    # Get number of MCs for each module chosen for the term
    for module_code in module_codes_for_term:
        module_mcs = float(
            conn.query(
                GET_MODULE_INFO_QUERY,
                params={
                    "code": module_code
                },
                ttl=3600
            ).iloc[0]["num_mcs"]
        )

        total_mcs += module_mcs

    return total_mcs


def get_prereq_tree(module_code: str, acad_year: str) -> dict | None:
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


def check_module_selection_for_term(acad_year: str, selected_module_codes: list[str], selected_total_mcs: float, sem_min_mcs: float, current_plan: dict[str, dict[int, list[str]]] | None) -> dict[str, bool | str]:
    # Returns a dictionary with keys "is_valid" and (possibly) "message"
    # If selection is valid, "message" will not exist - otherwise, "message" will be a string corresponding to the error message
    result = dict()

    # Check if plan is already invalid from previous terms
    if current_plan is None:
        result["is_valid"] = False
        result["message"] = "Module selections for previous terms are already invalid. Please review."
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
        # There are some modules whose prerequisites have not been taken
        result["is_valid"] = False
        result["message"] = f"You have not satisfied the prerequisties for the following modules: {', '.join(module_codes_with_failed_prereqs)}."
        return result

    # Check if minimum MC requirement is met
    if selected_total_mcs < sem_min_mcs:
        result["is_valid"] = False
        result["message"] = f"Minimum requirement of {sem_min_mcs} MCs is not met."
        return result
    
    # Selection is valid
    result["is_valid"] = True
    
    return result
