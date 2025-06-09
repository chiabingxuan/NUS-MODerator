from moderator.config import ACAD_YEAR
from moderator.utils.helpers import get_departments_list
from moderator.utils.user import Admin
import streamlit as st
import streamlit.components.v1 as components
import time


def close_dialog():
    components.html(
        """\
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const modal = parent.document.querySelector('div[data-baseweb="modal"]');
            if (modal) {
                // Apply a fade-out transition
                modal.style.transition = 'opacity 0.5s ease';
                modal.style.opacity = '0';

                // Remove the modal after the fade-out effect finishes
                setTimeout(function() {
                    modal.remove();
                }, 500);  // Time corresponds to the transition duration (0.5s)
            }
        });
        </script>
        """,
        height=0,
        scrolling=False,
    )

    
@st.dialog("Are you sure you want to proceed?")
def confirm_update(content_to_update: str) -> None:
    # Add button to confirm update
    confirm_button = st.button("Yes")
    
    # Add button to cancel update
    cancel_button = st.button("No")

    if confirm_button:
        # In session state, specify what to update 
        st.session_state["content_to_update"] = content_to_update
        close_dialog()
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
            if st.button("Update Academic Database"):
                # Admin wants to update academic database - ask them to confirm their request
                confirm_update("acad_db")
            
            if st.button("Update Vector Store"):
                # Admin wants to update vector store - ask them to confirm their request
                confirm_update("vector_store")
            
            if st.button("Update Bus Database"):
                # Admin wants to update bus database - ask them to confirm their request
                confirm_update("bus_db")

        else:
            # An update button has been clicked - proceed to update content requested
            with st.spinner("Update in progress. This might take a while - please go and touch some grass first...", show_time=True):
                if st.session_state["content_to_update"] == "acad_db":
                    # Update the academic-related tables in the PostgreSQL database
                    admin.update_acad_db(conn=conn, acad_year=ACAD_YEAR)

                elif st.session_state["content_to_update"] == "vector_store":
                    # Update Pinecone vector store
                    admin.update_vector_store(conn=conn, acad_year=ACAD_YEAR)

                else:
                    # Update the bus-related tables in the PostgreSQL database
                    # admin.update_bus_db(conn=conn)
                    time.sleep(5)
            
            st.success("Update completed!")
            st.session_state["content_to_update"] = None
            time.sleep(1)
            st.rerun()


def display_majors_panel(conn: st.connections.SQLConnection, admin: Admin) -> None:
    with st.form("majors_panel"):
        st.markdown("#### Add Majors")
        st.markdown("Specify the details of the major to be added:")

        # Input major name
        major_name = st.text_input("Major")

        # Input department that the major is associated with
        department_list = get_departments_list(conn=conn, acad_year=ACAD_YEAR)  # Consider only the departments available this AY
        department_name = st.selectbox("Department of Major", options=department_list)

        # Input number of years for this major programme
        num_years_for_major = st.number_input(
            "Length of Programme (in years)",
            min_value=1,
            max_value=6,
            value=4
        )

        if st.form_submit_button("Submit"):
            if not major_name or not department_name or not num_years_for_major:
                st.error("Please ensure that all fields are filled up.")
            
            # Try to add the major, and check whether or not it is successful
            elif admin.add_new_major(conn=conn, major=major_name, department=department_name, num_years_for_major=num_years_for_major):
                # Action is successful
                st.success("Major has been added!")
            
            else:
                # Action is not successful - major already exists in database
                st.error("That major already exists.")


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

# Display panel to add majors
display_majors_panel(conn=conn, admin=user)

# Display panel to manage admins
display_admin_panel(conn=conn, admin=user)