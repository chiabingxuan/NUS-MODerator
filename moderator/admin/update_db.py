from moderator.config import DISQUS_RETRIEVAL_LIMIT, DISQUS_SHORT_NAME, SEMESTER_LIST
from moderator.sql.acad_years import INSERT_NEW_ACAD_YEAR_STATEMENT
from moderator.sql.departments import INSERT_NEW_DEPARTMENT_STATEMENT, DELETE_OUTDATED_DEPARTMENTS_STATEMENT
from moderator.sql.modules import GET_MODULE_CODES_QUERY, INSERT_NEW_MODULE_STATEMENT
from moderator.sql.offers import INSERT_NEW_OFFER_STATEMENT
from moderator.sql.reviews import INSERT_NEW_REVIEW_STATEMENT
import requests
from sqlalchemy import text
import streamlit as st

DISQUS_API_KEY = st.secrets["DISQUS_API_KEY"]

def get_module_info_this_acad_year(acad_year: str) -> tuple[list[dict[str, int | str | list[int]]], dict[str, str]]:
    print(f"Getting module information for AY{acad_year}...")

    # Use NUSMods API to get detailed information of modules, for the chosen academic year
    nusmods_endpoint_url = f"https://api.nusmods.com/v2/{acad_year}/moduleInfo.json"
    response = requests.get(url=nusmods_endpoint_url)

    if response.status_code != 200:
        raise Exception("Unsuccessful request to NUSMods API")

    # Successful GET request
    module_infos = response.json()
    
    # Loop through each module retrieved from NUSMods API
    available_modules_this_ay = list()
    departments_to_faculties_this_ay = dict()
    for module_info in module_infos:
        # Get details of this module
        module_code, module_title, module_dept, module_faculty, module_description, module_sem_data, module_mcs = module_info["moduleCode"], module_info["title"], module_info["department"], module_info["faculty"], module_info["description"], module_info["semesterData"], module_info["moduleCredit"]

        if not module_sem_data:
            # Semester data is empty for this module - module is not offered this academic year
            continue

        print(f"{module_code} {module_title} is offered for AY{acad_year}.")

        # Update mapping of departments to faculties for this academic year
        # NOTE: For the NUSMods dataset, it is actually possible that a department belongs to multiple faculties
        # for the same academic year. But oh well, we shall overwrite the faculty for now - it doesn't
        # really matter for our use case at the moment
        departments_to_faculties_this_ay[module_dept] = module_faculty
            
        # Get the semesters where the module will be offered
        # 1 = Sem 1 only, 2 = Sem 2, 3 = Special Term 1, 4 = Special Term 2
        sems_offered = [sem_data["semester"] for sem_data in module_sem_data]

        # Update list of available modules this academic year
        available_modules_this_ay.append({
            "code": module_code,
            "title": module_title,
            "department": module_dept,
            "description": module_description,
            "num_mcs": module_mcs,
            "sems_offered": sems_offered
        })

    return available_modules_this_ay, departments_to_faculties_this_ay

    
def update_departments_table(conn: st.connections.SQLConnection, departments_to_faculties_this_ay: dict[str, str]) -> None:
    print("Updating departments table...")

    with conn.session as s:
        # Loop through each department for this academic year
        for department, faculty in departments_to_faculties_this_ay.items():
            print(f"Adding / updating department information for {department}...")
            
            # Either insert new row for this department, or:
            # If department already exists in table, update the row
            s.execute(
                text(INSERT_NEW_DEPARTMENT_STATEMENT),
                params={
                    "department": department,
                    "faculty": faculty
                }
            )
        
        s.commit()


def update_modules_table(conn: st.connections.SQLConnection, available_modules_this_ay: list[dict[str, int | str | list[int]]]) -> None:
    print("Updating modules table...")

    with conn.session as s:
        # For the available modules this academic year, we need to update the table
        for available_module in available_modules_this_ay:
            # Get information for this module
            available_module_code, available_module_title, available_module_dept, available_module_description, available_module_num_mcs = available_module["code"], available_module["title"], available_module["department"], available_module["description"], available_module["num_mcs"]
            
            print(f"Adding / updating module information for {available_module_code}...")

            # Either insert new row for this module, or:
            # If module already exists in table, update the row
            s.execute(
                text(INSERT_NEW_MODULE_STATEMENT),
                params={
                    "code": available_module_code,
                    "title": available_module_title,
                    "department": available_module_dept,
                    "description": available_module_description,
                    "num_mcs": available_module_num_mcs
                }
            )
        
        s.commit()


def delete_outdated_departments(conn: st.connections.SQLConnection) -> None:
    print("Deleting outdated departments...")

    # Delete outdated department information from "departments" table
    # If department does not appear in "modules" table, we take it to be outdated
    with conn.session as s:
        s.execute(text(DELETE_OUTDATED_DEPARTMENTS_STATEMENT))

        s.commit()
        

def use_disqus_api(short_name: str, retrieval_limit: int) -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    thread_ids_to_names = dict()        # Maps thread ids to thread names
    thread_ids_to_posts = dict()        # Maps thread ids to lists of posts
    for endpoint in ["Threads", "Posts"]:
        print(f"Retrieving {endpoint.lower()}...")

        url = f"https://disqus.com/api/3.0/forums/list{endpoint}.json"
        params = {
            "api_key": DISQUS_API_KEY,
            "forum": short_name,
            "limit": retrieval_limit
        }
        has_next = True

        # Get Disqus information in a batchwise manner
        while has_next:
            # Get the response and, from it, the dictionary containing all the information in this batch
            response = requests.get(
                url=url,
                params=params
            )
            response_json = response.json()
            batch_data = response_json["response"]

            # Loop through each piece of information (either thread / post) in this batch
            for piece_of_info in batch_data:
                if endpoint == "Threads":
                    # If we are retrieving threads
                    # Get thread information
                    thread_name, thread_id = piece_of_info["clean_title"], piece_of_info["id"]

                    # Update mapping that links the thread ids to thread names
                    thread_ids_to_names[thread_id] = {
                        "thread_name": thread_name
                    }
                
                else:
                    # If we are retrieving posts
                    # Get post information
                    post_id, thread_id_containing_post, post_message = piece_of_info["id"], piece_of_info["thread"], piece_of_info["raw_message"]

                    # Include id and text content in the post to be added
                    post = {
                        "post_id": post_id,
                        "post_message": post_message
                    }

                    # Update mapping that links the thread ids to lists of posts
                    if thread_id_containing_post not in thread_ids_to_posts:
                        thread_ids_to_posts[thread_id_containing_post] = list()
                    
                    thread_ids_to_posts[thread_id_containing_post].append(post)
                
            # Check if there is a next batch
            has_next = response_json["cursor"]["hasNext"]

            # Update cursor to the next one if there is a next batch
            if has_next:
                params["cursor"] = response_json["cursor"]["next"]

    return thread_ids_to_names, thread_ids_to_posts


def update_reviews_table(conn: st.connections.SQLConnection, thread_ids_to_names: dict[str, dict[str, str]], thread_ids_to_posts: dict[str, list[dict[str, str]]]) -> None:
    print("Updating reviews table...")

    # Get set of module codes that is being kept track of, in the database
    module_code_records = set(conn.query(GET_MODULE_CODES_QUERY, ttl=0)["code"])

    # Loop through each thread retrieved from Disqus
    for thread_id, reviews in thread_ids_to_posts.items():
        # Get module information
        module_name = thread_ids_to_names[thread_id]["thread_name"]
        module_code = module_name.split()[0]

        if module_code not in module_code_records:
            # Module code is not in "modules" table - module does not exist in the chosen timeframe,
            # from first academic year to current academic year. Skip reviews
            print(f"{module_name} does not exist in the chosen timeframe. Skipping reviews.")
            continue

        print(f"{module_name} exists in the chosen timeframe. Checking reviews...")

        # Loop through each review for this module, and update the "reviews" table
        with conn.session as s:
            for review in reviews:
                # Get review information
                review_id, review_message = review["post_id"], review["post_message"]

                # Either insert new row for this review, or:
                # If review already exists in table, update the row
                s.execute(
                    text(INSERT_NEW_REVIEW_STATEMENT),
                    params={
                        "id": review_id,
                        "module_code": module_code,
                        "message": review_message
                    }
                )
                
            s.commit()


def update_acad_years_table(conn: st.connections.SQLConnection, acad_year: str) -> None:
    print("Updating academic years table...")

    with conn.session as s:
        # Add this academic year (newest and latest one) to the table
        s.execute(
            text(INSERT_NEW_ACAD_YEAR_STATEMENT),
            params={
                "acad_year": acad_year
            }
        )

        s.commit()


def update_offers_table(conn: st.connections.SQLConnection, acad_year: str, available_modules_this_ay: list[dict[str, int | str | list[int]]], semester_list: list[dict[str, int | str]]) -> None:
    # For the available modules this academic year, we need to update the "offers" table
    with conn.session as s:
        for available_module in available_modules_this_ay:
            # Get the list of semesters when this module is offered
            available_module_code, available_module_sems_offered = available_module["code"], available_module["sems_offered"]
            
            print(f"Adding offer information for {available_module_code}...")

            # Get the list of all semesters
            all_sems = [sem_data["num"] for sem_data in semester_list]

            # Loop through each semester and check whether module is offered
            for sem_num in all_sems:
                if sem_num in available_module_sems_offered:
                    # Module is offered for this semester
                    # Either insert new row for this offer, or:
                    # If offer already exists, do nothing
                    s.execute(
                        text(INSERT_NEW_OFFER_STATEMENT),
                        params={
                            "module_code": available_module_code,
                            "acad_year": acad_year,
                            "sem_num": sem_num
                        }
                    )

        s.commit()


def update_db(conn: st.connections.SQLConnection, acad_year: str) -> None:
    # Fetch latest information from NUSMods API
    # Get the modules offered, the modules not offered, and the departments available this academic year
    available_modules_this_ay, departments_to_faculties_this_ay = get_module_info_this_acad_year(acad_year=acad_year)

    # Update "departments" table in PostgreSQL database
    update_departments_table(conn=conn, departments_to_faculties_this_ay=departments_to_faculties_this_ay)

    # Update "modules" table in PostgreSQL database
    update_modules_table(conn=conn, available_modules_this_ay=available_modules_this_ay)

    # Deleted outdated departments from "departments" table
    delete_outdated_departments(conn=conn)

    # Retrieve reviews, by fetching latest information from Disqus API
    thread_ids_to_names, thread_ids_to_posts = use_disqus_api(short_name=DISQUS_SHORT_NAME, retrieval_limit=DISQUS_RETRIEVAL_LIMIT)

    # Update "reviews" table in PostgreSQL database, by fetching latest information from NUSMods API
    update_reviews_table(conn=conn, thread_ids_to_names=thread_ids_to_names, thread_ids_to_posts=thread_ids_to_posts)

    # Update "acad_years" table in PostgreSQL database
    update_acad_years_table(conn=conn, acad_year=acad_year)

    # Update "offers" table in PostgreSQL database
    update_offers_table(conn=conn, acad_year=acad_year, available_modules_this_ay=available_modules_this_ay, semester_list=SEMESTER_LIST)

    print("Update completed!")