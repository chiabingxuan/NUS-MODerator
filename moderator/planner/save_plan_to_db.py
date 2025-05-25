from moderator.sql.enrollments import DELETE_USER_ENROLLMENT_STATEMENT, INSERT_NEW_ENROLLMENT_STATEMENT, GET_ENROLLMENTS_OF_USER_QUERY
from moderator.utils.helpers import get_semester_name_to_num_mapping
import streamlit as st
from sqlalchemy import text


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