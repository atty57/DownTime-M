# Downtime-M (Flask + SQLite)

A Python/Flask application that periodically checks configured services, stores results
in a local SQLite database, sends email alerts on status changes, and provides a simple
web dashboard (current status + recent history).

## Features

- **Periodic Checks**: Uses `requests` to get each service's URL every X seconds.
- **Email Alerts**: Uses SMTP to send an email when a service changes from UP→DOWN or DOWN→UP.
- **SQLite**: Stores each check result in a local `downtime_monitor.db` via SQLAlchemy.
- **Flask Dashboard**:
  - Home page (`/`) shows color-coded UP/DOWN statuses.
  - `/status` returns a JSON version of the current status.
  - `/history` shows recent checks (up to N) for each service.

## Requirements
- Python 3.7+ (or any modern Python)
- Installed libraries from `requirements.txt`:
  ```bash
  pip install -r requirements.txt
