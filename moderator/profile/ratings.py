from moderator.sql.enrollments import UPDATE_ENROLLMENT_RATING_STATEMENT
import streamlit as st
from sqlalchemy import text

def update_ratings(conn: st.connections.SQLConnection, username: str, ratings_list: list[str | int], sem_names_to_nums: dict[str, int]) -> None:
    with conn.session as s:
        # Loop through each rating to be updated
        for module_name, rating, acad_year, sem_name in ratings_list:
            # Get module code
            module_code = module_name.split()[0]

            # Get semester number
            sem_num = sem_names_to_nums[sem_name]

            # Update rating in database
            s.execute(
                text(UPDATE_ENROLLMENT_RATING_STATEMENT),
                params={
                    "rating": rating,
                    "username": username,
                    "module_code": module_code,
                    "acad_year": acad_year,
                    "sem_num": sem_num
                }
            )

        s.commit()