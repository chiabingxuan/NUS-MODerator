from dotenv import load_dotenv
from langchain.chains.retrieval import create_retrieval_chain
from langchain import hub
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_groq.chat_models import ChatGroq
from langchain_huggingface.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_community.vectorstores.faiss import FAISS
from typing import List, Dict, Any
from helpers.config import EMBEDDINGS_MODEL_NAME, VECTOR_STORE_FOLDER_NAME, VECTOR_EMBEDDINGS_FILENAME

load_dotenv()


def run_chatbot(query: str, chat_history: List[Dict[str, Any]] = list()):
    # Load the vector store containing the embeddings of the module descriptions
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL_NAME)
    vector_store = FAISS.load_local(
        folder_path=VECTOR_STORE_FOLDER_NAME,
        embeddings=embeddings,
        index_name=VECTOR_EMBEDDINGS_FILENAME,
        allow_dangerous_deserialization=True
    )
    
    # Initialise LLM
    llm = ChatGroq(model="llama3-8b-8192", temperature=0)

    # Create chain that will stuff relevant document chunks (past context) into the QA prompt, before having the LLM answer based on this prompt
    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    stuff_documents_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)
    
    # Initialise retriever that will receive a rephrased query (rephrased using both the chat history and the LLM)
    # This retriever will then pick the relevant document chunks to answer this rephrased query
    rephrase_prompt = hub.pull("langchain-ai/chat-langchain-rephrase")
    history_aware_retriever = create_history_aware_retriever(
        llm=llm, retriever=vector_store.as_retriever(), prompt=rephrase_prompt
    )
    
    # Create the complete QA chain
    # 1. Using original query and chat history, have the LLM create a rephrased prompt
    # 2. Based on rephrased prompt, the retriever picks the most relevant document chunks
    # 3. Chunks are stuffed into the final QA prompt
    # 4. Based on final QA prompt, have the LLM come up with an answer
    qa = create_retrieval_chain(retriever=history_aware_retriever, combine_docs_chain=stuff_documents_chain)

    # Invoke the complete QA chain
    result = qa.invoke(input={"input": query, "chat_history": chat_history})
    new_result = {
        "query": result["input"],
        "result": result["answer"],
        "source_documents": result["context"]
    }

    return new_result