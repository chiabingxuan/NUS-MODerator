from dotenv import load_dotenv
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_groq.chat_models import BaseChatModel, ChatGroq
from langchain_huggingface.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_community.vectorstores.faiss import FAISS
import re

from moderator.chatbot.prompts import REPHRASE_PROMPT, EXTRACT_MODULE_CODES_PROMPT, DOCUMENT_FORMAT_PROMPT, RETRIEVAL_QA_CHAT_PROMPT
from moderator.config import EMBEDDINGS_MODEL_NAME, VECTOR_STORE_FOLDER_NAME, VECTOR_EMBEDDINGS_FILENAME

load_dotenv()


def remove_think_from_llm_output(llm_output: str) -> str:
    # Remove <think>...</think> and strip the result
    actual_llm_response = re.sub(r"<think>.*?</think>", "", llm_output, flags=re.DOTALL).strip()

    return actual_llm_response


def get_list_of_module_codes_for_retrieval(original_query: str, chat_history: list[dict[str, str]], llm: BaseChatModel) -> list[str] | None:
    # Chain to get the rephrased query, given the original query and chat history. 
    # At the end of the chain, must remove think tags from LLM output
    get_rephrased_query_chain = REPHRASE_PROMPT | llm | StrOutputParser() | RunnableLambda(remove_think_from_llm_output)

    # Runnable to convert the output of get_rephrased_query_chain (rephrased query) into a dictionary
    convert_rephrased_query_to_dict = RunnableLambda(lambda query: {"query": query})
    
    # Chain to extract module codes from the rephrased query. If no module codes extracted, output is "None". 
    #  must remove think tags from LLM output
    get_module_codes_chain = EXTRACT_MODULE_CODES_PROMPT | llm | StrOutputParser() | RunnableLambda(remove_think_from_llm_output)

    # Runnable to convert the output of get_module_codes_chain (module codes) into a list of module codes. If output is "None", convert to empty list
    convert_module_codes_to_list = RunnableLambda(lambda module_codes_str: module_codes_str.upper().split() if module_codes_str.upper() != "NONE" else [])

    # Invoke the full chain of operations
    if not chat_history:
        # Chat history is empty - bypass rephrasing phase. Extract module codes from original query
        full_chain = get_module_codes_chain | convert_module_codes_to_list
        module_code_list = full_chain.invoke({"query": original_query})

    else:
        full_chain = get_rephrased_query_chain | convert_rephrased_query_to_dict | get_module_codes_chain | convert_module_codes_to_list
        module_code_list = full_chain.invoke({"chat_history": chat_history, "input": original_query})

    return module_code_list


def run_chatbot(query: str, chat_history: list[dict[str, str]] = list()) -> dict[str, str]:
    # Load the vector store containing the embeddings of the module descriptions
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL_NAME)
    vector_store = FAISS.load_local(
        folder_path=VECTOR_STORE_FOLDER_NAME,
        embeddings=embeddings,
        index_name=VECTOR_EMBEDDINGS_FILENAME,
        allow_dangerous_deserialization=True
    )
    
    # Initialise LLM
    llm = ChatGroq(model="deepseek-r1-distill-llama-70b", temperature=0)

    # Create chain that will format and then stuff relevant document chunks (past context) into the QA prompt, before having the LLM answer based on this prompt
    stuff_documents_chain = create_stuff_documents_chain(llm=llm, prompt=RETRIEVAL_QA_CHAT_PROMPT, document_prompt=DOCUMENT_FORMAT_PROMPT)
    
    # Get module codes relevant for the query provided, taking chat history into account. If query is general (all modules are relevant), module_codes is an empty list
    module_codes = get_list_of_module_codes_for_retrieval(original_query=query, chat_history=chat_history, llm=llm)
    print(module_codes)

    # Initialise retriever. If retrieval must be specific to certain modules, retriever must have metadata filtering by module code
    if module_codes:
        retriever = vector_store.as_retriever(
            search_kwargs={
                "filter": {
                    "module_code": {
                        "$in": module_codes
                    }  
                }
            }
        )
    else:
        retriever = vector_store.as_retriever()
    
    # Initialise retriever that will receive a rephrased query (rephrased using both the chat history and the LLM)
    # This retriever will then pick the relevant document chunks to answer this rephrased queryge
    # history_aware_retriever = create_history_aware_retriever(
    #     llm=llm, retriever=vector_store.as_retriever(), prompt=REPHRASE_PROMPT
    # )
   
    # Create the complete QA chain
    # 1. Using original query and chat history, have the LLM create a rephrased prompt
    # 2. Based on rephrased prompt, the retriever picks the most relevant document chunks
    # 3. Chunks are formatted and then stuffed into the final QA prompt
    # 4. Based on final QA prompt, have the LLM come up with an answer
    qa = create_retrieval_chain(retriever=retriever, combine_docs_chain=stuff_documents_chain)

    # Invoke the complete QA chain
    qa_output = qa.invoke(input={"input": query, "chat_history": chat_history})
    result = {
        "query": qa_output["input"],
        "answer": remove_think_from_llm_output(llm_output=qa_output["answer"]),     # Remove think tage from LLM output
        "source_documents": qa_output["context"]
    }

    return result