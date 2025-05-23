import streamlit as st


def display_personal_particulars() -> None:
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


def display_user_enrollments() -> None:
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
        for acad_year, acad_year_tab in zip(ays_in_enrollments, course_records_tabs):
            with acad_year_tab:
                is_first_sem_of_ay = True

                # Loop through each term in the AY, considering the list of modules taken
                for sem_name, sem_courses in user_enrollments[acad_year].items():
                    # Add divider to split the selection fields
                    if not is_first_sem_of_ay:
                        st.divider()

                    st.markdown(f"**<u>{sem_name}</u>**", unsafe_allow_html=True)

                    # Display courses taken in this term
                    for module_name in sem_courses:
                        st.markdown(module_name)
                    
                    is_first_sem_of_ay = False


# Display header and introduction
st.header("Your Profile")

# Display user information
display_personal_particulars()

# Display the modules that the user has taken
display_user_enrollments()
