import datetime
from moderator.bus_services.fetch_timings import get_bus_stop_names_to_codes, fetch_timings_from_api
from moderator.bus_services.handle_routes import get_subsequent_bus_stops
from moderator.bus_services.record_trips import get_eta_date, get_weather, record_trip
from moderator.config import BUS_TIMINGS_AUTOREFRESH_INTERVAL, HOURS_WRT_UTC
import pytz
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time


# Callable when bus stop selectbox changes
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


@st.dialog("Record Your Trip")
def confirm_record_of_bus_trip(conn: st.connections.SQLConnection, username: str, bus_num: str, bus_plate_num: str, start_bus_stop: str, start_date: datetime.datetime, weather: str) -> None:
    # Display bus plate number
    st.markdown(f"**Bus License Plate Number**: {bus_plate_num}")
    
    # Get information of the bus stops after the one that the user has boarded from
    ordered_subsequent_bus_stop_names, subsequent_bus_stop_names_to_codes = get_subsequent_bus_stops(conn=conn, bus_num=bus_num, bus_stop_code=start_bus_stop)
    
    if not ordered_subsequent_bus_stop_names:
        # No more subsequent bus stops - starting bus stop is terminal
        st.markdown(f"Bus service {bus_num} terminates at this bus stop. You cannot board this bus.")
        return
    
    # Bus can be boarded
    # Get and save estimated datetimes when user will alight at all possible destinations (using NUSNextBus ETA data)
    # This is only done once, when dialog is opened
    if not st.session_state["eta_dates_dialog"]:
        for bus_stop_name in ordered_subsequent_bus_stop_names:
            bus_stop_code = subsequent_bus_stop_names_to_codes[bus_stop_name]
            eta_date = get_eta_date(
                conn=conn,
                bus_num=bus_num,
                end_bus_stop=bus_stop_code,
                bus_plate_num=bus_plate_num
            )
            st.session_state["eta_dates_dialog"][bus_stop_code] = eta_date
    
    # Get user's destination from his / her selection
    selected_end_bus_stop_name = st.selectbox("Choose your destination", options=ordered_subsequent_bus_stop_names)
    selected_end_bus_stop_code = subsequent_bus_stop_names_to_codes[selected_end_bus_stop_name]

    # Get actual time when user alights at his destination
    end_time = st.time_input("When did you arrive at your destination?", value=datetime.datetime.now() + datetime.timedelta(hours=HOURS_WRT_UTC), step=60)
    end_date = datetime.datetime.combine((datetime.datetime.now() + datetime.timedelta(hours=HOURS_WRT_UTC)).date(), end_time)

    confirm_button = st.button("Submit Trip")
    cancel_button = st.button("Cancel")

    # Record trip data in database
    if confirm_button:
        # Check validity of time of arrival
        if end_date <= start_date:
            st.error("Time of arrival must be later than time of boarding. Please review.")
            return
    
        record_trip(
            conn=conn,
            username=username,
            bus_num=bus_num,
            start_bus_stop=start_bus_stop,
            end_bus_stop=selected_end_bus_stop_code,
            start_date=start_date,
            end_date=end_date,
            eta_date=st.session_state["eta_dates_dialog"][selected_end_bus_stop_code],   # Get ETA from session state
            weather=weather
        )

        st.success("Bus trip has been recorded!")
        time.sleep(1)
        st.rerun()
    
    if cancel_button:
        # If cancellation is triggered, use a rerun to close the dialog
        st.rerun()


# Will return a boolean that indicates whether or not this waiting time corresponds to an "Arr" button that has been pressed
def display_waiting_time(conn: st.connections.SQLConnection, username: str, waiting_time: str, bus_stop_code: str, bus_num: str, bus_type: str, bus_plate_num: str | None) -> bool:
    if waiting_time == "Arr":
        if not bus_num.startswith("PUB:"):
            # Non-public bus has arrived
            # Mark the time now as the arrival time
            # Start date for the user's recorded trip: Defined as the point in time when the "Arr" button appears
            start_date = datetime.datetime.now() + datetime.timedelta(hours=HOURS_WRT_UTC)

            # Display a centralised button for user to record his bus trip (if he / she boarded this arrived bus)
            left_col, middle_col, right_col = st.columns((1, 1, 1), vertical_alignment="center")
            with middle_col:
                record_trip_button = st.button(
                    label=f"**{waiting_time}**",     # Bold the "Arr" text using Markdown (st.button only accepts Markdown formatting)
                    key=f"arr_{bus_stop_code}_{bus_num}_{bus_type}_{bus_plate_num}",
                    help="Did you board this bus? Click to record your bus trip!",
                    use_container_width=True
                )

            if record_trip_button:
                if bus_plate_num is None:
                    # If this happens, there is big big problem because non-public buses (NUS buses)
                    # should have known plate numbers
                    raise Exception("Plate number for this NUS bus is unknown")
                
                # Clear ETAs from session state
                st.session_state["eta_dates_dialog"] = dict()

                # Get current weather
                weather = get_weather()

                confirm_record_of_bus_trip(
                    conn=conn,
                    username=username,
                    bus_num=bus_num,
                    bus_plate_num=bus_plate_num,
                    start_bus_stop=bus_stop_code,
                    start_date=start_date,
                    weather=weather
                )

                # This "Arr" button has been pressed - return True
                return True
            
            # This "Arr" button has not been pressed - return False
            return False
        
        # Don't need to record public bus trips
        # Bold the "Arr" text using HTML
        waiting_time = f"<b>{waiting_time}</b>"
    
    elif waiting_time != "-":
        # Waiting time corresponds to an actual numerical value - append "min" as a suffix
        waiting_time = f"{waiting_time} min"
    
    # Add HTML tags to the formatted waiting time, so as to centralise the text
    formatted_waiting_time_with_centralising_html = add_html_tags_with_center_style(formatted_text=waiting_time)
    st.markdown(formatted_waiting_time_with_centralising_html, unsafe_allow_html=True)

    # Waiting time displayed is not "Arr" - no "Arr" button displayed, return False
    return False


def display_live_bus_timings(conn: st.connections.SQLConnection, username: str) -> bool:
    with st.container(border=True):
        st.markdown("#### Live Updates")

        # Display selectbox for user to choose bus stop, and get the bus stop code of choice
        selected_bus_stop_code = display_bus_stop_selectbox(conn=conn)

        # Fetch bus timings for the selected bus stop
        selected_bus_stop_timings = fetch_timings_from_api(bus_stop_code=selected_bus_stop_code)

        # Update session state with fetched data
        st.session_state["bus_timings"][selected_bus_stop_code] = selected_bus_stop_timings

        # Get list of sorted bus numbers
        # Public buses will be displayed after school buses
        nus_bus_nums, public_bus_nums = list(), list()
        for bus_num in selected_bus_stop_timings.keys():
            if bus_num.startswith("PUB:"):
                public_bus_nums.append(bus_num)
            
            else:
                nus_bus_nums.append(bus_num)

        nus_bus_nums.sort()
        public_bus_nums.sort()
        bus_nums = nus_bus_nums + public_bus_nums

        # Lambda to add style tag to centralise header text
        centralise_column_header = lambda text: f"<h5 style='text-align: center;'>{text}</h5>"

        # Add column headers
        bus_num_header, next_bus_header, second_bus_header = st.columns((1, 1, 1), vertical_alignment="center")
        bus_num_header.markdown(centralise_column_header(text="Service"), unsafe_allow_html=True)
        next_bus_header.markdown(centralise_column_header(text="Next Bus"), unsafe_allow_html=True)
        second_bus_header.markdown(centralise_column_header(text="Second Bus"), unsafe_allow_html=True)

        arr_button_pressed = False      # Boolean flag to check if an "Arr" button has been pressed in this rerun
        for bus_num in bus_nums:
            # Get waiting times for this bus number
            next_bus_waiting_time, second_bus_waiting_time = selected_bus_stop_timings[bus_num]["next_bus"]["waiting_time"], selected_bus_stop_timings[bus_num]["second_bus"]["waiting_time"]
            
            # Get plate numbers of next bus and second bus
            next_bus_plate_num, second_bus_plate_num = selected_bus_stop_timings[bus_num]["next_bus"]["plate_num"], selected_bus_stop_timings[bus_num]["second_bus"]["plate_num"]

            # Initialise the columns that we will use to display the timings: bus number, next bus waiting time and second bus waiting time
            bus_num_col, next_bus_col, second_bus_col = st.columns((1, 1, 1), vertical_alignment="center")
            st.markdown("<hr style='margin-top: 0px; margin-bottom: 15px;'>", unsafe_allow_html=True)

            # Fill the columns with the details for this bus number
            with bus_num_col:
                bus_num_without_pub_tag = bus_num.removeprefix("PUB:")      # Remove "PUB:" tag for public bus services
                st.markdown(add_html_tags_with_center_style(formatted_text=bus_num_without_pub_tag), unsafe_allow_html=True)

            with next_bus_col:
                # Display next bus waiting time
                # Also check if this waiting time corresponds to an "Arr" button that has been pressed
                next_bus_arr_button_pressed = display_waiting_time(
                    conn=conn,
                    username=username,
                    waiting_time=next_bus_waiting_time,
                    bus_stop_code=selected_bus_stop_code,
                    bus_num=bus_num,
                    bus_type="next",
                    bus_plate_num=next_bus_plate_num
                )

                if next_bus_arr_button_pressed:
                    arr_button_pressed = True

            with second_bus_col:
                # Display second bus waiting time
                second_bus_arr_button_pressed = display_waiting_time(
                    conn=conn,
                    username=username,
                    waiting_time=second_bus_waiting_time,
                    bus_stop_code=selected_bus_stop_code,
                    bus_num=bus_num,
                    bus_type="second",
                    bus_plate_num=second_bus_plate_num
                )

                if second_bus_arr_button_pressed:
                    arr_button_pressed = True

        # Display last update time for this bus stop
        last_updated_time = datetime.datetime.now() + datetime.timedelta(hours=HOURS_WRT_UTC)
        st.markdown(f"**Last updated**: {last_updated_time.strftime("%d/%m/%Y %I:%M:%S %p")}")

        # Update session state with the last update time for this bus stop
        st.session_state["bus_timings_last_updated"][selected_bus_stop_code] = last_updated_time

        update_button = st.button("Update Timings")

        return arr_button_pressed


# Remove X button from any dialogs
st.html(
    '''
        <style>
            div[aria-label="dialog"]>button[aria-label="Close"] {
                display: none;
            }
        </style>
    '''
)

# Retrieve connection from session state
conn = st.session_state["conn"]

# Initialise session state with the default bus stop name to display timings of
if "default_bus_stop_name" not in st.session_state:
    st.session_state["default_bus_stop_name"] = None

# Initialise bus timing data in session state
# Dictionary mapping bus stop code to most updated timings requested from API
if "bus_timings" not in st.session_state:
    st.session_state["bus_timings"] = dict()

# Initialise the last update times (maps each bus stop code to the time of last update)
if "bus_timings_last_updated" not in st.session_state:
    st.session_state["bus_timings_last_updated"] = dict()

# Initialise dictionary containing the ETAs (datetime format) for
# all possible destinations (using NUSNextBus ETA data), 
# retrieved when "Record Your Trip" dialog is first opened
# Maps end bus stop codes to ETAs
if "eta_dates_dialog" not in st.session_state:
    st.session_state["eta_dates_dialog"] = dict()

# Display header and introduction
st.header("NUS Bus Services")

# Get user from session state
user = st.session_state["user"]

# Display bus updates
# Also returns a boolean flag that indicates whether or not an "Arr" button has been pressed
arr_button_pressed = display_live_bus_timings(conn=conn, username=user.username)

# If an "Arr" button has been pressed, dialog will be triggered - do not activate autorefresh
if not arr_button_pressed:
    # Continually rerun page after a given time interval, so as to auto-update bus timings
    st_autorefresh(interval=BUS_TIMINGS_AUTOREFRESH_INTERVAL, key="bus_timings_autorefresh")