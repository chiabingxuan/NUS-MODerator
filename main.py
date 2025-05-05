from dotenv import load_dotenv
from moderator.chatbot.chatbot import run_chatbot
from moderator.chatbot.chatbot_setup import setup_chatbot
from moderator.admin.update_db import update_db

load_dotenv()


if __name__ == "__main__":
    update_db()