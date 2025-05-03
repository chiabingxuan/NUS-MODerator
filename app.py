from dotenv import load_dotenv
import json
from moderator.chatbot.chatbot_setup import setup_chatbot
from moderator.config import MAX_DAYS_UNTIL_NEW_CHATBOT_SETUP, DATA_FOLDER_PATH, DETAILS_FILENAME
import os
import streamlit as st
import time

load_dotenv()

def check_if_have_chatbot_setup(data_folder_path: str) -> bool:
    # If data folder exists, then we have ingested the data for the chatbot
    return os.path.isdir(data_folder_path)


def check_if_chatbot_setup_is_updated(data_folder_path: str, details_filename: str, max_days_until_update_needed: int) -> bool:
    # Use previous setup details to find the time of the last setup
    details_path = os.path.join(data_folder_path, details_filename)
    with open(details_path, "r") as file:
        details = json.load(file)
    last_setup_time = details["epoch"]

    # Check whether the last setup is still up to date or not
    current_time = int(time.time())
    days_since_last_setup = (current_time - last_setup_time) // (60 * 60 * 24)

    return days_since_last_setup <= max_days_until_update_needed


def handle_setup_button_clicked():
    # Update session state once setup button has been clicked
    st.session_state["setup_button_clicked"] = True


if "setup_button_clicked" not in st.session_state:
    st.session_state["setup_button_clicked"] = False

# Check if chatbot setup does not exist / is outdated. Either way, need to setup again
if not check_if_have_chatbot_setup(data_folder_path=DATA_FOLDER_PATH) or not check_if_chatbot_setup_is_updated(data_folder_path=DATA_FOLDER_PATH, details_filename=DETAILS_FILENAME, max_days_until_update_needed=MAX_DAYS_UNTIL_NEW_CHATBOT_SETUP): 
    # Handle the case of missing / outdated setup
    with st.container(border=True):
        st.markdown("### Welcome to NUS-MODerator!")
        st.markdown(
            """
            We detected that your system does not have the latest setup required for the application. This could be because:
            - You are launching the application for the first time, or
            - Your existing setup is outdated                      
            """
        )
        st.markdown("Please click the button below to begin the setup.")

        if not st.session_state["setup_button_clicked"]:
            # Display setup button if it has not been clicked
            setup_button = st.button("Set Up", on_click=handle_setup_button_clicked)

        else:
            # Setup button has been clicked - proceed to set up
            with st.spinner("Setup in progress. This may take a while - please go and touch some grass first...", show_time=True):
                setup_chatbot()
            
            st.success("Setup completed! Please refresh the page.")
            st.session_state["setup_button_clicked"] = False

else:
    # Add and run navigation sidebar
    pages = [
        st.Page(os.path.join("templates", "home.py"), title="Home"),
        st.Page(os.path.join("templates", "ama.py"), title="AMA"),
        st.Page(os.path.join("templates", "about.py"), title="About"),
    ]
    page_nav = st.navigation(pages)
    page_nav.run()