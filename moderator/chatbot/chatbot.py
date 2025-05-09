from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_groq.chat_models import BaseChatModel, ChatGroq
from langchain_huggingface.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from moderator.chatbot.prompts import REPHRASE_PROMPT, EXTRACT_MODULE_CODES_PROMPT, DOCUMENT_FORMAT_PROMPT, RETRIEVAL_QA_CHAT_PROMPT
from moderator.config import EMBEDDINGS_MODEL_NAME, NUM_DOCUMENTS_RETRIEVED_GENERAL, NUM_DOCUMENTS_RETRIEVED_SPECIFIC, LLM_NAME
import re
import streamlit as st

PINECONE_INDEX_NAME = st.secrets["PINECONE_INDEX_NAME"]

def remove_think_from_llm_output(llm_output: str) -> str:
    # Remove <think>...</think> and strip the result
    actual_llm_response = re.sub(r"<think>.*?</think>", "", llm_output, flags=re.DOTALL).strip()

    return actual_llm_response


def rephrase_query(query: str, chat_history: list[dict[str, str]], llm: BaseChatModel, rephrase_prompt: str) -> str:
    # Chain to get the rephrased query, given the original query and chat history. 
    # At the end of the chain, must remove think tags from LLM output
    get_rephrased_query_chain = rephrase_prompt | llm | StrOutputParser() | RunnableLambda(remove_think_from_llm_output)
    
    # Invoke chain to rephrase query
    rephrased_query = get_rephrased_query_chain.invoke({"chat_history": chat_history, "input": query})

    return rephrased_query


def get_list_of_module_codes_for_retrieval(query: str, llm: BaseChatModel, extract_module_codes_prompt: str) -> list[str] | None:
    # Chain to extract module codes from the query. If no module codes extracted, output is "None". 
    # Must remove think tags from LLM output
    get_module_codes_chain = extract_module_codes_prompt | llm | StrOutputParser() | RunnableLambda(remove_think_from_llm_output)

    # Runnable to convert the output of get_module_codes_chain (module codes) into a list of module codes. If output is "None", convert to empty list
    convert_module_codes_to_list = RunnableLambda(lambda module_codes_str: module_codes_str.upper().split() if module_codes_str.upper() != "NONE" else [])

    # Invoke the full chain of operations 
    full_chain = get_module_codes_chain | convert_module_codes_to_list
    module_code_list = full_chain.invoke({"query": query})

    return module_code_list


def run_chatbot(query: str, chat_history: list[dict[str, str]] = list()) -> dict[str, str]:
    # Outline of workflow:
    # 1. Using original query and chat history, have the LLM create a rephrased prompt
    # 2. Have the LLM extract module codes from the rephrased prompt (if any)
    # 3. First treat prompt as a generic query - initialise retriever without any metadata filtering
    # 4. Based on rephrased prompt, this retriever will pick the most relevant document chunks
    # 5. If there are module codes extracted, initialise retrievers with metadata filtering by these module codes.
    # 6. Based on rephrased prompt, these specialised retriever(s) will pick the most relevant document chunks
    # 7. All the chunks retrieved are formatted and then stuffed into the final QA prompt
    # 8. Based on final QA prompt, have the LLM come up with an answer

    # Load the vector store containing the embeddings of the module descriptions
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL_NAME)
    vector_store = PineconeVectorStore(index_name=PINECONE_INDEX_NAME, embedding=embeddings)
    
    # Initialise LLM
    llm = ChatGroq(model=LLM_NAME, temperature=0)

    # If there is chat history, rephrase query using chat history and LLM
    if chat_history:
        rephrased_query = rephrase_query(query=query, chat_history=chat_history, llm=llm, rephrase_prompt=REPHRASE_PROMPT)

    else:
        # Empty chat history - just use original query
        rephrased_query = query
    
    # Get module codes relevant for the rephrased query. If all modules are relevant, module_codes is an empty list
    module_codes = get_list_of_module_codes_for_retrieval(query=rephrased_query, llm=llm, extract_module_codes_prompt=EXTRACT_MODULE_CODES_PROMPT)
    print(module_codes)

    # Initialise retriever and use it for retrieval
    # First initialise a retriever without metadata filtering (general retrieval)
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": NUM_DOCUMENTS_RETRIEVED_GENERAL
        }
    )

    # Use general retriever to get relevant document chunks, based on the rephrased query
    document_chunks = retriever.invoke(rephrased_query)

    if module_codes:
        # Should also have a retrieval that is specific to certain modules - in this case we need metadata filtering by module code
        # Loop through each module and retrieve a few documents for it
        for module_code in module_codes:
            # Create retriever that filters out documents for this module only
            # Must create retriever for each module, to ensure that at least 1 document is being retrieved per module
            retriever = vector_store.as_retriever(
                search_kwargs={
                    "k": NUM_DOCUMENTS_RETRIEVED_SPECIFIC,
                    "filter": {
                        "module_code": {
                            "$eq": module_code
                        } 
                    }
                }
            )

            # Get relevant document chunks for this module, based on the rephrased query
            document_chunks_for_module_code = retriever.invoke(rephrased_query)
            document_chunks.extend(document_chunks_for_module_code)

    # Create QA chain that will format and then stuff relevant document chunks (past context) into the QA prompt, before having the LLM answer based on this prompt
    stuff_documents_chain = create_stuff_documents_chain(llm=llm, prompt=RETRIEVAL_QA_CHAT_PROMPT, document_prompt=DOCUMENT_FORMAT_PROMPT)

    # Invoke the QA chain, to get the chatbot's response in str format
    qa_output = stuff_documents_chain.invoke(input={
        "input": query,
        "context": document_chunks,
        "chat_history": chat_history
    })

    # Format the relevant information (original query, chatbot's response and document chunks retrieved) appropriately
    result = {
        "query": query,
        "answer": remove_think_from_llm_output(llm_output=qa_output),     # Remove think tage from LLM output
        "source_documents": document_chunks
    }

    return result