import getpass
from telegram import Update
from telegram.ext import ContextTypes
import os
import subprocess
import re

from config import SCRIPTS_DIR
from keyboards import get_back_button, get_disk_retry_root_menu
from utils import get_disk_space_report, get_linux_user, strip_ansi_codes

async def check_auth(update: Update):
    user_id = update.effective_user.id
    linux_user = get_linux_user(user_id)
    if not linux_user:
        await update.effective_message.reply_text("⛔️ Accesso negato.")
        return None
    return linux_user

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
        processes = [p for p in processes if p.get('user') == filter_user]
        if not processes:
            return f"✅ Nessun processo GPU attivo per `{filter_user}`."
    
    cards = []
    gpu_vram_totals = {}  # Dizionario per sommare VRAM per GPU
    
    for proc in processes:
        gpu_id = proc.get('gpu_id', 'N/A')
        pid = proc.get('pid', 'N/A')
        user = proc.get('user', 'N/A')
        mem = proc.get('gpu_memory', 'N/A')
        cmd = proc.get('command', 'N/A')
        
        # Calcola totale VRAM per GPU
        if gpu_id != 'N/A' and mem != 'N/A':
            try:
                # Estrai il valore numerico da "2.50GB"
                vram_value = float(mem.replace('GB', '').strip())
                if gpu_id not in gpu_vram_totals:
                    gpu_vram_totals[gpu_id] = 0.0
                gpu_vram_totals[gpu_id] += vram_value
            except ValueError:
                pass
        
        if len(cmd) > 100:
            cmd_lines = [cmd[i:i+80] for i in range(0, len(cmd), 80)]
            cmd_formatted = '\n'.join(cmd_lines)
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
    
    lines = output.strip().split('\n')
    
    # Estrai informazioni chiave
    magic_token = None
    http_status = None
    success = False
    error_msg = None
    saved_path = None
    
    for line in lines:
        clean_line = strip_ansi_codes(line).strip()
        
        # Estrai magic token
        if 'Magic Token estratto:' in clean_line or 'magic token' in clean_line.lower():
            parts = clean_line.split(':')
            if len(parts) >= 2:
                magic_token = parts[-1].strip()
        
        # Estrai HTTP status
        if 'HTTP' in clean_line and any(str(code) in clean_line for code in ['200', '201', '400', '401', '403', '404', '500']):
            import re
            match = re.search(r'HTTP\s+(\d{3})', clean_line)
            if match:
                http_status = match.group(1)
                success = http_status in ['200', '201']
        
        # Estrai path salvato
        if 'Risposta salvata' in clean_line or 'salvata in' in clean_line.lower():
            parts = clean_line.split('in')
            if len(parts) >= 2:
                saved_path = parts[-1].strip()
        
        # Rileva errori
        if any(err in clean_line.lower() for err in ['errore', 'error', 'failed', 'fallito']):
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

async def execute_script_generic(update, context, script_name, args, override_user=None, folder=None, message_to_edit=None):
    """Esecutore generico di script"""
    linux_user = await check_auth(update)
    if not linux_user: return

    base_folder = folder if folder else SCRIPTS_DIR
    full_path = os.path.join(base_folder, script_name)
    target_user = override_user if override_user else linux_user
    
    # Costruzione comando
    if target_user == 'root':
        cmd = ['sudo', '-n', full_path] + args
        user_msg = "🔥 ROOT"
    elif target_user == getpass.getuser():
        cmd = [full_path] + args
        user_msg = f"👤 {target_user}"
    else:
        cmd = ['sudo', '-n', '-u', target_user, full_path] + args
        user_msg = f"👤 {target_user}"

    # Feedback iniziale - Edit existing message or create new one
    if message_to_edit:
        msg = message_to_edit
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=f"⚙️ Eseguo `{script_name}` ({user_msg})...",
            parse_mode='Markdown'
        )
    else:
        msg = await update.effective_message.reply_text(f"⚙️ Eseguo `{script_name}` ({user_msg})...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        raw_output = strip_ansi_codes(result.stdout + result.stderr)[:3000] or "✅ Fatto (nessun output)"
        is_login_script = 'login' in script_name.lower()

        if is_login_script:
            formatted_output = format_login_output(raw_output)
        else:
            formatted_output = raw_output[:3000] or "✅ Fatto (nessun output)"
            formatted_output = f"📝 **Risultato `{script_name}`:**\n```\n{formatted_output}\n```"
        
        if message_to_edit:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=formatted_output,
                parse_mode='Markdown',
                reply_markup=get_back_button()
            )
        else:
            await msg.edit_text(
                formatted_output,
                parse_mode='Markdown',
                reply_markup=get_back_button()
            )
    except Exception as e:
        if message_to_edit:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=f"💥 Errore: {e}",
                reply_markup=get_back_button()
            )
        else:
            await msg.edit_text(f"💥 Errore: {e}", reply_markup=get_back_button())

async def handle_input_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Gestisce l'input testuale dell'utente.
    Cancella il messaggio dell'utente per privacy e pulizia.
    """
    pending = context.user_data.get('pending_action')
    if not pending: return

    # 1. CANCELLA IL MESSAGGIO DELL'UTENTE (Privacy/Pulizia)
    try:
        await update.message.delete()
    except Exception:
        pass # Se fallisce (es. permessi admin mancanti), pazienza

    text = update.message.text.strip()
    action_type = pending.get('type')
    message_to_edit = pending.get('message_id')
    chat_id = update.effective_chat.id
    del context.user_data['pending_action']

    # --- AZIONE: DISK CHECK ---
    if action_type == 'disk_check':
        path = text
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=message_to_edit, 
            text=f"⏳ Analisi disco su `{path}`...", 
            parse_mode='Markdown'
        )
        report = get_disk_space_report(path, as_root=False)
        
        kb = get_back_button()
        if "Permesso negato" in report:
            kb = get_disk_retry_root_menu(path)
            
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_to_edit,
            text=report,
            reply_markup=kb,
            parse_mode='Markdown'
        )
    elif action_type == 'script_run':
        script_name = pending.get('script')
        args = text.split()
        
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=message_to_edit, 
            text=f"🔄 Avvio `{script_name}`..."
        )
        await execute_script_generic(update, context, script_name, args, folder=pending.get('folder'))

# ================ NOT USED FUNCTIONS ================
def mask_sensitive_args(script_name: str, args: list) -> str:
    """Maschera gli argomenti sensibili per la visualizzazione"""
    if script_name == 'login.sh' and len(args) >= 2:
        username = args[0]
        username_masked = username[:3] + '•' * (len(username) - 3) if len(username) > 3 else username
        password = args[1]
        password_masked = password[0] + '•' * (len(password) - 1) if len(password) > 1 else password
        display_args = [username_masked, password_masked] + args[2:]
        return " ".join(display_args)
    else:
        return " ".join(args) if args else "(nessuno)"

def format_disk_space_status(output: str) -> str:
    """Formatta l'output di check_space.sh in card leggibili"""
    lines = output.strip().split('\n')
    disk_info = None
    folders = []
    
    for line in lines:
        # Rimuovi codici ANSI
        clean_line = strip_ansi_codes(line)
        
        # Estrai informazioni disco
        if '💾 Disco:' in clean_line:
            disk_info = clean_line.replace('💾 Disco:', '').strip()
        
        # Estrai cartelle (linee con emoji di colore e dimensione)
        if clean_line.startswith('●') or any(emoji in clean_line for emoji in ['🟢', '🟡', '🔴']):
            continue
        
        # Parse cartelle: "● 2.3G   folder_name"
        match = re.match(r'(.{1,20})\s+(\S+)\s+(.+)', clean_line)
        if match:
            size = match.group(2).strip()
            name = match.group(3).strip()
            
            # Determina icona in base alla size
            try:
                size_value = float(size.replace('G', '').replace('M', '').replace('K', ''))
                if 'G' in size and size_value > 5:
                    icon = "🔴"
                elif 'G' in size and size_value > 1:
                    icon = "🟡"
                else:
                    icon = "🟢"
                
                folders.append({
                    'icon': icon,
                    'size': size,
                    'name': name
                })
            except:
                pass
    
    # Costruisci messaggio formattato
    if not folders:
        return "✅ Nessun dato disponibile."
    
    header = "📊 **Analisi Spazio Disco**\n"
    if disk_info:
        header += f"💾 {disk_info}\n\n"
    
    header += "🟢 < 1GB | 🟡 1GB - 5GB | 🔴 > 5GB\n"
    header += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Crea card per le cartelle
    cards = []
    for folder in folders:
        card = (
            f"{folder['icon']} **{folder['name']}**\n"
            f"   💾 `{folder['size']}`"
        )
        cards.append(card)
    
    body = "\n\n".join(cards)
    
    return header + body
