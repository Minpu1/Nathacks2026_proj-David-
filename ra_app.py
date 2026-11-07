import folium
from privacy_triage import process_incident
from storage import load_data, update_status  # Added update_status here!
import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
from streamlit_autorefresh import st_autorefresh

TOWER_COORDS = {
    "Henday Hall": (53.52119827024105, -113.53060577851979),
    "Mackenzie Hall": (53.521327840257364, -113.53172497898909),
    "Kelsey Hall": (53.522029186520335, -113.5317608351634),
    "Shaffer Hall": (53.52248095835739, -113.53156635838),
    "Chalifoux Hall": (53.520643630132334, -113.5313884780551),
}
URGENCY_COLORS = {"High": "red", "Medium": "orange", "Low": "blue"}

st.title("🔒 RA Shift-Handoff Portal")

# Login is handled by auth.py, which only routes RA accounts to this page.
st.success("Authenticated as Resident Advisor")


# Auto-refresh the page every 10 seconds
st_autorefresh(interval=10000, limit=None, key="ra_dashboard_refresh")

df = load_data()

# Check if data is empty first!
if df.empty or "building" not in df.columns:
  st.info("No incidents logged yet.")
else:
  col1, col2 = st.columns(2)
  with col1:
    selected_building = st.selectbox(
        "Filter by Building", ["All Towers"] + list(TOWER_COORDS.keys())
    )
  with col2:
    status_filter = st.selectbox("Filter by Status", ["Open", "Resolved", "All"])

  filtered_df = df.copy()
  if selected_building != "All Towers":
    filtered_df = filtered_df[filtered_df["building"] == selected_building]
  if status_filter != "All":
    filtered_df = filtered_df[filtered_df["status"] == status_filter]

  # --- DRAW MAP ---
  if filtered_df.empty:
    st.info("No incidents match your current filter.")
  else:
    ra_map = folium.Map(location=[53.5222, -113.5310], zoom_start=17)
    
    for idx, row in filtered_df.iterrows():
      if pd.notna(row.get("latitude")) and pd.notna(row.get("longitude")):
        lat, lon = row["latitude"], row["longitude"]
      else:
        base_lat, base_lon = TOWER_COORDS.get(
            row["building"], (53.5222, -113.5310)
        )
        lat = base_lat + ((idx % 5) - 2) * 0.00005
        lon = base_lon + (((idx // 5) % 5) - 2) * 0.00005
      
      # Now correctly inside the for loop!
      color = URGENCY_COLORS.get(row["urgency"], "blue")
      
      # Fixed the typo in the HTML string below
      popup_html = f"""
              <div style="width: 200px; font-family: sans-serif;">
                  <h4 style="margin: 0; color: {color};">{row['category']}</h4>
                  <b>{row['building']} - {row['floor']}</b><br>
                  <b>Status:</b> {row['status']}<br>
                  <hr style="margin: 5px 0;">
                  {row['raw_text']}
              </div>
          """
      folium.CircleMarker(
          location=[lat, lon],
          radius=8,
          color=color,
          fill=True,
          fill_opacity=0.9,
          popup=folium.Popup(popup_html, max_width=250),
      ).add_to(ra_map)

    # st_folium is now properly indented inside the else block
    st_folium(ra_map, height=450, use_container_width=True)

  # --- INCIDENT CARDS ---
  st.write("### 📋 Active Incident Cards & Triage")

  if filtered_df.empty:
    st.info("No incidents match your current filter.")
  else:
    for idx, row in filtered_df.iterrows():
      urgency_badge = (
          "🔴 HIGH"
          if row["urgency"] == "High"
          else ("🟠 MED" if row["urgency"] == "Medium" else "🔵 LOW")
      )

      with st.container(border=True):
        col_a, col_b = st.columns([4, 1])

        with col_a:
          st.markdown(
              f"**{urgency_badge} | {row['building']} — {row['floor']} ({row['zone']})**"
          )
          st.caption(
              f"Category: {row['category']} | Logged: {row['timestamp']}"
          )
          st.write(row["raw_text"])

        with col_b:
          current_status = row["status"]
          st.text(f"Status:\n{current_status}")

          if current_status == "Open":
            # Using the row's actual database ID for the button key
            if st.button("Resolve", key=f"resolve_{row.get('id', idx)}", type="primary"):
              # Using the Supabase cloud update instead of local CSV
              update_status(row["id"], "Resolved")
              st.success("Resolved!")
              st.rerun()
          else:
            st.success("Done ✓")
            