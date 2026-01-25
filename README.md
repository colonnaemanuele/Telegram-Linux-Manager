# Telegram Linux Manager Bot

A powerful server information manager bot for your Linux server, built using Python and the Telegram Bot API. Monitor GPU usage, manage disk space, execute scripts, and run custom commands directly from Telegram.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
- [⚠️ Security Notice](#⚠️-security-notice)
- [Running the Bot](#running-the-bot)
- [Bot Features](#bot-features)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

✅ **GPU Monitoring** - Track active GPU processes and VRAM usage  
✅ **Disk Analysis** - Analyze disk usage across `/home` with color-coded alerts  
✅ **Script Manager** - Execute custom scripts with arguments  
✅ **Command Runner** - Run arbitrary shell commands as your user  
✅ **Auto-login** - Activate internet connectivity with one click  
✅ **Beautiful Formatting** - Clean, readable Markdown output in Telegram  
✅ **User Authentication** - Telegram ID-based access control  

## Requirements

- **Python 3.11+**
- **Linux Server** with GPU support (NVIDIA GPU for GPU features)
- **uv Astral** (Python package manager)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Telegram-Linux-Manager.git
cd Telegram-Linux-Manager
```

### 2. Create Virtual Environment and install dependences

```bash
uv sync
```

### 3. Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Copy the bot token provided (it looks like `123456789:ABCdefGHIjklmnoPQRstuvWXYZ`)

### 4. Get Your Telegram User ID

1. Search for [@userinfobot](https://t.me/userinfobot) on Telegram
2. Start the bot and it will show your user ID
3. Note this number down

### 5. Configure Environment Variables

```bash
cp .env.sample .env
```

Edit `.env` with your favorite editor:

```bash
nano .env
```

Set the following variables:

```plaintext
TOKEN=your_telegram_bot_token_here
USER_MAPPING={"your_telegram_user_id": "your_linux_username"}
SCRIPTS_DIR=~/script/scripts
```

**Example:**
```plaintext
TOKEN=123456789:ABCdefGHIjklmnoPQRstuvWXYZ
USER_MAPPING = "123456789:username,987654321:anotheruser"
SCRIPTS_DIR=~/scripts
```

### 6. Configure Sudoers (Optional but Recommended)

For some features (like analyzing `/home` or GPU info), you may need sudo access without password:

```bash
sudo visudo
```

Add these lines at the end:

```bash
your_username ALL=(ALL) NOPASSWD: /usr/bin/nvidia-smi
your_username ALL=(ALL) NOPASSWD: /usr/bin/du
your_username ALL=(ALL) NOPASSWD: /path/to/script.sh
```

Replace `your_username` and paths accordingly.


if you are a sudouser in your server just add:

```bash
your_username ALL=(ALL) NOPASSWD: ALL
```

## ⚠️ Security Notice

**CRITICAL:** Never share or commit your `.env` file!

- ✅ `.env` is already in `.gitignore`
- ✅ Keep your `TOKEN` secret
- ✅ Don't share your Telegram User ID publicly
- ✅ Review all scripts before execution
- ✅ Use in private chats only, never in groups
- ✅ Regenerate bot token if exposed

See [SECURITY.md](SECURITY.md) for detailed security guidelines.

## Running the Bot

### Simple Method

```bash
cd /path/to/Telegram-Linux-Manager
uv run bot/main.py
```

### Background Process (using nohup)

```bash
nohup python /path/to/bot/main.py > bot.log 2>&1 &
```

### Systemd Service (Recommended for Production)

Create `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Linux Manager Bot
After=network.target

[Service]
# L'utente che deve eseguire lo script (NON usare root se possibile)
User=username
Group=group

# La cartella dove risiede il tuo codice (importante per file .env o database locali)
WorkingDirectory=/path/to/Telegram-Linux-Manager

# SE USI UN VIRTUALENV: metti il percorso completo dell'eseguibile python nel venv
# Esempio: /home/utente/bot/venv/bin/python main.py
ExecStart=/path/to/venv/bin/python /path/to/bot/main.py

# Riavvia il bot automaticamente se crasha
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable and start:

```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

View logs:

```bash
sudo journalctl -u telegram-bot -f
```

## Bot Features

### 📊 GPU Status
- **Solo i tuoi processi** - Shows only your active GPU processes
- **Tutti i processi** - Shows all GPU processes on the system
- Displays: GPU ID, PID, User, Memory Usage, Command

### 💽 Disk Usage
- **Analizza /home** - Scan entire `/home` directory
- **Analizza /home/username** - Scan only your home directory
- **Path personalizzato** - Analyze any custom path
- Color-coded alerts:
  - 🟢 < 100GB
  - 🟡 100-350GB
  - 🟠 350-600GB
  - 🔴 > 600GB

### 📂 Script Manager
- Lists all `.sh` and `.py` files in `SCRIPTS_DIR`
- Execute scripts with one click
- Pass arguments to scripts

### ⚡️ Run Command
- Execute any shell command
- Runs as your user (not root)
- Perfect for one-off commands
- Max timeout: 30 seconds

### 🔐 Autologin
- Activates internet connectivity on the server
- Requires `private/login_auto.sh` script (based on your server)
- One-click activation

## Project Structure

```
Telegram-Linux-Manager/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── command.py           # Command handlers
│   ├── config.py            # Configuration loader
│   ├── format.py            # Output formatting
│   ├── helpers.py           # Helper functions
│   ├── keyboards.py         # Telegram keyboard layouts
│   ├── utils.py             # Utility functions
│   ├── .env                 # Environment variables (DO NOT COMMIT)
│   └── .env.sample          # Environment template
├── README.md                # This file
├── SECURITY.md              # Security guidelines
├── LICENSE                  # MIT License
└── pyproject.toml           # Project metadata
```

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TOKEN` | Telegram Bot Token | `123456789:ABCdefGHIjklmnoPQRstuvWXYZ` |
| `USER_MAPPING` | User ID to Linux username mapping | `{"987654321": "emanuele"}` |
| `SCRIPTS_DIR` | Directory containing scripts | `~/script/scripts` |

### User Mapping

Add multiple users to `USER_MAPPING`:

```plaintext
USER_MAPPING={"user_id_1": "username_1", "user_id_2": "username_2"}
```

Only users in this mapping can access the bot.

## Troubleshooting

### Bot doesn't respond
- Check if `TOKEN` is correct
- Verify bot token with @BotFather
- Ensure your Telegram ID is in `USER_MAPPING`

### "Accesso negato" (Access Denied)
- Your Telegram ID is not in `USER_MAPPING`
- Add your ID to the configuration and restart

### GPU Status shows nothing
- GPU not properly configured on server
- NVIDIA drivers not installed
- User doesn't have permission to run `nvidia-smi`

### Disk Analysis is slow
- Large directories take time to analyze
- Timeout may occur with very large filesystems
- Consider analyzing smaller paths first

### Sudo commands fail
- Sudoers not configured properly
- Check `/etc/sudoers` configuration
- Run: `sudo -n nvidia-smi` to test sudo access

### "Cannot execute script"
- Script is not in `SCRIPTS_DIR`
- Script doesn't have execute permissions: `chmod +x script.sh`
- Python script issues: verify shebang line `#!/usr/bin/env python3`

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## Security Policy

Please review [SECURITY.md](SECURITY.md) before deploying this bot to production.

---

**Enjoy managing your Linux server from Telegram! 🚀**