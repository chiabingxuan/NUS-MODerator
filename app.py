from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()

# Add and run navigation sidebar
pages = [
    st.Page(os.path.join("pages", "home.py"), title="Home"),
    st.Page(os.path.join("pages", "ama.py"), title="AMA"),
    st.Page(os.path.join("pages", "about.py"), title="About"),
]
page_nav = st.navigation(pages)
page_nav.run()