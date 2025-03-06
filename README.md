# DownTime-M
# How to Run the Downtime Monitor

1. **Install Python**
   - Make sure you have Python 3.x installed. Check by opening a terminal and running:

     ```bash
     python --version
     ```

   - If you need to install or update Python, visit [https://www.python.org/](https://www.python.org/) to download the latest version.

2. **Clone or Download the Project**
   - **Clone** from GitHub (if you have Git installed):
     ```bash
     git clone https://github.com/YourUserName/YourRepoName.git
     cd YourRepoName
     ```
   - Or **download the ZIP** from GitHub, extract it, then open your terminal and `cd` into the extracted folder.

3. **(Optional) Create a Virtual Environment**
   *Recommended to keep dependencies isolated.*
   ```bash
   python -m venv venv
   ```
   - **Activate** the virtual environment:
     - On **Windows**:
       ```bash
       venv\Scripts\activate
       ```
     - On **Mac/Linux**:
       ```bash
       source venv/bin/activate
       ```

4. **Install Dependencies**
   Inside the project folder, run:
   ```bash
   pip install -r requirements.txt
   ```
   This installs **Flask**, **requests**, **SQLAlchemy**, and any other libraries listed.

5. **Configure Your Services & Email Credentials**
   - Open `monitor.py` in a text editor.
   - Modify the `SERVICES` list to add/remove sites you want monitored.
   - Update **email settings** (e.g., `SENDER_EMAIL`, `SENDER_PASSWORD`, `ALERT_RECIPIENT`) for alerts.
   - Change `CHECK_INTERVAL` to define how often (in seconds) checks occur.

6. **Run the Monitor**
   From within the same folder:
   ```bash
   python monitor.py
   ```
   - The script will begin monitoring in the background.
   - A Flask web server will start on **http://127.0.0.1:5000**.

7. **View the Dashboard**
   - Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.
   - You’ll see a color-coded table of each service and whether it’s UP or DOWN.

8. **Other Endpoints**
   - **/status**: Returns a JSON object with current statuses.
   - **/history**: Shows up to `MAX_HISTORY` recent checks per service.

9. **Stop the Monitor**
   - Press **Ctrl + C** in the terminal where `monitor.py` is running.


## Troubleshooting & Tips

- **Email Issues**: Double-check SMTP details and the use of an App Password if on Gmail.
- **Virtual Environment**: Remember to re-activate it in every new terminal session.
- **Database**: `downtime_monitor.db` is automatically created for storing results. Delete it if you want a fresh start (with the app not running).
- **Local Network Access**: To let other devices on your LAN see the dashboard, update `app.run()` in `monitor.py` to:
  ```python
  app.run(host="0.0.0.0", port=5000, debug=True)
  ```
  Then browse to `http://<your_local_ip>:5000/` from another device.


That’s it! Enjoy monitoring your services.

