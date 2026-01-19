import os
from dotenv import load_dotenv

load_dotenv()

ALLOWED_CHAT_ID = int(os.getenv('CHAT_ID'))
PROCESSES_FILE = os.getenv('PROCESSES_FILE')
TOKEN = os.getenv('TOKEN')
SCRIPTS_DIR = '/home/emanuele/script/scripts'