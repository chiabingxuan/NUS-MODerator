from moderator.sql.enrollments import GET_ENROLLMENTS_OF_USER_QUERY
from moderator.sql.semesters import GET_SEMESTERS_QUERY
import numpy as np
import streamlit as st


def get_semester_info(conn: st.connections.SQLConnection) -> list[list[int | str | np.float64]]:
    # Get list of lists in the form (sem_num, sem_name, min_mcs)
    sem_info = conn.query(GET_SEMESTERS_QUERY, ttl=3600).values.tolist()

    return sem_info


def get_semester_name_to_num_mapping(conn: st.connections.SQLConnection) -> dict[str, int]:
    # Get info for semesters
    # List of lists in the form (sem_num, sem_name, min_mcs)
    semester_info_rows_queried = get_semester_info(conn=conn)

    # Get mapping of semester names to semester numbers
    sem_names_to_nums = dict()
    for sem_num, sem_name, _ in semester_info_rows_queried:
        sem_names_to_nums[sem_name] = sem_num
    
    return sem_names_to_nums


def format_user_enrollments_from_db(user_enrollments: list[str]) -> dict[str, dict[str, list[dict[str, str | int]]]]:
    # Format: Keys are AYs. Values are themselves dictionaries, with keys = semester name and 
    # values = list of modules taken for that semester
    # Each module is a dictionary consisting of module name and user rating
    # If user has not declared any enrollments, empty dictionary will be returned
    
    formatted_user_enrollments = dict()
    for acad_year, sem_name, module_code, module_title, rating in user_enrollments:
        if acad_year not in formatted_user_enrollments:
            formatted_user_enrollments[acad_year] = dict()
        
        if sem_name not in formatted_user_enrollments[acad_year]:
            formatted_user_enrollments[acad_year][sem_name] = list()
        
        module_name = f"{module_code} {module_title}"
        module_info = {
            "name": module_name,
            "rating": rating
        }
        formatted_user_enrollments[acad_year][sem_name].append(module_info)
    
    return formatted_user_enrollments


def get_formatted_user_enrollments_from_db(conn: st.connections.SQLConnection, username: str) -> dict[str, dict[str, list[dict[str, str | int]]]]:
    # Get courses that user is enrolled in, if any
    # List of lists in the form (acad_year, sem_name, module_code, module_title)
    user_enrollments = conn.query(GET_ENROLLMENTS_OF_USER_QUERY, params={"username": username}, ttl=0).values.tolist()

    # Format the user's courses
    formatted_user_enrollments = format_user_enrollments_from_db(user_enrollments=user_enrollments)

    return formatted_user_enrollments