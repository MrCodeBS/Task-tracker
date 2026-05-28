
from flask import Flask, render_template, request
from database import db
from groq_api import forecasting
from core import logic

app = Flask(__name__)


def _task_by_id(tasks, task_id):
    for task in tasks:
        if str(task["id"]) == str(task_id):
            return task
    return None


@app.route('/', methods=['GET', 'POST'])
def index():
    rows = db.get_tasks()
    tasks = logic.format_tasks_list(rows)
    forecast = None
    forecast_error = None
    selected_task_id = ""
    custom_description = ""

    if request.method == 'POST':
        selected_task_id = request.form.get('task_id', '').strip()
        custom_description = request.form.get('custom_description', '').strip()

        source_description = ""
        if custom_description:
            source_description = custom_description
        elif selected_task_id:
            selected_task = _task_by_id(tasks, selected_task_id)
            if selected_task:
                source_description = selected_task['description']
            else:
                forecast_error = "Selected task was not found."
        else:
            forecast_error = "Choose a task or enter a custom description."

        if source_description:
            result = forecasting.get_forecast(source_description)
            if 'error' in result:
                forecast_error = result['error']
            else:
                forecast = result
                forecast['source_description'] = source_description

    summary = logic.tasks_summary(tasks)
    total_tasks = summary['total']
    done_tasks = summary['done']
    pending_tasks = summary['pending']
    due_tasks = summary['due']

    return render_template(
        'index.html',
        tasks=tasks,
        total_tasks=total_tasks,
        done_tasks=done_tasks,
        pending_tasks=pending_tasks,
        due_tasks=due_tasks,
        forecast=forecast,
        forecast_error=forecast_error,
        selected_task_id=selected_task_id,
        custom_description=custom_description,
    )

if __name__ == '__main__':
    app.run(debug=True, port=5001)
