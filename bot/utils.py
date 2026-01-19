from datetime import datetime
import os
import re
from config import PROCESSES_FILE

def check_process_exists(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False
    
def strip_ansi_codes(text):
    """Rimuove i codici colore ANSI dall'output"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)    

def get_process_status_logic():
    """Replica la logica di check_nohup.sh e ritorna il testo del messaggio."""
    if not os.path.exists(PROCESSES_FILE) or os.path.getsize(PROCESSES_FILE) == 0:
        return "⚠️ Monitoraggio processi: nessun processo registrato nel file."

    with open(PROCESSES_FILE, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        return "⚠️ Monitoraggio processi: nessun processo registrato nel file."

    process_count = len(lines)
    message = (
        f"🔍 *Monitoraggio processi nohup*\n"
        f"🗓 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"📊 Processi trovati: {process_count}\n\n"
        "Stato dei processi:\n"
    )
    print('Lines:', lines)
    terminated_processes = []
    for line in lines:
        parts = line.split()
        pid, cmd = parts[0], " ".join(parts[1:]) if len(parts) > 1 else ""
        if check_process_exists(pid):
            status = "🟢 Attivo"
        else:
            status = "🔴 Terminato"
            terminated_processes.append(pid)
        message += f"- PID {pid} ({cmd}): {status}\n"

    # Rimuovi i processi terminati dal file
    if terminated_processes:
        with open(PROCESSES_FILE, "w") as f:
            for line in lines:
                pid = line.split()[0]
                if pid not in terminated_processes:
                    f.write(line + "\n")
        message += "\n🗑 _Processi terminati rimossi dal file._"

        # Se il file è ora vuoto
        if not os.path.getsize(PROCESSES_FILE):
            message += "\n✅ Tutti i processi nohup monitorati risultano terminati."

    return message