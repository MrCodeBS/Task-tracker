"""Pure business logic helpers for Task Tracker.

These functions are side-effect free and operate only on inputs to produce outputs.
They make the codebase easier to reason about and test in a functional style.
"""
from typing import Iterable, Mapping, Dict, Any
from typing import Iterable, Mapping, Dict, Any, List, Callable
from functools import reduce
from itertools import groupby


def format_task_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    """Convert a DB row (mapping-like) into a plain dict with predictable keys."""
    row_dict = dict(row)
    return {
        "id": int(row_dict["id"]),
        "description": str(row_dict["description"]),
        "status": str(row_dict.get("status") or "pending"),
        "due_date": row_dict.get("due_date") or None,
    }


def format_tasks_list(rows: Iterable[Dict[str, Any]]) -> list:
    """Return a list of formatted task dicts from DB rows."""
    return [format_task_row(r) for r in rows]


# C2E: Closures und Currying zur Erzeugung spezialisierter Filter (Band C)
def status_is(target_status: str) -> Callable[[Dict[str, Any]], bool]:
    """Return a function that checks if a task has a specific status."""
    return lambda task: str(task.get("status", "")).lower() == target_status.lower()


# C3/C4: Verwendung von Lambdas, Map und Filter zur Datenverarbeitung
def get_pending_descriptions(tasks: Iterable[Dict[str, Any]]) -> List[str]:
    """Return descriptions of all non-done tasks using a functional pipeline."""
    # Lambda zur Extraktion (C3G)
    get_desc = lambda t: t.get("description", "No description")
    
    # Filter und Map Kombination (C4F)
    pending_tasks = filter(lambda t: t.get("status") != "done", tasks)
    return list(map(get_desc, pending_tasks))


# C4G/C4F: Einsatz von reduce zur Aggregation (Summe der IDs als Beispiel für C4)
def get_total_id_sum(tasks: Iterable[Dict[str, Any]]) -> int:
    """Calculate the sum of all task IDs using reduce (C4G/C4F)."""
    # C3F: Lambda mit zwei Parametern (Accumulator und Element)
    return reduce(lambda acc, t: acc + t.get("id", 0), tasks, 0)


# C4E: Komplexe Datenverarbeitung - Gruppierung von Tasks nach Status
def group_tasks_by_status(tasks: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Groups tasks by their status using a functional approach (C4E)."""
    # C1G: Ein Algorithmus ist eine endliche Folge von eindeutigen Anweisungen.
    # Eigenschaften: Finitheit (endet nach endlichen Schritten) und Determiniertheit.
    sorted_tasks = sorted(tasks, key=lambda t: t.get("status", "unknown"))
    return {
        status: list(group) 
        for status, group in groupby(sorted_tasks, key=lambda t: t.get("status", "unknown"))
    }


def tasks_summary(tasks: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    """Return simple aggregated counts for a list of tasks."""
    total = 0
    done = 0
    due = 0
    for t in tasks:
        total += 1
        if str(t.get("status", "")).lower() == "done":
            done += 1
        if t.get("due_date"):
            due += 1
    return {"total": total, "done": done, "pending": total - done, "due": due}


def format_tasks_message(tasks: Iterable[Dict[str, Any]]) -> str:
    """Create a telegram-friendly tasks list message (pure)."""
    items = []
    for t in tasks:
        due = f", due: {t['due_date']}" if t.get("due_date") else ""
        items.append(f"{t['id']}: {t['description']} ({t['status']}{due})")
    if not items:
        return "You have no tasks."
    return "Your tasks:\n" + "\n".join(items)


def normalize_optional_text(value: str) -> str | None:
    """Normalize user input where empty/none-like text means no value."""
    cleaned = str(value or "").strip()
    if not cleaned or cleaned.lower() == "none":
        return None
    return cleaned


def build_task_description(base_description: str, extra_description: str) -> str:
    """Append extra description to an existing description using a stable separator."""
    base = str(base_description or "").strip()
    extra = str(extra_description or "").strip()
    if not base:
        return extra
    if not extra:
        return base
    return f"{base}\n{extra}"


def select_task_by_id(tasks: Iterable[Dict[str, Any]], task_id: int) -> Dict[str, Any] | None:
    """Return the first task with the given id or None."""
    return next((task for task in tasks if int(task.get("id", -1)) == int(task_id)), None)


def format_forecast_message(source_description: str, forecast: Dict[str, Any]) -> str:
    """Format forecast dict into a concise message (pure)."""
    if not forecast or "error" in forecast:
        return forecast.get("error") if forecast else "No forecast available."

    lines = [f"Forecast for '{source_description}':"]
    lines.append(f"Mood: {forecast.get('mood', 'N/A')} ({forecast.get('mood_score', 'N/A')})")
    lines.append(f"Stress: {forecast.get('stress', 'N/A')} ({forecast.get('stress_score', 'N/A')})")
    lines.append(f"Load: {forecast.get('load', 'N/A')} ({forecast.get('load_score', 'N/A')})")
    if forecast.get('summary'):
        lines.append("")
        lines.append(f"Summary: {forecast['summary']}")
    return "\n".join(lines)


def build_help_message() -> str:
    """Return the bot help text as a pure string."""
    return (
        "Welcome to the Task Tracker Bot! Use /add, /tasks, /list, /done <id>, "
        "/delete <id>, /add_description, /forecast <id>, or /forecast_refresh <id>"
    )
