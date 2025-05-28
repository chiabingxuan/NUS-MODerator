from moderator.bus_services.fetch_timings import get_bus_stop_names_to_codes, fetch_timings_from_api
import streamlit as st


def update_default_bus_stop() -> None:
    # Update session state with user's choice of bus stop
    st.session_state["default_bus_stop_name"] = st.session_state.bus_stop_selection


def display_bus_stop_selectbox(conn: st.connections.SQLConnection) -> str:
    # Get bus stop name to display as default option
    default_bus_stop_name = st.session_state["default_bus_stop_name"]

    # Get mapping of bus stop names to their corresponding codes
    bus_stop_names_to_codes = get_bus_stop_names_to_codes(conn=conn)
    
    # Get sorted list of bus stop names
    bus_stop_names = sorted(bus_stop_names_to_codes.keys())

    # Get index corresponding to default bus stop (wrt sorted list of bus stop names)
    if default_bus_stop_name is None:
        default_index = 0       # On first run for the session, just show the first bus stop

    else:
        default_index = bus_stop_names.index(default_bus_stop_name)

    # Get code corresponding to user's choice of bus stop
    selected_bus_stop_name = st.selectbox("Select bus stop", options=bus_stop_names, index=default_index, key="bus_stop_selection", on_change=update_default_bus_stop)
    selected_bus_stop_code = bus_stop_names_to_codes[selected_bus_stop_name]

    return selected_bus_stop_code


# Function to add HTML p tags with styling that centralises the text
def add_html_tags_with_center_style(formatted_text: str) -> str:
    return f"<p style='text-align: center;'>{formatted_text}</p>"


def format_waiting_time(waiting_time: str) -> str:
    # Carry out text formatting for the waiting time
    if waiting_time != "-" and waiting_time != "Arr":
        # Waiting time corresponds to an actual numerical value - append "min" as a suffix
        waiting_time = f"{waiting_time} min"
    
    # Add HTML tags to the formatted waiting time, so as to centralise it
    return add_html_tags_with_center_style(formatted_text=waiting_time)


def display_live_bus_timings(conn: st.connections.SQLConnection) -> None:
    with st.container(border=True):
        st.markdown("#### Live Updates")

        # Display selectbox for user to choose bus stop, and get the bus stop code of choice
        selected_bus_stop_code = display_bus_stop_selectbox(conn=conn)

        # Fetch bus timings for the selected bus stop
        selected_bus_stop_timings = fetch_timings_from_api(bus_stop_code=selected_bus_stop_code)

        # Get list of sorted bus numbers
        bus_nums = sorted(selected_bus_stop_timings.keys())

        # Initialise the columns that we will use to display the timings: bus number, next bus waiting time and second bus waiting time
        bus_num_col, next_bus_col, second_bus_col = st.columns((1, 1, 1))

        # Add column headers
        # Lambda to add style tag to centralise header text
        centralise_column_header = lambda text: f"<h5 style='text-align: center;'>{text}</h5>"
        bus_num_col.markdown(centralise_column_header(text="Service"), unsafe_allow_html=True)
        next_bus_col.markdown(centralise_column_header(text="Next Bus"), unsafe_allow_html=True)
        second_bus_col.markdown(centralise_column_header(text="Second Bus"), unsafe_allow_html=True)

        for bus_num in bus_nums:
            # Get waiting times for this bus number
            next_bus_waiting_time, second_bus_waiting_time = selected_bus_stop_timings[bus_num]["next_bus"]["waiting_time"], selected_bus_stop_timings[bus_num]["second_bus"]["waiting_time"]
            
            # Fill the columns with the details for this bus number
            with bus_num_col:
                st.markdown(add_html_tags_with_center_style(formatted_text=bus_num), unsafe_allow_html=True)

            with next_bus_col:
                st.markdown(format_waiting_time(waiting_time=next_bus_waiting_time), unsafe_allow_html=True)

            with second_bus_col:
                st.markdown(format_waiting_time(waiting_time=second_bus_waiting_time), unsafe_allow_html=True)
    
        update_button = st.button("Update Timings")


# Retrieve connection from session state
conn = st.session_state["conn"]

# Initialise session state with the default bus stop name to display timings of
if "default_bus_stop_name" not in st.session_state:
    st.session_state["default_bus_stop_name"] = None

# Display header and introduction
st.header("NUS Bus Services")

# Get user from session state
user = st.session_state["user"]

# Display bus updates
display_live_bus_timings(conn=conn)