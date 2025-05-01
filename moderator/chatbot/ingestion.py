from dotenv import load_dotenv
import json
from langchain_chroma import Chroma
from langchain_community.document_loaders.text import TextLoader
from langchain_core.documents.base import Document
from langchain_core.load import dumps, load
from langchain_core.vectorstores import VectorStore
from langchain_huggingface.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
import os
import requests
import time

from moderator.config import ACAD_YEAR, DISQUS_RETRIEVAL_LIMIT, DISQUS_SHORT_NAME, DISQUS_FOLDER_NAME, THREAD_IDS_TO_NAMES_AND_LINKS_FILENAME, THREAD_IDS_TO_MESSAGES_FILENAME, DISQUS_RETRIEVAL_DETAILS_FILENAME, MODULE_DOCUMENTS_FILENAME, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDINGS_MODEL_NAME, VECTOR_STORE_FOLDER_NAME, VECTOR_EMBEDDINGS_FILENAME

load_dotenv()
DISQUS_API_KEY = os.getenv("DISQUS_API_KEY")


def use_disqus_api(short_name: str, retrieval_limit: int, disqus_folder_name: str, thread_ids_to_names_and_links_filename: str, thread_ids_to_messages_filename: str, disqus_retrieval_details_filename: str) -> tuple[dict[str, dict[str, str]], dict[str, list[str]]]:
    # Get epoch
    epoch = int(time.time())
    retrieval_details = {"epoch": epoch}

    thread_ids_to_names_and_links = dict()        # Maps thread ids to thread names and thread links
    thread_ids_to_messages = dict()               # Maps thread ids to lists of messages
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
                    thread_name, thread_id, thread_link = piece_of_info["clean_title"], piece_of_info["id"], piece_of_info["link"]

                    # Update mapping that links the thread ids to thread names and thread links
                    thread_ids_to_names_and_links[thread_id] = {
                        "thread_name": thread_name,
                        "thread_link": thread_link
                    }
                
                else:
                    # If we are retrieving posts
                    # Get post information
                    thread_id_containing_post, post_message = piece_of_info["thread"], piece_of_info["raw_message"]

                    # Update mapping that links the thread ids to lists of messages
                    if thread_id_containing_post not in thread_ids_to_messages:
                        thread_ids_to_messages[thread_id_containing_post] = list()
                    
                    thread_ids_to_messages[thread_id_containing_post].append(post_message)
                
            # Check if there is a next batch
            has_next = response_json["cursor"]["hasNext"]

            # Update cursor to the next one if there is a next batch
            if has_next:
                params["cursor"] = response_json["cursor"]["next"]

    # Create folder to store data obtained from Disqus API, if it does not exist
    os.makedirs(disqus_folder_name, exist_ok=True)

    # Save mappings as JSON
    thread_ids_to_names_and_links_json = json.dumps(thread_ids_to_names_and_links, indent=4)
    with open(os.path.join(disqus_folder_name, thread_ids_to_names_and_links_filename), "w") as file:
        file.write(thread_ids_to_names_and_links_json)

    thread_ids_to_messages_json = json.dumps(thread_ids_to_messages, indent=4)
    with open(os.path.join(disqus_folder_name, thread_ids_to_messages_filename), "w") as file:
        file.write(thread_ids_to_messages_json)

    # Save retrieval details as JSON
    retrieval_details_json = json.dumps(retrieval_details, indent=4)
    with open(os.path.join(disqus_folder_name, disqus_retrieval_details_filename), "w") as file:
        file.write(retrieval_details_json)

    return thread_ids_to_names_and_links, thread_ids_to_messages


def make_module_textual_info(thread_ids_to_names_and_links: dict[str, dict[str, str]], thread_ids_to_messages: dict[str, list[str]], acad_year: str, disqus_folder_name: str, module_documents_filename: str) -> list[Document]:
    print("Making module textual info...")

    # Loop through each thread
    module_documents = list()
    for thread_id, thread_messages in thread_ids_to_messages.items():
        module_name, module_link = thread_ids_to_names_and_links[thread_id]["thread_name"], thread_ids_to_names_and_links[thread_id]["thread_link"]
        print(f"Making textual info for {module_name}...")

        # Use NUSMods API to get description of module for the chosen academic year
        module_code = module_name.split()[0]
        nusmods_endpoint_url = f"https://api.nusmods.com/v2/{acad_year}/modules/{module_code}.json"
        response = requests.get(url=nusmods_endpoint_url)
        
        if response.status_code == 200:
            # Successful GET request. Module exists for this academic year
            # Get official description of module
            module_description = response.json()["description"]

            # Combine all the reviews (messages) for this module
            module_reviews = "\n".join(thread_messages)

            # Combine description of module + reviews of module to make a document
            module_text = f"{module_description}\n{module_reviews}"
            module_document = Document(
                page_content=module_text,
                metadata={
                    "module_code": module_code,
                    "module_name": module_name,
                    "module_link": module_link
                }
            )
            module_documents.append(module_document)
    
    # Save module documents as JSON
    module_documents_json = dumps(module_documents, pretty=True)
    with open(os.path.join(disqus_folder_name, module_documents_filename), "w") as file:
        file.write(module_documents_json)
       
    return module_documents


def make_documents(disqus_folder_name: str, module_documents_filename: str, chunk_size: int, chunk_overlap: int) -> list[Document]:
    print("Making document chunks...")

    # Load the list of module documents
    with open(os.path.join(disqus_folder_name, module_documents_filename), "r") as file:
        documents = load(json.load(file))
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    document_chunks = text_splitter.split_documents(documents)
    
    return document_chunks


def make_and_save_embeddings(document_chunks: list[Document], embeddings_model_name: str, vector_store_folder_name: str, vector_embeddings_filename: str) -> VectorStore:
    # Create folder for vector store, if it does not exist
    os.makedirs(vector_store_folder_name, exist_ok=True)

    # Make and save vector store
    print("Making embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
    vectorstore = Chroma.from_documents(
        documents=document_chunks,
        embedding=embeddings,
        collection_name=vector_embeddings_filename,
        persist_directory=vector_store_folder_name
    )

    return vectorstore


def ingest():
    # Retrieve module reviews from Disqus API
    thread_ids_to_names_and_links, thread_ids_to_messages = use_disqus_api(
        short_name=DISQUS_SHORT_NAME,
        retrieval_limit=DISQUS_RETRIEVAL_LIMIT,
        disqus_folder_name=DISQUS_FOLDER_NAME,
        thread_ids_to_names_and_links_filename=THREAD_IDS_TO_NAMES_AND_LINKS_FILENAME,
        thread_ids_to_messages_filename=THREAD_IDS_TO_MESSAGES_FILENAME,
        disqus_retrieval_details_filename=DISQUS_RETRIEVAL_DETAILS_FILENAME
    )

    # with open(r"disqus\thread_ids_to_names_and_links.json", "r") as file:
    #     thread_ids_to_names_and_links = json.load(file)

    # with open(r"disqus\thread_ids_to_messages.json", "r") as file:
    #     thread_ids_to_messages = json.load(file)

    # Save textual info of modules, in text format
    make_module_textual_info(
        thread_ids_to_names_and_links=thread_ids_to_names_and_links,
        thread_ids_to_messages=thread_ids_to_messages,
        acad_year=ACAD_YEAR,
        disqus_folder_name=DISQUS_FOLDER_NAME,
        module_documents_filename=MODULE_DOCUMENTS_FILENAME
    )

    # Make document chunks
    document_chunks = make_documents(
        disqus_folder_name=DISQUS_FOLDER_NAME,
        module_documents_filename=MODULE_DOCUMENTS_FILENAME,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    # Create a vector store containing embeddings of these chunks, before saving it
    vectorstore = make_and_save_embeddings(
        document_chunks=document_chunks,
        embeddings_model_name=EMBEDDINGS_MODEL_NAME,
        vector_store_folder_name=VECTOR_STORE_FOLDER_NAME,
        vector_embeddings_filename=VECTOR_EMBEDDINGS_FILENAME
    )

    print("Ingestion completed!")