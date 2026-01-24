from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu():
    """Tastiera principale: Matrice 2x2 + Tasto Aggiorna"""
    keyboard = [
        [
            InlineKeyboardButton("📊 GPU Status", callback_data="cmd_status"),
            InlineKeyboardButton("📂 Script Manager", callback_data="cmd_scripts"),
        ],
        [
            InlineKeyboardButton("💽 Disk Usage", callback_data="cmd_disk_check"),
            InlineKeyboardButton("🔐 Autologin", callback_data="cmd_autologin_prompt"),
        ],
        [InlineKeyboardButton("⚡️ Run Command", callback_data="cmd_run")],
        [InlineKeyboardButton("🔄 Aggiorna Menu", callback_data="cmd_start")],
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