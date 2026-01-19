import os
import subprocess
from telegram import Update
from telegram.ext import ContextTypes

from config import ALLOWED_CHAT_ID, SCRIPTS_DIR
from utils import get_process_status_logic, strip_ansi_codes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Comandi disponibili:\n"
        "/status - Controlla i processi attivi\n"
        "/scripts - Lista i file nella cartella script\n"
        "/esegui - Lancia un comando specifico"
    )
    
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(ALLOWED_CHAT_ID):
        return
    await update.message.reply_text("⏳ Controllo in corso...")
    response_text = get_process_status_logic()
    await update.message.reply_text(response_text, parse_mode='Markdown')

async def scripts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(ALLOWED_CHAT_ID): return
    if not os.path.exists(SCRIPTS_DIR):
        await update.message.reply_text(f"⚠️ Errore: La cartella `{SCRIPTS_DIR}` non esiste.", parse_mode='Markdown')
        return

    try:
        files = [f for f in os.listdir(SCRIPTS_DIR)]
        if not files:
            await update.message.reply_text(f"📂 La cartella `{SCRIPTS_DIR}` è vuota.", parse_mode='Markdown')
            return

        message = f"📂 **File in {SCRIPTS_DIR}:**\n\n"
        for file_name in files:
            message += f"📜 `{file_name}`\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Errore nella lettura della cartella: {e}")

async def run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(ALLOWED_CHAT_ID):
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Specifica lo script da avviare.\nEsempio: `/run backup.sh full`", parse_mode='Markdown')
        return

    script_name = context.args[0]
    script_params = context.args[1:]
    if '..' in script_name or '/' in script_name or '\\' in script_name:
        await update.message.reply_text("⛔️ Tentativo di accesso non autorizzato rilevato.")
        return

    full_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(full_path):
        await update.message.reply_text(f"❌ Script `{script_name}` non trovato nella cartella scripts.", parse_mode='Markdown')
        return
    
    await update.message.reply_text(f"🚀 Eseguo `{script_name}` con parametri: {script_params}.", parse_mode='Markdown')

    try:
        cmd = [full_path] + script_params
        my_env = os.environ.copy()
        my_env["TERM"] = "dumb"
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60,
            env=my_env
        )

        raw_output = result.stdout
        if result.stderr:
            raw_output += f"\n\n⚠️ Errori:\n{result.stderr}"
            
        clean_output = strip_ansi_codes(raw_output)
        if not clean_output.strip():
            clean_output = "✅ Eseguito (Nessun output restituito)."

        if len(clean_output) > 4000:
            clean_output = clean_output[:4000] + "\n... [Output troncato]"
        await update.message.reply_text(f"📝 **Risultato:**\n```{clean_output}```", parse_mode='Markdown')

    except subprocess.TimeoutExpired:
        await update.message.reply_text("⏰ Lo script ha impiegato troppo tempo ed è stato interrotto.")
    except PermissionError:
        await update.message.reply_text("🚫 Errore permessi: Assicurati che lo script abbia `chmod +x`.")
    except Exception as e:
        await update.message.reply_text(f"💥 Errore imprevisto: {str(e)}")