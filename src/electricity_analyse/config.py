# ----------------------------
# Location of files
# ----------------------------
from pathlib import Path
script_dir = Path(__file__).resolve().parent
ROOT_DIRECTORY = script_dir.parent.parent

# ----------------------------
# Input filenames
# ----------------------------

HOURLY_GENERATION_FILE_RAW = ROOT_DIRECTORY/"data/yearly/energy/2025/raw/Actual_generation_202501010000_202601010000_Hour.csv"
HOURLY_CONSUMPTION_FILE_RAW = ROOT_DIRECTORY/"data/yearly/energy/2025/raw/Actual_consumption_202501010000_202601010000_Hour.csv"
DAILY_GENERATION_FILE_RAW = ROOT_DIRECTORY/"data/yearly/energy/2025/raw/Actual_generation_202501010000_202601010000_Day.csv"

HOURLY_GENERATION_FILE_PROC = ""
HOURLY_CONSUMPTION_FILE_PROC = ""
DAILY_GENERATION_FILE_PROC = ""

CSV_SEPARATOR = ";"

# ----------------------------
# Output filename
# ----------------------------
analysis_file_dir = ROOT_DIRECTORY/"docs/Analysis"
analysis_file_dir.mkdir(parents=True,exist_ok=True)

figure_export_dir = ROOT_DIRECTORY/"docs"
figure_export_dir.mkdir(parents=True,exist_ok=True)

# ----------------------------
# Specify expected time formats
# ----------------------------
DATE_FORMATS = [
    "%b %d, %Y %I:%M %p",   # Jan 1, 2025 12:00 AM
    "%b %d, %Y",             # Jan 1, 2025
    "%Y-%m-%d %H:%M:%S",    # 2025-01-01 00:00:00
    "%Y-%m-%d %H:%M",       # 2025-01-01 00:00
    "%Y-%m-%d",             # 2025-01-01
]


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

# ----------------------------
# Energy categories (daily analysis + sunburst)
# ----------------------------
ENERGY_TYPES_RENEWABLE = [
    "Biomass",
    "Hydropower",
    "Wind offshore",
    "Wind onshore",
    "Photovoltaics",
    "Other renewable",
]

ENERGY_TYPES_CONVENTIONAL = [
    "Nuclear",
    "Lignite",
    "Hard coal",
    "Fossil gas",
    "Hydro pumped storage",
    "Other conventional",
]

SUNBURST_LABELS = ["Renewable", "Conventional"]
SUNBURST_PARENTS = (["Renewable"] * len(ENERGY_TYPES_RENEWABLE)) + (
    ["Conventional"] * len(ENERGY_TYPES_CONVENTIONAL)
)
grid_max_days = 31

# A flat list used in loops (same order as you used later)
ALL_DAILY_CATEGORIES = ENERGY_TYPES_RENEWABLE + ENERGY_TYPES_CONVENTIONAL

# ----------------------------
# Column naming conventions (daily dataframe)
# ----------------------------
# Daily based CSV data columns look like: "Biomass [MWh] Calculated resolutions"
MWH_SUFFIX = " [MWh] Calculated resolutions"
DAILY_CONSUMPTION_COL = "grid load [MWh] Calculated resolutions"

# ----------------------------
# Derived / convenience sets
# ----------------------------
# Helpful to decide energy type
RENEWABLE_SET = set(ENERGY_TYPES_RENEWABLE)

# A flat list used in loops (same order as you used later)
ALL_DAILY_CATEGORIES = ENERGY_TYPES_RENEWABLE + ENERGY_TYPES_CONVENTIONAL
