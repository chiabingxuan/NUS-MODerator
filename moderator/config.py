### UPDATING DATABASE ###
# Set academic year
ACAD_YEAR = "2024-2025"

# Configure retrieval of Disqus information
DISQUS_RETRIEVAL_LIMIT = 100
DISQUS_SHORT_NAME = "nusmods-prod"

### CHATBOT SETUP ###
# Set duration (in days) before the user should be forced to carry out the chatbot setup again
MAX_DAYS_UNTIL_NEW_CHATBOT_SETUP = 160

# Configure saving of ingestion by user
DATA_FOLDER_PATH = "data"
DETAILS_FILENAME = "details.json"
MODULE_DOCUMENTS_FILENAME = "module_documents.json"

# Configurations for chunk creation
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 50

# Choose model that we will use to create vector embeddings of chunks
EMBEDDINGS_MODEL_NAME = "all-MiniLM-L6-v2"

# Configure saving of vector embeddings
VECTOR_STORE_FOLDER_NAME = "vector_stores"
VECTOR_EMBEDDINGS_FILENAME = "module_text_embeddings"

### QA CONFIGS ###
# Choose number of documents to be retrieved
NUM_DOCUMENTS_RETRIEVED = 4

# Choose LLM for QA
LLM_NAME = "deepseek-r1-distill-llama-70b"