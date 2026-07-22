import csv
import pandas as pd

from pathlib import Path

from .config import (
    CSV_SEPARATOR,
    DATE_FORMATS,
    HOURLY_DATE_COL,
    HOURLY_START_COL,
    HOURLY_CONSUMPTION_COL,
    HOURLY_SERIES,
    )

def parse_float(value):
    """
    Convert a numeric string with optional thousand separators into a float.
    This helper strips whitespace, removes commas and converts the result to
    `float`. Empty strings are treated as missing values and returned as NaN.

    Args:
        value: String representation of a number (e.g., "1,234", "  500 ", "").

    Returns:
        Parsed floating-point value. Returns `float("nan")` if the input is empty.

    Raises:
        ValueError: If the cleaned string cannot be converted to float.
        AttributeError: If `value` is not a string-like object with `.strip()`.
    """
    value = value.strip()
    if value == "":
        return float("nan")
    return float(value.replace(",", ""))

def normalize_data_headers(path):
    df = pd.read_csv(path,sep=CSV_SEPARATOR)
    df.columns = (
        df.columns
        .str.strip()
        .str.replace("\ufeff", "", regex=False)
    )

    first_col = df.columns[0]

    if first_col == "Date":
        return path

    if first_col == "Start date":
        if "End date" not in df.columns:
            raise ValueError("'End date' column not found.")

        start_dt, end_dt = [],[]
        for date_format in DATE_FORMATS:
            start_dt = pd.to_datetime(df["Start date"], format=date_format, errors="coerce")
            end_dt = pd.to_datetime(df["End date"], format=date_format, errors="coerce")

            if not start_dt.isna().any() and not end_dt.isna().any():
                break

        if start_dt.isna().any() or end_dt.isna().any():
            raise ValueError("Some Start date or End date values could not be parsed.")

        df.insert(0, "Date", start_dt.dt.strftime("%b %-d, %Y"))
        df.insert(1, "Start", start_dt.dt.strftime("%-I:%M %p"))
        df.insert(2, "End", end_dt.dt.strftime("%-I:%M %p"))

        df = df.drop(columns=["Start date", "End date"])
        if "Nuclear [MWh] Calculated resolutions" in df.columns:
            df["Nuclear [MWh] Calculated resolutions"] = df["Nuclear [MWh] Calculated resolutions"].replace("-",0)
        processed_dir = path.parents[1] / "processed"
        processed_dir.mkdir(parents=True,exist_ok=True)
        processed_path = processed_dir / f"{path.stem}_processed.csv"
        df.to_csv(processed_path, sep=CSV_SEPARATOR, index=False, encoding="utf-8")
        return processed_path

    raise ValueError(f"Unrecognised first column '{first_col}'. Expected 'Date' or 'Start date'.")

def read_hourly_generation(path):
    """
    This function loads the hourly generation file using the standard `csv` module,
    extracts the configured energy-type columns (via `HOURLY_SERIES`) and builds a
    single datetime index by combining the `Date` and `Start` columns.

    Args:
        path: Path to the hourly generation CSV file.

    Returns:
        A tuple `(timestamps, series)` where:
          - `timestamps` is a `pd.DatetimeIndex` of hourly timestamps
          - `series` is a dictionary mapping energy type name to a list of hourly values,
            e.g. `{"Biomass": [...], "Hydropower": [...], ...}`

    Notes:
        - Numeric fields are parsed using `parse_float()`, which removes commas.
        - Datetime parsing uses `pd.to_datetime(..., errors="coerce")`. If any
          timestamps fail to parse, the function raises an error.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If one or more timestamps cannot be parsed from Date/Start columns.
        IndexError: If expected columns are missing (unexpected CSV format).
        ValueError: If numeric parsing fails for a non-empty value.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Hourly generation file not found: {path}")

    # Prepare output containers from config
    series = {s["name"]: [] for s in HOURLY_SERIES}
    date_parts = []
    start_parts = []

    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=CSV_SEPARATOR)
        next(reader, None)  # skip header

        for row in reader:
            date_parts.append(row[HOURLY_DATE_COL])
            start_parts.append(row[HOURLY_START_COL])

            for s in HOURLY_SERIES:
                series[s["name"]].append(parse_float(row[s["hourly_col"]]))

    # Build a single proper x-axis
    timestamps = pd.to_datetime([f"{d} {t}" for d, t in zip(date_parts, start_parts)], format=DATE_FORMATS[0], errors="coerce")

    # Validation for time stamps
    if timestamps.isna().any():
        bad = timestamps.isna().sum()
        raise ValueError(f"Failed to parse {bad} timestamps in {path.name}. Check Date/Start format.")

    return pd.DatetimeIndex(timestamps), series

def read_hourly_consumption(path):
    """
    This function loads the hourly consumption CSV file using the standard `csv`
    module and extracts the consumption column configured by `HOURLY_CONSUMPTION_COL`.

    Args:
        path: Path to the hourly consumption CSV file.

    Returns:
        A list of hourly consumption values as floats.

    Notes:
        - Values are parsed using `parse_float()`, which strips whitespace and removes
          comma thousand separators.
        - Empty numeric fields are returned as NaN (via `parse_float()`).

    Raises:
        FileNotFoundError: If the file does not exist.
        IndexError: If the configured consumption column index is out of range.
        ValueError: If numeric parsing fails for a non-empty value.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Hourly consumption file not found: {path}")

    consumption= []

    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=CSV_SEPARATOR)
        next(reader, None)  # skip header

        for row in reader:
            consumption.append(parse_float(row[HOURLY_CONSUMPTION_COL]))

    return consumption

def read_daily_generation_df(path):
    """
    Load the daily generation CSV file into a pandas DataFrame and normalize numeric formatting.
    The cleaned DataFrame is returned for downstream analysis and plotting.

    Args:
        path: Path to the daily generation CSV file.

    Returns:
        A pandas DataFrame containing the daily generation data (including the `Date` column
        and energy-category columns such as `"<category> [MWh] Calculated resolutions"`).

    Notes:
        - The cleaning step uses `df.replace(",", "", regex=True)` to remove commas globally.
          This is appropriate for datasets where commas are used only as thousand separators.
        - If you expect commas to appear as part of text fields, consider limiting the
          replacement to numeric columns only.

    Raises:
        FileNotFoundError: If the file does not exist.
        pandas.errors.ParserError: If the file cannot be parsed as a CSV with the given separator.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Daily generation file not found: {path}")

    df = pd.read_csv(path, sep=CSV_SEPARATOR)
    # Remove commas from ALL string cells (safe enough for your dataset)
    df = df.replace(",", "", regex=True)
    return df
