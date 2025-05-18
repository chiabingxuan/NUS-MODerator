from moderator.sql.users import GET_EXISTING_USER_QUERY, MAKE_USER_ADMIN_STATEMENT
import pandas as pd
import streamlit as st
from sqlalchemy import text


def get_existing_user_details(conn: st.connections.SQLConnection, username: str) -> pd.DataFrame:
    # Query the details of the user, using his / her username
    existing_user_info_df = conn.query(GET_EXISTING_USER_QUERY, params={"username": username}, ttl=0)
    return existing_user_info_df


def make_user_admin(conn: st.connections.SQLConnection, username: str) -> None:
    # Give user admin rights, using his / her username
    with conn.session as s:
        s.execute(
            text(MAKE_USER_ADMIN_STATEMENT),
            params={
                "username": username
            }
        )

        s.commit()