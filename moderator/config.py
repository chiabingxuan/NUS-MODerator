### REGISTRATION ###
# Set list of majors
AVAILABLE_MAJORS = [
    "Business Analytics",
    "Data Science and Analytics",
    "Life Sciences",
    "Quantitative Finance"
]

# Set list of academic years. Will also be used as the list of matriculation years
LIST_OF_AYS = [
    "2022-2023",
    "2023-2024",
    "2024-2025"
]

### UPDATING DATABASE ###
# Set the current (most recent) academic year
ACAD_YEAR = LIST_OF_AYS[-1]

# Set semesters
SEMESTER_LIST = [
    {
        "num": 1,
        "name": "Semester 1"
    },
    {
        "num": 2,
        "name": "Semester 2"
    },
    {
        "num": 3,
        "name": "Special Term 1"
    },
    {
        "num": 4,
        "name": "Special Term 2"
    }
]

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
PINECONE_BATCH_SIZE = 500

### QA CONFIGS ###
# Choose number of documents to be retrieved
NUM_DOCUMENTS_RETRIEVED_GENERAL = 4
NUM_DOCUMENTS_RETRIEVED_SPECIFIC = 2

# Choose LLM for QA
LLM_NAME = "deepseek-r1-distill-llama-70b"