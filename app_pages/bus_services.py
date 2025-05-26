import streamlit as st



# Retrieve connection from session state
conn = st.session_state["conn"]

# Display header and introduction
st.header("NUS Bus Services")

# Get user from session state
user = st.session_state["user"]