from dotenv import load_dotenv
import json
from langchain_chroma import Chroma
from langchain_core.documents.base import Document
from langchain_core.load import dumps, load
from langchain_core.vectorstores import VectorStore
from langchain_huggingface.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from moderator.config import DATA_FOLDER_PATH, DETAILS_FILENAME, MODULE_DOCUMENTS_FILENAME, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDINGS_MODEL_NAME, VECTOR_STORE_FOLDER_NAME, VECTOR_EMBEDDINGS_FILENAME
from moderator.sql.chatbot_setup import SET_CONCAT_MAX_LENGTH_STATEMENT, GET_MODULE_COMBINED_REVIEWS_QUERY
import mysql.connector
import os
import shutil
import time

load_dotenv()
MYSQL_DB_NAME = os.getenv("MYSQL_DB_NAME")
MYSQL_USERNAME = os.getenv("MYSQL_USERNAME")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

def make_module_textual_info(conn: mysql.connector.connection_cext.CMySQLConnection, data_folder_path: str, module_documents_filename: str) -> list[Document]:
    print("Making module textual info...")

    # Create cursor
    cur = conn.cursor()

    # Query the official module description and combined reviews, for each module
    cur.execute(SET_CONCAT_MAX_LENGTH_STATEMENT)        # Increase max length for GROUP_CONCAT()
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


def make_and_save_embeddings(document_chunks: list[Document], embeddings_model_name: str, vector_store_folder_name: str, vector_embeddings_filename: str) -> VectorStore:
    # Create folder for vector store
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


def setup_chatbot():
    # Get epoch
    epoch = int(time.time())

    # Create data folder, if it does not exist
    os.makedirs(DATA_FOLDER_PATH, exist_ok=True)

    # Save setup details as JSON
    details = {"epoch": epoch}
    details_json = json.dumps(details, indent=4)
    with open(os.path.join(DATA_FOLDER_PATH, DETAILS_FILENAME), "w") as file:
        file.write(details_json)

    # Connect to MySQL database
    conn = mysql.connector.connect(
        user=MYSQL_USERNAME,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB_NAME,
        host="localhost",
        port=3306
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

    # Remove existing folder containing vector store
    if os.path.isdir(VECTOR_STORE_FOLDER_NAME):
        shutil.rmtree(VECTOR_STORE_FOLDER_NAME)

    # Create a vector store containing embeddings of these chunks, before saving it
    vectorstore = make_and_save_embeddings(
        document_chunks=document_chunks,
        embeddings_model_name=EMBEDDINGS_MODEL_NAME,
        vector_store_folder_name=VECTOR_STORE_FOLDER_NAME,
        vector_embeddings_filename=VECTOR_EMBEDDINGS_FILENAME
    )

    print("Chatbot setup completed!")