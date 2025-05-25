from moderator.config import ACAD_YEAR
from moderator.utils.user import Admin
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


def display_update_db_panel(conn: st.connections.SQLConnection, admin: Admin) -> None:
    # Display buttons to update data
    with st.container(border=True):
        st.markdown("#### Update Data")

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
                    admin.update_db(conn=conn, acad_year=ACAD_YEAR)

                else:
                    # Update Pinecone vector store
                    admin.update_vector_store(conn=conn, acad_year=ACAD_YEAR)
            
            st.success("Update completed! Please refresh the page.")
            st.session_state["content_to_update"] = None


def display_admin_panel(conn: st.connections.SQLConnection, admin: Admin) -> None:
    with st.form("admin_panel"):
        st.markdown("#### Grant Admin Rights")
        st.markdown("Select the username to give admin rights to:")

        # Input target username
        username_to_give_admin = st.text_input("Username")
        if st.form_submit_button("Submit"):
            if not username_to_give_admin:
                st.error("Please ensure that the username field is filled up.")
            
            # Try to grant admin rights, and check whether or not it is successful
            elif admin.make_user_admin(conn=conn, username=username_to_give_admin):
                # Action is successful
                st.success("Admin rights have been granted!")
            
            else:
                # Action is not successful - username does not exist in database
                st.error("The username does not exist.")


# Retrieve connection from session state
conn = st.session_state["conn"]

# Retrieve user from session state
user = st.session_state["user"]

# Initialise variable to keep track of to nature of the update requested, if any
if "content_to_update" not in st.session_state:
    st.session_state["content_to_update"] = None

# Display header
st.header("Admin")

# Display panel to update databases (ie. for the new AY)
display_update_db_panel(conn=conn, admin=user)

# Display panel to manage admins
display_admin_panel(conn=conn, admin=user)