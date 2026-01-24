import getpass
from telegram import Update
from telegram.ext import ContextTypes
import os
import subprocess

from format import format_disk_space_status, format_login_output
from config import SCRIPTS_DIR
from keyboards import get_back_button, get_back_disk
from utils import get_disk_space_report, get_linux_user, strip_ansi_codes

async def check_auth(update: Update):
    user_id = update.effective_user.id
    linux_user = get_linux_user(user_id)
    if not linux_user:
        await update.effective_message.reply_text("⛔️ Accesso negato.")
        return None
    return linux_user

async def execute_script_generic(update, context, script_name, args, override_user=None, folder=None, message_to_edit=None):
    """Esecutore generico di script"""
    linux_user = await check_auth(update)
    if not linux_user:
        return

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
    if not pending:
        return

    # 1. CANCELLA IL MESSAGGIO DELL'UTENTE (Privacy/Pulizia)
    try:
        await update.message.delete()
    except Exception:
        pass # Se fallisce (es. permessi admin mancanti), pazienza

    text = update.message.text.strip()
    action_type = pending.get('type')
    message_id = pending.get('message_id')
    chat_id = update.effective_chat.id
    del context.user_data['pending_action']
    
    
    if action_type == 'run_command':
        linux_user = await check_auth(update)
        if not linux_user:
            return
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="⚡️ Esecuzione comando in corso...",
            parse_mode='Markdown'
        )
        
        try:
            # Esegui comando come utente (NOT root)
            result = subprocess.run(
                text,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = strip_ansi_codes(result.stdout + result.stderr)[:2000]
            
            if not output.strip():
                output = "✅ Comando eseguito (nessun output)"
            
            formatted_output = f"⚡️ **Comando:**\n```\n{text}\n```\n\n📝 **Risultato:**\n```\n{output}\n```"
        except subprocess.TimeoutExpired:
            formatted_output = f"⚡️ **Comando:**\n```\n{text}\n```\n\n💥 **Errore:** Timeout - comando impiegato troppo tempo"
        except Exception as e:
            formatted_output = f"⚡️ **Comando:**\n```\n{text}\n```\n\n💥 **Errore:** {str(e)}"
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=formatted_output,
            reply_markup=get_back_button(),
            parse_mode='Markdown'
        )

     # --- AZIONE: DISK CHECK CUSTOM ---
    elif action_type == 'disk_check_custom':
        path = text
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text=f"⏳ Analisi disco su `{path}` in corso...", 
            parse_mode='Markdown'
        )
        
        try:
            raw_report = get_disk_space_report(path, as_root=False)
            report = format_disk_space_status(raw_report, path=path)
        except Exception as e:
            report = f"💥 Errore scansione disco: {e}"
        
        kb = get_back_disk()
            
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=report,
            reply_markup=kb,
            parse_mode='Markdown'
        )
    elif action_type == 'script_run':
        script_name = pending.get('script')
        args = text.split()
        
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text=f"🔄 Avvio `{script_name}`..."
        )
        await execute_script_generic(update, context, script_name, args, folder=pending.get('folder'))