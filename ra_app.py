"""RA PORTAL.  Run with:  python -m streamlit run ra_app.py --server.port 8502"""
import html

import folium
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_folium import st_folium

from storage import load_data, update_status
from ui import apply_theme, page_title, site_footer

st.set_page_config(page_title="RA Shift Handoff | Residence Safety", layout="wide")
apply_theme("1180px")

TOWER_COORDS = {
    "Henday Hall": (53.52119827024105, -113.53060577851979),
    "Mackenzie Hall": (53.521327840257364, -113.53172497898909),
    "Kelsey Hall": (53.522029186520335, -113.5317608351634),
    "Shaffer Hall": (53.52248095835739, -113.53156635838),
    "Chalifoux Hall": (53.520643630132334, -113.5313884780551),
}
URGENCY_COLORS = {"High": "#B71C1C", "Medium": "#F2CD00", "Low": "#6B6B6B"}
URGENCY_ORDER = {"High": 0, "Medium": 1, "Low": 2}
BADGES = {
    "High": ("high", "HIGH"),
    "Medium": ("medium", "MEDIUM"),
    "Low": ("low", "LOW"),
}


def shown_text(row):
    """Text the RA sees. Uses the redacted version when there is one."""
    for column in ("scrubbed_text", "raw_text"):
        value = row.get(column)
        if pd.notna(value) and str(value).strip():
            return str(value)
    return ""


page_title("RA Shift Handoff", "Every report from residence, sorted by urgency.")

# --- PASSWORD PROTECTION GATE ---
RA_PASSWORD = "admin"  # Set your hackathon passcode here

if "ra_authenticated" not in st.session_state:
    st.session_state["ra_authenticated"] = False

if not st.session_state["ra_authenticated"]:
    _, middle, _ = st.columns([1, 1.4, 1])
    with middle:
        with st.container(key="card_login"):
            st.subheader("Authorized personnel only")
            entered_password = st.text_input("RA passcode", type="password")
            if st.button("Log in", type="primary", key="login_btn"):
                if entered_password == RA_PASSWORD:
                    st.session_state["ra_authenticated"] = True
                    st.rerun()
                else:
                    st.error("Incorrect passcode. Access denied.")
    site_footer()
    st.stop()

# --- RA DASHBOARD (only loads after a successful login) ---
top_left, top_right = st.columns([5, 1])
top_left.caption("Signed in as Resident Advisor. This page checks for new reports every 10 seconds.")
if top_right.button("Log out", key="logout_btn"):
    st.session_state["ra_authenticated"] = False
    st.rerun()

# Auto-refresh the page every 10 seconds
st_autorefresh(interval=10000, limit=None, key="ra_dashboard_refresh")

df = load_data()

if df.empty or "building" not in df.columns:
    st.info("No incidents logged yet.")
    site_footer()
    st.stop()

col1, col2 = st.columns(2)
with col1:
    selected_building = st.selectbox(
        "Filter by building", ["All towers"] + list(TOWER_COORDS.keys())
    )
with col2:
    status_filter = st.selectbox("Filter by status", ["Open", "Resolved", "All"])

filtered_df = df.copy()
if selected_building != "All towers":
    filtered_df = filtered_df[filtered_df["building"] == selected_building]
if status_filter != "All":
    filtered_df = filtered_df[filtered_df["status"] == status_filter]

# --- Summary tiles ---
m1, m2, m3 = st.columns(3)
m1.metric("Shown", len(filtered_df))
m2.metric("High urgency", int((filtered_df["urgency"] == "High").sum()))
m3.metric("Resolved", int((filtered_df["status"] == "Resolved").sum()))

# --- DRAW MAP ---
st.subheader("Patrol map")
if filtered_df.empty:
    st.info("No incidents match your current filter.")
else:
    st.markdown(
        '<div class="legend">'
        '<span><i style="background:#B71C1C"></i>High</span>'
        '<span><i style="background:#F2CD00"></i>Medium</span>'
        '<span><i style="background:#6B6B6B"></i>Low</span></div>',
        unsafe_allow_html=True,
    )
    ra_map = folium.Map(location=[53.5222, -113.5310], zoom_start=17)

    for idx, row in filtered_df.iterrows():
        if pd.notna(row.get("latitude")) and pd.notna(row.get("longitude")):
            lat, lon = row["latitude"], row["longitude"]
        else:
            base_lat, base_lon = TOWER_COORDS.get(row["building"], (53.5222, -113.5310))
            lat = base_lat + ((idx % 5) - 2) * 0.00005
            lon = base_lon + (((idx // 5) % 5) - 2) * 0.00005

        color = URGENCY_COLORS.get(row["urgency"], "#6B6B6B")
        popup_html = f"""
            <div style="width: 210px; font-family: Arial, sans-serif;">
                <h4 style="margin: 0 0 4px 0; color: #275D38;">{html.escape(str(row['category']))}</h4>
                <b>{html.escape(str(row['building']))} - {html.escape(str(row['floor']))}</b><br>
                <b>Status:</b> {html.escape(str(row['status']))}<br>
                <hr style="margin: 5px 0;">
                {html.escape(shown_text(row))}
            </div>
        """
        folium.CircleMarker(
            location=[lat, lon],
            radius=9,
            color="#1F1F1F",
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.95,
            popup=folium.Popup(popup_html, max_width=260),
        ).add_to(ra_map)

    st_folium(ra_map, height=460, use_container_width=True, returned_objects=[])


# --- INCIDENT CARDS ---
@st.fragment
def render_triage_board(filtered_df):
    st.subheader("Incidents, most urgent first")

    if filtered_df.empty:
        st.info("No incidents match your current filter.")
        return

    ranked = filtered_df.assign(
        _rank=filtered_df["urgency"].map(URGENCY_ORDER).fillna(3)
    ).sort_values(["_rank", "timestamp"], ascending=[True, False])

    for idx, row in ranked.iterrows():
        uid = row.get("id", idx)
        css_class, label = BADGES.get(row["urgency"], ("low", "LOW"))

        with st.container(key=f"card_incident_{uid}"):
            col_a, col_b = st.columns([5, 1])

            with col_a:
                st.markdown(
                    f'<span class="badge {css_class}">{label}</span> '
                    f"<b>{html.escape(str(row['building']))} · "
                    f"{html.escape(str(row['floor']))} · {html.escape(str(row['zone']))}</b>",
                    unsafe_allow_html=True,
                )
                st.caption(f"{row['category']} · Logged {row['timestamp']}")
                st.write(shown_text(row))

            with col_b:
                if row["status"] == "Open":
                    if st.button("Resolve", key=f"resolve_{uid}", type="primary"):
                        update_status(row["id"], "Resolved")
                        st.rerun()
                else:
                    st.markdown('<span class="badge done">RESOLVED</span>', unsafe_allow_html=True)


render_triage_board(filtered_df)
site_footer()