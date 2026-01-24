import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
SCRIPTS_DIR = os.getenv('SCRIPTS_DIR', 'scripts')
PROCESSES_FILE = os.getenv('PROCESSES_FILE')

_mapping_str = os.getenv('USER_MAPPING', '')
USER_MAPPING = {}

# Parsing mappatura utenti
if _mapping_str:
    try:
        for pair in _mapping_str.split(','):
            if ':' in pair:
                chat_id, linux_user = pair.split(':')
                USER_MAPPING[int(chat_id.strip())] = linux_user.strip()
    except Exception as e:
        print(f"Errore parsing USER_MAPPING: {e}")

ALLOWED_LINUX_USERS = set(USER_MAPPING.values())