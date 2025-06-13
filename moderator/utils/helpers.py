import datetime
from moderator.config import HOURS_WRT_UTC, ANNOUNCEMENT_LIMIT
from moderator.sql.announcements import GET_LATEST_ANNOUNCEMENTS_QUERY
from moderator.sql.departments import GET_SPECIFIC_AY_DEPARTMENTS_QUERY
from moderator.sql.enrollments import GET_ENROLLMENTS_OF_USER_QUERY
from moderator.sql.majors import GET_MAJORS_QUERY
from moderator.sql.modules import COUNT_SPECIFIC_AY_MODULES_QUERY
from moderator.sql.reviews import COUNT_SPECIFIC_AY_REVIEWS_QUERY
from moderator.sql.semesters import GET_SEMESTERS_QUERY
from moderator.sql.users import COUNT_CURRENT_USERS_QUERY, COUNT_CURRENT_USERS_BY_DATE_QUERY
import numpy as np
import pandas as pd
import streamlit as st


### GETTING STATISTICS ###
def get_general_statistics(conn: st.connections.SQLConnection, acad_year: str) -> tuple[int, int, int, int]:
    # Get general statistics to display in home page
    num_depts = len(conn.query(GET_SPECIFIC_AY_DEPARTMENTS_QUERY, params={"acad_year": acad_year}, ttl=3600)["department"])
    num_modules = conn.query(COUNT_SPECIFIC_AY_MODULES_QUERY, params={"acad_year": acad_year}, ttl=3600).iloc[0]["num_modules"]
    num_reviews = conn.query(COUNT_SPECIFIC_AY_REVIEWS_QUERY, params={"acad_year": acad_year}, ttl=3600).iloc[0]["num_reviews"]
    num_users = conn.query(COUNT_CURRENT_USERS_QUERY, params={"acad_year": acad_year}, ttl=0).iloc[0]["num_users"]

    return num_depts, num_modules, num_reviews, num_users


def get_user_growth_statistics(conn: st.connections.SQLConnection) -> pd.DataFrame:
    # Query the number of new registered users per date, in a dataframe
    new_users_by_date_df = conn.query(COUNT_CURRENT_USERS_BY_DATE_QUERY, ttl=0)

    # Add a column that corresponds to the running total number of registered users over time
    new_users_by_date_df["cumulative_num_registered"] = new_users_by_date_df["num_users_registered"].cumsum()

    return new_users_by_date_df


### GET ANNOUNCEMENTS ###
def get_latest_announcements(conn: st.connections.SQLConnection) -> tuple[str, str, datetime.datetime]:
    # Query the latest announcements, in descending order of recency, in the form (username, message, publish_date)
    latest_announcements_rows_queried = conn.query(
        GET_LATEST_ANNOUNCEMENTS_QUERY,
        params={
            "announcement_limit": ANNOUNCEMENT_LIMIT
        },
        ttl=3600
    ).values.tolist()

    return latest_announcements_rows_queried


### HANDLING SEMESTER DATA ###
def get_semester_info(conn: st.connections.SQLConnection) -> list[list[int | str | np.float64]]:
    # Get list of lists in the form (sem_num, sem_name, min_mcs)
    sem_info = conn.query(GET_SEMESTERS_QUERY, ttl=0).values.tolist()

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


### FORMATTING ENROLLMENTS ###
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


### GET LISTS FROM DATABASE ###
def get_major_list(conn: st.connections.SQLConnection) -> list[str]:
    # Get ordered list of existing majors
    return list(conn.query(GET_MAJORS_QUERY, ttl=0)["major"])


def get_departments_list(conn: st.connections.SQLConnection, acad_year: str) -> list[str]:
    # Get ordered list of departments available, for the specified AY
    return list(
        conn.query(
            GET_SPECIFIC_AY_DEPARTMENTS_QUERY,
            params={
                "acad_year": acad_year
            },
            ttl=3600
        )["department"]
    )


### HANDLE TIMEZONES ###
def adjust_to_timezone(time: datetime.datetime, hours_shift: int = HOURS_WRT_UTC) -> datetime.datetime:
    # Offset to the timezone required
    return time + datetime.timedelta(hours=hours_shift)
