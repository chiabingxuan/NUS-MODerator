import altair as alt
from moderator.config import ACAD_YEAR
from moderator.utils.helpers import get_general_statistics, get_user_growth_statistics, get_latest_announcements
import streamlit as st


def display_stats(conn: st.connections.SQLConnection, acad_year: str):
    # Query the relevant statistics from database
    num_depts, num_modules, num_reviews, num_users = get_general_statistics(conn=conn, acad_year=acad_year)
    new_users_by_date_df = get_user_growth_statistics(conn=conn)

    # Display statistics
    with st.container(border=True):
        display_stats_tab, user_growth_tab = st.tabs(["Current Statistics", "User Growth"])

        # Display general statistics
        with display_stats_tab:
            st.markdown(f"##### :red[{num_users}] registered users")
            st.markdown(f"##### :red[{num_modules}] modules offered")
            st.markdown(f"##### :red[{num_depts}] departments in NUS")
            st.markdown(f"##### :red[{num_reviews}] reviews posted on NUSMods")

        # Display user growth
        with user_growth_tab:
            # Make line graph of total number of registered users against time
            chart = alt.Chart(new_users_by_date_df).mark_line().encode(
                x=alt.X("date", axis=alt.Axis(format="%d/%m/%y", labelAlign="center")).title("Date"),
                y=alt.Y("cumulative_num_registered").title("Number of users")
            )

            # Display line graph
            st.altair_chart(chart)


def display_announcements(conn: st.connections.SQLConnection):
    # Query the latest announcements, in the form (username, message, publish_date)
    latest_announcements_rows_queried = get_latest_announcements(conn=conn)
    
    # Display announcements in descending order of recency
    with st.container(border=True):
        st.markdown("#### Announcements")
        for username, message, publish_date in latest_announcements_rows_queried:
            st.markdown(f"**{username}** [{publish_date.strftime("%d/%m/%Y %I:%M:%S %p")}]: {message}")


# Retrieve connection from session state
conn = st.session_state["conn"]

# Get name to be displayed in welcome message
user = st.session_state["user"]
display_name = user.first_name

# Display header
st.header(f"Welcome, {display_name}!")

# Display statistics
display_stats(conn=conn, acad_year=ACAD_YEAR)

# Display latest announcements
display_announcements(conn=conn)