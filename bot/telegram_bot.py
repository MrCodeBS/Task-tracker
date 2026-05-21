
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
from database import db
from groq_api import forecasting

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# States for conversation
DESCRIPTION, DUE_DATE, ADD_DESCRIPTION_ID, ADD_DESCRIPTION_TEXT = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome to the Task Tracker Bot! Use /add, /tasks, /list, /done <id>, /delete <id>, /add_description, /forecast <task>, or /forecast_refresh <task>")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please provide a task description.")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Please provide a due date (e.g., YYYY-MM-DD) or type \"none\".")
    return DUE_DATE

async def due_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    due_date_val = update.message.text
    if due_date_val.lower() == "none":
        due_date_val = None
    description_val = context.user_data["description"]
    db.add_task(description_val, due_date_val)
    await update.message.reply_text(f"Task \"{description_val}\" added.")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Action cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    all_tasks = db.get_tasks()
    if all_tasks:
        message = "Your tasks:\n"
        for task in all_tasks:
            due_str = f" (Due: {task['due_date']})" if task["due_date"] else ""
            message += f"{task['id']}: {task['description']} [{task['status']}] {due_str}\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("You have no tasks.")

async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        task_id = int(context.args[0])
        db.update_task_status(task_id, "done")
        await update.message.reply_text(f"Task {task_id} marked as done.")
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid task ID: /done <id>")

async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        task_id = int(context.args[0])
        db.delete_task(task_id)
        await update.message.reply_text(f"Task {task_id} deleted.")
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid task ID: /delete <id>")

async def forecast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task_description = " ".join(context.args)
    if task_description:
        forecast_data = forecasting.get_forecast(task_description)
        if "error" in forecast_data:
            await update.message.reply_text(forecast_data["error"])
        else:
            msg = f"Forecast for \"{task_description}\":\n"
            msg += f"Mood: {forecast_data.get('mood', 'N/A')}\n"
            msg += f"Stress: {forecast_data.get('stress', 'N/A')}\n"
            msg += f"Load: {forecast_data.get('load', 'N/A')}"
            await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Please provide a task description: /forecast <task>")

async def forecast_refresh_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task_description = " ".join(context.args)
    if task_description:
        forecast_data = forecasting.get_forecast(task_description, force_refresh=True)
        if "error" in forecast_data:
            await update.message.reply_text(forecast_data["error"])
        else:
            msg = f"Refreshed forecast for \"{task_description}\":\n"
            msg += f"Mood: {forecast_data.get('mood', 'N/A')}\n"
            msg += f"Stress: {forecast_data.get('stress', 'N/A')}\n"
            msg += f"Load: {forecast_data.get('load', 'N/A')}"
            await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Please provide a task description: /forecast_refresh <task>")

async def add_description_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please provide the task ID to update.")
    return ADD_DESCRIPTION_ID

async def add_description_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        task_id = int(update.message.text)
        context.user_data["task_id"] = task_id
        await update.message.reply_text("Please provide the additional description.")
        return ADD_DESCRIPTION_TEXT
    except ValueError:
        await update.message.reply_text("Invalid ID. Please provide a number.")
        return ADD_DESCRIPTION_ID

async def add_description_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    task_id = context.user_data["task_id"]
    extra_desc = update.message.text
    all_tasks = db.get_tasks()
    task_item = next((t for t in all_tasks if t["id"] == task_id), None)
    if task_item:
        new_desc = f"{task_item['description']}\n{extra_desc}"
        db.update_task_description(task_id, new_desc)
        await update.message.reply_text(f"Task {task_id} updated.")
    else:
        await update.message.reply_text("Task not found.")
    context.user_data.clear()
    return ConversationHandler.END

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Unknown command. Type /start for help.")

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            DUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, due_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    desc_conv = ConversationHandler(
        entry_points=[CommandHandler("add_description", add_description_start)],
        states={
            ADD_DESCRIPTION_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description_id)],
            ADD_DESCRIPTION_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(add_conv)
    application.add_handler(desc_conv)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tasks", tasks))
    application.add_handler(CommandHandler("list", tasks))
    application.add_handler(CommandHandler("done", done_cmd))
    application.add_handler(CommandHandler("delete", delete_cmd))
    application.add_handler(CommandHandler("forecast", forecast_cmd))
    application.add_handler(CommandHandler("forecast_refresh", forecast_refresh_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    application.run_polling()

if __name__ == "__main__":
    main()