from moderator.config import ACAD_YEAR
from moderator.sql.departments import COUNT_SPECIFIC_AY_DEPARTMENTS_QUERY
from moderator.sql.modules import COUNT_SPECIFIC_AY_MODULES_QUERY
from moderator.sql.reviews import COUNT_SPECIFIC_AY_REVIEWS_QUERY
from moderator.sql.users import COUNT_CURRENT_USERS_QUERY
import streamlit as st


def display_stats(conn: st.connections.SQLConnection, acad_year: str):
    # Query the relevant statistics from database
    num_depts = conn.query(COUNT_SPECIFIC_AY_DEPARTMENTS_QUERY, params={"acad_year": acad_year}, ttl=3600).iloc[0]["num_depts"]
    num_modules = conn.query(COUNT_SPECIFIC_AY_MODULES_QUERY, params={"acad_year": acad_year}, ttl=3600).iloc[0]["num_modules"]
    num_reviews = conn.query(COUNT_SPECIFIC_AY_REVIEWS_QUERY, params={"acad_year": acad_year}, ttl=3600).iloc[0]["num_reviews"]
    num_users = conn.query(COUNT_CURRENT_USERS_QUERY, params={"acad_year": acad_year}, ttl=0).iloc[0]["num_users"]

    # Display statistics
    with st.container(border=True):
        st.markdown(f"#### <u>AY{acad_year}</u>", unsafe_allow_html=True)
        st.markdown(f"##### :red[{num_users}] registered users")
        st.markdown(f"##### :red[{num_modules}] modules offered")
        st.markdown(f"##### :red[{num_depts}] departments in NUS")
        st.markdown(f"##### :red[{num_reviews}] reviews posted on NUSMods")


# Initialise connection
conn = st.connection("nus_moderator", type="sql")

# Get name to be displayed in welcome message
username = st.session_state["user_details"]["username"]
display_name = st.session_state["user_details"]["first_name"]

# Display header
st.header(f"Welcome, {display_name}!")

# Display statistics
display_stats(conn=conn, acad_year=ACAD_YEAR)