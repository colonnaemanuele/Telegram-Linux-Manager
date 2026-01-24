import os
from telegram import Update
from telegram.ext import ContextTypes

from helpers import check_auth, execute_script_generic, format_gpu_status
from keyboards import get_main_menu, get_scripts_menu, get_back_button, get_cancel_menu
from config import SCRIPTS_DIR
from utils import get_disk_space_report, get_gpu_info

# --- START & MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    linux_user = await check_auth(update)
    if not linux_user: return

    context.user_data.pop('pending_action', None)
    msg = f"👋 Ciao `{linux_user}`.\nPannello di controllo server."
    kb = get_main_menu()

    if update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=kb, parse_mode='Markdown')
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=msg, 
            reply_markup=kb, 
            parse_mode='Markdown'
        )
        
        if update.message:
            try:
                await update.message.delete()
            except Exception:
                pass

# --- STATUS GPU ---
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    if query:
        await query.answer("Scansione GPU in corso...")

    processes = get_gpu_info()
    msg_text = format_gpu_status(processes, filter_user=linux_user)
    
    if query:
        await query.edit_message_text(
            text=msg_text, 
            reply_markup=get_back_button(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(msg_text, reply_markup=get_back_button(), parse_mode='Markdown')

# --- LISTA SCRIPT ---
async def list_scripts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update): return
    
    try:
        files = sorted([f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.sh') or f.endswith('.py')])
        kb = get_scripts_menu(files)
        await update.callback_query.edit_message_text("📂 Seleziona uno script:", reply_markup=kb)
    except Exception as e:
        await update.callback_query.edit_message_text(f"Errore folder script: {e}", reply_markup=get_back_button())

async def disk_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Chiede all'utente quale cartella controllare"""
    query = update.callback_query
    context.user_data['pending_action'] = {
        'type': 'disk_check',
        'message_id': query.message.message_id
    }
    
    await query.edit_message_text(
        "💽 **Analisi Disco**\n\n"
        "Scrivi il percorso da analizzare (es: `/var` o `/home`).\n"
        "Il tuo messaggio verrà cancellato automaticamente dopo l'invio.",
        reply_markup=get_cancel_menu(),
        parse_mode='Markdown'
    )

async def retry_disk_root(update: Update, context: ContextTypes.DEFAULT_TYPE, path):
    """Esegue il check disco direttamente come ROOT su un path specifico"""
    report = get_disk_space_report(path, as_root=True)
    await update.callback_query.edit_message_text(
        report, 
        reply_markup=get_back_button(), 
        parse_mode='Markdown'
    )

async def autologin_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # context.user_data['pending_action'] = {
    #     'type': 'script_run',
    #     'script': 'login_auto.sh',
    #     'folder': os.path.expanduser('~/script/private'),
    #     'message_id': query.message.message_id
    # }
    await execute_script_generic(
        update, 
        context, 
        'login_auto.sh', 
        [], 
        folder=os.path.expanduser('~/script/private'),
        message_to_edit=query.message

    )

# --- MAIN BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # Navigazione Base
    if data == "cmd_start": await start(update, context)
    elif data == "cmd_status": await status(update, context)
    elif data == "cmd_scripts": await list_scripts(update, context)
    
    # Prompt Interattivi
    elif data == "cmd_disk_prompt": await disk_prompt(update, context)
    elif data == "cmd_autologin_prompt": await autologin_prompt(update, context)
    elif data == "cancel_action":
        context.user_data.pop('pending_action', None)
        await start(update, context)

    # Logica specifica
    elif data.startswith("retry_disk_root|"):
        path = data.split("|")[1]
        await retry_disk_root(update, context, path)

    elif data.startswith("run_"):
        # Qui potresti implementare la logica per argomenti script generici se vuoi
        script = data[4:]
        # Esegui diretto o chiedi args (puoi usare la stessa logica di prompt)
        await execute_script_generic(update, context, script, [])