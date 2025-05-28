from moderator.config import NEXTBUS_API_BASE_URL
from moderator.sql.bus_stops import GET_BUS_STOPS_QUERY
import requests
import streamlit as st


def get_bus_stop_names_to_codes(conn: st.connections.SQLConnection) -> dict[str, str]:
    # Get bus stop information from database
    bus_stop_rows_queried = conn.query(GET_BUS_STOPS_QUERY, ttl=3600).values.tolist()

    # Get mapping of bus stop names to their corresponding codes
    bus_stop_names_to_codes = dict()
    for bus_stop_code, bus_stop_name, bus_stop_lat, bus_stop_long in bus_stop_rows_queried:
        bus_stop_names_to_codes[bus_stop_name] = bus_stop_code

    return bus_stop_names_to_codes


def fetch_timings_from_api(bus_stop_code: str) -> dict[str, dict[str, dict[str, str | int | None]]]:
    # Get timings for the selected bus stop, from the NextBus API
    url = f"{NEXTBUS_API_BASE_URL}/ShuttleService"
    response = requests.get(url=url, params={"busstopname": bus_stop_code})

    if response.status_code != 200:
        # Something went wrong with the fetch
        raise Exception("Unsuccessful request to NextBus API")

    # Get data for the bus numbers serviced at the bus stop
    # "name": Name of bus service
    # "arrivalTime": Time (in min) before next bus
    # "arrivalTime_veh_plate": License plate number of next bus (not available for public buses)
    # "nextArrivalTime": Time (in min) before second bus
    # "nextArrivalTime_veh_plate": License plate number of second bus (not available for public buses)
    # "_etas": List of buses. Each bus: dictionary with keys "plate", "eta"
    json_response = response.json()
    bus_services_at_bus_stop = json_response["ShuttleServiceResult"]["shuttles"]

    # Initialise dictionary to be returned
    # Each bus number is a key. Value is a dictionary:
    # Keys: "next_bus", "second_bus", "bus_timings"
    # Value of "next_bus": Dictionary that stores waiting time and plate number of next bus (for public buses, plate number is None)
    # Value of "second_bus": Dictionary that stores waiting time and plate number of second bus (for public buses, plate number is None)
    # Value of "bus_timings": Dictionary mapping bus plate numbers (of all the buses whose waiting times can be forecasted) to their estimated waiting times (for public buses, "bus_timings" maps to empty dictionary)
    bus_stop_timings = dict()
    for bus_service_data in bus_services_at_bus_stop:
        # Get bus number and update dictionary
        bus_num = bus_service_data["name"]
        bus_num = bus_num.removeprefix("PUB:")      # Remove "PUB:" tag for public bus services
        bus_stop_timings[bus_num] = dict()
        
        # Get details of next bus and update dictionary
        next_bus_waiting_time, next_bus_plate_num = bus_service_data["arrivalTime"], bus_service_data.get("arrivalTime_veh_plate")
        bus_stop_timings[bus_num]["next_bus"] = {
            "waiting_time": next_bus_waiting_time,
            "plate_num": next_bus_plate_num
        }

        # Get details of second bus and update dictionary
        second_bus_waiting_time, second_bus_plate_num = bus_service_data["nextArrivalTime"], bus_service_data.get("nextArrivalTime_veh_plate")
        bus_stop_timings[bus_num]["second_bus"] = {
            "waiting_time": second_bus_waiting_time,
            "plate_num": second_bus_plate_num
        }

        # Get estimated arrival times of all buses that can be forecasted
        forecastable_buses = bus_service_data.get("_etas", list())  # For public buses, no "_etas" key. Just return empty list
        bus_stop_timings[bus_num]["bus_timings"] = dict()
        for forecastable_bus_data in forecastable_buses:
            # Get details of each of these buses and update dictionary
            forecastable_bus_plate_num, forecastable_bus_waiting_time = forecastable_bus_data["plate"], forecastable_bus_data["eta"]
            bus_stop_timings[bus_num]["bus_timings"][forecastable_bus_plate_num] = forecastable_bus_waiting_time
        
    return bus_stop_timings