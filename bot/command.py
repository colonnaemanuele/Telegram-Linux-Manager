import asyncio
import os
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from helpers import check_auth, execute_script_generic
from format import format_disk_space_status, format_gpu_status, format_leonardo_status
from keyboards import (
    get_back_button,
    get_back_disk,
    get_back_gpu,
    get_back_leonardo,
    get_back_users,
    get_cancel_menu,
    get_condor_pagination,
    get_disk_usage_menu,
    get_gpu_usage_menu,
    get_leonardo_menu,
    get_main_menu,
    get_scripts_menu,
    get_users_menu,
)
from config import ALLOWED_LINUX_USERS, SCRIPTS_DIR
from utils import (
    disconnect_user_temporarily,
    get_active_users,
    get_disk_space_report,
    get_gpu_info,
    get_leonardo_status,
    get_logger,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    linux_user = await check_auth(update)
    if not linux_user:
        return

    logger = get_logger("command.start", linux_user)
    logger.info("Accessed main menu")
    context.user_data.pop("pending_action", None)
    context.user_data.pop("condor_pages", None)
    context.user_data.pop("condor_page_index", None)
    msg = (
        f"👋 **Benvenuto `{linux_user}`!**\n"
        f"🖥️ _Pannello di Controllo Server_\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 **GPU Status**\n"
        f"   └ Monitora i tuoi processi GPU attivi\n\n"
        f"📂 **Script**\n"
        f"   └ Esegui script direttamente da qui\n\n"
        f"💽 **Disk Usage**\n"
        f"   └ Scopri chi vuole le mazzate su `/home`\n\n"
        f"👥 **Users**\n"
        f"   └ Utenti attivi e disconnessione temporanea\n\n"
        f"🔐 **Autologin**\n"
        f"   └ Attiva la connessione internet\n\n"
        f"🤖 **Leonardo HPC**\n"
        f"   └ Leggi stato operativo da CINECA\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Seleziona un'opzione dal menu qui sotto_ 👇"
    )
    kb = get_main_menu()

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                msg, reply_markup=kb, parse_mode="Markdown"
            )
        except BadRequest:
            pass
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

    logger = get_logger("command.run", linux_user)
    logger.info("Requested custom command execution")

    query = update.callback_query
    context.user_data['pending_action'] = {
        'type': 'run_command',
        'message_id': query.message.message_id
    }
    
    await query.edit_message_text(
        text="⚡️ **Run Command**\n\n"
             "Non sei amministratore =)\n\n"
             "Inserisci il comando da eseguire:\n\n"
             "_Esempio:_ `ls -la /home` oppure `python3 script.py`",
        reply_markup=get_cancel_menu(),
        parse_mode="Markdown"
    )

async def list_scripts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    linux_user = await check_auth(update)
    if not linux_user:
        return

    logger = get_logger("command.scripts", linux_user)
    logger.info("Listed scripts")

    try:
        files = sorted(
            [
                f
                for f in os.listdir(SCRIPTS_DIR)
                if f.endswith(".sh") or f.endswith(".py")
            ]
        )
        kb = get_scripts_menu(files)
        await update.callback_query.edit_message_text("📂 Seleziona uno script:", reply_markup=kb)
    except Exception as e:
        await update.callback_query.edit_message_text(f"Errore folder script: {e}", reply_markup=get_back_button())

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


async def leonardo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra il sottomenu Leonardo."""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    await query.edit_message_text(
        text="🤖 Server HPC\n\nSeleziona un'azione:",
        reply_markup=get_leonardo_menu(),
    )


async def leonardo_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recupera e mostra lo stato Leonardo dalla pagina CINECA."""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    logger = get_logger("command.leonardo", linux_user)
    logger.info("Checked Leonardo HPC status")

    query = update.callback_query
    await query.edit_message_text("⏳ Recupero stato Leonardo da CINECA in corso...")

    status_data = await asyncio.to_thread(get_leonardo_status)
    msg_text = format_leonardo_status(status_data)

    await query.edit_message_text(
        text=msg_text,
        reply_markup=get_back_leonardo(),
    )


async def leonardo_condor_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Richiede username e avvia il controllo Condor su RECAS."""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    context.user_data["pending_action"] = {
        "type": "leonardo_condor_user",
        "message_id": query.message.message_id,
    }

    await query.edit_message_text(
        text=(
            "🧮 **RECAS Condor**\n\n"
            "Inserisci lo username HPC da controllare."
        ),
        reply_markup=get_cancel_menu(),
        parse_mode="Markdown",
    )


async def leonardo_condor_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Naviga pagine risultato Condor nello stesso messaggio."""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    data = query.data or ""
    page_arg = data.split(":", 1)[1] if ":" in data else "0"

    if page_arg == "noop":
        return

    pages = context.user_data.get("condor_pages") or []
    if not pages:
        await query.edit_message_text(
            text="⚠️ Nessuna pagina Condor disponibile. Lancia una nuova query.",
            reply_markup=get_back_leonardo(),
        )
        return

    try:
        idx = int(page_arg)
    except ValueError:
        idx = 0

    idx = max(0, min(idx, len(pages) - 1))
    context.user_data["condor_page_index"] = idx

    await query.edit_message_text(
        text=pages[idx],
        reply_markup=get_condor_pagination(idx, len(pages)),
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

    logger = get_logger("command.gpu_check", linux_user)
    logger.info("Checked GPU status (all)")

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

    logger = get_logger("command.gpu_check", linux_user)
    logger.info("Checked GPU status (personal)")

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

    logger = get_logger("command.disk_check", linux_user)
    logger.info("Checked disk usage (/home)")

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

    logger = get_logger("command.disk_check", linux_user)
    logger.info(f"Checked disk usage ({linux_user} directory)")

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


async def users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra gli utenti attivi e permette la disconnessione."""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    logger = get_logger("command.users", linux_user)
    logger.info("Viewed active users")

    query = update.callback_query
    active_users = get_active_users()
    protected_users = ALLOWED_LINUX_USERS
    actionable_users = [
        entry for entry in active_users if entry.get("username") not in protected_users
    ]

    if not active_users:
        try:
            await query.edit_message_text(
                text="👥 Nessun utente attivo rilevato al momento.",
                reply_markup=get_back_users(),
            )
        except BadRequest as exc:
            if "Message is not modified" not in str(exc):
                raise
        return

    lines = [
        "👥 **Utenti attivi adesso**",
        "",
        "Chi vuoi punire tra questi coglioni?",
        "",
    ]
    for entry in active_users:
        username = entry.get("username", "unknown")
        sessions = entry.get("sessions", 0)
        host = entry.get("host", "local")
        protected_label = " | `protetto`" if username in protected_users else ""
        lines.append(f"• `{username}` | `{sessions}` | `{host}`{protected_label}")

    lines.extend([
        "",
        f"Utenti disconnettibili ora: `{len(actionable_users)}`",
        "Seleziona un utente dai pulsanti qui sotto o usa il tasto per inserirlo a mano.",
    ])

    try:
        await query.edit_message_text(
            text="\n".join(lines),
            reply_markup=get_users_menu(active_users, hidden_users=protected_users),
            parse_mode="Markdown",
        )
    except BadRequest as exc:
        if "Message is not modified" not in str(exc):
            raise


async def user_disconnect_manual_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Richiede uno username manuale da disconnettere."""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    query = update.callback_query
    context.user_data["pending_action"] = {
        "type": "user_disconnect_manual",
        "message_id": query.message.message_id,
    }

    await query.edit_message_text(
        text="✍️ Inserisci lo username Linux da disconnettere per 2 minuti:",
        reply_markup=get_cancel_menu(),
    )


async def user_disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user: str):
    """Disconnette un utente e lo blocca per 2 minuti."""
    linux_user = await check_auth(update)
    if not linux_user:
        return

    logger = get_logger("command.users", linux_user)

    query = update.callback_query
    if target_user in ALLOWED_LINUX_USERS:
        await query.edit_message_text(
            text=f"🛡️ L'utente {target_user} e' protetto e non puo' essere disconnesso.",
            reply_markup=get_back_users(),
        )
        return

    await query.edit_message_text(f"⏳ Disconnessione di {target_user} in corso...")

    ok, detail = disconnect_user_temporarily(target_user, timeout_seconds=120)
    if ok:
        logger.info(f"Disconnected user: {target_user}")
        text = (
            f"✅ Utente {target_user} disconnesso.\n"
            "⏱️ Blocco login attivo per 2 minuti."
        )
    else:
        text = (
            f"💥 Impossibile disconnettere {target_user}.\n"
            f"Dettaglio: {detail}"
        )

    await query.edit_message_text(
        text=text,
        reply_markup=get_back_users(),
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
    elif data == "cmd_users":
        await users_menu(update, context)
    elif data == "cmd_user_manual":
        await user_disconnect_manual_prompt(update, context)
    elif data == "cmd_leonardo":
        await leonardo_menu(update, context)
    elif data == "cmd_leonardo_status":
        await leonardo_status(update, context)
    elif data == "cmd_leonardo_condor":
        await leonardo_condor_status(update, context)
    elif data.startswith("cmd_condor_page:"):
        await leonardo_condor_page(update, context)

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

    # User Disconnect
    elif data.startswith("cmd_user_disconnect:"):
        target_user = data.split(":", 1)[1].strip()
        await user_disconnect(update, context, target_user)

    elif data.startswith("run_"):
        script = data[4:]
        if 'login' in script.lower():
            context.user_data['pending_action'] = {
                'type': 'login_username',
                'script': script,
                'message_id': query.message.message_id
            }
            await query.edit_message_text(
                text=f"🔐 **Login Script: `{script}`**\n\n"
                     "📝 Inserisci lo **username**:",
                reply_markup=get_cancel_menu(),
                parse_mode="Markdown"
            )
        else:
            await execute_script_generic(update, context, script, [], message_to_edit=query.message)