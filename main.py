from moderator.chatbot.chatbot import run_chatbot
from moderator.chatbot.chatbot_setup import setup_chatbot
from moderator.admin.update_db import update_db
import os
import streamlit as st

# Set LangSmith credentials
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = st.secrets["LANGCHAIN_TRACING_V2"]
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN_ENDPOINT"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]


if __name__ == "__main__":
    setup_chatbot()