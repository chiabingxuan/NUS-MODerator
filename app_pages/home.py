from moderator.config import ACAD_YEAR
from moderator.sql.departments import COUNT_CURRENT_DEPARTMENTS_QUERY
from moderator.sql.modules import COUNT_CURRENT_MODULES_QUERY
from moderator.sql.reviews import COUNT_CURRENT_REVIEWS_QUERY
from moderator.sql.users import COUNT_CURRENT_USERS_QUERY
import streamlit as st


def display_stats():
    # Initialise connection
    conn = st.connection("nus_moderator", type="sql")

    # Query the relevant statistics from database
    num_depts = conn.query(COUNT_CURRENT_DEPARTMENTS_QUERY, params={"acad_year": ACAD_YEAR}, ttl=0).iloc[0]["num_depts"]
    num_modules = conn.query(COUNT_CURRENT_MODULES_QUERY, params={"acad_year": ACAD_YEAR}, ttl=0).iloc[0]["num_modules"]
    num_reviews = conn.query(COUNT_CURRENT_REVIEWS_QUERY, params={"acad_year": ACAD_YEAR}, ttl=0).iloc[0]["num_reviews"]
    num_users = conn.query(COUNT_CURRENT_USERS_QUERY, params={"acad_year": ACAD_YEAR}, ttl=0).iloc[0]["num_users"]

    # Display statistics
    with st.container(border=True):
        st.markdown("### <u>Current Statistics</u>", unsafe_allow_html=True)
        st.markdown(f"##### :red[{num_users}] registered user(s)")
        st.markdown(f"##### :red[{num_modules}] module(s) offered")
        st.markdown(f"##### :red[{num_depts}] department(s) in NUS")
        st.markdown(f"##### :red[{num_reviews}] review(s) posted on NUSMods")


# Get name to be displayed in welcome message
username = st.session_state["user_details"]["username"]
if username is None:
    # User is anonymous guest
    display_name = "Guest"

else:
    display_name = st.session_state["user_details"]["first_name"]

# Display header
st.header(f"Welcome, {display_name}!")

# Display statistics
display_stats()