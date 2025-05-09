import json
from langchain_core.documents.base import Document
from langchain_core.load import dumps, load
from langchain_core.vectorstores import VectorStore
from langchain_huggingface.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from moderator.config import DATA_FOLDER_PATH, DETAILS_FILENAME, MODULE_DOCUMENTS_FILENAME, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDINGS_MODEL_NAME, PINECONE_BATCH_SIZE
from moderator.sql.chatbot_setup import GET_MODULE_COMBINED_REVIEWS_QUERY
import psycopg2
import os
import streamlit as st
import time

PGSQL_DB_NAME = st.secrets["connections"]["nus_moderator"]["database"]
PGSQL_USERNAME = st.secrets["connections"]["nus_moderator"]["username"]
PGSQL_PASSWORD = st.secrets["connections"]["nus_moderator"]["password"]
HOST = st.secrets["connections"]["nus_moderator"]["host"]
PORT = st.secrets["connections"]["nus_moderator"]["port"]
PINECONE_INDEX_NAME = st.secrets["PINECONE_INDEX_NAME"]

def make_module_textual_info(conn: psycopg2.extensions.connection, data_folder_path: str, module_documents_filename: str) -> list[Document]:
    print("Making module textual info...")

    # Create cursor
    cur = conn.cursor()

    # Query the official module description and combined reviews, for each module
    cur.execute(GET_MODULE_COMBINED_REVIEWS_QUERY)
    rows_queried = cur.fetchall()

    # Loop through each row
    module_documents = list()
    for module_code, module_title, module_description, module_combined_text in rows_queried:
        # Concatenate module code and title to get the full module name
        module_name = f"{module_code} {module_title}"

        # Get link to NUSMods page for the module
        module_link = f"https://nusmods.com/courses/{module_code}"
                
        print(f"Making textual info for {module_name}...")

        # Combine description of module + reviews of module to make a document
        module_text_with_description = f"{module_description}\n{module_combined_text}"
        module_document = Document(
            page_content=module_text_with_description,
            metadata={
                "module_code": module_code,
                "module_name": module_name,
                "module_link": module_link
            }
        )
        module_documents.append(module_document)
    
    # Save module documents as JSON
    module_documents_json = dumps(module_documents, pretty=True)
    with open(os.path.join(data_folder_path, module_documents_filename), "w") as file:
        file.write(module_documents_json)
    
    return module_documents


def make_documents(data_folder_path: str, module_documents_filename: str, chunk_size: int, chunk_overlap: int) -> list[Document]:
    print("Making document chunks...")

    # Load the list of module documents
    with open(os.path.join(data_folder_path, module_documents_filename), "r") as file:
        documents = load(json.load(file))
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    document_chunks = text_splitter.split_documents(documents)
    
    return document_chunks


def make_and_save_embeddings(document_chunks: list[Document], embeddings_model_name: str, batch_size: int) -> VectorStore:
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


def update_vector_store():
    # Get epoch
    epoch = int(time.time())

    # Create data folder, if it does not exist
    os.makedirs(DATA_FOLDER_PATH, exist_ok=True)

    # Save setup details as JSON
    details = {"epoch": epoch}
    details_json = json.dumps(details, indent=4)
    with open(os.path.join(DATA_FOLDER_PATH, DETAILS_FILENAME), "w") as file:
        file.write(details_json)

    # Connect to PostgreSQL database
    conn = psycopg2.connect(
        user=PGSQL_USERNAME,
        password=PGSQL_PASSWORD,
        database=PGSQL_DB_NAME,
        host=HOST,
        port=PORT
    )

    # Get textual info of modules, in the form of documents
    module_documents = make_module_textual_info(
        conn=conn,
        data_folder_path=DATA_FOLDER_PATH,
        module_documents_filename=MODULE_DOCUMENTS_FILENAME
    )

    # Make document chunks
    document_chunks = make_documents(
        data_folder_path=DATA_FOLDER_PATH,
        module_documents_filename=MODULE_DOCUMENTS_FILENAME,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    # Create a vector store containing embeddings of these chunks, before storing it in Pinecone
    vector_store = make_and_save_embeddings(
        document_chunks=document_chunks,
        embeddings_model_name=EMBEDDINGS_MODEL_NAME,
        batch_size=PINECONE_BATCH_SIZE
    )

    print("Completed the vector store update!")