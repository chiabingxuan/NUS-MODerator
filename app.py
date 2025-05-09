# Keep this here to avoid SQLite error on Streamlit Community Cloud
# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Import other libraries
import os
import streamlit as st
import torch

# Keep this here to avoid RuntimeError during launch
torch.classes.__path__ = []

# Set LangSmith credentials
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = st.secrets["LANGCHAIN_TRACING_V2"]
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN_ENDPOINT"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]

# Add and run navigation sidebar
pages = [
    st.Page(os.path.join("app_pages", "home.py"), title="Home"),
    st.Page(os.path.join("app_pages", "ama.py"), title="AMA"),
    st.Page(os.path.join("app_pages", "about.py"), title="About"),
]
page_nav = st.navigation(pages)
page_nav.run()