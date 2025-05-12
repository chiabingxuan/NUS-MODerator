from moderator.sql.modules import GET_SPECIFIC_TERM_MODULES_QUERY, GET_MODULE_INFO_QUERY
from moderator.sql.semesters import GET_SEMESTERS_QUERY
import numpy as np
import streamlit as st


def get_semester_info(conn: st.connections.SQLConnection) -> list[list[int | str | np.float64]]:
    # Get list of lists in the form (sem_num, sem_name, min_mcs)
    sem_info = conn.query(GET_SEMESTERS_QUERY, ttl=3600).values.tolist()

    return sem_info


def get_completed_module_codes_from_plan(current_plan: dict[str, dict[int, list[str]]]) -> set[str]:
    completed_module_codes = set()

    for acad_year, acad_year_plan in current_plan.items():
        for sem_num, module_codes in acad_year_plan.items():
            # We have already ensured that there will never be repeated module codes across the terms
            # This is because user will only choose among modules that they have not taken yet
            completed_module_codes = completed_module_codes.union(set(module_codes))

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

    # Get set of module codes completed already
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


def check_module_selection_for_term(selected_module_codes: list[str], selected_total_mcs: float, sem_min_mcs: float, current_plan: dict[str, dict[int, list[str]]] | None) -> dict[str, bool | str]:
    # Returns a dictionary with keys "is_valid" and (possibly) "message"
    # If selection is valid, "message" will not exist - otherwise, "message" will be a string corresponding to the error message
    result = dict()

    # Check if plan is already invalid from previous terms
    if current_plan is None:
        result["is_valid"] = False
        result["message"] = f"Module selections for previous terms are already invalid. Please review."
        return result

    # Check if minimum MC requirement is met
    if selected_total_mcs < sem_min_mcs:
        result["is_valid"] = False
        result["message"] = f"Minimum requirement of {sem_min_mcs} MCs is not met."
        return result
    
    # Get the module codes that have already been taken
    completed_module_codes = get_completed_module_codes_from_plan(current_plan=current_plan)
    
    # Check if prerequisites have already been taken
    # TODO: Add this
    
    result["is_valid"] = True
    
    return result
