
import json
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT NOT NULL, status TEXT NOT NULL, due_date TEXT)')

    # Backward-compatible migration for existing DBs created before due_date existed.
    columns = [row['name'] for row in conn.execute('PRAGMA table_info(tasks)').fetchall()]
    if 'due_date' not in columns:
        conn.execute('ALTER TABLE tasks ADD COLUMN due_date TEXT')

    conn.execute(
        'CREATE TABLE IF NOT EXISTS forecast_cache ('
        'task_key TEXT PRIMARY KEY, '
        'task_description TEXT NOT NULL, '
        'forecast_json TEXT NOT NULL, '
        'updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'
    )

    conn.commit()
    conn.close()

def add_task(description: str, due_date: str):
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (description, status, due_date) VALUES (?, ?, ?)', (description, 'pending', due_date))
    conn.commit()
    conn.close()

def get_tasks():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()
    return tasks

def update_task_status(task_id: int, status: str):
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id: int):
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

def update_task_description(task_id: int, description: str):
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET description = ? WHERE id = ?', (description, task_id))
    conn.commit()
    conn.close()

def get_cached_forecast(task_key: str):
    conn = get_db_connection()
    row = conn.execute(
        'SELECT forecast_json FROM forecast_cache WHERE task_key = ?',
        (task_key,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    try:
        return json.loads(row['forecast_json'])
    except json.JSONDecodeError:
        return None

def save_cached_forecast(task_key: str, task_description: str, forecast: dict):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO forecast_cache (task_key, task_description, forecast_json, updated_at) '
        'VALUES (?, ?, ?, CURRENT_TIMESTAMP) '
        'ON CONFLICT(task_key) DO UPDATE SET '
        'task_description = excluded.task_description, '
        'forecast_json = excluded.forecast_json, '
        'updated_at = CURRENT_TIMESTAMP',
        (task_key, task_description, json.dumps(forecast))
    )
    conn.commit()
    conn.close()

create_table()
