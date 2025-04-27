### INGESTION CONFIGS ###
# Configure scraping of Disqus information
DISQUS_SCRAPING_LIMIT = 100
DISQUS_SHORT_NAME = "nusmods-prod"

# Configure saving of Disqus information
DISQUS_FOLDER_NAME = "disqus"
THREAD_IDS_TO_NAMES_FILENAME = "thread_ids_to_names.json"
THREAD_IDS_TO_MESSAGES_FILENAME = "thread_ids_to_messages.json"
DISQUS_SCRAPING_DETAILS_FILENAME = "details.txt" 
REVIEWS_FILENAME = "reviews.txt"

# Configurations for chunk creation
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 50

# Choose model that we will use to create vector embeddings of chunks
EMBEDDINGS_MODEL_NAME = "all-MiniLM-L6-v2"

# Configure saving of vector embeddings
VECTOR_STORE_FOLDER_NAME = "vector_stores"
VECTOR_EMBEDDINGS_FILENAME = "mod_description_embeddings"