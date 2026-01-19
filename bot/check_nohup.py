#!/usr/bin/env python3
import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# Constants
load_dotenv()
PROCESSES_FILE = os.getenv('PROCESSES_FILE')
TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
USER_NAME = os.getlogin()


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)


def main():
    # Check if processes file exists and is not empty
    if not os.path.exists(PROCESSES_FILE) or os.path.getsize(PROCESSES_FILE) == 0:
        send_telegram_message("Monitoraggio processi: nessun processo attivo.")
        sys.exit(0)

    # Count number of processes
    with open(PROCESSES_FILE, "r") as f:
        process_count = sum(1 for _ in f)

    message = f"Monitoraggio processi nohup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. {process_count} processi trovati.\n\nStato dei processi:"
    terminated_processes = []

    # Check each process
    with open(PROCESSES_FILE, "r") as f:
        for line in f:
            pid = line.split()[0]
            cmd = " ".join(line.split()[1:])

            if check_process_exists(pid):
                status = "🟢 Attivo"
            else:
                status = "🔴 Terminato"
                terminated_processes.append(pid)

            message += f"\n- PID {pid} ({cmd}): {status}"

    # Remove terminated processes from file
    if terminated_processes:
        with open(PROCESSES_FILE, "r") as f:
            lines = f.readlines()
        with open(PROCESSES_FILE, "w") as f:
            for line in lines:
                if line.split()[0] not in terminated_processes:
                    f.write(line)

    # Send status message
    send_telegram_message(message)


if __name__ == "__main__":
    main()
