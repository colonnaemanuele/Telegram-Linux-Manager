from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("⚡️ Run Command", callback_data="cmd_run")],
        [
            InlineKeyboardButton("📊 GPU Status", callback_data="cmd_status"),
            InlineKeyboardButton("📂 Script Manager", callback_data="cmd_scripts"),
        ],
        [
            InlineKeyboardButton("💽 Disk Usage", callback_data="cmd_disk_check"),
            InlineKeyboardButton("🔐 Autologin", callback_data="cmd_autologin_prompt"),
        ],
        [
            InlineKeyboardButton("👥 Users Banner", callback_data="cmd_users"),
            InlineKeyboardButton("🤖 Leonardo HPC", callback_data="cmd_leonardo")
        ],
        [InlineKeyboardButton("🔄 Aggiorna Menu", callback_data="cmd_start")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_leonardo_menu():
    """Menu opzioni Leonardo HPC"""
    keyboard = [
        [InlineKeyboardButton("🛰️ Stato Leonardo", callback_data="cmd_leonardo_status")],
        [InlineKeyboardButton("🔙 Menu Principale", callback_data="cmd_start")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_scripts_menu(files):
    """Menu lista script"""
    keyboard = []
    # Crea un pulsante per ogni file
    for file_name in files:
        keyboard.append(
            [InlineKeyboardButton(f"🚀 {file_name}", callback_data=f"run_{file_name}")]
        )

    keyboard.append([InlineKeyboardButton("🔙 Indietro", callback_data="cmd_start")])
    return InlineKeyboardMarkup(keyboard)


def get_disk_usage_menu(linux_user):
    """Menu opzioni disk usage"""
    keyboard = [
        [InlineKeyboardButton("🏠 /home", callback_data="cmd_disk_check_all")],
        [InlineKeyboardButton(f"👤 /home/{linux_user}", callback_data="cmd_disk_check_user")],
        [InlineKeyboardButton("🆓 Path personalizzato", callback_data="cmd_disk_check_custom")],
        [InlineKeyboardButton("🔙 Menu Principale", callback_data="cmd_start")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_gpu_usage_menu(linux_user):
    """Menu opzioni gpu"""
    keyboard = [
        [InlineKeyboardButton(f"👤 Solo i tuoi ({linux_user})", callback_data="cmd_gpu_check_user")],
        [InlineKeyboardButton("🏠 Tutti i processi", callback_data="cmd_gpu_check_all")],
        [InlineKeyboardButton("🔙 Menu Principale", callback_data="cmd_start")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_menu():
    """Menu semplice per annullare un'operazione in attesa di input"""
    keyboard = [[InlineKeyboardButton("❌ Annulla", callback_data="cancel_action")]]
    return InlineKeyboardMarkup(keyboard)


def get_back_button():
    """Tasto indietro standard"""
    keyboard = [[InlineKeyboardButton("🔙 Menu Principale", callback_data="cmd_start")]]
    return InlineKeyboardMarkup(keyboard)


def get_back_disk():
    """Tasto indietro al menu disk"""
    keyboard = [[InlineKeyboardButton("🔙 Menu Disk Usage", callback_data="cmd_disk_check")]]
    return InlineKeyboardMarkup(keyboard)


def get_back_gpu():
    """Tasto indietro al menu gpu"""
    keyboard = [[InlineKeyboardButton("🔙 Menu GPU Status", callback_data="cmd_status")]]
    return InlineKeyboardMarkup(keyboard)


def get_back_leonardo():
    """Tasto indietro al menu Leonardo"""
    keyboard = [[InlineKeyboardButton("🔙 Menu Leonardo", callback_data="cmd_leonardo")]]
    return InlineKeyboardMarkup(keyboard)


def get_users_menu(active_users, hidden_users=None):
    """Menu utenti attivi con azione disconnessione."""
    hidden_users = set(hidden_users or [])
    keyboard = []
    row = []

    for entry in active_users:
        username = entry.get("username", "")
        if username in hidden_users:
            continue

        sessions = entry.get("sessions", 0)
        label = f"🔌 {username} ({sessions})"
        row.append(InlineKeyboardButton(label, callback_data=f"cmd_user_disconnect:{username}"))

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("✍️ Inserisci username", callback_data="cmd_user_manual")])

    keyboard.append([InlineKeyboardButton("🔄 Aggiorna Lista", callback_data="cmd_users")])
    keyboard.append([InlineKeyboardButton("🔙 Menu Principale", callback_data="cmd_start")])
    return InlineKeyboardMarkup(keyboard)


def get_back_users():
    """Tasto indietro al menu users."""
    keyboard = [[InlineKeyboardButton("🔙 Menu Users", callback_data="cmd_users")]]
    return InlineKeyboardMarkup(keyboard)
