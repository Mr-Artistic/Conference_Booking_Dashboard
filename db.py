import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_NAME

# Columns we expect in 'bookings' (name, type, default)
REQUIRED_COLUMNS = [
    ("booking_date", "TEXT", None),
    ("start_time", "TEXT", None),
    ("end_time", "TEXT", None),
    ("conference_type", "TEXT", ""),  # <- new column; default empty string
    ("person_name", "TEXT", None),
    ("company_name", "TEXT", None),
    ("affiliation", "TEXT", None),
    ("email", "TEXT", None),
]


def _column_names(conn, table):
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]  # r[1] = column name


def _add_column(conn, table, name, coltype, default=None):
    if default is None:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {coltype}")
    else:
        # quote TEXT defaults
        if isinstance(default, (int, float)):
            defval = str(default)
        else:
            defval = str(default).replace("'", "''")
            defval = f"'{defval}'"
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN {name} {coltype} DEFAULT {defval}"
        )


def init_db():
    conn = sqlite3.connect(DB_NAME)
    try:
        # Create table if it doesn't exist (latest shape)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_date TEXT,
                start_time TEXT,
                end_time TEXT,
                conference_type TEXT,
                person_name TEXT,
                company_name TEXT,
                affiliation TEXT,
                email TEXT
            )
            """
        )

        # 🔧 Migrate older DBs: add any missing columns
        existing = set(_column_names(conn, "bookings"))
        for name, coltype, default in REQUIRED_COLUMNS:
            if name not in existing:
                _add_column(conn, "bookings", name, coltype, default)

        conn.commit()
    finally:
        conn.close()


def add_booking(
    booking_date,
    start_time,
    end_time,
    conference_type,
    person_name,
    company_name,
    affiliation,
    email,
):
    # Normalize to strings for consistency
    booking_date = str(booking_date) if booking_date is not None else ""
    start_time = str(start_time) if start_time is not None else ""
    end_time = str(end_time) if end_time is not None else ""
    conference_type = str(conference_type or "")
    person_name = str(person_name or "")
    company_name = str(company_name or "")
    affiliation = str(affiliation or "")
    email = str(email or "")

    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute(
            """
            INSERT INTO bookings
            (booking_date, start_time, end_time, conference_type, person_name, company_name, affiliation, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                booking_date,
                start_time,
                end_time,
                conference_type,
                person_name,
                company_name,
                affiliation,
                email,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_bookings():
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM bookings", conn)
        return df
    finally:
        conn.close()


def check_conflict(booking_date, start_time, end_time):
    df = get_bookings()
    if df.empty:
        return False, None
    same_day = df[df["booking_date"] == str(booking_date)]
    if same_day.empty:
        return False, None

    new_start = datetime.strptime(f"{booking_date} {start_time}", "%Y-%m-%d %H:%M:%S")
    new_end = datetime.strptime(f"{booking_date} {end_time}", "%Y-%m-%d %H:%M:%S")

    for _, row in same_day.iterrows():
        existing_start = datetime.strptime(
            f"{row['booking_date']} {row['start_time']}", "%Y-%m-%d %H:%M:%S"
        )
        existing_end = datetime.strptime(
            f"{row['booking_date']} {row['end_time']}", "%Y-%m-%d %H:%M:%S"
        )
        if new_start < existing_end and new_end > existing_start:
            details = (
                f"Existing booking by **{row['person_name']} ({row['company_name']})** "
                f"from {row['start_time']} to {row['end_time']}"
            )
            return True, details
    return False, None
