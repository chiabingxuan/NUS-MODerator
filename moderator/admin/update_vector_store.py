from langchain_core.documents.base import Document
from langchain_core.vectorstores import VectorStore
from langchain_huggingface.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from moderator.config import CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDINGS_MODEL_NAME, PINECONE_BATCH_SIZE
from moderator.sql.vector_store_update import GET_MODULE_COMBINED_REVIEWS_QUERY
import streamlit as st

PINECONE_INDEX_NAME = st.secrets["PINECONE_INDEX_NAME"]

def make_module_textual_info(conn: st.connections.SQLConnection, acad_year: str) -> list[Document]:
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


def make_documents(module_documents: list[Document], chunk_size: int, chunk_overlap: int) -> list[Document]:
    print("Making document chunks...")

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    document_chunks = text_splitter.split_documents(module_documents)
    
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


def update_vector_store(conn: st.connections.SQLConnection, acad_year: str):
    # Get textual info of modules, in the form of documents
    module_documents = make_module_textual_info(
        conn=conn,
        acad_year=acad_year
    )

    # Make document chunks
    document_chunks = make_documents(
        module_documents=module_documents,
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