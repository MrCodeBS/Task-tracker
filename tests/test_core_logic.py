import pytest
from core import logic


def sample_row(id=1, description="Test task", status="pending", due_date=None):
    return {"id": id, "description": description, "status": status, "due_date": due_date}


def test_format_task_row_and_list():
    r = sample_row()
    formatted = logic.format_task_row(r)
    assert formatted["id"] == 1
    assert formatted["description"] == "Test task"
    assert formatted["status"] == "pending"

    lst = logic.format_tasks_list([r, sample_row(id=2, description="Other")])
    assert isinstance(lst, list) and len(lst) == 2


def test_tasks_summary_and_message():
    rows = [sample_row(id=1), sample_row(id=2, status="done", due_date="2026-06-01")]
    tasks = logic.format_tasks_list(rows)
    summary = logic.tasks_summary(tasks)
    assert summary["total"] == 2
    assert summary["done"] == 1
    assert summary["due"] == 1

    msg = logic.format_tasks_message(tasks)
    assert "Your tasks" in msg or "You have no tasks." not in msg


def test_normalize_and_build_desc():
    assert logic.normalize_optional_text("none") is None
    assert logic.normalize_optional_text("  ") is None
    assert logic.normalize_optional_text("2026-06-01") == "2026-06-01"

    base = "Base";
    extra = "More details"
    combined = logic.build_task_description(base, extra)
    assert "Base" in combined and "More details" in combined


def test_select_task_by_id():
    tasks = logic.format_tasks_list([sample_row(id=10), sample_row(id=20)])
    picked = logic.select_task_by_id(tasks, 20)
    assert picked and picked["id"] == 20


def test_format_forecast_message():
    forecast = {"mood": "positive", "mood_score": 80, "stress": "low", "stress_score": 20, "load": "medium", "load_score": 50, "summary": "Looks good."}
    msg = logic.format_forecast_message("A task", forecast)
    assert "Forecast for" in msg
    assert "Mood:" in msg and "Stress:" in msg and "Load:" in msg
