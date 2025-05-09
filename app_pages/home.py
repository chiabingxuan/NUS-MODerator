import streamlit as st
from moderator.admin.update_db import update_db

# Display header
st.header("NUS-MODerator")

if st.button("Test"):
    update_db()