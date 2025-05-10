from moderator.admin.update_db import update_db
from moderator.chatbot.chatbot_setup import update_vector_store
import streamlit as st

@st.dialog("Are you sure you want to proceed?")
def confirm_update(content_to_update: str) -> None:
    # Add button to confirm update
    confirm_button = st.button("Yes")
    
    # Add button to cancel update
    cancel_button = st.button("No")

    if confirm_button:
        # In session state, specify what to update 
        st.session_state["content_to_update"] = content_to_update
        st.rerun()
    
    if cancel_button:
        # If cancellation is triggered, use a rerun to close the dialog
        st.rerun()

# Initialise variable to keep track of to nature of the update requested, if any
if "content_to_update" not in st.session_state:
    st.session_state["content_to_update"] = None

# Check user permission
if st.session_state["user_details"]["username"] is None or st.session_state["user_details"]["role"] != "admin":
    # User is either a guest or is not an admin - no permission to access this page
    with st.container(border=True):
        st.markdown("### Sorry, you are not the chosen one :(")
        st.markdown("You do not have permission to access this page. Please convince Bing Xuan to give you admin rights.")

else:
    # User is an admin
    # Display header
    st.header("Admin Workspace")

    # Display buttons to update data
    with st.container(border=True):
        st.markdown("### Update Data")
        left_col, middle_col, right_col = st.columns((1, 1, 1))

        # Display update buttons if they have not been clicked
        if st.session_state["content_to_update"] is None:
            if st.button("Update Database"):
                # Admin wants to update database - ask them to confirm their request
                confirm_update("database")
            
            if st.button("Update Vector Store"):
                # Admin wants to update vector store - ask them to confirm their request
                confirm_update("vector_store")

        else:
            # An update button has been clicked - proceed to update content requested
            with st.spinner("Update in progress. This will take a while - please go and touch some grass first...", show_time=True):
                if st.session_state["content_to_update"] == "database":
                    # Update the PostgreSQL database
                    update_db()

                else:
                    # Update Pinecone vector store
                    update_vector_store()
            
            st.success("Update completed! Please refresh the page.")
            st.session_state["content_to_update"] = None