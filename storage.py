from datetime import datetime
import pandas as pd
from supabase import create_client
import streamlit as st

# Initialize Supabase client safely with error catching
try:
  url = st.secrets["SUPABASE_URL"]
  key = st.secrets["SUPABASE_KEY"]
  supabase = create_client(url, key)
except Exception as e:
  supabase = None


def load_data():
  """Fetches all incident rows from Supabase with safe empty & error handling."""
  empty_df = pd.DataFrame(columns=[
      "timestamp", "building", "floor", "zone", 
      "raw_text", "scrubbed_text", "category", "urgency", 
      "status", "latitude", "longitude"
  ])

  if supabase is None:
    st.error("⚠️ Database credentials missing or invalid in `.streamlit/secrets.toml`.")
    return empty_df

  try:
    response = supabase.table("incidents").select("*").execute()
    data = response.data
    
    # Check if table is empty
    if not data:
      return empty_df
      
    return pd.DataFrame(data)
    
  except Exception as e:
    st.error(f"⚠️ Error loading data from Supabase: {e}. Check if the 'incidents' table exists.")
    return empty_df


def save_data(building, floor, zone, raw_text, scrubbed_text, category, urgency, lat=None, lon=None):
  """Saves a new student report to Supabase with error catching."""
  if supabase is None:
    st.error("⚠️ Cannot save report: Database is not initialized.")
    return False

  try:
    new_row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "building": building,
        "floor": floor,
        "zone": zone,
        "raw_text": raw_text,
        "scrubbed_text": scrubbed_text,
        "category": category,
        "urgency": urgency,
        "status": "Open",
        "latitude": lat,
        "longitude": lon
    }
    supabase.table("incidents").insert(new_row).execute()
    return True
  except Exception as e:
    st.error(f"⚠️ Failed to submit report to database: {e}")
    return False

def update_status(row_id, new_status):
  """Updates an incident's status in the cloud database."""
  if supabase is None:
    st.error("⚠️ Cannot update report: Database is not initialized.")
    return False

  try:
    supabase.table("incidents").update({"status": new_status}).eq("id", row_id).execute()
    return True
  except Exception as e:
    st.error(f"⚠️ Failed to update status: {e}")
    return False  
  