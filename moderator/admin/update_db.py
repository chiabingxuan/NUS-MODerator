from dotenv import load_dotenv
import json
from moderator.config import ACAD_YEAR, DISQUS_RETRIEVAL_LIMIT, DISQUS_SHORT_NAME
from moderator.sql.update_departments import COUNT_EXISTING_ROWS_FOR_DEPARTMENT_QUERY, INSERT_NEW_DEPARTMENT_STATEMENT, UPDATE_EXISTING_DEPARTMENT_STATEMENT, DELETE_OUTDATED_DEPARTMENTS_STATEMENT
from moderator.sql.update_modules import COUNT_EXISTING_ROWS_FOR_MODULE_QUERY, INSERT_NEW_MODULE_STATEMENT, UPDATE_EXISTING_MODULE_STATEMENT, DELETE_EXISTING_MODULE_STATEMENT
from moderator.sql.update_reviews import COUNT_EXISTING_ROWS_FOR_REVIEW_QUERY, INSERT_NEW_REVIEW_STATEMENT, UPDATE_EXISTING_REVIEW_STATEMENT
import mysql.connector
import os
import requests

load_dotenv()
DISQUS_API_KEY = os.getenv("DISQUS_API_KEY")
MYSQL_DB_NAME = os.getenv("MYSQL_DB_NAME")
MYSQL_USERNAME = os.getenv("MYSQL_USERNAME")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

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


def update_departments_table(conn: mysql.connector.connection_cext.CMySQLConnection, department: str, faculty: str) -> None:
    # Create cursor
    cur = conn.cursor()
    
    # Get number of existing rows corresponding to this module, from "modules" table (either 0 or 1)
    cur.execute(
        COUNT_EXISTING_ROWS_FOR_DEPARTMENT_QUERY,
        (department,)
    )

    [(num_existing_rows_for_dept,),] = cur.fetchall()

    if num_existing_rows_for_dept == 0:
        # Department does not exist in "department" table - department is new
        # Insert new row for this department
        cur.execute(
            INSERT_NEW_DEPARTMENT_STATEMENT,
            (
                department,
                faculty
            )
        )
    
    else:
        # Department already exists in "departments" table
        # Update the row for this department
        cur.execute(
            UPDATE_EXISTING_DEPARTMENT_STATEMENT,
            (
                faculty,
                department
            )
        )
    
    conn.commit()

    # Close cursor
    cur.close()


def delete_outdated_departments(conn: mysql.connector.connection_cext.CMySQLConnection) -> None:
    print("Deleting outdated departments...")

    # Create cursor
    cur = conn.cursor()

    # Delete outdated department information from "departments" table
    # If department does not appear in "modules" table, we take it to be outdated
    cur.execute(DELETE_OUTDATED_DEPARTMENTS_STATEMENT)
    print(f"Departments deleted: {cur.rowcount}")

    conn.commit()
    

def update_modules_table(conn: mysql.connector.connection_cext.CMySQLConnection, acad_year: str) -> None:
    mods_deleted = 0
    mods_updated = 0
    # Create cursor
    cur = conn.cursor()

    print("Updating modules table...")

    # Use NUSMods API to get detailed information of modules, for the chosen academic year
    nusmods_endpoint_url = f"https://api.nusmods.com/v2/{acad_year}/moduleInfo.json"
    response = requests.get(url=nusmods_endpoint_url)

    # Based on the modules offered for this academic year, add new modules and update existing ones
    if response.status_code == 200:
        # Successful GET request
        module_infos = response.json()
        
        # Loop through each module retrieved from NUSMods API
        for module_info in module_infos:
            # Get details of this module
            module_code, module_title, module_dept, module_faculty, module_description, module_sem_data = module_info["moduleCode"], module_info["title"], module_info["department"], module_info["faculty"], module_info["description"], module_info["semesterData"]

            if not module_sem_data:
                # Semester data is empty for this module - module is not offered this academic year
                print(f"{module_code} {module_title} is not offered for AY{acad_year}.")

                # Delete module information from "modules" table
                cur.execute(
                    DELETE_EXISTING_MODULE_STATEMENT,
                    (module_code,)
                )
                
                if cur.rowcount > 0:
                    mods_deleted += 1

                conn.commit()

                continue

            print(f"{module_code} {module_title} is offered for AY{acad_year}. Updating information...")

            # Update department information in "departments" table
            update_departments_table(conn=conn, department=module_dept, faculty=module_faculty)

            # Get number of existing rows corresponding to this module, from "modules" table (either 0 or 1)
            cur.execute(
                COUNT_EXISTING_ROWS_FOR_MODULE_QUERY,
                (module_code,)
            )

            [(num_existing_rows_for_module,),] = cur.fetchall()

            if num_existing_rows_for_module == 0:
                # Module code does not exist in "modules" table - module is new
                # Insert new row for this module
                cur.execute(
                    INSERT_NEW_MODULE_STATEMENT,
                    (
                        module_code,
                        module_title,
                        module_dept,
                        module_description
                    )
                )
            
            else:
                # Module code already exists in "modules" table
                # Update the row for this module
                cur.execute(
                    UPDATE_EXISTING_MODULE_STATEMENT,
                    (
                        module_title,
                        module_dept,
                        module_description,
                        module_code
                    )
                )
            
                if cur.rowcount > 0:
                    mods_updated += 1

            conn.commit()

    print(f"Mods deleted: {mods_deleted}")
    print(f"Mods updated: {mods_updated}")

    # Close cursor
    cur.close()


def update_reviews_table(conn: mysql.connector.connection_cext.CMySQLConnection, thread_ids_to_names: dict[str, dict[str, str]], thread_ids_to_posts: dict[str, list[dict[str, str]]]) -> None:
    # Create cursor
    cur = conn.cursor()

    print("Updating reviews table...")

    # Loop through each thread retrieved from Disqus
    for thread_id, reviews in thread_ids_to_posts.items():
        # Get module information
        module_name = thread_ids_to_names[thread_id]["thread_name"]
        module_code = module_name.split()[0]

        # Get number of existing rows corresponding to this module, from "modules" table (either 0 or 1)
        cur.execute(
            COUNT_EXISTING_ROWS_FOR_MODULE_QUERY,
            (module_code,)
        )

        [(num_existing_rows_for_module,),] = cur.fetchall()

        if num_existing_rows_for_module == 0:
            # Module code does not exist in "modules" table - module is not offered this academic year. Skip reviews
            print(f"{module_name} is not offered for this academic year. Skipping reviews.")
            continue

        print(f"{module_name} is offered for this academic year. Checking reviews...")

        # Loop through each review for this module
        for review in reviews:
            # Get review information
            review_id, review_message = review["post_id"], review["post_message"]

            # Get number of existing rows corresponding to this review, from "reviews" table (either 0 or 1)
            cur.execute(
                COUNT_EXISTING_ROWS_FOR_REVIEW_QUERY,
                (review_id,)
            )

            [(num_existing_rows_for_review,),] = cur.fetchall()

            if num_existing_rows_for_review == 0:
                # Review ID does not exist in "reviews" table - review is new
                # Insert new row for this review
                cur.execute(
                    INSERT_NEW_REVIEW_STATEMENT,
                    (
                        review_id,
                        module_code,
                        review_message
                    )
                )
            
            else:
                # Review ID already exists in "reviews" table
                # Update the row for this review
                cur.execute(
                    UPDATE_EXISTING_REVIEW_STATEMENT,
                    (
                        module_code,
                        review_message,
                        review_id
                    )
                )
            
            conn.commit()

    # Close cursor
    cur.close()


def update_db():
    # Connect to MySQL database
    conn = mysql.connector.connect(
        user=MYSQL_USERNAME,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB_NAME,
        host="localhost",
        port=3306
    )

    # Update "modules" table in MySQL database, by fetching latest information from NUSMods API
    update_modules_table(conn=conn, acad_year=ACAD_YEAR)

    # Deleted outdated departments from "departments" table
    delete_outdated_departments(conn=conn)

    # Retrieve reviews, by fetching latest information from Disqus API
    thread_ids_to_names, thread_ids_to_posts = use_disqus_api(short_name=DISQUS_SHORT_NAME, retrieval_limit=DISQUS_RETRIEVAL_LIMIT)

    # Update "reviews" table in MySQL database, by fetching latest information from NUSMods API
    update_reviews_table(conn=conn, thread_ids_to_names=thread_ids_to_names, thread_ids_to_posts=thread_ids_to_posts)

    # Close connection
    conn.close()

    print("Update completed!")