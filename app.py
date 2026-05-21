
import asyncio
from multiprocessing import Process
from bot.telegram_bot import main as telegram_main
from dashboard.app import app as flask_app

def run_flask():
    flask_app.run(debug=True, port=5001, use_reloader=False)

if __name__ == "__main__":
    print("Starting the application...")
    
    # Run Flask app in a separate process
    flask_process = Process(target=run_flask)
    flask_process.start()

    # Run Telegram bot
    try:
        telegram_main()
    except KeyboardInterrupt:
        print("Stopping application...")
    finally:
        flask_process.terminate()
        flask_process.join()
        print("Application stopped.")
