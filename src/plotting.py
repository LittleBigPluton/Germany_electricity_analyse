import math
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px

from plotly.subplots import make_subplots

from config import (
    CONSUMPTION_TRACE,
    HOURLY_SERIES,
    ALL_DAILY_CATEGORIES,
    SUNBURST_LABELS,
    SUNBURST_PARENTS,
    ENERGY_TYPES_RENEWABLE,
    MWH_SUFFIX,
    )

from stats_utils import summarize

def _add_stacked_trace(fig, name, x, y, color, fill, stackgroup):
    """
    This adds a `go.Scatter` trace configured for line or stacked-area plotting.
    It also computes the mean and sample standard deviation of the provided y-values
    (via `summarize`) and includes those statistics in the trace name for hover/legend
    display.

    Args:
        fig: Target Plotly figure to which the trace will be added.
        name: Display name for the trace (e.g., "Biomass").
        x: X-axis values for the trace (typically a `pd.DatetimeIndex`).
        y: Y-axis values for the trace (numeric sequence).
        color: Line color (and fill color when `fill` is provided).
        fill: Plotly fill mode (e.g., `"tozeroy"`, `"tonexty"`). If `None`, the trace
            will be rendered as a line without area fill.
        stackgroup: Plotly stack group name for stacking filled areas (e.g., `"one"`).
            If `None`, stacking is disabled for this trace.

    Returns:
        A tuple `(avg, sd)` where:
          - `avg` is the arithmetic mean of `y`
          - `sd` is the sample standard deviation of `y` (ddof=1)

    Notes:
        - If `fill` is not `None`, the trace uses `fillcolor=color` for the area.
        - `summarize(y)` may raise `ValueError` if `y` is empty or has fewer than
          two values (depending on `mean/stddev_sample` implementation).
    """
    avg, sd = summarize(y)

    scatter_kwargs = dict(
        name=f"{name}: <br>  Mean: {avg:.2f} MWh<br>  Std: {sd:.2f} MWh",
        x=x,
        y=y,
        mode="lines",
        line_color=color,
    )

    # Check Plotly params
    if fill is not None:
        scatter_kwargs["fill"] = fill
        scatter_kwargs["fillcolor"] = color
    if stackgroup is not None:
        scatter_kwargs["stackgroup"] = stackgroup

    fig.add_trace(go.Scatter(**scatter_kwargs))
    return avg, sd

def plot_hourly_stacked_area(timestamps, generation_series, consumption = None):
    """
    Create an hourly stacked-area chart for generation series and a consumption line.
    The generation series are plotted as stacked filled areas according to the configuration
    in `HOURLY_SERIES` (colors, fill mode, and stackgroup). If `consumption` is provided,
    it is overlaid as a regular line (not stacked).

    Args:
        timestamps: X-axis values for the hourly data (typically a `pd.DatetimeIndex` or
            sequence of datetimes) with the same length as each series in `generation_series`.
        generation_series: Mapping from series name (e.g., `"Biomass"`) to a list/array of
            hourly generation values. Keys must match the `"name"` fields in `HOURLY_SERIES`.
        consumption: Optional list/array of hourly consumption values to plot as a line.
            If provided, it should have the same length as `timestamps`.

    Returns:
        A Plotly `go.Figure` containing:
          - stacked area traces for each generation category
          - an optional line trace for consumption

    Raises:
        KeyError: If a series name from `HOURLY_SERIES` is missing in `generation_series`.
        ValueError: If summary-stat computation inside `_add_stacked_trace` fails (e.g.,
            empty series).
    """
    fig = go.Figure()

    # Generation series (stacked)
    for s in HOURLY_SERIES:
        name = s["name"]
        y = generation_series[name]
        _add_stacked_trace(
            fig=fig,
            name=name,
            x=timestamps,
            y=y,
            color=s["color"],
            fill=s.get("fill"),
            stackgroup=s.get("stackgroup"),
        )

    # Consumption as a line (no stackgroup, no fill)
    if consumption is not None:
        fig.add_trace(
            go.Scatter(
                name=CONSUMPTION_TRACE["name"],
                x=timestamps,
                y=consumption,
                mode="lines",
                line_color=CONSUMPTION_TRACE["color"],
            )
        )

    fig.update_layout(
        hovermode="x unified",
        plot_bgcolor="white",
        xaxis=dict(
            title="Time",
            showgrid=False,
            showdividers=False,
        ),
        yaxis=dict(title="Electricity [MWh]"),
        legend=dict(title="Series"),
    )
    return fig

def plot_sunburst_grid(df_daily):
    """
    Build a grid of daily sunburst plots for renewable vs. conventional energy breakdown.
    For each day (row) in the input dataframe, it creates a Plotly sunburst chart
    with two top-level nodes ("Renewable", "Conventional") and leaf nodes for each configured
    generation category. All daily sunburst charts are arranged in a subplot grid with an
    automatically chosen number of rows/columns.

    Args:
        df_daily: Daily generation dataframe. Must contain a `Date` column and one column
            per energy category following the naming convention
            `"<category> [MWh] Calculated resolutions"` (see `ALL_DAILY_CATEGORIES`).

    Returns:
        A Plotly `go.Figure` containing a subplot grid of sunburst charts (one chart per day).

    Notes:
        - The layout uses up to 5 columns and computes rows as `ceil(period / cols)` to avoid
          interactive input and keep the output deterministic.
        - Category values are converted via `float(...)` per cell; ensure the dataframe has
          already been cleaned of thousand separators (e.g., commas) if applicable.

    Raises:
        ValueError: If the dataframe is missing the `Date` column or contains no rows.
        KeyError: If one or more expected category columns are missing from `df_daily`.
        ValueError: If a required category value cannot be converted to float.
    """
    if "Date" not in df_daily.columns:
        raise ValueError("df_daily must contain a 'Date' column")

    period = len(df_daily["Date"])
    if period == 0:
        raise ValueError("df_daily has no rows")

    # Choose a stable automatic layout (no interactive input)
    cols = min(period, 5)
    rows = math.ceil(period / cols)

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=df_daily["Date"].astype(str).tolist(),
        specs=[[{"type": "domain"}] * cols] * rows,
    )

    categories = ALL_DAILY_CATEGORIES
    labels = SUNBURST_LABELS
    parents = [""] * len(labels) + SUNBURST_PARENTS

    for i in range(period):
        # values array: [Total Renewable, Total Conventional] + per-category values
        values = [0.0] * (len(labels) + len(categories))

        for j, category in enumerate(categories):
            col_name = f"{category}{MWH_SUFFIX}"
            daily_val = float(df_daily.loc[i, col_name])
            values[len(labels) + j] = daily_val

            if category in ENERGY_TYPES_RENEWABLE:
                values[0] += daily_val
            else:
                values[1] += daily_val

        sunburst = px.sunburst(
            names=labels + categories,
            parents=parents,
            values=values,
            branchvalues="total",
        )

        fig.add_trace(
            sunburst.data[0],
            row=(i // cols) + 1,
            col=(i % cols) + 1,
        )

    fig.update_layout(title="Daily Energy Generation Sunburst Chart")
    return fig

def plot_error_bars_by_type(df_daily, categories, title, ext = MWH_SUFFIX):
    """
    Create a bar chart of daily means with sample-standard-deviation error bars.
    For each category in `categories`, this function selects the corresponding column
    from `df_daily`, converts it to numeric values, and computes:
      - mean (bar height)
      - sample standard deviation (error bar; ddof=1)

    Args:
        df_daily: Daily dataframe containing the numeric columns to summarize.
        categories: List of category names. For each name, the target column is resolved
            as `f"{name}{ext}"` (e.g., `"Biomass [MWh] Calculated resolutions"`).
        title: Figure title shown at the top of the chart.
        ext: Column suffix appended to each category name to form the dataframe column.
            If `ext` is an empty string, the category name itself is used as the column
            name. Defaults to `MWH_SUFFIX`.

    Returns:
        A Plotly `go.Figure` containing one bar per category with an error bar showing
        the sample standard deviation.

    Notes:
        - Values are converted with `pd.to_numeric(..., errors="coerce")`; non-numeric
          values become NaN and are dropped.
        - Standard deviation is computed with `ddof=1` (sample std dev), matching
          common statistical reporting conventions.
        - If a column contains no valid numeric values, `np.mean`/`np.std` will yield
          NaN; consider adding an explicit check if you want to skip empty categories.

    Raises:
        KeyError: If a resolved column name does not exist in `df_daily`.
    """
    fig = go.Figure()

    for name in categories:
        col = f"{name}{ext}" if ext else name
        data = pd.to_numeric(df_daily[col], errors="coerce").dropna().values

        fig.add_trace(
            go.Bar(
                x=[name],
                y=[float(np.mean(data))],
                name=name,
                error_y=dict(type="data", array=[float(np.std(data, ddof=1))], visible=True),
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="Type",
        yaxis_title="Energy [MWh]",
        barmode="group",
    )
    return fig

def plot_trends(
    df_daily: pd.DataFrame,
    title: str = "Total Consumption & Production with Trend Lines",
) -> go.Figure:
    """
    Plot Total Consumption and Total Production with linear trend lines.
    Expects df_daily indexed by datetime (Date) and containing:
      - 'Total Consumption'
      - 'Total Production'
    """
    if not isinstance(df_daily.index, (pd.DatetimeIndex, pd.Index)):
        raise ValueError("df_daily should be indexed by Date (DatetimeIndex preferred)")

    df = df_daily.copy()

    # Ensure numeric
    df["Total Consumption"] = pd.to_numeric(df["Total Consumption"], errors="coerce")
    df["Total Production"] = pd.to_numeric(df["Total Production"], errors="coerce")

    # Create time axis for regression
    t = np.arange(len(df), dtype=float)

    # Consumption trend
    cons = df["Total Consumption"].values.astype(float)
    slope_c, intercept_c = np.polyfit(t, cons, 1)
    cons_trend = intercept_c + slope_c * t

    # Production trend
    prod = df["Total Production"].values.astype(float)
    slope_p, intercept_p = np.polyfit(t, prod, 1)
    prod_trend = intercept_p + slope_p * t

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Total Consumption"], mode="lines", name="Total Consumption"))
    fig.add_trace(go.Scatter(x=df.index, y=cons_trend, mode="lines", name="Consumption Trend", line=dict(dash="dash")))
    fig.add_trace(go.Scatter(x=df.index, y=df["Total Production"], mode="lines", name="Total Production"))
    fig.add_trace(go.Scatter(x=df.index, y=prod_trend, mode="lines", name="Production Trend", line=dict(dash="dash")))

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Energy [MWh]",
        hovermode="x unified",
    )
    return fig
