# Telegram Linux Manager Bot

A simple server information manager bot for your Linux server, built using Python and the Telegram Bot API.

## Table of Contents
- [Requirements](#requirements)
- [Setup](#setup)
- [⚠️ Security Notice](#⚠️-security-notice)
- [Run the Bot](#run-the-bot)
- [Commands](#commands)
- [Files](#files)
- [Notes](#notes)

## Requirements
- Python 3.11+
- Install project dependencies using:
    ```bash
    pip install -r requirements.txt
    ```

## Setup
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/Telegram-Linux-Manager.git
   cd Telegram-Linux-Manager
   ```

2. **Copy Environment File:**
   ```bash
   cp .env.sample .env
   ```

3. **Edit the `.env` File:**
   Open the `.env` file in a text editor and set the required environment variables:
   ```plaintext
   TOKEN=your_telegram_bot_token
   USER_MAPPING={"your_telegram_user_id": "your_linux_username"}
   ```
   - Replace `your_telegram_bot_token` with the token you received from [BotFather](https://core.telegram.org/bots#botfather).
   - Replace `your_telegram_user_id` with your Telegram user ID and `your_linux_username` with your Linux username.

4. **Install Dependencies:**
   Make sure you have the required Python packages installed:
   ```bash
   pip install python-dotenv python-telegram-bot requests
   ```

## ⚠️ Security Notice
**IMPORTANT:** Never commit your `.env` file or share your Telegram bot token publicly!
- The `.env` file is already in `.gitignore` to prevent accidental commits.
- Keep your `TOKEN` and `USER_MAPPING` configuration private.
- Do not share screenshots or logs that might contain your bot token or user IDs.
- Review all code before running it with elevated privileges (sudo).

## Run the Bot
- Start the bot normally:
    ```bash
    python main.py
    ```
- Alternatively, you can run it in the background or as a service.

## Commands
1. **`/start`**: Sends a welcome message and displays the list of available commands.
2. **`/status`**: Checks active processes and returns the formatted result in Markdown.
3. **`/scripts`**: Lists the files present in the configured `SCRIPTS_DIR`.
4. **`/run <script> [args...]`**: Executes a script present in `SCRIPTS_DIR` with optional arguments.

## Files
- `.env`, `.env.sample` — Environment variables.
- `main.py` — Entry point for the bot.
- `command.py` — Command definitions and CLI logic.
- `config.py` — Configuration loader.
- `utils.py` — Helper utilities.
- `helpers.py` — Helper functions for bot operations.
- `keyboards.py` — Keyboard layouts for Telegram bot interactions.
- `format.py` — Formatting functions for output messages.

## Notes
- Use a virtual environment for isolation.
- Adjust logging/output redirection as needed.
- Ensure your bot has the necessary permissions to operate in the Telegram chat.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.