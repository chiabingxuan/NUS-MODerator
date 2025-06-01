import datetime
from moderator.bus_services.fetch_timings import fetch_timings_from_api
from moderator.config import TERMINAL_BUS_STOP_SEQ_NUM, WEATHER_API_URL, NUS_REGION, HOURS_WRT_UTC
from moderator.sql.bus_routes import GET_TERMINAL_BUS_STOP_QUERY
from moderator.sql.bus_trips import INSERT_BUS_TRIP_STATEMENT
import requests
import streamlit as st
from sqlalchemy import text


def get_eta_date(conn: st.connections.SQLConnection, bus_num: str, end_bus_stop: str, bus_plate_num: str) -> datetime.datetime:
    # Check if end bus stop is terminal
    terminal_bus_stop_code = conn.query(
        GET_TERMINAL_BUS_STOP_QUERY,
        params={
            "bus_num": bus_num,
            "max_seq_num": TERMINAL_BUS_STOP_SEQ_NUM
        },
        ttl=3600
    ).iloc[0]["bus_stop_code"]

    if end_bus_stop == terminal_bus_stop_code:
        # End bus stop is terminal. Bus data from API does not contain any information about ETA at terminal bus stop
        eta_date = None
    
    else:
        # End bus stop is not terminal. We can get ETA at this bus stop by getting the updated bus timings
        # for destination bus stop and looking for the license plate number of the bus that the user has boarded
        end_bus_stop_bus_timings = fetch_timings_from_api(bus_stop_code=end_bus_stop)[bus_num]["bus_timings"]
        if bus_plate_num not in end_bus_stop_bus_timings:
            # Cannot find the bus the user has boarded
            # Could be because bus has already left the destination bus stop
            # Just set ETA as None
            eta_date = None

        else:
            # Get ETA at destination, in seconds. Use it to get ETA in datetime format
            eta_time = end_bus_stop_bus_timings[bus_plate_num] 
            eta_date = datetime.datetime.now() + datetime.timedelta(seconds=eta_time) + datetime.timedelta(hours=HOURS_WRT_UTC)

    return eta_date


def get_weather() -> str:
    # Get 2 hour weather forecast from data.gov.sg API
    weather_forecast_response = requests.get(
        url=WEATHER_API_URL
    )

    if weather_forecast_response.status_code != 200:
        raise Exception("Unsuccessful request to weather API")
    
    # Get list of weather forecasts for various regions in Singapore
    [weather_data_unpacked,] = weather_forecast_response.json()["data"]["items"]
    forecasts = weather_data_unpacked["forecasts"]

    # Get weather forecast for NUS
    # Should only be of length 1 (only one region corresponding to NUS)
    nus_forecast_data_list = [forecast for forecast in forecasts if forecast["area"] == NUS_REGION]
    if len(nus_forecast_data_list) != 1:
        raise Exception("Either multiple forecasts or no forecasts corresponding to NUS region - something is wrong")

    # Unpack and get NUS forecast
    [nus_forecast_data,] = nus_forecast_data_list
    nus_forecast = nus_forecast_data["forecast"]

    return nus_forecast


def record_trip(conn: st.connections.SQLConnection, username: str, bus_num: str, start_bus_stop: str, end_bus_stop: str, start_date: datetime.datetime, end_date: datetime.datetime, eta_date: datetime.datetime, weather: str) -> None:
    with conn.session as s:
        s.execute(
            text(INSERT_BUS_TRIP_STATEMENT),
            params={
                "username": username,
                "bus_num": bus_num,
                "start_bus_stop": start_bus_stop,
                "end_bus_stop": end_bus_stop,
                "start_date": start_date,
                "end_date": end_date,
                "eta": eta_date,
                "weather": weather
            }
        )

        s.commit()
