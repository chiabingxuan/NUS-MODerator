### REGISTRATION ###
# Set list of majors
AVAILABLE_MAJORS = [
    "Accountancy",
    "Business Analytics",
    "Computer Science",
    "Data Science and Analytics",
    "Life Sciences",
    "Psychology",
    "Quantitative Finance"
]

### UPDATING DATABASE ###
# Set the current (most recent) academic year
ACAD_YEAR = "2024-2025"

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

### UPDATE VECTOR STORE ###
# Configurations for chunk creation
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 100

# Choose model that we will use to create vector embeddings of chunks
EMBEDDINGS_MODEL_NAME = "all-MiniLM-L6-v2"

# Configure saving of vector embeddings
PINECONE_BATCH_SIZE = 500

### COURSE PLANNER ###
# Set number of years spent in university
NUM_OF_YEARS_TO_GRAD = 4

### QA CONFIGS ###
# Choose number of documents to be retrieved
NUM_DOCUMENTS_RETRIEVED_GENERAL = 4
NUM_DOCUMENTS_RETRIEVED_SPECIFIC = 2

# Choose LLM for QA
LLM_NAME = "deepseek-r1-distill-llama-70b"