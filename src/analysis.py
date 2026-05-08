import pandas as pd
import numpy as np

from config import (
    ALL_DAILY_CATEGORIES,
    MWH_SUFFIX,
    ENERGY_TYPES_RENEWABLE,
    RENEWABLE_SET,
    analysis_file_path,
)

from dataclasses import dataclass

@dataclass(frozen=True)
class TrendResult:
    slope: float
    intercept: float

def export_analysis(analysis_file_path,analysis, echo = True):
    """
    Export analysis to a text file and optionally echo them to stdout.

    Args:
        analysis_file_path: Path of the output text file.
        analysis: Iterable of lines to write (newline will be added automatically).
        echo: If True, print each line after writing.
    """

    with analysis_file_path.open("a", encoding="utf-8") as analysis_file:
        for analyse in analysis:
            analysis_file.write(f"{analyse}\n")
            if echo:
                print(analyse)


def add_daily_totals(df_daily):
    """
    This function converts the per-category daily energy columns to numeric values and then
    computes three new columns:
      - `Total Renewable`: sum of all renewable categories
      - `Total Conventional`: sum of all conventional categories
      - `Total Production`: renewable + conventional

    The function does not mutate the input dataframe; it returns a copied dataframe with
    the additional columns.

    Args:
        df_daily: Daily generation dataframe that contains one column per energy category
            using the naming convention `"<category> [MWh] Calculated resolutions"`.

    Returns:
        A new dataframe with the columns `Total Renewable`, `Total Conventional`
        and `Total Production` appended.

    Raises:
        KeyError: If one or more expected category columns are missing from `df_daily`.
    """
    # Copy data frame to make sure no change in raw data
    df_copy = df_daily.copy()

    # Make sure daily category columns are numeric
    for cat in ALL_DAILY_CATEGORIES:
        col = f"{cat}{MWH_SUFFIX}"
        df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce")

    # Extract column names from the data
    renewable_cols = [f"{c}{MWH_SUFFIX}" for c in ENERGY_TYPES_RENEWABLE]
    conventional_cols = [f"{c}{MWH_SUFFIX}" for c in ALL_DAILY_CATEGORIES if c not in RENEWABLE_SET]

    # Store total production of energy by category
    df_copy["Total Renewable"] = df_copy[renewable_cols].sum(axis=1, skipna=True)
    df_copy["Total Conventional"] = df_copy[conventional_cols].sum(axis=1, skipna=True)
    df_copy["Total Production"] = df_copy["Total Renewable"] + df_copy["Total Conventional"]

    return df_copy


def set_date_index(df_daily, date_col):
    """
    This function validates that `date_col` exists, converts it to datetime using
    `pd.to_datetime` and then returns a new dataframe indexed by that datetime
    column in ascending order. The input dataframe is not mutated.

    Args:
        df_daily: Input dataframe that contains a date column.
        date_col: Name of the column to convert to datetime and use as the index.
            Defaults to `"Date"`.

    Returns:
        A new dataframe where `date_col` has been converted to datetime and set
        as the index (sorted increasingly).

    Raises:
        ValueError: If `date_col` is missing from `df_daily`.
        ValueError: If one or more values in `date_col` cannot be parsed as datetime.
    """
    if date_col not in df_daily.columns:
        raise ValueError(f"Expected '{date_col}' column in daily dataframe")

    df = df_daily.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    if df[date_col].isna().any():
        bad = int(df[date_col].isna().sum())
        raise ValueError(f"Failed to parse {bad} date values in '{date_col}'")

    return df.set_index(date_col).sort_index()

def add_daily_consumption_from_hourly(
    df_daily_indexed,
    df_hourly_consumption,
    hourly_date_col,
    hourly_value_col):
    """
    This function takes a daily dataframe indexed by date (DatetimeIndex) and an hourly
    consumption dataframe. It converts the hourly datetime column to pandas datetime,
    sets it as the index, resamples the hourly consumption values to daily sums and
    aligns (reindexes) the resulting daily series to the daily dataframe index.

    Args:
        df_daily_indexed: Daily dataframe indexed by date (DatetimeIndex). The output
            will preserve this index and add a new column.
        df_hourly_consumption: Hourly consumption dataframe containing a datetime column
            (`hourly_date_col`) and a numeric consumption column (`hourly_value_col`).
        hourly_date_col: Name of the datetime column in `df_hourly_consumption`.
            Defaults to `"Date"`.
        hourly_value_col: Name of the consumption value column in `df_hourly_consumption`.
            Defaults to `DAILY_CONSUMPTION_COL`.

    Returns:
        A new daily dataframe with an additional column:
          - `Total Consumption`: daily summed consumption aligned to the daily index.

    Raises:
        ValueError: If `df_daily_indexed` is not indexed by `pd.DatetimeIndex`.
    """
    if not isinstance(df_daily_indexed.index, pd.DatetimeIndex):
        raise ValueError("df_daily_indexed must be indexed by Date (DatetimeIndex)")

    df = df_daily_indexed.copy()

    hourly = df_hourly_consumption.copy()
    hourly[hourly_date_col] = pd.to_datetime(hourly[hourly_date_col], errors="coerce")
    hourly = hourly.set_index(hourly_date_col).sort_index()

    hourly[hourly_value_col] = pd.to_numeric(hourly[hourly_value_col], errors="coerce")

    daily_sum = hourly[hourly_value_col].resample("D").sum(min_count=1)
    df["Total Consumption"] = daily_sum.reindex(df.index)

    return df

def comparison_days(df, lhs, rhs):
    """
    The function compares `df[lhs]` and `df[rhs]` row-wise (after coercing both columns
    to numeric) and returns a list of date strings for which `lhs > rhs` holds true.
    The dataframe is expected to be indexed by a `DatetimeIndex` so that dates can be
    extracted reliably.

    Args:
        df: Input dataframe indexed by datetime (pd.DatetimeIndex).
        lhs: Name of the left-hand-side column to compare.
        rhs: Name of the right-hand-side column to compare.

    Returns:
        A list of ISO-formatted date strings (e.g., `"2023-07-16"`) where
        `df[lhs] > df[rhs]`.

    Raises:
        ValueError: If `df` does not have a `pd.DatetimeIndex`.
        KeyError: If `lhs` or `rhs` is not present in `df`.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Dataframe must have a DatetimeIndex for comparison_days()")

    mask = pd.to_numeric(df[lhs], errors="coerce") > pd.to_numeric(df[rhs], errors="coerce")
    days = df.index[mask].date
    return [str(d) for d in days]

def build_comparison_messages(df):
    """
    Build the 3 comparison messages according to comparison of days.

    Args:
        df: Daily dataframe indexed by datetime (pd.DatetimeIndex). Must contain the
            columns `Total Production`, `Total Consumption`, `Total Renewable`,
            and `Total Conventional`.

    Returns:
        A list of three strings, each describing whether the condition occurred and,
        if so, on which dates.

    Raises:
        ValueError: If `df` is not indexed by `pd.DatetimeIndex` (raised by
            `comparison_days()`).
        KeyError: If one or more required columns are missing (raised by
            `comparison_days()` when accessing columns).
    """
    msgs = []
    exceeded_days = comparison_days(df, "Total Production", "Total Consumption")
    count_exceeded_days = len(exceeded_days)
    eco_days = comparison_days(df, "Total Renewable", "Total Conventional")
    count_eco_days = len(eco_days)
    green_days = comparison_days(df, "Total Renewable", "Total Consumption")
    total_days = len(df)

    msgs.append(
        f"Germany generated more electricity than demand on {', '.join(exceeded_days)}. "
        f"That is {count_exceeded_days} out of {total_days} days where generation exceeded demand."
        if exceeded_days
        else "Germany has not generated more electricity than demand on any day."
    )

    msgs.append(
        f"Germany has generated more renewable electricity than demand on {', '.join(green_days)}"
        f"Germany exceeded demanded energy on {count_eco_days} out of {total_days} by renewable energies only."
        if green_days
        else "Germany has not generated more renewable electricity than demand on any day."
    )

    msgs.append(
        f"Germany has generated more renewable electricity than conventional ones on {', '.join(eco_days)}."
        f"That is occurred on {count_eco_days} out of {total_days} days."
        if eco_days
        else "Germany has not generated more renewable electricity than conventional ones on any day."
    )
    return msgs

def compute_stats_table(df, category_columns, extra_columns=["Total Renewable", "Total Conventional", "Total Production", "Total Consumption"]):
    """
    This function produces a separate "stats table" rather than appending summary rows
    (e.g., Average/Std Dev/Percentage) to the time-series dataframe. For each requested
    column, it computes:
      - `mean`: arithmetic mean
      - `std`: sample standard deviation (ddof=1)
      - `cv_percent`: coefficient of variation in percent, defined as (std / mean) * 100

    Args:
        df: Input dataframe containing numeric time-series columns.
        category_columns: List of column names (typically per-energy-type daily columns)
            to include in the stats table.
        extra_columns: Additional aggregate columns to include (e.g., totals). Defaults
            to `["Total Renewable", "Total Conventional", "Total Production", "Total Consumption"]`.

    Returns:
        A dataframe indexed by column name (one row per input column) with three statistic
        columns: `mean`, `std`, and `cv_percent`.

    Raises:
        KeyError: If any requested column in `category_columns` or `extra_columns`
          is not present in `df`.
    """
    cols = []
    for c in category_columns:
        cols.append(c)
    cols.extend(extra_columns)

    stats = {}
    for col in cols:
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(s) == 0:
            stats[col] = {"mean": np.nan, "std": np.nan, "cv_percent": np.nan}
            continue
        mean = float(s.mean())
        std = float(s.std(ddof=1))
        cv = float(std / mean * 100) if mean != 0 else np.nan
        stats[col] = {"mean": mean, "std": std, "cv_percent": cv}

    stats_df = pd.DataFrame(stats).T
    # transpose to have rows = metrics if you prefer
    return stats_df

def rank_stability(df, category_columns):
    """
    Rank columns by stability using sample standard deviation. Stability is defined
    here as having a lower sample standard deviation (ddof=1) across the available
    observations. Columns with fewer than two valid numeric values cannot produce a
    sample standard deviation and are treated as having infinite variability, so they
     appear at the end of the ranking.

    Args:
        df: Input dataframe containing the columns to be ranked.
        category_columns: List of column names to evaluate and rank.

    Returns:
        A list of column names sorted by increasing sample standard deviation
        (most stable first).

    Raises:
        KeyError: If any column in `category_columns` is missing from `df`.
    """
    stds = {}
    for col in category_columns:
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        stds[col] = float(s.std(ddof=1)) if len(s) > 1 else np.inf

    return sorted(stds.keys(), key=lambda c: stds[c])

def linear_trend(series):
    """
    Fit a linear trend line to a time-ordered series.

    The model is: y(t) = intercept + slope * t, where t is a simple integer index
    from 0 to n-1. This is useful for estimating whether the series is increasing
    or decreasing over time.

    Args:
        series: Input series of values ordered in time (or any consistent order).
            Values are coerced to numeric.

    Returns:
        A `TrendResult` containing:
          - `slope`: slope of the fitted line
          - `intercept`: intercept of the fitted line

    Raises:
        TypeError: If `series` cannot be converted to numeric values suitable for fitting.
        ValueError: If fewer than two data points are available for fitting.
    """
    y = pd.to_numeric(series, errors="coerce").values.astype(float)
    t = np.arange(len(y), dtype=float)
    slope, intercept = np.polyfit(t, y, 1)
    return TrendResult(slope=float(slope), intercept=float(intercept))


def describe_trend(name, slope):
    """
    Description of a trend based on the slope.

    Args:
        name: Name of the metric being described (e.g., "Total Consumption").
        slope: Slope value from a fitted linear trend model.

    Returns:
        A sentence describing whether the metric has an increasing, decreasing,
        or stable trend, including the slope formatted to two decimals.
    """
    if slope > 0:
        return f"{name} has an increasing trend (slope={slope:.2f})."
    if slope < 0:
        return f"{name} has a decreasing trend (slope={slope:.2f})."
    return f"{name} has a stable trend (slope={slope:.2f})."
