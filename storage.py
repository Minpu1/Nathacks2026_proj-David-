from datetime import datetime
import os
import pandas as pd

FILE_PATH = "incidents.csv"
COLUMNS = ["timestamp", "building", "floor", "zone", "scrubbed_text",
           "category", "urgency", "status", "latitude", "longitude"]

def load_data():
    if not os.path.exists(FILE_PATH) or os.path.getsize(FILE_PATH) == 0:
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(FILE_PATH).drop(columns=["raw_text"], errors="ignore")

def save_data(building, floor, zone, scrubbed_text, category, urgency, lat=None, lon=None):
    df = load_data()
    new_row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "building": building, "floor": floor, "zone": zone,
        "scrubbed_text": scrubbed_text, "category": category,
        "urgency": urgency, "status": "Open",
        "latitude": lat, "longitude": lon,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)