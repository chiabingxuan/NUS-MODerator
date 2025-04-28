from langchain import hub
from langchain_core.prompts.prompt import PromptTemplate

# Prompt that asks LLM to come up with a rephrased query, based on original query and chat history
REPHRASE_PROMPT = hub.pull("langchain-ai/chat-langchain-rephrase")

# Prompt that formats each document retrieved
DOCUMENT_FORMAT_TEMPLATE = "Module: {module_name}\nInformation: {page_content}"
DOCUMENT_FORMAT_PROMPT = PromptTemplate.from_template(DOCUMENT_FORMAT_TEMPLATE)

# Prompt that asks LLM to come up with an answer, based on rephrased query and documents retrieved
RETRIEVAL_QA_CHAT_PROMPT = hub.pull("langchain-ai/retrieval-qa-chat")