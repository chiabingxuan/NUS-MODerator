from moderator.sql.enrollments import GET_ENROLLMENTS_OF_USER_QUERY
import streamlit as st


def format_user_enrollments_from_db(user_enrollments: list[str]) -> dict[str, dict[str, list[str]]]:
    # Format: Keys are AYs. Values are themselves dictionaries, with keys = semester name and 
    # values = list of module names (code + title) taken for that semester
    # If user has not declared any enrollments, empty dictionary will be returned
    
    formatted_user_enrollments = dict()
    for acad_year, sem_name, module_code, module_title in user_enrollments:
        if acad_year not in formatted_user_enrollments:
            formatted_user_enrollments[acad_year] = dict()
        
        if sem_name not in formatted_user_enrollments[acad_year]:
            formatted_user_enrollments[acad_year][sem_name] = list()
        
        module_name = f"{module_code} {module_title}"
        formatted_user_enrollments[acad_year][sem_name].append(module_name)
    
    return formatted_user_enrollments


def get_formatted_user_enrollments_from_db(conn: st.connections.SQLConnection, username: str) -> dict[str, dict[str, list[str]]]:
    # Get courses that user is enrolled in, if any
    # List of lists in the form (acad_year, sem_name, module_code, module_title)
    user_enrollments = conn.query(GET_ENROLLMENTS_OF_USER_QUERY, params={"username": username}, ttl=0).values.tolist()

    # Format the user's courses
    formatted_user_enrollments = format_user_enrollments_from_db(user_enrollments=user_enrollments)

    return formatted_user_enrollments