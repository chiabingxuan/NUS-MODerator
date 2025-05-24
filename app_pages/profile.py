from moderator.helpers.utils import get_semester_name_to_num_mapping, get_formatted_user_enrollments_from_db
from moderator.profile.ratings import update_ratings
import numpy as np
import pandas as pd
import streamlit as st
import time


def display_personal_particulars() -> str:
    with st.container(border=True):
        st.markdown("#### Personal Particulars")

        # Display username
        username = st.session_state["user_details"]["username"]
        st.markdown(f"**Username**: {username}")

        # Display name
        full_name = f"{st.session_state["user_details"]["first_name"]} {st.session_state["user_details"]["last_name"]}"
        st.markdown(f"**Name**: {full_name}")

        # Display major
        major = st.session_state["user_details"]["major"]
        st.markdown(f"**Major**: {major}")

        # Display matriculation AY
        matriculation_ay = st.session_state["user_details"]["matriculation_ay"]
        st.markdown(f"**Matriculation AY**: {matriculation_ay}")
    
    return username


@st.dialog("This will overwrite your previous ratings for these courses (if any). Are you sure you want to proceed?")
def confirm_saving_of_ratings(conn: st.connections.SQLConnection, username: str, ratings_list: list[str | int]) -> None:
    # Add button to confirm saving of plan
    confirm_button = st.button("Yes")
    
    # Add button to cancel saving of plan
    cancel_button = st.button("No")

    if confirm_button:
        # Get dictionary to map names of semesters to their corresponding numbers
        sem_names_to_nums = get_semester_name_to_num_mapping(conn=conn)

        # Save ratings to database
        update_ratings(conn=conn, username=username, ratings_list=ratings_list, sem_names_to_nums=sem_names_to_nums)
        
        # Get formatted plan from database (with updated ratings)
        formatted_plan = get_formatted_user_enrollments_from_db(conn=conn, username=username)

        # Update session state with this updated and formatted plan
        st.session_state["user_details"]["user_enrollments"] = formatted_plan

        st.success("Ratings have been saved!")
        time.sleep(1)
        st.rerun()

    if cancel_button:
        # If cancellation is triggered, use a rerun to close the dialog
        st.rerun()
            

def display_user_enrollments(conn: st.connections.SQLConnection, username: str) -> None:
    with st.container(border=True):
        st.markdown("#### Your Courses")

        # Get the valid and formatted course plan of user
        user_enrollments = st.session_state["user_details"]["user_enrollments"]

        # If user has not saved any courses, inform him / her about it
        if not user_enrollments:
            st.markdown("You have not enrolled for any courses. Use the Course Planner to save courses to your profile!")
            return

        # Get the list of AYs involved in the plan and create one tab for each
        ays_in_enrollments = list(user_enrollments.keys())
        course_records_tabs = st.tabs(ays_in_enrollments)

        # Fill up the tabs for each AY
        ratings_dfs = list()     # To store ratings in the form (acad_year, sem_name, sem_num, module_code, rating)
        for acad_year, acad_year_tab in zip(ays_in_enrollments, course_records_tabs):
            with acad_year_tab:
                is_first_sem_of_ay = True

                # Loop through each term in the AY, considering the list of modules taken
                for sem_name, sem_courses in user_enrollments[acad_year].items():
                    # Add divider to split the selection fields
                    if not is_first_sem_of_ay:
                        st.divider()

                    st.markdown(f"**<u>{sem_name}</u>**", unsafe_allow_html=True)

                    # Get list of module names and list of module ratings for this term
                    sem_courses_names, sem_courses_ratings = list(), list()
                    for sem_course in sem_courses:
                        sem_courses_names.append(sem_course["name"])
                        sem_courses_ratings.append(sem_course["rating"])

                    # Display courses taken in this term, in dataframes
                    # Allow user to give course ratings
                    term_enrollments_df = pd.DataFrame({
                        "course_names": sem_courses_names,
                        "rating": sem_courses_ratings   # Use existing ratings, if any, as default value
                    })
                    term_enrollments_df = st.data_editor(
                        term_enrollments_df,
                        column_config={
                            # Module name column
                            "course_names": st.column_config.TextColumn(
                                label="Course Name",
                                disabled=True
                            ),
                            # Colour dropdown column
                            "rating": st.column_config.NumberColumn(
                                label="Rating",
                                help="Rate the course out of 10",
                                min_value=0,
                                max_value=10,
                                step=1
                            )
                        },
                        key=f"profile_courses_{acad_year}_{sem_name}",
                        hide_index=True
                    )

                    # Make ratings dataframe and add columns for AY and semester names to it
                    # Ratings dataframe has columns (module_name, rating, acad_year, sem_name)
                    ratings_df = term_enrollments_df.copy(deep=True)
                    ratings_df["acad_year"] = acad_year
                    ratings_df["sem_names"] = sem_name

                    # Add to list of rating dataframes
                    ratings_dfs.append(ratings_df)
                        
                    is_first_sem_of_ay = False

        st.divider()

        # Concatenate all the rating dataframes
        combined_ratings_df = pd.concat(ratings_dfs, ignore_index=True, axis=0)

        # In concatenated dataframe, replace NaN with None, and convert to list of lists
        combined_ratings_df = combined_ratings_df.replace({np.nan: None})
        ratings_list = combined_ratings_df.values.tolist()

        # Add button for user to submit ratings
        if st.button("Submit All Ratings"):
            confirm_saving_of_ratings(conn=conn, username=username, ratings_list=ratings_list)


# Initialise connection
conn = st.connection("nus_moderator", type="sql")

# Display header and introduction
st.header("Your Profile")

# Display user information
username = display_personal_particulars()

# Display the modules that the user has taken
display_user_enrollments(conn=conn, username=username)
