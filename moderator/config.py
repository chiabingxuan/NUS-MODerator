### INGESTION CONFIGS ###
# Set duration (in days) before an update is needed (ingest again)
MAX_DAYS_UNTIL_UPDATE_NEEDED = 160

# Set academic year
ACAD_YEAR = "2024-2025"

# Configure saving of ingestion details
DATA_FOLDER_PATH = "data"
RETRIEVAL_DETAILS_FILENAME = "details.json"

# Configure retrieval of Disqus information
DISQUS_RETRIEVAL_LIMIT = 100
DISQUS_SHORT_NAME = "nusmods-prod"

# Configure saving of Disqus information
DISQUS_FOLDER_NAME = "disqus"
THREAD_IDS_TO_NAMES_AND_LINKS_FILENAME = "thread_ids_to_names_and_links.json"
THREAD_IDS_TO_MESSAGES_FILENAME = "thread_ids_to_messages.json"
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