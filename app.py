import datetime
import hashlib
from moderator.sql.acad_years import GET_LIST_OF_AYS_QUERY
from moderator.sql.users import GET_EXISTING_USER_QUERY, INSERT_NEW_USER_STATEMENT
from moderator.utils.helpers import get_formatted_user_enrollments_from_db, get_major_list, adjust_to_timezone
from moderator.utils.user import User, Admin
import os
from sqlalchemy import text
import streamlit as st
import time
import torch

# Keep this here to avoid RuntimeError during launch
torch.classes.__path__ = []

# Set LangSmith credentials
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = st.secrets["LANGCHAIN_TRACING_V2"]
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN_ENDPOINT"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]


def get_list_of_ays(conn: st.connections.SQLConnection) -> list[str]:
    # Query the list of academic years from the database, from oldest to newest
    list_of_ays = list(conn.query(GET_LIST_OF_AYS_QUERY, ttl=3600)["acad_year"])

    return list_of_ays


def check_username_validity(username: str) -> bool:
    # Check if username is 8 - 20 characters long
    username_length = len(username)

    if username_length < 8 or username_length > 20:
        return False
    
    return True


def check_password_validity(password: str) -> bool:
    # Check if password is 8 - 20 characters long
    password_length = len(password)

    if password_length < 8 or password_length > 20:
        return False
    
    return True


def get_sha256_hash(password: str) -> str:
    # Use SHA256 algorithm for encryption
    password_encoded = password.encode("utf-8")
    return hashlib.sha256(password_encoded).hexdigest()


def handle_login(conn: st.connections.SQLConnection, username_input: str, password_input: str) -> None:
    if not (username_input and password_input):
        # Not all fields are filled up
        st.error("Please ensure that all fields are filled up.")

    else:
        # Query the existing user information from database, if any
        existing_user_info_df = conn.query(GET_EXISTING_USER_QUERY, params={"username": username_input}, ttl=0)

        if len(existing_user_info_df) == 0:
            # Username does not exist in database
            st.error("The username does not exist.")
        
        else:
            # Get existing user information
            existing_user_info = existing_user_info_df.iloc[0].to_dict()
            password_encrypted, first_name, last_name, matriculation_ay, major, role, reg_datetime = existing_user_info["password"], existing_user_info["first_name"], existing_user_info["last_name"], existing_user_info["matriculation_ay"], existing_user_info["major"], existing_user_info["role"], existing_user_info["reg_datetime"]

            # Check if hash of the password input matches with that of the stored encryption
            if get_sha256_hash(password=password_input) != password_encrypted:
                st.error("The password is incorrect.")
            
            else:
                # Successful login
                # Get a formatted dictionary of the courses taken by the user
                formatted_user_enrollments = get_formatted_user_enrollments_from_db(conn=conn, username=username_input)

                # Initialise user
                if role == "user":
                    # User is not an admin
                    user = User(
                        username=username_input,
                        first_name=first_name,
                        last_name=last_name,
                        matriculation_ay=matriculation_ay,
                        major=major,
                        reg_datetime=reg_datetime,
                        user_enrollments=formatted_user_enrollments
                    )

                    user_role = "user"
   
                else:
                    user = Admin(
                        username=username_input,
                        first_name=first_name,
                        last_name=last_name,
                        matriculation_ay=matriculation_ay,
                        major=major,
                        reg_datetime=reg_datetime,
                        user_enrollments=formatted_user_enrollments
                    )

                    user_role = "admin"

                # Update session state
                st.session_state["user"] = user
                st.session_state["user_role"] = user_role
                st.success("Login successful!")
                time.sleep(1)
                st.rerun()


def handle_registration(conn: st.connections.SQLConnection, username_input: str | None, password_input: str | None, first_name_input: str | None, last_name_input: str | None, matriculation_ay_input: str | None, major_input: str | None) -> None:
    if not (username_input and password_input and first_name_input and last_name_input and matriculation_ay_input and major_input):
        # Not all fields are filled up
        st.error("Please ensure that all fields are filled up.")

    elif not check_username_validity(username=username_input) or not check_password_validity(password=password_input):
        # Either username or password is invalid
        st.error("Invalid username or password. Please ensure that both username and password are 8 to 20 characters long.")

    else:
        # Query the existing user information from database, if any
        existing_user_info_df = conn.query(GET_EXISTING_USER_QUERY, params={"username": username_input}, ttl=0)

        if len(existing_user_info_df) > 0:
            # Username exists in database already
            st.error("The username has already been taken.")
        
        else:
            # Registration successful
            # Add new user to database
            # Hash the password input using SHA256 algorithm
            hashed_password = get_sha256_hash(password=password_input)

            with conn.session as s:
                s.execute(
                    text(INSERT_NEW_USER_STATEMENT),
                    params={
                        "username": username_input,
                        "password": hashed_password,
                        "first_name": first_name_input,
                        "last_name": last_name_input,
                        "matriculation_ay": matriculation_ay_input,
                        "major": major_input,
                        "reg_datetime": adjust_to_timezone(time=datetime.datetime.now())
                    }
                )

                s.commit()

            st.success("Registration successful! Please proceed to log in.")


def display_and_handle_auth_tabs(conn: st.connections.SQLConnection) -> None:
    login_tab, register_tab = st.tabs([
        ":material/login: Login to existing account",
        ":material/add_circle: Register for new account"
    ])

    # Display login form if user toggles to it
    with login_tab:
        with st.form("login_form"):
            # Display username and password fields
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")

        # Try to log in upon form submission
        if login_button:
            handle_login(conn=conn, username_input=username_input, password_input=password_input)
            
    # Display registration form if user toggles to it
    with register_tab:
        with st.form("register_form"):
            # Get major list
            major_list = get_major_list(conn=conn)

            # Display fields for registration
            username_input = st.text_input("Username")
            first_name_input = st.text_input("First Name")
            last_name_input = st.text_input("Last Name")
            matriculation_ay_input = st.selectbox("Matriculation AY", options=st.session_state["list_of_ays"][1:], index=None)  # Earliest AY (2021-2022) will be used as the IBLOC AY for users that matriculated in AY 2022-2023. AY 2022-2023 is the earliest matriculation AY
            major_input = st.selectbox("Major", options=major_list, index=None)
            password_input = st.text_input("Password", type="password")
            register_button = st.form_submit_button("Register")

        # Try to register upon form submission
        if register_button:
            handle_registration(conn=conn, username_input=username_input, password_input=password_input, first_name_input=first_name_input, last_name_input=last_name_input, matriculation_ay_input=matriculation_ay_input, major_input=major_input)


# Inject global CSS to hide anchor buttons on headings
st.markdown(
    """
    <style>
    [data-testid='stHeaderActionElements'] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialise connection and save it in session state
conn = st.connection("nus_moderator", type="sql")
if "conn" not in st.session_state:
    st.session_state["conn"] = conn

# Get list of academic years considered, and save in session state
if "list_of_ays" not in st.session_state:
    list_of_ays = get_list_of_ays(conn=conn)
    st.session_state["list_of_ays"] = list_of_ays
    
# List of pages of app
pages = [
    st.Page(os.path.join("app_pages", "home.py"), title="Home"),
    st.Page(os.path.join("app_pages", "bus_services.py"), title="Bus Services"),
    st.Page(os.path.join("app_pages", "planner.py"), title="Course Planner"),
    st.Page(os.path.join("app_pages", "ama.py"), title="AMA"),
    st.Page(os.path.join("app_pages", "profile.py"), title="Profile"),
    st.Page(os.path.join("app_pages", "about.py"), title="About")
]


if "user" not in st.session_state:
    # No user saved in session state - user has not logged in
    # Display placeholder header of app
    st.header("NUS-MODerator")

    # Hide navigation bar
    page_nav = st.navigation(pages, position="hidden")

    # Display the selection of forms
    display_and_handle_auth_tabs(conn=conn)

    # Display terms of service
    st.markdown("[NUS Policy for IT Resources](https://nus.edu.sg/registrar/docs/info/registration-guides/aup-form.pdf)")

else:
    # User has already logged in
    if st.session_state["user_role"] == "admin":
        # If user is admin, add the admin page
        pages.append(st.Page(os.path.join("app_pages", "admin.py"), title="Admin"))

    # Display and run navigation sidebar
    page_nav = st.navigation(pages, position="sidebar")
    page_nav.run()