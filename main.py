from moderator.chatbot.chatbot import run_chatbot
from moderator.chatbot.chatbot_setup import update_vector_store
from moderator.admin.update_db import update_db
import os
import requests
import streamlit as st
from sqlalchemy import text

# Set LangSmith credentials
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = st.secrets["LANGCHAIN_TRACING_V2"]
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets["LANGCHAIN_ENDPOINT"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]


if __name__ == "__main__":
    conn = st.connection("nus_moderator", type="sql")
    mod_codes = list(conn.query("select code from modules;", ttl=0)["code"])
    with conn.session as s:
        for mod_code in mod_codes:
            print(mod_code)
            mod_info = requests.get(f"https://api.nusmods.com/v2/2024-2025/modules/{mod_code}.json").json()
            mcs, sem_data = mod_info["moduleCredit"], mod_info["semesterData"]
            sems_offered = sum([sem_data["semester"] for sem_data in sem_data])
            s.execute(text("update modules set num_mcs = :num_mcs, sems_offered = :sems_offered where code = :code"), params={
                "num_mcs": mcs,
                "code": mod_code,
                "sems_offered": sems_offered
            })
        s.commit()
