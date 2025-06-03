import datetime
from langchain_core.documents.base import Document
from langchain_core.vectorstores import VectorStore
from langchain_huggingface.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from moderator.config import DISQUS_RETRIEVAL_LIMIT, DISQUS_SHORT_NAME, SEMESTER_LIST, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDINGS_MODEL_NAME, PINECONE_BATCH_SIZE, BUS_STOPS_URL, BUS_ROUTES_URL
from moderator.sql.acad_years import INSERT_NEW_ACAD_YEAR_STATEMENT
from moderator.sql.bus_numbers import GET_BUS_NUMBERS_QUERY, INSERT_BUS_NUMBER_STATEMENT, DELETE_BUS_NUMBER_STATEMENT
from moderator.sql.bus_routes import GET_BUS_ROUTES_QUERY, INSERT_BUS_ROUTE_STATEMENT, DELETE_BUS_ROUTE_STATEMENT
from moderator.sql.bus_stops import GET_BUS_STOPS_QUERY, INSERT_BUS_STOP_STATEMENT, DELETE_BUS_STOP_STATEMENT
from moderator.sql.departments import INSERT_NEW_DEPARTMENT_STATEMENT, DELETE_OUTDATED_DEPARTMENTS_STATEMENT
from moderator.sql.majors import GET_EXISTING_MAJOR_QUERY, INSERT_NEW_MAJOR_QUERY
from moderator.sql.modules import GET_MODULE_CODES_QUERY, INSERT_NEW_MODULE_STATEMENT
from moderator.sql.offers import INSERT_NEW_OFFER_STATEMENT
from moderator.sql.reviews import INSERT_NEW_REVIEW_STATEMENT
from moderator.sql.users import GET_EXISTING_USER_QUERY, MAKE_USER_ADMIN_STATEMENT
from moderator.sql.vector_store_update import GET_MODULE_COMBINED_REVIEWS_QUERY
import requests
import streamlit as st
from sqlalchemy import text

DISQUS_API_KEY = st.secrets["DISQUS_API_KEY"]
PINECONE_INDEX_NAME = st.secrets["PINECONE_INDEX_NAME"]

# Base class for a user of the app
class User(object):
    def __init__(self, username: str, first_name: str, last_name: str, matriculation_ay: str, major: str, reg_datetime: datetime.datetime, user_enrollments: dict[str, dict[str, list[dict[str, str | int]]]]) -> None:
        self._username = username
        self._first_name = first_name
        self._last_name = last_name
        self._matriculation_ay = matriculation_ay
        self._major = major
        self._reg_datetime = reg_datetime
        self._user_enrollments = user_enrollments
    

    @property
    def username(self) -> str:
        return self._username
    

    @property
    def first_name(self) -> str:
        return self._first_name
    

    @property
    def last_name(self) -> str:
        return self._last_name
    

    @property
    def matriculation_ay(self) -> str:
        return self._matriculation_ay
    

    @property
    def major(self) -> str:
        return self._major
    

    @property
    def reg_datetime(self) -> datetime.datetime:
        return self._reg_datetime
    

    @property
    def user_enrollments(self) -> dict[str, dict[str, list[dict[str, str | int]]]]:
        return self._user_enrollments
    

    @user_enrollments.setter
    def user_enrollments(self, new_user_enrollments: dict[str, dict[str, list[dict[str, str | int]]]]) -> None:
        self._user_enrollments = new_user_enrollments


# Admin class inherits from base User class
class Admin(User):
    def __init__(self, username: str, first_name: str, last_name: str, matriculation_ay: str, major: str, reg_datetime: datetime.datetime, user_enrollments: dict[str, dict[str, list[dict[str, str | int]]]]) -> None:
        super().__init__(
            username=username,
            first_name=first_name,
            last_name=last_name,
            matriculation_ay=matriculation_ay,
            major=major,
            reg_datetime=reg_datetime,
            user_enrollments=user_enrollments
        )


    ### ACADEMIC DATABASE UPDATE ###
    # Admin can update the academic-related tables in PostgreSQL database
    def get_module_info_this_acad_year(self, acad_year: str) -> tuple[list[dict[str, int | str | list[int]]], dict[str, str]]:
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
            
            # Module is year-long if it is either explicitly mentioned in the attributes, or it is a FYP
            if "attributes" not in module_info:
                module_is_year_long = False
            
            else:
                module_attributes = module_info["attributes"]
                module_is_year_long = module_attributes.get("year", False)
                module_is_fyp = module_attributes.get("fyp", False)
                if module_is_fyp:
                    module_is_year_long = True

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
                "sems_offered": sems_offered,
                "is_year_long": module_is_year_long
            })

        return available_modules_this_ay, departments_to_faculties_this_ay
        
        
    def update_departments_table(self, conn: st.connections.SQLConnection, departments_to_faculties_this_ay: dict[str, str]) -> None:
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


    def update_modules_table(self, conn: st.connections.SQLConnection, available_modules_this_ay: list[dict[str, int | str | list[int]]]) -> None:
        print("Updating modules table...")

        with conn.session as s:
            # For the available modules this academic year, we need to update the table
            for available_module in available_modules_this_ay:
                # Get information for this module
                available_module_code, available_module_title, available_module_dept, available_module_description, available_module_num_mcs, available_module_is_year_long = available_module["code"], available_module["title"], available_module["department"], available_module["description"], available_module["num_mcs"], available_module["is_year_long"]
                
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
                        "num_mcs": available_module_num_mcs,
                        "is_year_long": available_module_is_year_long
                    }
                )
            
            s.commit()


    def delete_outdated_departments(self, conn: st.connections.SQLConnection) -> None:
        print("Deleting outdated departments...")

        # Delete outdated department information from "departments" table
        # If department does not appear in "modules" table, we take it to be outdated
        with conn.session as s:
            s.execute(text(DELETE_OUTDATED_DEPARTMENTS_STATEMENT))

            s.commit()
            

    def use_disqus_api(self, short_name: str, retrieval_limit: int) -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
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


    def update_reviews_table(self, conn: st.connections.SQLConnection, thread_ids_to_names: dict[str, dict[str, str]], thread_ids_to_posts: dict[str, list[dict[str, str]]]) -> None:
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

    def update_acad_years_table(self, conn: st.connections.SQLConnection, acad_year: str) -> None:
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


    def update_offers_table(self, conn: st.connections.SQLConnection, acad_year: str, available_modules_this_ay: list[dict[str, int | str | list[int]]], semester_list: list[dict[str, int | str]]) -> None:
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


    # This updates the departments, modules, reviews, acad_years and offers tables
    # Useful when NUSMods data for the new AY has just been released        
    def update_acad_db(self, conn: st.connections.SQLConnection, acad_year: str) -> None:
        # Fetch latest information from NUSMods API
        # Get the modules offered, the modules not offered, and the departments available this academic year
        available_modules_this_ay, departments_to_faculties_this_ay = self.get_module_info_this_acad_year(acad_year=acad_year)

        # Update "departments" table in PostgreSQL database
        self.update_departments_table(conn=conn, departments_to_faculties_this_ay=departments_to_faculties_this_ay)

        # Update "modules" table in PostgreSQL database
        self.update_modules_table(conn=conn, available_modules_this_ay=available_modules_this_ay)

        # Deleted outdated departments from "departments" table
        self.delete_outdated_departments(conn=conn)

        # Retrieve reviews, by fetching latest information from Disqus API
        thread_ids_to_names, thread_ids_to_posts = self.use_disqus_api(short_name=DISQUS_SHORT_NAME, retrieval_limit=DISQUS_RETRIEVAL_LIMIT)

        # Update "reviews" table in PostgreSQL database, by fetching latest information from NUSMods API
        self.update_reviews_table(conn=conn, thread_ids_to_names=thread_ids_to_names, thread_ids_to_posts=thread_ids_to_posts)

        # Update "acad_years" table in PostgreSQL database
        self.update_acad_years_table(conn=conn, acad_year=acad_year)

        # Update "offers" table in PostgreSQL database
        self.update_offers_table(conn=conn, acad_year=acad_year, available_modules_this_ay=available_modules_this_ay, semester_list=SEMESTER_LIST)

        print("Update completed!")


    ### VECTOR STORE UPDATE ###
    # Admin can update the Pinecone vector store containing the vector embeddings for the chatbot
    def make_module_textual_info(self, conn: st.connections.SQLConnection, acad_year: str) -> list[Document]:
        print("Making module textual info...")

        # Query the official module description and combined reviews, for each module
        rows_queried = conn.query(
            GET_MODULE_COMBINED_REVIEWS_QUERY,
            params={
                "acad_year": acad_year
            },
            ttl=0
        ).values.tolist()

        # Loop through each row
        module_documents = list()
        for module_code, module_title, module_description, module_combined_text in rows_queried:
            # Concatenate module code and title to get the full module name
            module_name = f"{module_code} {module_title}"

            # Get link to NUSMods page for the module
            module_link = f"https://nusmods.com/courses/{module_code}"
                    
            print(f"Making textual info for {module_name}...")

            # Combine description of module + combined module reviews (if any) to make a document
            module_text_with_description = module_description
            if module_combined_text is not None:
                module_text_with_description = f"{module_text_with_description}\n{module_combined_text}"

            module_document = Document(
                page_content=module_text_with_description,
                metadata={
                    "module_code": module_code,
                    "module_name": module_name,
                    "module_link": module_link
                }
            )
            module_documents.append(module_document)

        return module_documents


    def make_documents(self, module_documents: list[Document], chunk_size: int, chunk_overlap: int) -> list[Document]:
        print("Making document chunks...")

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        document_chunks = text_splitter.split_documents(module_documents)
        
        return document_chunks


    def make_and_save_embeddings(self, document_chunks: list[Document], embeddings_model_name: str, batch_size: int) -> VectorStore:
        # Make and store vector store in Pinecone
        print("Making embeddings...")
        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
        vector_store = PineconeVectorStore(embedding=embeddings, index_name=PINECONE_INDEX_NAME)

        # First delete all the existing vectors in the vector store
        vector_store.delete(delete_all=True)

        # Add documents batchwise to avoid exceeding upsert limit
        num_documents = len(document_chunks)
        start_index = 0
        while start_index < num_documents:
            document_chunks_in_batch = document_chunks[start_index: start_index + batch_size]
            vector_store.add_documents(documents=document_chunks_in_batch)
            
            # Increment start_index
            start_index += batch_size

        return vector_store
    

    # Will format data from reviews table into documents, before chunking and embedding them
    # Useful when NUSMods data for the new AY has just been released
    def update_vector_store(self, conn: st.connections.SQLConnection, acad_year: str) -> None:
        # Get textual info of modules, in the form of documents
        module_documents = self.make_module_textual_info(
            conn=conn,
            acad_year=acad_year
        )

        # Make document chunks
        document_chunks = self.make_documents(
            module_documents=module_documents,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        # Create a vector store containing embeddings of these chunks, before storing it in Pinecone
        vector_store = self.make_and_save_embeddings(
            document_chunks=document_chunks,
            embeddings_model_name=EMBEDDINGS_MODEL_NAME,
            batch_size=PINECONE_BATCH_SIZE
        )

        print("Completed the vector store update!")


    ### BUS DATABASE UPDATE ###
    # Admin can update the bus-related tables in PostgreSQL database
    def update_bus_stops_table(self, conn: st.connections.SQLConnection) -> None:
        # Get list of existing bus stop codes in table
        existing_bus_stop_codes = list(conn.query(GET_BUS_STOPS_QUERY, ttl=0)["code_name"])

        # Get bus stop data - a list of dictionaries
        bus_stops = requests.get(url=BUS_STOPS_URL).json()

        with conn.session as s:
            # Loop through each bus stop requested
            new_bus_stop_codes = set()
            new_bus_stop_info = list()
            for bus_stop in bus_stops:
                # Get information for this bus stop
                bus_stop_code, bus_stop_name, bus_stop_lat, bus_stop_long = bus_stop["name"], bus_stop["caption"], bus_stop["latitude"], bus_stop["longitude"]

                # Add bus stop code to the new set
                new_bus_stop_codes.add(bus_stop_code)

                # Append bus stop info to the new list
                new_bus_stop_info.append((bus_stop_code, bus_stop_name, bus_stop_lat, bus_stop_long))

            # Loop through each existing bus stop
            for existing_bus_stop_code in existing_bus_stop_codes:
                if existing_bus_stop_code not in new_bus_stop_codes:
                    # Bus stop code exists in table but does not exist in the new batch of bus stops
                    # Delete this bus stop code from table
                    s.execute(
                        text(DELETE_BUS_STOP_STATEMENT),
                        params={
                            "code_name": existing_bus_stop_code
                        }
                    )

            # Upsert new bus stops into table
            for bus_stop_code, bus_stop_name, bus_stop_lat, bus_stop_long in new_bus_stop_info:
                s.execute(
                    text(INSERT_BUS_STOP_STATEMENT),
                    params={
                        "code_name": bus_stop_code,
                        "display_name": bus_stop_name,
                        "latitude": bus_stop_lat,
                        "longitude": bus_stop_long
                    }
                )
            
            s.commit()

            
    def update_bus_nums_and_bus_routes_table(self, conn: st.connections.SQLConnection) -> None:
        # Get list of existing bus numbers in bus_numbers table
        existing_bus_nums = list(conn.query(GET_BUS_NUMBERS_QUERY, ttl=0)["bus_num"])

        # Get list of existing (bus_num, bus_stop_code, seq_num) triples from bus_routes table
        existing_bus_routes = conn.query(GET_BUS_ROUTES_QUERY, ttl=0).values.tolist()

        # Get bus route data - a dictionary
        # Keys: Bus numbers
        # Values: List of bus stops (dictionaries) in sequential order of route
        bus_route_data = requests.get(url=BUS_ROUTES_URL).json()
        
        with conn.session as s:
            # Loop through each bus number requested
            new_bus_nums, new_bus_routes = set(), set()
            for bus_num, bus_num_route in bus_route_data.items():
                # Add bus number to the new set
                new_bus_nums.add(bus_num)

                for bus_stop in bus_num_route:
                    # Get route information for the bus stop
                    # Seq num: Represents position of the bus stop in the route
                    # If seq num is 32767, bus stop is the terminal bus stop
                    bus_stop_seq_num, bus_stop_code = bus_stop["seq"], bus_stop["busstopcode"]

                    # Add (bus_num, bus_stop_code, seq_num) triple to the new set
                    new_bus_routes.add((bus_num, bus_stop_code, bus_stop_seq_num))

            # Loop through each existing bus number
            for existing_bus_num in existing_bus_nums:
                if existing_bus_num not in new_bus_nums:
                    # Bus number exists in bus_numbers table but does not exist in the new batch of bus numbers
                    # Delete this bus number from bus_numbers table
                    s.execute(
                        text(DELETE_BUS_NUMBER_STATEMENT),
                        params={
                            "bus_num": existing_bus_num
                        }
                    )
            
            # Loop through each existing (bus_num, bus_stop_code, seq_num) triple
            for existing_bus_num, existing_bus_stop_code, existing_bus_stop_seq_num in existing_bus_routes:
                if (existing_bus_num, existing_bus_stop_code, existing_bus_stop_seq_num) not in new_bus_routes:
                    # (bus_num, bus_stop_code, seq_num) triple exists in bus_routes table but does not exist in the new batch of (bus_num, bus_stop_code, seq_num) triples
                    # Delete the corresponding bus route from bus_routes table
                    s.execute(
                        text(DELETE_BUS_ROUTE_STATEMENT),
                        params={
                            "bus_num": existing_bus_num,
                            "bus_stop_code": existing_bus_stop_code,
                            "seq_num": existing_bus_stop_seq_num
                        }
                    )

            # Insert new bus numbers into bus_numbers table
            for bus_num in new_bus_nums:
                s.execute(
                    text(INSERT_BUS_NUMBER_STATEMENT),
                    params={
                        "bus_num": bus_num
                    }
                )

            # Insert new route information into bus_routes table, or update the row if it already exists
            for bus_num, bus_stop_code, bus_stop_seq_num in new_bus_routes:
                s.execute(
                    text(INSERT_BUS_ROUTE_STATEMENT),
                    params={
                        "bus_num": bus_num,
                        "bus_stop_code": bus_stop_code,
                        "seq_num": bus_stop_seq_num
                    }
                )

            s.commit()


    # This updates the bus_stops, bus_numbers and bus_routes tables
    # Useful when changes to the NUS bus system have been announced
    def update_bus_db(self, conn: st.connections.SQLConnection) -> None:
        # Update bus stops
        self.update_bus_stops_table(conn=conn)

        # Update bus numbers and bus routes
        self.update_bus_nums_and_bus_routes_table(conn=conn)


    ### ADD MAJORS ###
    # Admin can add a new major into the database
    # If the action is successful, this returns True, False otherwise
    def add_new_major(self, conn: st.connections.SQLConnection, major: str, department: str) -> bool:
        # Query the existing major information from database, if any
        existing_major_info_df = conn.query(GET_EXISTING_MAJOR_QUERY, params={"major": major}, ttl=0)

        if len(existing_major_info_df) > 0:
            # Major already exists in database - return a failed response
            return False

        # Major does not exist yet
        # Add this major
        with conn.session as s:
            s.execute(
                text(INSERT_NEW_MAJOR_QUERY),
                params={
                    "major": major,
                    "department": department
                }
            )

            s.commit()

        return True
    

    ### GRANT ADMIN RIGHTS ###
    # Admin can grant admin rights to a selected user
    # If the action is successful, this returns True, False otherwise
    def make_user_admin(self, conn: st.connections.SQLConnection, username: str) -> bool:
        # Query the existing user information from database, if any
        existing_user_info_df = conn.query(GET_EXISTING_USER_QUERY, params={"username": username}, ttl=0)

        if len(existing_user_info_df) == 0:
            # Username does not exist in database - return a failed response
            return False

        # Username exists
        # Give user admin rights, using his / her username
        with conn.session as s:
            s.execute(
                text(MAKE_USER_ADMIN_STATEMENT),
                params={
                    "username": username
                }
            )

            s.commit()
        
        return True
    

