import os
from telegram import Update
from telegram.ext import ContextTypes

from helpers import check_auth, execute_script_generic
from format import format_disk_space_status, format_gpu_status
from keyboards import get_back_disk, get_back_gpu, get_cancel_menu, get_disk_usage_menu, get_gpu_usage_menu, get_main_menu, get_scripts_menu, get_back_button
from config import SCRIPTS_DIR
from utils import get_disk_space_report, get_gpu_info


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    linux_user = await check_auth(update)
    if not linux_user:
        return

    context.user_data.pop("pending_action", None)
    msg = (
        f"👋 **Benvenuto `{linux_user}`!**\n"
        f"🖥️ _Pannello di Controllo Server_\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 **GPU Status**\n"
        f"   └ Monitora i tuoi processi GPU attivi\n\n"
        f"📂 **Script**\n"
        f"   └ Esegui script direttamente da qui\n\n"
        f"💽 **Disk Usage**\n"
        f"   └ Scopri chi vuole le mazzate su `/home`\n\n"
        f"🔐 **Autologin**\n"
        f"   └ Attiva la connessione internet\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Seleziona un'opzione dal menu qui sotto_ 👇"
    )
    kb = get_main_menu()

    if update.callback_query:
        await update.callback_query.edit_message_text(
            msg, reply_markup=kb, parse_mode="Markdown"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=msg,
            reply_markup=kb,
            parse_mode="Markdown",
        )

        if update.message:
            try:
                await update.message.delete()
            except Exception:
                pass

async def run_command_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Richiede comando personalizzato"""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    context.user_data['pending_action'] = {
        'type': 'run_command',
        'message_id': query.message.message_id
    }
    
    await query.edit_message_text(
        text="⚡️ **Run Command**\n\n"
             "Inserisci il comando da eseguire:\n\n"
             "_Esempio:_ `ls -la /home` oppure `python3 script.py`",
        reply_markup=get_cancel_menu(),
        parse_mode="Markdown"
    )

async def list_scripts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth(update):
        return

    try:
        files = sorted(
            [
                f
                for f in os.listdir(SCRIPTS_DIR)
                if f.endswith(".sh") or f.endswith(".py")
            ]
        )
        kb = get_scripts_menu(files)
        await update.callback_query.edit_message_text(
            "📂 Seleziona uno script:", reply_markup=kb
        )
    except Exception as e:
        await update.callback_query.edit_message_text(
            f"Errore folder script: {e}", reply_markup=get_back_button()
        )

async def autologin_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await execute_script_generic(
        update,
        context,
        "login_auto.sh",
        [],
        folder=os.path.expanduser("~/script/private"),
        message_to_edit=query.message,
    )

async def gpu_check_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra il menu delle opzioni di gpu check"""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    kb = get_gpu_usage_menu(linux_user)
    
    await query.edit_message_text(
        text="🖥️ **GPU Status - Seleziona opzione:**\n\n"
             f"👤 Visualizza solo i tuoi processi ({linux_user}) \n"
             "🏠 Visualizza tutti i processi",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    
async def gpu_check_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra tutti i processi GPU"""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    await query.edit_message_text(
        text="⏳ Recupero stato GPU in corso...", parse_mode="Markdown"
    )

    processes = get_gpu_info()
    msg_text = format_gpu_status(processes, filter_user=None)
    
    await query.edit_message_text(
        text=msg_text,
        reply_markup=get_back_gpu(),
        parse_mode="Markdown",
    )
    
async def gpu_check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra solo i processi GPU dell'utente"""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    await query.edit_message_text(
        text="⏳ Recupero stato GPU in corso...", parse_mode="Markdown"
    )

    processes = get_gpu_info()
    msg_text = format_gpu_status(processes, filter_user=linux_user)
    
    await query.edit_message_text(
        text=msg_text,
        reply_markup=get_back_gpu(),
        parse_mode="Markdown",
    )
    
    
    
async def disk_check_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra il menu delle opzioni di disk check"""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    kb = get_disk_usage_menu(linux_user)
    
    await query.edit_message_text(
        text="💽 **Disk Usage - Seleziona opzione:**\n\n"
             "🏠 Analizza `/home` \n"
             f"👤 Analizza `/home/{linux_user}` \n"
             "🆓 Inserisci path personalizzato",
        reply_markup=kb,
        parse_mode="Markdown"
    )

async def disk_check_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analizza /home"""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    await query.edit_message_text(
        text="⏳ Analisi disco `/home` in corso.\nPotrebbe richiedere alcuni minuti...", parse_mode="Markdown"
    )

    try:
        raw_report = get_disk_space_report(path="/home", as_root=True)
        report = format_disk_space_status(raw_report, path="/home")
    except Exception as e:
        report = f"💥 Errore scansione disco: {e}"
    
    await query.edit_message_text(
        text=report,
        reply_markup=get_back_disk(),
        parse_mode="Markdown",
    )

async def disk_check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analizza /home/username"""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    user_path = f"/home/{linux_user}"
    
    await query.edit_message_text(
        text=f"⏳ Analisi disco `{user_path}` in corso.\nPotrebbe richiedere alcuni minuti...", parse_mode="Markdown"
    )

    try:
        raw_report = get_disk_space_report(path=user_path, as_root=False)
        report = format_disk_space_status(raw_report, path=user_path)
    except Exception as e:
        report = f"💥 Errore scansione disco: {e}"
    
    await query.edit_message_text(
        text=report,
        reply_markup=get_back_disk(),
        parse_mode="Markdown",
    )

async def disk_check_custom_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Richiede path personalizzato"""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    context.user_data['pending_action'] = {
        'type': 'disk_check_custom',
        'message_id': query.message.message_id
    }
    
    await query.edit_message_text(
        text="📝 Inserisci il path da analizzare (es. `/home/username/folder`):",
        reply_markup=get_cancel_menu(),
        parse_mode="Markdown"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # Navigazione Base
    if data == "cmd_start":
        await start(update, context)
    elif data == "cmd_scripts":
        await list_scripts(update, context)
    elif data == "cmd_run":
        await run_command_prompt(update, context)

    elif data == "cmd_status":
        await gpu_check_menu(update, context)
    elif data == 'cmd_gpu_check_all':
        await gpu_check_all(update, context)
    elif data == 'cmd_gpu_check_user':
        await gpu_check_user(update, context)
    
    # Disk Usage
    elif data == "cmd_disk_check":
        await disk_check_menu(update, context)
    elif data == 'cmd_disk_check_all':
        await disk_check_all(update, context)
    elif data == 'cmd_disk_check_user':
        await disk_check_user(update, context)
    elif data == 'cmd_disk_check_custom':
        await disk_check_custom_prompt(update, context)
    
    # Autologin     
    elif data == "cmd_autologin_prompt":
        await autologin_prompt(update, context)
    elif data == "cancel_action":
        context.user_data.pop("pending_action", None)
        await start(update, context)

    elif data.startswith("run_"):
        script = data[4:]
        await execute_script_generic(update, context, script, [])
