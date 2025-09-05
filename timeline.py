import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import config as cfg


def _parse_hhmm_to_hours(series: pd.Series) -> pd.Series:
    """
    Convert 'HH:MM:SS' or 'HH:MM' to fractional hours. Returns float hours; NaN if unparsable.
    """
    ts = pd.to_datetime(series, format="%H:%M:%S", errors="coerce")
    ts = ts.fillna(pd.to_datetime(series, format="%H:%M", errors="coerce"))
    return ts.dt.hour + ts.dt.minute / 60.0 + ts.dt.second / 3600.0


def build_vertical_day_time_timeline(df: pd.DataFrame, bar_color="#E53935"):
    """
    Vertical 'day vs time-of-day' booking chart:
      - X axis: Dates (fixed to last month, current month, next month from config)
      - Y axis: Time of day (0..24 hours)
      - Each booking is a vertical bar from start_time to end_time at its booking_date.

    Returns: (fig, info_dict) or (None, info_dict) when nothing to plot.
    """
    if df is None or df.empty:
        return None, {"reason": "empty_df"}

    # Ensure required columns exist
    required = {
        "booking_date",
        "start_time",
        "end_time",
        "person_name",
        "company_name",
        "affiliation",
        "email",
    }
    missing = required - set(df.columns)
    if missing:
        return None, {"reason": "missing_columns", "missing": sorted(missing)}

    # Work on a copy
    df = df.copy()

    # Normalize date and parse times
    df["DateOnly"] = pd.to_datetime(df["booking_date"], errors="coerce").dt.normalize()
    start_h = _parse_hhmm_to_hours(df["start_time"])
    end_h = _parse_hhmm_to_hours(df["end_time"])

    # Drop rows that failed to parse
    mask_bad = start_h.isna() | end_h.isna() | df["DateOnly"].isna()
    bad_rows = df[mask_bad]
    df = df[~mask_bad].copy()
    start_h = start_h.loc[df.index]
    end_h = end_h.loc[df.index]

    if df.empty:
        return None, {"reason": "all_rows_unparsable", "bad_count": len(bad_rows)}

    # Compute duration; keep invalid as thin bars and count them
    df["StartH"] = start_h
    df["EndH"] = end_h
    df["DurH_raw"] = df["EndH"] - df["StartH"]

    invalid_count = int((df["DurH_raw"] <= 0).sum())
    df["DurH"] = df["DurH_raw"]
    df.loc[df["DurH"] <= 0, "DurH"] = 0.25  # show a thin 15-minute bar so it’s visible

    # Filter to fixed 3-month window from config
    start_window = pd.to_datetime(cfg.TIMELINE_START)
    end_window = pd.to_datetime(cfg.TIMELINE_END)
    in_window = (df["DateOnly"] >= start_window) & (df["DateOnly"] < end_window)
    dfw = df[in_window].copy()

    if dfw.empty:
        return None, {
            "reason": "out_of_window",
            "window_start": start_window.strftime("%Y-%m-%d"),
            "window_end": end_window.strftime("%Y-%m-%d"),
            "min_date": df["DateOnly"].min().strftime("%Y-%m-%d"),
            "max_date": df["DateOnly"].max().strftime("%Y-%m-%d"),
        }

    fig = go.Figure()

    # Width for each vertical bar on a date axis (milliseconds)
    bar_width_ms = 12 * 60 * 60 * 1000  # 12h wide bars look good on a day slot

    for _, row in dfw.iterrows():
        fig.add_bar(
            x=[row["DateOnly"]],
            y=[row["DurH"]],
            base=[row["StartH"]],
            marker_color=bar_color,
            width=[bar_width_ms],
            name=str(row["company_name"]),
            hovertemplate=(
                "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
                "Date: %{x|%Y-%m-%d}<br>"
                "From: %{customdata[2]}<br>"
                "To: %{customdata[3]}<br>"
                "Conference: %{customdata[4]}<br>"
                "Email: %{customdata[5]}<extra></extra>"
            ),
            customdata=[
                [
                    row["person_name"],
                    row["company_name"],
                    row["start_time"],
                    row["end_time"],
                    row["conference_type"],
                    row["email"],
                ]
            ],
            showlegend=False,
        )

    # Y axis ticks (time of day)
    tick_vals = list(range(0, 25, 2))
    tick_text = [f"{h:02d}:00" for h in tick_vals]

    fig.update_layout(
        height=cfg.GRAPH_HEIGHT,
        bargap=0.6,
        xaxis=dict(
            type="date",
            range=[start_window, end_window],
            fixedrange=True,
            title="Date",
        ),
        yaxis=dict(
            range=[0, 24],
            tickvals=tick_vals,
            ticktext=tick_text,
            fixedrange=True,
            title="Time of Day",
        ),
        margin=dict(l=40, r=20, t=40, b=40),
    )

    # Today marker
    now_dt = datetime.now()
    fig.add_vline(
        x=now_dt,
        line_width=1,
        line_dash=cfg.LINE_STYLE,
        line_color=cfg.LINE_COLOR,
    )
    fig.add_annotation(
        x=now_dt,
        y=1,
        xref="x",
        yref="paper",
        text="Today",
        showarrow=False,
        font=dict(color=cfg.LINE_COLOR),
        yanchor="bottom",
    )

    return fig, {
        "reason": "ok",
        "rows_plotted": int(len(dfw)),
        "invalid_durations": invalid_count,
    }
