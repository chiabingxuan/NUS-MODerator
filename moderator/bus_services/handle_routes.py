from moderator.sql.bus_routes import GET_SUBSEQUENT_BUS_STOPS_QUERY
import pandas as pd
import streamlit as st


def get_subsequent_bus_stops(conn: st.connections.SQLConnection, bus_num: str, bus_stop_code: str) -> tuple[list[str], dict[str, str]]:
    # Get dataframe of subsequent bus stop codes and names (in sequential order of route)
    subsequent_bus_stops_df = conn.query(
        GET_SUBSEQUENT_BUS_STOPS_QUERY,
        params={
            "bus_num": bus_num,
            "bus_stop_code": bus_stop_code
        },
        ttl=3600
    )

    # Get ordered list of subsequent bus stop names
    ordered_subsequent_bus_stop_names = list(subsequent_bus_stops_df["display_name"])

    # Get mapping of these bus stop names to their bus stop codes
    subsequent_bus_stop_names_to_codes = pd.Series(
        subsequent_bus_stops_df["bus_stop_code"].values,
        index=subsequent_bus_stops_df["display_name"]
    ).to_dict()

    return ordered_subsequent_bus_stop_names, subsequent_bus_stop_names_to_codes


