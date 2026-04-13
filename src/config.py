# ----------------------------
# Location of files
# ----------------------------
from pathlib import Path
script_dir = Path(__file__).resolve().parent

# ----------------------------
# Input filenames
# ----------------------------
HOURLY_GENERATION_FILE = script_dir.parent/"data/Actual_generation_202307160000_202307252359_Hour.csv"
HOURLY_CONSUMPTION_FILE = script_dir.parent/"data/Actual_consumption_202307160000_202307252359_Hour.csv"
DAILY_GENERATION_FILE = script_dir.parent/"data/Actual_generation_202307160000_202307252359_Day.csv"

CSV_SEPARATOR = ";"

# ----------------------------
# Hourly CSV column indices (csv module reading)
# ----------------------------
# In hourly generation CSV Date is line[0], Start is line[1]
HOURLY_DATE_COL = 0
HOURLY_START_COL = 1

# Hourly consumption is line[3]
HOURLY_CONSUMPTION_COL = 3

# ----------------------------
# Plot styling config (hourly stacked area)
# ----------------------------
# - name: label used in legends
# - hourly_col: index in hourly generation CSV (your old line[3], line[4]... etc.)
# - fill/stackgroup: Plotly stacked area settings
# - color: Plotly color name (kept same as your script)
HOURLY_SERIES = [
    {"name": "Biomass", "hourly_col": 3, "color": "green", "fill": "tozeroy", "stackgroup": "one"},
    {"name": "Hydropower", "hourly_col": 4, "color": "lightblue", "fill": "tonexty", "stackgroup": "one"},
    {"name": "Wind offshore", "hourly_col": 5, "color": "cyan", "fill": "tonexty", "stackgroup": "one"},
    {"name": "Wind onshore", "hourly_col": 6, "color": "mediumslateblue", "fill": "tonexty", "stackgroup": "one"},
    {"name": "Photovoltaics", "hourly_col": 7, "color": "yellow", "fill": "tonexty", "stackgroup": "one"},
    {"name": "Other renewable", "hourly_col": 8, "color": "greenyellow", "fill": "tonexty", "stackgroup": "one"},
    {"name": "Lignite", "hourly_col": 10, "color": "sienna", "fill": "tonexty", "stackgroup": "one"},
    {"name": "Hard coal", "hourly_col": 11, "color": "black", "fill": "tonexty", "stackgroup": "one"},
    {"name": "Fossil gas", "hourly_col": 12, "color": "lightgrey", "fill": "tonexty", "stackgroup": "one"},
    {"name": "Hydro pumped storage", "hourly_col": 13, "color": "darkblue", "fill": "tonexty", "stackgroup": "one"},
    {"name": "Other conventional", "hourly_col": 14, "color": "grey", "fill": "tonexty", "stackgroup": "one"},
]

# Consumption line styling (hourly plot)
CONSUMPTION_TRACE = {"name": "Consumption", "color": "red"}
