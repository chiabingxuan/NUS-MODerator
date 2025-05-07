from moderator.config import ACAD_YEAR, DISQUS_RETRIEVAL_LIMIT, DISQUS_SHORT_NAME
from moderator.sql.departments import INSERT_NEW_DEPARTMENT_STATEMENT, DELETE_OUTDATED_DEPARTMENTS_STATEMENT
from moderator.sql.modules import GET_MODULE_CODES_QUERY, INSERT_NEW_MODULE_STATEMENT, DELETE_EXISTING_MODULE_STATEMENT
from moderator.sql.reviews import INSERT_NEW_REVIEW_STATEMENT
import requests
from sqlalchemy import text
import streamlit as st

DISQUS_API_KEY = st.secrets.api_keys.DISQUS_API_KEY

def get_module_info_this_acad_year(acad_year: str) -> tuple[list[dict[str, str]], dict[str, str]]:
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
        module_code, module_title, module_dept, module_faculty, module_description, module_sem_data = module_info["moduleCode"], module_info["title"], module_info["department"], module_info["faculty"], module_info["description"], module_info["semesterData"]

        if not module_sem_data:
            # Semester data is empty for this module - module is not offered this academic year
            continue

        print(f"{module_code} {module_title} is offered for AY{acad_year}.")

        # Update mapping of departments to faculties for this academic year
        # NOTE: For the NUSMods dataset, it is actually possible that a department belongs to multiple faculties
        # for the same academic year. But oh well, we shall overwrite the faculty for now - it doesn't
        # really matter for our use case at the moment
        departments_to_faculties_this_ay[module_dept] = module_faculty
            
        # Update list of available modules this academic year
        available_modules_this_ay.append({
            "code": module_code,
            "title": module_title,
            "department": module_dept,
            "description": module_description
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


def update_modules_table(conn: st.connections.SQLConnection, available_modules_this_ay: list[dict[str, str]]) -> None:
    print("Updating modules table...")

    with conn.session as s:
        # Get set of module codes for the previous academic year
        # Will use this to remove modules that were offered previously, 
        # but no longer offered this academic year
        outdated_module_codes_last_ay = set(conn.query(GET_MODULE_CODES_QUERY, ttl=0)["code"])

        # For the available modules, we need to update the table
        for available_module in available_modules_this_ay:
            # Get information for this module
            available_module_code, available_module_title, available_module_dept, available_module_description = available_module["code"], available_module["title"], available_module["department"], available_module["description"]
            
            print(f"Adding / updating module information for {available_module_code}...")

            # Either insert new row for this module, or:
            # If module already exists in table, update the row
            s.execute(
                text(INSERT_NEW_MODULE_STATEMENT),
                params={
                    "code": available_module_code,
                    "title": available_module_title,
                    "department": available_module_dept,
                    "description": available_module_description
                }
            )

            # Remove this module code from outdated_module_codes_last_ay (if it did exist for the previous academic year), 
            # since this module is offered
            outdated_module_codes_last_ay.discard(available_module_code)

        # From the table, delete outdated modules that had been offered the previous academic year
        for outdated_module_code in outdated_module_codes_last_ay:
            print(f"Deleting module information for {outdated_module_code}...")

            s.execute(
                text(DELETE_EXISTING_MODULE_STATEMENT),
                params={"code": outdated_module_code}
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

    # Get set of available module codes this academic year
    available_module_codes = set(conn.query(GET_MODULE_CODES_QUERY, ttl=0)["code"])

    # Loop through each thread retrieved from Disqus
    for thread_id, reviews in thread_ids_to_posts.items():
        # Get module information
        module_name = thread_ids_to_names[thread_id]["thread_name"]
        module_code = module_name.split()[0]

        if module_code not in available_module_codes:
            # Module code does not exist in "modules" table - module is not offered this academic year. Skip reviews
            print(f"{module_name} is not offered for this academic year. Skipping reviews.")
            continue

        print(f"{module_name} is offered for this academic year. Checking reviews...")

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


def update_db() -> None:
    # Initialise connection
    conn = st.connection("nus_moderator", type="sql")

    # Fetch latest information from NUSMods API
    # Get the modules offered, the modules not offered, and the departments available this academic year
    available_modules_this_ay, departments_to_faculties_this_ay = get_module_info_this_acad_year(acad_year=ACAD_YEAR)

    # Update "departments" table in MySQL database
    update_departments_table(conn=conn, departments_to_faculties_this_ay=departments_to_faculties_this_ay)

    # Update "modules" table in MySQL database
    update_modules_table(conn=conn, available_modules_this_ay=available_modules_this_ay)

    # Deleted outdated departments from "departments" table
    delete_outdated_departments(conn=conn)

    # Retrieve reviews, by fetching latest information from Disqus API
    thread_ids_to_names, thread_ids_to_posts = use_disqus_api(short_name=DISQUS_SHORT_NAME, retrieval_limit=DISQUS_RETRIEVAL_LIMIT)

    # Update "reviews" table in MySQL database, by fetching latest information from NUSMods API
    update_reviews_table(conn=conn, thread_ids_to_names=thread_ids_to_names, thread_ids_to_posts=thread_ids_to_posts)

    print("Update completed!")