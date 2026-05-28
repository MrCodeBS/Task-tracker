"""Refresh forecasts for all tasks using the Groq API.

Usage:
    python scripts/refresh_all_forecasts.py

This will iterate all tasks and call `groq_api.forecasting.get_forecast(..., force_refresh=True)`
for each task description. Useful for batch-refresh or CI-run maintenance.
"""
from database import db
from groq_api import forecasting


def main():
    rows = db.get_tasks()
    tasks = [dict(r) for r in rows]
    total = len(tasks)
    refreshed = 0
    failed = 0
    for t in tasks:
        desc = t.get("description")
        if not desc:
            failed += 1
            continue
        res = forecasting.get_forecast(desc, force_refresh=True)
        if isinstance(res, dict) and res.get("error"):
            failed += 1
        else:
            refreshed += 1
    print(f"Refreshed: {refreshed}, Failed: {failed}, Total: {total}")


if __name__ == "__main__":
    main()
