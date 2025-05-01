from dotenv import load_dotenv
import json
from moderator.ingestion import ingest
from moderator.config import MAX_DAYS_UNTIL_UPDATE_NEEDED, DATA_FOLDER_PATH, RETRIEVAL_DETAILS_FILENAME
import os
import streamlit as st
import time

load_dotenv()

def check_if_have_ingested(data_folder_path: str) -> bool:
    # If data folder exists, then we have ingested the data
    return os.path.isdir(data_folder_path)


def check_if_data_is_updated(data_folder_path: str, retrieval_details_filename: str, max_days_until_update_needed: int) -> bool:
    # Use previous ingestion details to find the time of the last ingestion
    details_path = os.path.join(data_folder_path, retrieval_details_filename)
    with open(details_path, "r") as file:
        details = json.load(file)
    download_time = details["epoch"]

    # Check whether the last ingestion is still up to date or not
    current_time = int(time.time())
    days_since_last_download = (current_time - download_time) // (60 * 60 * 24)

    return days_since_last_download <= max_days_until_update_needed


def handle_ingest_button_clicked():
    # Update session state once download button has been clicked
    st.session_state["ingest_button_clicked"] = True


if "ingest_button_clicked" not in st.session_state:
    st.session_state["ingest_button_clicked"] = False

# Check if data does not exist / is outdated. Either way, need to ingest data again
if not check_if_have_ingested(data_folder_path=DATA_FOLDER_PATH) or not check_if_data_is_updated(data_folder_path=DATA_FOLDER_PATH, retrieval_details_filename=RETRIEVAL_DETAILS_FILENAME, max_days_until_update_needed=MAX_DAYS_UNTIL_UPDATE_NEEDED): 
    # Handle the case of missing / outdated data
    with st.container(border=True):
        st.markdown("### Welcome to NUS-MODerator!")
        st.markdown("We detected that your system does not have the latest NUSMods data required for the application. Please click the button below to begin the download.")
        
        if not st.session_state["ingest_button_clicked"]:
            # Display download button if it has not been clicked
            download_button = st.button("Download", on_click=handle_ingest_button_clicked)

        else:
            # Download button has been clicked - proceed to ingest
            with st.spinner("Download in progress. This may take a while - please go and touch some grass first..."):
                ingest()
            
            st.success("Download completed! Please refresh the page.")
            st.session_state["ingest_button_clicked"] = False

else:
    # Add and run navigation sidebar
    pages = [
        st.Page(os.path.join("templates", "home.py"), title="Home"),
        st.Page(os.path.join("templates", "ama.py"), title="AMA"),
        st.Page(os.path.join("templates", "about.py"), title="About"),
    ]
    page_nav = st.navigation(pages)
    page_nav.run()