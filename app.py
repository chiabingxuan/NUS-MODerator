# Keep this here to avoid SQLite error on Streamlit Community Cloud
# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Import other libraries
import os
import streamlit as st

# Add and run navigation sidebar
pages = [
    st.Page(os.path.join("templates", "home.py"), title="Home"),
    st.Page(os.path.join("templates", "ama.py"), title="AMA"),
    st.Page(os.path.join("templates", "about.py"), title="About"),
]
page_nav = st.navigation(pages)
page_nav.run()