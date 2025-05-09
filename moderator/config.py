### UPDATING DATABASE ###
# Set academic year
ACAD_YEAR = "2024-2025"

# Configure retrieval of Disqus information
DISQUS_RETRIEVAL_LIMIT = 100
DISQUS_SHORT_NAME = "nusmods-prod"

### CHATBOT SETUP ###
# Configure saving of files
DATA_FOLDER_PATH = "data"
DETAILS_FILENAME = "details.json"
MODULE_DOCUMENTS_FILENAME = "module_documents.json"

# Configurations for chunk creation
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 100

# Choose model that we will use to create vector embeddings of chunks
EMBEDDINGS_MODEL_NAME = "all-MiniLM-L6-v2"

# Configure saving of vector embeddings
VECTOR_STORE_FOLDER_NAME = "vector_stores"
VECTOR_EMBEDDINGS_FILENAME = "module_text_embeddings"
PINECONE_BATCH_SIZE = 500

### QA CONFIGS ###
# Choose number of documents to be retrieved
NUM_DOCUMENTS_RETRIEVED_GENERAL = 3
NUM_DOCUMENTS_RETRIEVED_SPECIFIC = 2

# Choose LLM for QA
LLM_NAME = "deepseek-r1-distill-llama-70b"