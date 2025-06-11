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

### UPDATE BUS STOPS AND ROUTES DATA ###
BUS_STOPS_URL = "https://raw.githubusercontent.com/hewliyang/nus-nextbus-web/refs/heads/main/src/lib/data/stops.json"
BUS_ROUTES_URL = "https://raw.githubusercontent.com/hewliyang/nus-nextbus-web/refs/heads/main/src/lib/data/routes.json"
TERMINAL_BUS_STOP_SEQ_NUM = 32767

### LIVE BUS TIMINGS ###
NEXTBUS_API_BASE_URL = "https://nnextbus.nusmods.com"
BUS_TIMINGS_AUTOREFRESH_INTERVAL = 60000        # In milliseconds

### TWO HOUR WEATHER FORECAST ###
WEATHER_API_URL = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
NUS_REGION = "Queenstown"

### COURSE PLANNER ###
# Set maximum number of MCs for first semester
MAX_MCS_FIRST_SEM = 23.0

# Set average number of MCs that a student takes per AY. Typically, it should be 40 MCs
AVERAGE_MCS_PER_AY = 40.0

# Set the semester number when IBLOCs are offered. Typically, we set this to Special Term 1 (sem_num = 3)
IBLOCS_SEM_NUM = 3

### QA CONFIGS ###
# Choose number of documents to be retrieved
NUM_DOCUMENTS_RETRIEVED_GENERAL = 4
NUM_DOCUMENTS_RETRIEVED_SPECIFIC = 3

# Choose LLM for QA
LLM_NAME = "deepseek-r1-distill-llama-70b"

### OTHERS ###
HOURS_WRT_UTC = 8       # UTC to SGT
