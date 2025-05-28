from moderator.bus_services.fetch_timings import fetch_timings_from_api
import hashlib
import os
import requests
import streamlit as st
from sqlalchemy import text

# Set LangSmith credentials
# os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]
# os.environ["LANGCHAIN_TRACING_V2"] = st.secrets["LANGCHAIN_TRACING_V2"]
# os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN_ENDPOINT"]
# os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]


if __name__ == "__main__":
    fetch_timings_from_api(bus_stop_code="UHALL")

