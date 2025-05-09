from langchain import hub
from langchain_core.prompts.prompt import PromptTemplate

# Prompt that asks LLM to come up with a rephrased query, based on original query and chat history
REPHRASE_PROMPT = hub.pull("chiabingxuan/nus-moderator-rephrase")

# Prompt that asks LLM to extract module codes from the rephrased query
EXTRACT_MODULE_CODES_TEMPLATE = "Extract all module codes mentioned in the following text. Respond only with a list of module codes separated by spaces, and nothing else. If none are mentioned, only respond with 'None', and nothing else.\n\nText: {query}"
EXTRACT_MODULE_CODES_PROMPT = PromptTemplate.from_template(EXTRACT_MODULE_CODES_TEMPLATE)

# Prompt that formats each document retrieved
DOCUMENT_FORMAT_TEMPLATE = "Module: {module_name}\nInformation: {page_content}"
DOCUMENT_FORMAT_PROMPT = PromptTemplate.from_template(DOCUMENT_FORMAT_TEMPLATE)

# Prompt that asks LLM to come up with an answer, based on rephrased query and documents retrieved
RETRIEVAL_QA_CHAT_PROMPT = hub.pull("chiabingxuan/nus-moderator-retrieval-qa")