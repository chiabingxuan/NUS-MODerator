from dotenv import load_dotenv
from moderator.chatbot.chatbot import run_chatbot
from moderator.chatbot.ingestion import ingest

load_dotenv()


if __name__ == "__main__":
    ingest()