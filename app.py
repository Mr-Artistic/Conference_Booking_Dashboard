# Defualt Libraries
import streamlit as st
import pandas as pd
import config as cfg
import base64
from pathlib import Path

# Custom Modules
from db import init_db, get_bookings
from ui import booking_form, st_red_alert
from timeline import build_vertical_day_time_timeline

# --------------------------------
# Page setup
# --------------------------------
st.set_page_config(page_title="Conference Room Booking", layout="wide")
if "_flash" in st.session_state:
    st.success(st.session_state.pop("_flash"))


# --------------------------------
# Branded Header Bar (title + logo)
# --------------------------------
def render_header_bar(
    title: str, logo_path: str, logo_height: int = 50, bg_color: str = "#1E3A8A"
):
    p = Path(logo_path)
    logo_html = ""
    if p.exists():
        b64 = base64.b64encode(p.read_bytes()).decode()
        logo_html = f"<img src='data:image/png;base64,{b64}' height='{logo_height}'>"

    st.markdown(
        f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: {bg_color};
            padding: 12px 8px;
            border-radius: 8px;
            margin-bottom: 10px;
        ">
            <h1 style="margin: 0; color: black; font-size: 28px;">{title}</h1>
            {logo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


render_header_bar(
    "Conference Room Booking App",
    "assets/logo.png",
    logo_height=50,
    bg_color="#CBD9F8",
)

# --------------------------------
# Ensure DB exists / migrate columns
# --------------------------------
init_db()

# Two-column layout
left_col, right_col = st.columns([2, 1], gap="small")

# --------------------------------
# Left: Graph + Table
# --------------------------------


@st.cache_data(ttl=30)
def load_bookings():
    return get_bookings()


with st.spinner("Loading bookings…"):
    df = load_bookings()

with left_col:

    # Bordered container for the graph
    with st.container(border=True):
        st.write("📊 Current Bookings Timeline (Day vs Time)")

        fig, info = build_vertical_day_time_timeline(df)

        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
            inv = (info or {}).get("invalid_durations", 0)
            if inv > 0:
                st_red_alert(
                    f"{inv} booking(s) has end_time ≤ start_time (displayed as dots). "
                    f"Admin to correct these entries."
                )
        else:
            reason = (info or {}).get("reason")
            if reason == "empty_df":
                st.info("No bookings in the database yet.")
            elif reason == "missing_columns":
                st.error(f"Missing columns: {info.get('missing')}")
            elif reason == "all_rows_unparsable":
                st.error(
                    f"All rows failed to parse times/dates (bad rows: {info.get('bad_count')})."
                )
            elif reason == "zero_duration":
                st.warning(
                    "All rows have zero or negative duration (start_time == end_time)."
                )
            elif reason == "out_of_window":
                st.warning(
                    f"No bookings in the 3-month window "
                    f"[{info.get('window_start')} → {info.get('window_end')}]. "
                    f"Data spans {info.get('min_date')} → {info.get('max_date')}."
                )
            else:
                st.info("No data to plot.")

    st.subheader("📌 All Existing Bookings")
    if not df.empty:
        st.dataframe(
            df[
                [
                    "booking_date",
                    "start_time",
                    "end_time",
                    "conference_type",  # <- show the new column
                    "person_name",
                    "company_name",
                    "affiliation",
                    "email",
                ]
            ]
            .sort_values(by=["booking_date", "start_time"])
            .reset_index(drop=True),
            height=cfg.TABLE_HEIGHT,
        )
    else:
        st.info("No bookings to show in the table yet.")

    st.write(
        f"💡 Tip: Hover the :red[red bars]  to see the booking instance."
        f"  \nUse the table's **column headers** to sort/filter bookings."
        f"  \nFound a bug? 🪲 Report to: sumiet_t@quantech.org.in"
    )
# --------------------------------
# Right: Booking Form
# --------------------------------
with right_col:
    booking_form()

