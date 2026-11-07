import folium
from privacy_triage import process_incident
from storage import save_data
import streamlit as st
from streamlit_folium import st_folium

TOWER_FLOORS = {
    "Henday Hall": 10,
    "Mackenzie Hall": 11,
    "Kelsey Hall": 10,
    "Shaffer Hall": 12,
    "Chalifoux Hall": 5,
}

st.title("Lister Centre Incident Reporting")
st.caption("Submit anonymous or confidential maintenance & safety reports.")

if "lat" not in st.session_state:
  st.session_state["lat"] = None
  st.session_state["lon"] = None

building = st.selectbox("Building", list(TOWER_FLOORS.keys()))
floor = st.selectbox(
    "Floor", [f"Floor {i}" for i in range(1, TOWER_FLOORS[building] + 1)]
)
zone = st.selectbox(
    "Location Zone",
    [
        "North Wing",
        "South Wing",
        "Main Lounge",
        "West Stairwell",
        "Exterior/Grounds",
    ],
)
raw_text = st.text_area(
    "What happened?", placeholder="Include exact room number if known..."
)

st.write("📍 **Optional: Tap on the map to pin the exact location**")
pin_map = folium.Map(location=[53.5222, -113.5310], zoom_start=17)
pin_map.add_child(folium.ClickForMarker(popup="Incident Location"))
map_interaction = st_folium(pin_map, height=300, use_container_width=True)

if map_interaction and map_interaction.get("last_clicked"):
  st.session_state["lat"] = map_interaction["last_clicked"]["lat"]
  st.session_state["lon"] = map_interaction["last_clicked"]["lng"]
  st.success("✅ Custom location pinned!")

if st.button("Submit Confidential Report", type="primary"):
  if not raw_text.strip():
    st.warning("Please enter a description of the incident.")
  else:
    result = process_incident(raw_text)
    save_data(
        building,
        floor,
        zone,
        raw_text,
        result["scrubbed_text"],
        result["category"],
        result["urgency"],
        st.session_state["lat"],
        st.session_state["lon"],
    )
    st.success("Report submitted successfully. The RA team has been notified.")
    st.session_state["lat"] = None
    st.session_state["lon"] = None