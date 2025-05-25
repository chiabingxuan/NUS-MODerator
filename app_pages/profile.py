from moderator.profile.ratings import update_ratings
from moderator.utils.helpers import get_semester_name_to_num_mapping, get_formatted_user_enrollments_from_db
from moderator.utils.user import User
import numpy as np
import pandas as pd
import streamlit as st
import time


def display_personal_particulars(user: User):
    with st.container(border=True):
        st.markdown("#### Personal Particulars")

        # Display username
        st.markdown(f"**Username**: {user.username}")

        # Display name
        full_name = f"{user.first_name} {user.last_name}"
        st.markdown(f"**Name**: {full_name}")

        # Display major
        st.markdown(f"**Major**: {user.major}")

        # Display matriculation AY
        st.markdown(f"**Matriculation AY**: {user.matriculation_ay}")


@st.dialog("This will overwrite your previous ratings for these courses (if any). Are you sure you want to proceed?")
def confirm_saving_of_ratings(conn: st.connections.SQLConnection, user: User, ratings_list: list[str | int]) -> None:
    # Add button to confirm saving of plan
    confirm_button = st.button("Yes")
    
    # Add button to cancel saving of plan
    cancel_button = st.button("No")

    if confirm_button:
        # Get dictionary to map names of semesters to their corresponding numbers
        sem_names_to_nums = get_semester_name_to_num_mapping(conn=conn)

        # Save ratings to database
        update_ratings(conn=conn, username=user.username, ratings_list=ratings_list, sem_names_to_nums=sem_names_to_nums)
        
        # Get formatted plan from database (with updated ratings)
        formatted_plan = get_formatted_user_enrollments_from_db(conn=conn, username=user.username)

        # Update user with this updated and formatted plan
        user.user_enrollments = formatted_plan

        st.success("Ratings have been saved!")
        time.sleep(1)
        st.rerun()

    if cancel_button:
        # If cancellation is triggered, use a rerun to close the dialog
        st.rerun()
            

def display_user_enrollments(conn: st.connections.SQLConnection, user: User) -> None:
    with st.container(border=True):
        st.markdown("#### Your Courses")

        # Get the valid and formatted course plan of user
        user_enrollments = user.user_enrollments

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
                # Loop through each term in the AY, considering the list of modules taken
                for sem_name, sem_courses in user_enrollments[acad_year].items():
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
                        
                    st.divider()

        # Concatenate all the rating dataframes
        combined_ratings_df = pd.concat(ratings_dfs, ignore_index=True, axis=0)

        # In concatenated dataframe, replace NaN with None, and convert to list of lists
        combined_ratings_df = combined_ratings_df.replace({np.nan: None})
        ratings_list = combined_ratings_df.values.tolist()

        # Add button for user to submit ratings
        if st.button("Submit All Ratings"):
            confirm_saving_of_ratings(conn=conn, user=user, ratings_list=ratings_list)


# Retrieve connection from session state
conn = st.session_state["conn"]

# Display header and introduction
st.header("Your Profile")

# Get user from session state
user = st.session_state["user"]

# Display user information
display_personal_particulars(user=user)

# Display the modules that the user has taken
display_user_enrollments(conn=conn, user=user)
