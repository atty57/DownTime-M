#!/usr/bin/env python3

"""
Downtime Monitor with SQLite + SQLAlchemy
-----------------------------------------
A Python/Flask application that periodically checks configured services,
stores results in a local SQLite database, sends email alerts on status changes,
and provides a simple web dashboard (current status + recent history).

Features:
    - Periodic checks for each service using requests.
    - Email alerts (uses SMTP) when a service goes UP->DOWN or DOWN->UP.
    - SQLite via SQLAlchemy for storing check results.
    - Flask web server with:
        * Home page: color-coded table for UP/DOWN.
        * /status endpoint: JSON output of current statuses.
        * /history endpoint: shows last N checks per service from the DB.

Usage:
    1) pip install -r requirements.txt
    2) python monitor.py
    3) Open http://127.0.0.1:5000 in your browser

Configuration:
    - Update SERVICES list for your target URLs.
    - Update CHECK_INTERVAL to change check frequency (default: 60s).
    - Update SMTP settings + credentials for your email alerts.
"""

import time
import threading
import smtplib
from datetime import datetime

import requests
from flask import Flask, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# -------------------- CONFIGURATION --------------------

# List of services to monitor (name + url)
SERVICES = [
    {"name": "Google", "url": "https://www.google.com"},
    {"name": "GitHub", "url": "https://github.com"},
]

# How many seconds to wait between checks
CHECK_INTERVAL = 60  # 1 minute

# Email alert settings (example for Gmail)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "[email protected]"      # Replace with your email
SENDER_PASSWORD = "YOUR_APP_PASSWORD"  # Use an App Password or secure method
ALERT_RECIPIENT = "[email protected]"    # Where alerts get sent

# Database configuration
DB_URL = "sqlite:///downtime_monitor.db"  # local SQLite file

# How many recent checks to show on /history page for each service
MAX_HISTORY = 20

# -------------------- SET UP DATABASE (SQLAlchemy) --------------------
Base = declarative_base()

class CheckResult(Base):
    __tablename__ = "check_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String, nullable=False)
    status = Column(Boolean, nullable=False)  # True=UP, False=DOWN
    timestamp = Column(DateTime, nullable=False)

engine = create_engine(DB_URL, echo=False)  # echo=True for SQL debug
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

# -------------------- FLASK APP SETUP --------------------
app = Flask(__name__)

# current_status dict to store the immediate UP/DOWN state in memory
# e.g., current_status["Google"] = True/False
current_status = {}

@app.route("/")
def home():
    """
    Render a color-coded table of current status for all services.
    """
    # Build HTML rows
    rows_html = ""
    for svc in SERVICES:
        name = svc["name"]
        is_up = current_status.get(name, False)
        color = "#c8e6c9" if is_up else "#ffcdd2"  # greenish if up, redish if down
        status_text = "UP" if is_up else "DOWN"
        rows_html += f"""
        <tr style="background-color: {color};">
            <td>{name}</td>
            <td>{status_text}</td>
        </tr>
        """

    html_template = f"""
    <html>
    <head>
        <title>Downtime Monitor</title>
    </head>
    <body>
        <h1>Downtime Monitor</h1>
        <p>Below is the current status of monitored services.</p>
        <table border="1" cellpadding="10" cellspacing="0">
            <tr>
                <th>Service</th>
                <th>Status</th>
            </tr>
            {rows_html}
        </table>
        <p>Check <a href="/history">/history</a> for recent checks.</p>
        <p>Check <a href="/status">/status</a> for JSON status.</p>
    </body>
    </html>
    """
    return html_template


@app.route("/status")
def status_json():
    """
    Returns the current status as JSON: {"Google": "UP", "GitHub": "DOWN", ...}
    """
    status_dict = {}
    for svc in SERVICES:
        name = svc["name"]
        is_up = current_status.get(name, False)
        status_dict[name] = "UP" if is_up else "DOWN"
    return jsonify(status_dict)


@app.route("/history")
def history():
    """
    Show recent history from the database for each service.
    Displays the last MAX_HISTORY checks per service.
    """
    session = SessionLocal()
    service_tables = ""

    for svc in SERVICES:
        name = svc["name"]
        # Query last MAX_HISTORY checks in descending order (newest first)
        records = (
            session.query(CheckResult)
            .filter(CheckResult.service_name == name)
            .order_by(CheckResult.id.desc())
            .limit(MAX_HISTORY)
            .all()
        )

        # Build table rows
        rows = ""
        for r in records:
            color = "#c8e6c9" if r.status else "#ffcdd2"
            status_txt = "UP" if r.status else "DOWN"
            ts_str = r.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            rows += f"""
            <tr style="background-color: {color};">
                <td>{ts_str}</td>
                <td>{status_txt}</td>
            </tr>
            """

        # Wrap the rows in a service-specific table
        service_tables += f"""
        <h3>{name}</h3>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>Timestamp</th>
                <th>Status</th>
            </tr>
            {rows}
        </table>
        <br/>
        """

    session.close()

    html_template = f"""
    <html>
    <head>
        <title>Downtime Monitor - History</title>
    </head>
    <body>
        <h1>Recent Check History</h1>
        {service_tables}
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """
    return html_template


# -------------------- EMAIL ALERT FUNCTION --------------------
def send_email_alert(service_name, was_up):
    """
    Sends an email alert when a service changes status.
    was_up=True => The service WAS up, now it's down.
    was_up=False => The service WAS down, now it's up.
    """
    new_status = "DOWN" if was_up else "UP"
    subject = f"[ALERT] {service_name} is {new_status}"
    body = f"Service '{service_name}' just went {new_status}. Check ASAP!"

    email_msg = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, ALERT_RECIPIENT, email_msg)
        print(f"[EMAIL ALERT] {service_name} is {new_status}")
    except Exception as e:
        print("Failed to send email alert:", e)


# -------------------- MONITORING LOOP --------------------
def monitor_services():
    """
    Runs in a background thread.
    Periodically checks each service, updates current_status,
    logs to DB, and sends email alerts on status changes.
    """
    previous_status = {}
    session = SessionLocal()

    # Initialize current_status so the main page has at least some data
    for svc in SERVICES:
        name = svc["name"]
        current_status[name] = False  # default false until first check

    while True:
        for svc in SERVICES:
            name = svc["name"]
            url = svc["url"]

            # Make an HTTP request
            try:
                resp = requests.get(url, timeout=10)
                is_up = (resp.status_code == 200)
            except Exception:
                is_up = False

            # If we don't have a previous status, set it now
            if name not in previous_status:
                previous_status[name] = is_up

            # Check for a status change
            if previous_status[name] != is_up:
                send_email_alert(name, was_up=previous_status[name])
                previous_status[name] = is_up

            # Update our in-memory status
            current_status[name] = is_up

            # Write a record into the database
            new_record = CheckResult(
                service_name=name,
                status=is_up,
                timestamp=datetime.now()
            )
            session.add(new_record)
            session.commit()

            # Print to console for debugging
            ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{ts_str} | {name} | {'UP' if is_up else 'DOWN'}")

        # Wait before the next check
        time.sleep(CHECK_INTERVAL)


# -------------------- MAIN ENTRY POINT --------------------
if __name__ == "__main__":
    # Start background monitoring thread
    monitor_thread = threading.Thread(target=monitor_services, daemon=True)
    monitor_thread.start()

    # Run Flask server
    app.run(port=5000, debug=True)
