from dotenv import load_dotenv
import json
from langchain_community.document_loaders.text import TextLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.documents.base import Document
from langchain_huggingface.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
import os
import requests
import time

from helpers.config import DISQUS_SCRAPING_LIMIT, DISQUS_SHORT_NAME, DISQUS_FOLDER_NAME, THREAD_IDS_TO_NAMES_FILENAME, THREAD_IDS_TO_MESSAGES_FILENAME, DISQUS_SCRAPING_DETAILS_FILENAME, REVIEWS_FILENAME, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDINGS_MODEL_NAME, VECTOR_STORE_FOLDER_NAME, VECTOR_EMBEDDINGS_FILENAME

load_dotenv()
DISQUS_API_KEY = os.getenv("DISQUS_API_KEY")


# def get_module_to_description(acad_year: str) -> dict[str, str]:
#     # Get API endpoint according to academic year configured
#     url_endpoint = f"https://api.nusmods.com/v2/{acad_year}/moduleInfo.json"

#     # Send GET request to NUSMods and get the JSON in response
#     response = requests.get(url_endpoint)
#     module_info_json = response.json()

#     # Map each module to its description
#     module_to_description = dict()
#     for module_info in module_info_json:
#         # Get information for this module
#         module_code, module_name, module_description = module_info["moduleCode"], module_info["title"], module_info["description"]
        
#         # Concatenate module code and module name
#         full_module_name = f"{module_code}: {module_name}"

#         # Update mapping of full module name to its description
#         module_to_description[full_module_name] = module_description

#     return module_to_description


def scrape_disqus(short_name: str, scraping_limit: int, disqus_folder_name: str, thread_ids_to_names_filename: str, thread_ids_to_messages_filename: str, disqus_scraping_details_filename: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    # Get epoch
    epoch = int(time.time())
    scraping_details = {"epoch": epoch}

    thread_ids_to_names = dict()        # Maps thread ids to thread names
    thread_ids_to_messages = dict()     # Maps thread ids to lists of messages
    for endpoint in ["Threads", "Posts"]:
        print(f"Scraping {endpoint.lower()}...")

        url = f"https://disqus.com/api/3.0/forums/list{endpoint}.json"
        params = {
            "api_key": DISQUS_API_KEY,
            "forum": short_name,
            "limit": scraping_limit
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
                # If we are scraping threads
                if endpoint == "Threads":
                    # Get thread information
                    thread_name, thread_id = piece_of_info["clean_title"], piece_of_info["id"]

                    # Update mapping that links the thread ids to thread names
                    thread_ids_to_names[thread_id] = thread_name
                
                # If we are scraping posts
                else:
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

    # Create folder to store data scraped from Disqus, if it does not exist
    os.makedirs(disqus_folder_name, exist_ok=True)

    # Save mappings as JSON
    thread_ids_to_names_json = json.dumps(thread_ids_to_names, indent=4)
    with open(os.path.join(disqus_folder_name, thread_ids_to_names_filename), "w") as file:
        file.write(thread_ids_to_names_json)

    thread_ids_to_messages_json = json.dumps(thread_ids_to_messages, indent=4)
    with open(os.path.join(disqus_folder_name, thread_ids_to_messages_filename), "w") as file:
        file.write(thread_ids_to_messages_json)

    # Save scraping details as JSON
    scraping_details_json = json.dumps(scraping_details, indent=4)
    with open(os.path.join(disqus_folder_name, disqus_scraping_details_filename), "w") as file:
        file.write(scraping_details_json)

    return thread_ids_to_names, thread_ids_to_messages


def make_reviews(thread_ids_to_names: dict[str, str], thread_ids_to_messages: dict[str, list[str]], disqus_folder_name: str, reviews_filename: str) -> None:
    print("Making module reviews...")

    # Open text file to write the reviews to
    with open(os.path.join(disqus_folder_name, reviews_filename), "a") as file:
        # Loop through each thread
        for thread_id, thread_messages in thread_ids_to_messages.items():
            # Construct reviews for the module, in paragraph format
            module_name = thread_ids_to_names[thread_id]
            print(f"Making reviews for {module_name}...")

            module_reviews = "\n".join(thread_messages)
            module_name_and_reviews = f"{module_name}\n{module_reviews}\n\n"

            # Write to text file
            file.write(module_name_and_reviews)


def make_documents(disqus_folder_name: str, reviews_filename: str, chunk_size: int, chunk_overlap: int) -> list[Document]:
    print("Making document chunks...")

    # Load the review document
    loader = TextLoader(os.path.join(disqus_folder_name, reviews_filename), encoding="utf-8")
    document = loader.load()
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    document_chunks = text_splitter.split_documents(document)
    
    return document_chunks


def make_and_save_embeddings(document_chunks: list[Document], embeddings_model_name: str, vector_store_folder_name: str, vector_embeddings_filename: str) -> None:
    # Create folder for vector store, if it does not exist
    os.makedirs(vector_store_folder_name, exist_ok=True)

    # Make vector store
    print("Making embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
    vectorstore = FAISS.from_documents(document_chunks, embeddings)

    # Save vector store
    print("Saving embeddings...")
    vectorstore.save_local(folder_path=vector_store_folder_name, index_name=vector_embeddings_filename)


def ingest():
    # Scrape Disqus for module reviews
    thread_ids_to_names, thread_ids_to_messages = scrape_disqus(
        short_name=DISQUS_SHORT_NAME,
        scraping_limit=DISQUS_SCRAPING_LIMIT,
        disqus_folder_name=DISQUS_FOLDER_NAME,
        thread_ids_to_names_filename=THREAD_IDS_TO_NAMES_FILENAME,
        thread_ids_to_messages_filename=THREAD_IDS_TO_MESSAGES_FILENAME,
        disqus_scraping_details_filename=DISQUS_SCRAPING_DETAILS_FILENAME
    )

    # Save reviews in text format
    make_reviews(
        thread_ids_to_names=thread_ids_to_names,
        thread_ids_to_messages=thread_ids_to_messages,
        disqus_folder_name=DISQUS_FOLDER_NAME,
        reviews_filename=REVIEWS_FILENAME
    )

    # Make document chunks
    document_chunks = make_documents(
        disqus_folder_name=DISQUS_FOLDER_NAME,
        reviews_filename=REVIEWS_FILENAME,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    # Create a vector store containing embeddings of these chunks, before saving it
    make_and_save_embeddings(
        document_chunks=document_chunks,
        embeddings_model_name=EMBEDDINGS_MODEL_NAME,
        vector_store_folder_name=VECTOR_STORE_FOLDER_NAME,
        vector_embeddings_filename=VECTOR_EMBEDDINGS_FILENAME
    )