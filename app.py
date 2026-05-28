
from multiprocessing import Process


def run_flask() -> None:
    from dashboard.app import app as flask_app

    flask_app.run(debug=True, port=5001, use_reloader=False)


def run_telegram_bot() -> None:
    from bot.telegram_bot import main as telegram_main

    telegram_main()


def main() -> None:
    print("Starting the application...")

    flask_process = Process(target=run_flask)
    flask_process.start()

    try:
        run_telegram_bot()
    except KeyboardInterrupt:
        print("Stopping application...")
    finally:
        flask_process.terminate()
        flask_process.join()
        print("Application stopped.")


if __name__ == "__main__":
    main()
