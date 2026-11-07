import folium
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd
from privacy_triage import process_incident
from storage import load_data, save_data

# --- Configuration & Setup ---
TOWER_COORDS = {
    "Henday Hall": (53.52155, -113.52950),     
    "Mackenzie Hall": (53.52155, -113.53120),  
    "Kelsey Hall": (53.52240, -113.53150),     
    "Shaffer Hall": (53.52320, -113.53050),    
    "Chalifoux Hall": (53.52250, -113.52920),  
}

TOWER_FLOORS = {
    "Henday Hall": 10, "Mackenzie Hall": 11, "Kelsey Hall": 10,
    "Shaffer Hall": 12, "Chalifoux Hall": 5
}

URGENCY_COLORS = {"High": "red", "Medium": "orange", "Low": "blue"}


# --- UI Functions ---

def init_session_state():
    """Initializes session state variables to prevent reset bugs on reload."""
    if "lat" not in st.session_state:
        st.session_state["lat"] = None
        st.session_state["lon"] = None

def render_student_view():
    """Renders the mobile-friendly student reporting form and custom map."""
    st.subheader("Report a Residence Issue")
    
    building = st.selectbox("Building", list(TOWER_FLOORS.keys()))
    floor = st.selectbox("Floor", [f"Floor {i}" for i in range(1, TOWER_FLOORS[building] + 1)])
    zone = st.selectbox("Location Zone", ["North Wing", "South Wing", "Main Lounge", "West Stairwell", "Exterior/Grounds"])
    raw_text = st.text_area("What happened? (Include exact room number)")

    st.write("📍 **Optional: Tap on the map to pin the exact location**")
    
    # Render the pin map
    pin_map = folium.Map(location=[53.5222, -113.5310], zoom_start=17)
    pin_map.add_child(folium.ClickForMarker(popup="Incident Location"))
    map_interaction = st_folium(pin_map, height=300, use_container_width=True)
    
    # Save tap coordinates to session state
    if map_interaction and map_interaction.get("last_clicked"):
        st.session_state["lat"] = map_interaction["last_clicked"]["lat"]
        st.session_state["lon"] = map_interaction["last_clicked"]["lng"]
        st.success("✅ Custom location pinned!")

    # Handle submission
    if st.button("Submit Confidential Report"):
        result = process_incident(raw_text)
        
        # NOTE: Make sure your save_data function in storage.py matches these exact arguments
        save_data(
            building, floor, zone, 
            result["scrubbed_text"], result["category"], result["urgency"],
            st.session_state["lat"], st.session_state["lon"]
        )
        st.success(f"Logged under '{result['category']}' for the RA team.")
        
        # Clear the map memory for the next user
        st.session_state["lat"] = None
        st.session_state["lon"] = None

def build_ra_map(filtered_df):
    """Builds and returns the Folium map containing the incident markers."""
    ra_map = folium.Map(location=[53.5222, -113.5310], zoom_start=17)

    for idx, row in filtered_df.iterrows():
        # Use custom GPS if available, else stack them over the base building
        if pd.notna(row.get("latitude")) and pd.notna(row.get("longitude")):
            lat = row["latitude"]
            lon = row["longitude"]
        else:
            base_lat, base_lon = TOWER_COORDS.get(row["building"], (53.5222, -113.5310))
            lat = base_lat + ((idx % 5) - 2) * 0.00005
            lon = base_lon + (((idx // 5) % 5) - 2) * 0.00005

        color = URGENCY_COLORS.get(row["urgency"], "blue")
        
        # Cleaned up HTML popup formatting
        popup_html = f"""
            <div style="width: 200px; font-family: sans-serif;">
                <h4 style="margin: 0; color: {color};">{row['category']}</h4>
                <b>{row['building']} - {row['floor']}</b><br>
                <b>Status:</b> {row['status']}<br>
                <hr style="margin: 5px 0;">
                {row['scrubbed_text']}
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
        
    return ra_map

def render_ra_dashboard():
    """Renders the filters, map, charts, and data tables for the RA shift view."""
    st.subheader("Overnight Shift Handoff & Interactive Patrol Map")
    df = load_data()

    if df.empty:
        st.info("No incidents logged yet. Submit one on the Student screen!")
        return

    # Map Filters
    col1, col2 = st.columns(2)
    with col1:
        selected_building = st.selectbox("Filter by Building", ["All Towers"] + list(TOWER_COORDS.keys()))
    with col2:
        status_filter = st.selectbox("Filter by Status", ["Open", "Resolved", "All"])

    filtered_df = df.copy()
    if selected_building != "All Towers":
        filtered_df = filtered_df[filtered_df["building"] == selected_building]
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["status"] == status_filter]

    # Draw RA Map using the helper function
    ra_map = build_ra_map(filtered_df)
    
    st.caption("🔴 Urgent Safety | 🟠 Maintenance | 🔵 Noise/Policy")
    st_folium(ra_map, height=450, use_container_width=True)

    # Hotspot chart & raw logs
    st.write("### Incident Hotspots by Zone")
    st.bar_chart(filtered_df["zone"].value_counts())
    
    st.write("### Incident Data Table")
    st.dataframe(filtered_df, use_container_width=True)

# --- Main App Execution ---

def main():
    st.title("Residence Safety & Shift Handoff")
    init_session_state()
    
    view = st.sidebar.radio("Select View", ["Student Report (Phone)", "RA Dashboard"])
    
    if view == "Student Report (Phone)":
        render_student_view()
    elif view == "RA Dashboard":
        render_ra_dashboard()

# Run the app
if __name__ == "__main__":
    main()