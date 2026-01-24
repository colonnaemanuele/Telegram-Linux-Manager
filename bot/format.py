from utils import strip_ansi_codes, get_size_format
import shutil
import os

def format_gpu_status(processes, filter_user=None):
    """Formatta lo stato GPU in card leggibili"""
    if not processes:
        return "✅ Nessun processo GPU attivo."

    # Se processes è una lista di stringhe (vecchio formato), restituiscila così com'è
    if processes and isinstance(processes[0], str):
        if filter_user:
            # Filtra le righe che contengono il nome utente
            filtered = [line for line in processes if filter_user in line]
            if not filtered:
                return f"✅ Nessun processo GPU attivo per `{filter_user}`."
            return "\n".join(filtered)
        return "\n".join(processes)

    # Altrimenti processa come lista di dizionari (nuovo formato)
    if filter_user:
        processes = [p for p in processes if p.get("user") == filter_user]
        if not processes:
            return f"✅ Nessun processo GPU attivo per `{filter_user}`."

    cards = []
    gpu_vram_totals = {}  # Dizionario per sommare VRAM per GPU

    for proc in processes:
        gpu_id = proc.get("gpu_id", "N/A")
        pid = proc.get("pid", "N/A")
        user = proc.get("user", "N/A")
        mem = proc.get("gpu_memory", "N/A")
        cmd = proc.get("command", "N/A")

        # Calcola totale VRAM per GPU
        if gpu_id != "N/A" and mem != "N/A":
            try:
                # Estrai il valore numerico da "2.50GB"
                vram_value = float(mem.replace("GB", "").strip())
                if gpu_id not in gpu_vram_totals:
                    gpu_vram_totals[gpu_id] = 0.0
                gpu_vram_totals[gpu_id] += vram_value
            except ValueError:
                pass

        if len(cmd) > 100:
            cmd_lines = [cmd[i : i + 80] for i in range(0, len(cmd), 80)]
            cmd_formatted = "\n".join(cmd_lines)
        else:
            cmd_formatted = cmd

        card = (
            f"┏━━━━━━━━━━━━━━━━━━━━\n"
            f"┃ 🖥 **GPU:** `{gpu_id}`\n"
            f"┃ 🔢 **PID:** `{pid}`\n"
            f"┃ 👤 **User:** `{user}`\n"
            f"┃ 💾 **Memory:** `{mem}`\n"
            f"┗━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ **Command:**\n`{cmd_formatted}`"
        )
        cards.append(card)

    header = f"📊 **Processi GPU Attivi** ({len(cards)}):\n\n"
    body = "\n\n".join(cards)

    # Aggiungi sommario VRAM per GPU
    if gpu_vram_totals:
        summary = "\n\n━━━━━━━━━━━━━━━━━━━━\n📈 **Riepilogo VRAM per GPU:**\n"
        for gpu_id in sorted(gpu_vram_totals.keys()):
            total_vram = gpu_vram_totals[gpu_id]
            summary += f"   GPU `{gpu_id}`: **{total_vram:.2f} GB**\n"

        # Calcola totale complessivo
        total_all = sum(gpu_vram_totals.values())
        summary += f"\n💎 **Totale:** **{total_all:.2f} GB**"

        return header + body + summary

    return header + body


def format_login_output(output: str) -> str:
    """Formatta l'output del login script in card leggibili"""
    if not output or output.strip() == "":
        return "✅ Login completato (nessun output)"

    lines = output.strip().split("\n")

    # Estrai informazioni chiave
    magic_token = None
    http_status = None
    success = False
    error_msg = None
    saved_path = None

    for line in lines:
        clean_line = strip_ansi_codes(line).strip()

        # Estrai magic token
        if "Magic Token estratto:" in clean_line or "magic token" in clean_line.lower():
            parts = clean_line.split(":")
            if len(parts) >= 2:
                magic_token = parts[-1].strip()

        # Estrai HTTP status
        if "HTTP" in clean_line and any(
            str(code) in clean_line
            for code in ["200", "201", "400", "401", "403", "404", "500"]
        ):
            import re

            match = re.search(r"HTTP\s+(\d{3})", clean_line)
            if match:
                http_status = match.group(1)
                success = http_status in ["200", "201"]

        # Estrai path salvato
        if "Risposta salvata" in clean_line or "salvata in" in clean_line.lower():
            parts = clean_line.split("in")
            if len(parts) >= 2:
                saved_path = parts[-1].strip()

        # Rileva errori
        if any(
            err in clean_line.lower()
            for err in ["errore", "error", "failed", "fallito"]
        ):
            error_msg = clean_line

    # Costruisci card formattata
    if success:
        status_icon = "✅"
        status_text = "**Autenticazione Riuscita**"
    elif error_msg:
        status_icon = "❌"
        status_text = "**Autenticazione Fallita**"
    else:
        status_icon = "⚠️"
        status_text = "**Stato Sconosciuto**"

    card = f"{status_icon} {status_text}\n"
    card += "┏━━━━━━━━━━━━━━━━━━━━\n"

    if magic_token:
        card += f"┃ 🔑 **Magic Token:** `{magic_token}`\n"

    if http_status:
        card += f"┃ 🌐 **HTTP Status:** `{http_status}`\n"

    if saved_path:
        card += f"┃ 📁 **Output:** `{saved_path}`\n"

    if error_msg:
        card += f"┃ 💥 **Errore:** `{error_msg}`\n"

    card += "┗━━━━━━━━━━━━━━━━━━━━\n"

    # Aggiungi log completo se ci sono informazioni extra
    if len(lines) > 5 or error_msg:
        card += "\n📋 **Log Completo:**\n```\n"
        for line in lines:
            clean = strip_ansi_codes(line).strip()
            if clean:
                card += f"{clean}\n"
        card += "```"

    return card


def format_disk_space_status(du_output: str, path: str = "/home") -> str:
    """Formatta l'output di du in card leggibili rispettando le soglie"""
    # Analisi disco
    header = ""
    try:
        if os.path.exists(path):
            total, used, free = shutil.disk_usage(path)
            percent = (used / total) * 100
            header += f"📊 Analisi: {path}\n"
            header += f"💾 Disco: {get_size_format(used)} / {get_size_format(total)} ({percent:.1f}%)\n"
    except Exception as e:
        header += f"⚠️ Errore lettura disco: {e}\n"

    if du_output is None:
        if not os.path.exists(path):
            return f"❌ Errore: Cartella `{path}` non trovata."
        return header + "\n⚠️ Errore durante la scansione delle cartelle."

    lines = du_output.strip().split("\n")
    folders = []

    for line in lines:
        clean_line = strip_ansi_codes(line)
        if not clean_line.strip():
            continue
        
        # Parse del formato du: "123456\t/path/to/folder"
        if '\t' in clean_line:
            parts = clean_line.split('\t')
            if len(parts) == 2:
                try:
                    size_kb = int(parts[0].strip())
                    fpath = parts[1].strip()
                    
                    # Salta la cartella padre
                    if fpath.rstrip('/') == path or fpath == path + '/':
                        continue
                    
                    # Estrai nome folder
                    name = fpath.rstrip('/').split('/')[-1]
                    
                    # Converti in GB
                    size_gb = size_kb / (1024 * 1024)
                    
                    # Formato leggibile
                    if size_gb >= 1:
                        human_size = f"{size_gb:.1f}GB"
                    else:
                        human_size = f"{size_kb / 1024:.1f}MB"
                    
                    # Applica soglie colore
                    if size_gb > 600:
                        icon = "🔴"
                    elif size_gb > 350:
                        icon = "🟠"
                    elif size_gb > 100:
                        icon = "🟡"
                    else:
                        icon = "🟢"

                    folders.append({"icon": icon, "size": human_size, "name": name, "size_gb": size_gb})
                except ValueError:
                    pass

    # Costruisci messaggio formattato
    if not folders:
        return header + "\n✅ Nessun dato disponibile o errore di parsing."

    # Ordina per dimensione descrescente
    folders.sort(key=lambda x: x["size_gb"], reverse=True)

    header += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    header += "🟢 < 100GB | 🟡 100-350GB | 🟠 350-600GB | 🔴 > 600GB\n"
    header += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    # Crea card per le cartelle - ESCAPE FOLDER NAMES
    cards = []
    for folder in folders:
        # Escape the folder name to prevent Markdown parsing issues
        safe_name = folder['name'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('`', '\\`')
        card = f"{folder['icon']} **{safe_name}** `{folder['size']}`"
        cards.append(card)

    body = "\n".join(cards)

    return header + body


def mask_sensitive_args(script_name: str, args: list) -> str:
    """Maschera gli argomenti sensibili per la visualizzazione"""
    if script_name == "login.sh" and len(args) >= 2:
        username = args[0]
        username_masked = (
            username[:3] + "•" * (len(username) - 3) if len(username) > 3 else username
        )
        password = args[1]
        password_masked = (
            password[0] + "•" * (len(password) - 1) if len(password) > 1 else password
        )
        display_args = [username_masked, password_masked] + args[2:]
        return " ".join(display_args)
    else:
        return " ".join(args) if args else "(nessuno)"