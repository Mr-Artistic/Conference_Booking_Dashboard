# config.py
from datetime import date
from dateutil.relativedelta import relativedelta

# Database
DB_NAME = "bookings.db"

# Timeline window (last month, this month, next month)
TODAY = date.today()
TIMELINE_START = TODAY.replace(day=1) - relativedelta(months=1)
TIMELINE_END = TODAY.replace(day=1) + relativedelta(months=2)

# Visual Styles
GRAPH_HEIGHT = 300
TABLE_HEIGHT = 250
LINE_COLOR = "grey"
LINE_STYLE = "dot"
