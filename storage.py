from datetime import datetime
import os
import pandas as pd

FILE_PATH = "incidents.csv"


def load_data():
    if not os.path.exists(FILE_PATH) or os.path.getsize(FILE_PATH) == 0:
        return pd.DataFrame(columns=[
            "timestamp", "building", "floor", "zone", 
            "raw_text", "scrubbed_text", "category", "urgency", "status", # <-- Added raw_text here
            "latitude", "longitude"
        ])
    return pd.read_csv(FILE_PATH)

def save_data(building, floor, zone, raw_text, scrubbed_text, category, urgency, lat=None, lon=None):
    df = load_data()
    new_row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "building": building,
        "floor": floor,
        "zone": zone,
        "raw_text": raw_text,              # <-- Saved here
        "scrubbed_text": scrubbed_text,
        "category": category,
        "urgency": urgency,
        "status": "Open",
        "latitude": lat,
        "longitude": lon
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)