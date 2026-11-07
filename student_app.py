"""STUDENT PORTAL.  Run with:  python -m streamlit run student_app.py --server.port 8501"""
import folium
import streamlit as st
from branca.element import MacroElement
from jinja2 import Template
from streamlit_folium import st_folium

from privacy_triage import process_incident
from storage import load_data, save_data

# --- Settings (same values Yevhen's version used) ---
TOWER_FLOORS = {
    "Henday Hall": 10,
    "Mackenzie Hall": 11,
    "Kelsey Hall": 10,
    "Shaffer Hall": 12,
    "Chalifoux Hall": 5,
}
ZONES = ["North Wing", "South Wing", "Main Lounge", "West Stairwell", "Exterior/Grounds"]
MAP_CENTER = [53.5222, -113.5310]


class SinglePin(MacroElement):
    """Drops ONE pin on the map inside the browser. Tapping again just moves it.
    Because the pin is drawn by the browser, the map never has to reload."""

    _template = Template("""
        {% macro script(this, kwargs) %}
        (function () {
            var map = {{ this._parent.get_name() }};
            var pin = null;
            map.on('click', function (e) {
                if (pin) { map.removeLayer(pin); }
                pin = L.marker(e.latlng).addTo(map);
            });
        })();
        {% endmacro %}
    """)

st.set_page_config(page_title="Lister Safety Reporting", page_icon="🛡️", layout="centered")

# --- Look and feel: all the CSS lives here, so it is easy to change ---
STYLE = """
<style>
/* Change this one colour to recolour the header and the progress steps */
:root { --accent: #07073D; --accent-edge: #5B84B8; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
.block-container { padding-top: 4rem; max-width: 680px; }

.hero {
    background: var(--accent); color: #FFFFFF;
    padding: 1.2rem 1.4rem; border-radius: 10px; margin-bottom: 1rem;
}
.hero h1 { color: #FFFFFF; font-size: 1.6rem; margin: 0; padding: 0; }
.hero p { color: #C9D6E8; margin: 0.3rem 0 0 0; font-size: 1rem; }

.notice {
    border-left: 4px solid #D97706; background: rgba(217, 119, 6, 0.12);
    padding: 0.6rem 0.9rem; border-radius: 6px; font-size: 0.9rem; margin-bottom: 1rem;
}

div.stButton > button {
    width: 100%; border-radius: 8px; padding: 0.7rem 1rem; font-weight: 600;
}

.steps { display: flex; gap: 0.6rem; margin: 1rem 0; }
.step {
    flex: 1; text-align: center; padding: 0.8rem 0.4rem; border-radius: 8px;
    border: 1px solid rgba(160, 160, 160, 0.4); font-size: 0.85rem;
}
.step b { display: block; font-size: 1.3rem; margin-bottom: 0.2rem; }
.step.done { background: rgba(31, 58, 95, 0.55); border-color: var(--accent-edge); }
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)


def hero(title, subtitle):
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


# --- Remember things between clicks ---
st.session_state.setdefault("lat", None)
st.session_state.setdefault("lon", None)
st.session_state.setdefault("map_id", 0)
st.session_state.setdefault("ref", None)

# =============== Screen 2: confirmation (shown after a report is sent) ===============
if st.session_state["ref"]:
    hero("Report received", f"Your reference number is {st.session_state['ref']}")
    with st.container(border=True):
        st.subheader("What happens next")
        st.markdown(
            """
            <div class="steps">
              <div class="step done"><b>✓</b>Received</div>
              <div class="step"><b>2</b>An RA reviews it</div>
              <div class="step"><b>3</b>Marked resolved</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Keep your reference number. You never need to give your name.")
    st.markdown(
        '<div class="notice">If anyone is in danger right now, call <b>911</b>. '
        "This form is not watched in real time.</div>",
        unsafe_allow_html=True,
    )
    if st.button("Report another issue"):
        st.session_state["ref"] = None
        st.session_state["lat"] = None
        st.session_state["lon"] = None
        st.session_state["map_id"] += 1
        st.rerun()
    st.stop()

# =============== Screen 1: the report form ===============
hero("Lister Safety Reporting", "Takes about a minute. Your report is confidential.")
st.markdown(
    '<div class="notice">In an emergency, call <b>911</b>. '
    "This form is not watched in real time.</div>",
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.subheader("1 · Where did it happen?")
    building = st.selectbox("Building", list(TOWER_FLOORS.keys()))
    floor = st.selectbox(
        "Floor", [f"Floor {i}" for i in range(1, TOWER_FLOORS[building] + 1)]
    )
    zone = st.selectbox("Location zone", ZONES)

with st.container(border=True):
    st.subheader("2 · What happened?")
    raw_text = st.text_area(
        "Describe the issue",
        placeholder="Include the exact room number if you know it...",
        height=120,
        key=f"description_{st.session_state['map_id']}",  # new key = empty box for the next report
    )

with st.container(border=True):
    st.subheader("3 · Pin the exact spot (optional)")
    st.caption("Tap the map to drop a pin. Zoom in for a more exact spot.")

    # The map never changes between clicks, so it does not reload or jump.
    pin_map = folium.Map(location=MAP_CENTER, zoom_start=18)
    pin_map.add_child(SinglePin())

    map_result = st_folium(
        pin_map,
        height=300,
        use_container_width=True,
        key=f"pin_map_{st.session_state['map_id']}",
        returned_objects=["last_clicked"],
    )

    # Quietly remember the last tap so it can be saved with the report.
    click = map_result.get("last_clicked") if map_result else None
    if click:
        st.session_state["lat"] = click["lat"]
        st.session_state["lon"] = click["lng"]

    if st.session_state["lat"] is not None:
        st.success("Location pinned")

if st.button("Submit confidential report", type="primary"):
    if not raw_text.strip():
        st.warning("Please describe what happened first.")
    else:
        result = process_incident(raw_text)
        saved = save_data(
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
        if saved is False:
            st.stop()  # storage.py already showed the error message
        st.session_state["ref"] = f"R-{len(load_data()):04d}"
        st.rerun()
        #