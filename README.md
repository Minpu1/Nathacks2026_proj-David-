# RA On-Shift Helper

A residence incident reporting and shift-handoff tool, built for natHacks 2026 (November 6 to 9, 2026, Edmonton, Alberta).

**Theme:** Defense & Security (infrastructure and operational security, public safety)

**Live demo:** [TO CHECK: add the link if you deploy it, or write "Runs locally, see How to run"]

---

## The problem

In student residence, safety problems get reported in many scattered ways: a quick word to an RA, a text, a note on a door. Students may not report because the process feels clunky or exposes their identity. RAs starting a shift inherit a messy overnight log, with no clear view of what is urgent, what is still open, or where problems keep happening (for example, a fire door that keeps getting propped open in the same stairwell).

## What it does

The project is two separate apps that share one incident record.

**Student Portal** (for residents)
- Report an issue by choosing the building, floor, and zone, then describing what happened.
- Optionally tap a map to pin the exact spot.
- Get a reference number as confirmation. No account is needed. [TO CHECK: confirm the final student page has no login]
- Phone numbers, emails, and 7-digit student IDs are detected and replaced with placeholders such as `[PHONE REDACTED]`.

**RA Portal** (for Residence Assistants)
- Passcode-protected dashboard.
- Patrol map with color-coded dots by urgency (red for urgent safety, orange for maintenance, blue for noise and policy).
- Filters by building and status, a table of incidents, and a chart of hotspots by zone.

## How it works

1. A student submits a report in the Student Portal.
2. `privacy_triage.py` removes personal identifiers with regular expressions, then sorts the report into a category and urgency level using keyword matching. Words like "fire," "door," or "smoke" mark it as urgent safety. Words like "leak" or "broken" mark it as maintenance. Everything else goes to the next-shift list.
3. `storage.py` saves the report to `incidents.csv`.
4. The RA Portal reads the same file and draws the map, table, and charts.

[TO CHECK: privacy. If `storage.py` still saves the original `raw_text` column, or the RA map popup shows `raw_text`, then either remove that column and show `scrubbed_text` in the popup, or change this README to say exactly what is stored. Do not claim identifiers are removed if the original text is still saved or shown.]

## Tech stack

- Python 3
- Streamlit for both web apps
- Folium and streamlit-folium for the maps
- pandas for the data table and filters
- Regular expressions for redaction and keyword triage
- A CSV file as the database (prototype only)

## Project structure

| File | What it does |
| --- | --- |
| `student_app.py` | The Student Portal |
| `ra_app.py` | The RA Portal |
| `privacy_triage.py` | Redacts identifiers, then sets category and urgency |
| `storage.py` | Reads and writes `incidents.csv` |
| `incidents.csv` | The incident records, pre-filled with simulated incidents for the demo |
| `requirements.txt` | Python libraries needed |
| `.streamlit/config.toml` | Colors and theme for both apps |

## How to run

1. Install Python 3.10 or newer.
2. Clone the repository and open a terminal inside the project folder:
   ```
   git clone <repository link>
   cd Nathacks2026_proj
   ```
3. Install the libraries:
   ```
   python -m pip install -r requirements.txt
   ```
4. Start the Student Portal in one terminal:
   ```
   python -m streamlit run student_app.py --server.port 8501
   ```
5. Start the RA Portal in a second terminal:
   ```
   python -m streamlit run ra_app.py --server.port 8502
   ```
6. Open `http://localhost:8501` for students and `http://localhost:8502` for RAs.

Both apps read and write the same `incidents.csv`, so run them from the same folder on the same computer.

**Demo access:** the RA Portal asks for a passcode. The demo passcode is set in `ra_app.py` (`RA_PASSWORD`). It is for the prototype only. [TO CHECK: whether you want to name the passcode here for judges]

## Suggested demo for judges

1. Open the Student Portal and submit a report: for example, "Fire door propped open near room 4021, call 780-555-1234."
2. Note the reference number on the confirmation screen.
3. Open the RA Portal, enter the passcode, and find the new report on the map and in the table. Look at how the phone number appears.
4. Try the building and status filters, and check the hotspot chart.

## Screenshots

[TO CHECK: add 2 or 3 screenshots to an `images` folder and link them here, for example `![Student Portal](images/student.png)`. Remove this section if you have none.]

## Honest limitations

- This is a prototype that uses simulated data. No real students, ONE Card data, or university systems are connected.
- Triage uses simple keywords, so it can misclassify a report. An RA should always review it.
- Reports without a map pin are placed near the center of the chosen building, so they are approximate. A map also cannot show which floor, which is why the report asks for the floor and zone.
- Reports are stored in one CSV file on one computer, which is fine for a demo but not for real use.
- The passcode login is a placeholder. A real deployment should use the university's single sign-on, so the app never handles passwords.
- The app is not monitored in real time and does not replace 911, campus security, or an RA in an emergency.
- A real deployment would need approval from the university and the residence team.

## What we would build next

- Mark incidents as resolved, with a required note, so every incident is answered and documented.
- Overdue alerts, for example "urgent report with no response in 20 minutes."
- A one-click shift handoff summary that lists everything still open.
- A shared database and real single sign-on.
- A better triage method than keyword matching, tested with real RAs.

## Team

- Yevhen Skorik, role
- Renee Dhadli, role
- David Wu, role
- Angel Li, role
- Shuoen Huang, role

## Credits and notes

Built during the natHacks 2026 competition window by students, with problem input from a residence RA. Built with open-source libraries: Streamlit, Folium, streamlit-folium, and pandas. Map tiles are from OpenStreetMap contributors. All incident data in the repository is simulated. [TO CHECK: add a line about any AI coding tools your team used, if the organizers asked for that.]