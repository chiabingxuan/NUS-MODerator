from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()

# Add and run navigation sidebar
pages = [
    st.Page(os.path.join("templates", "home.py"), title="Home"),
    st.Page(os.path.join("templates", "ama.py"), title="AMA"),
    st.Page(os.path.join("templates", "about.py"), title="About"),
]
page_nav = st.navigation(pages)
page_nav.run()