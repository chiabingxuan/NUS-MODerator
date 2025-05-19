import hashlib
from moderator.admin.update_vector_store import update_vector_store
from moderator.admin.update_db import update_db
from moderator.chatbot.chatbot import run_chatbot
import os
import requests
import streamlit as st
from sqlalchemy import text

# Set LangSmith credentials
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = st.secrets["LANGCHAIN_TRACING_V2"]
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN_ENDPOINT"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]


if __name__ == "__main__":
    pass