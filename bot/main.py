import sys 
import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from command import run, start, status, scripts
from config import TOKEN
# Configura il logging per vedere se il bot è vivo
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == "__main__":
    if not TOKEN:
        print("Errore: TOKEN non trovato nel file .env")
        sys.exit(1)

    application = ApplicationBuilder().token(TOKEN).build()

    # Collega i comandi alle funzioni
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('scripts', scripts))
    application.add_handler(CommandHandler('run', run)) # Secondo comando
    application.run_polling()