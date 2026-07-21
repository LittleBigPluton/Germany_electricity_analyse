import math
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px

from plotly.subplots import make_subplots

from .config import (
    CONSUMPTION_TRACE,
    HOURLY_SERIES,
    ALL_DAILY_CATEGORIES,
    SUNBURST_LABELS,
    SUNBURST_PARENTS,
    ENERGY_TYPES_RENEWABLE,
    MWH_SUFFIX,
    grid_max_days,
    )

from .stats_utils import summarize
from .export_utils import export_figure

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
    scatter_kwargs = dict(name=f"{name}: <br>  Mean: {avg:.2f} MWh<br>  Std: {sd:.2f} MWh",x=x,y=y,mode="lines",line_color=color)

    # Check Plotly params
    if fill is not None:
        scatter_kwargs["fill"] = fill
        scatter_kwargs["fillcolor"] = color
    if stackgroup is not None:
        scatter_kwargs["stackgroup"] = stackgroup

    fig.add_trace(go.Scatter(**scatter_kwargs))
    return avg, sd

def plot_hourly_stacked_area(timestamps, generation_series, consumption = None, save = False, fmt = 'html'):
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
        _add_stacked_trace(fig=fig,name=name,x=timestamps,y=y,color=s["color"],fill=s.get("fill"),stackgroup=s.get("stackgroup"))

    # Consumption as a line (no stackgroup, no fill)
    if consumption is not None:
        fig.add_trace(go.Scatter(name=CONSUMPTION_TRACE["name"],x=timestamps,y=consumption,mode="lines",line_color=CONSUMPTION_TRACE["color"]))

    fig.update_layout(hovermode="x unified",plot_bgcolor="white",xaxis=dict(title="Time",showgrid=False,showdividers=False),yaxis=dict(title="Electricity [MWh]"),legend=dict(title="Series"))

    # Export the hourly stacked figure if desired with given params
    if save:
        export_figure(fig,"Hourly_Stacked_Plot",fmt)
    return fig

def plot_sunburst_dropdown(df_daily):
    """
    Internal helper: one sunburst + dropdown to select day.
    """
    categories = ALL_DAILY_CATEGORIES
    labels = SUNBURST_LABELS
    parents = [""] * len(labels) + SUNBURST_PARENTS
    dates = df_daily["Date"].astype(str).tolist()

    # Precompute values for each day (fast switching, clean code)
    all_values = []
    for i in range(len(df_daily)):
        values = [0.0] * (len(labels) + len(categories))
        for j, category in enumerate(categories):
            col_name = f"{category}{MWH_SUFFIX}"
            daily_val = float(df_daily.loc[i, col_name])
            values[len(labels) + j] = daily_val
            values[0 if category in ENERGY_TYPES_RENEWABLE else 1] += daily_val
        all_values.append(values)

    # Start with day 0
    fig = go.Figure(data=[go.Sunburst(labels=labels + categories,parents=parents,values=all_values[0],branchvalues="total",insidetextorientation="radial")])

    # Dropdown buttons: update the trace values and the title
    buttons = []
    for i, day in enumerate(dates):
        buttons.append(dict(label=day,method="update",args=[{"values": [all_values[i]]},{"title": f"Daily Energy Generation Sunburst — {day}"}]))

    fig.update_layout(updatemenus=[dict(type="dropdown",x=0.0,y=1.15,showactive=True,buttons=buttons)],margin=dict(t=80, l=10, r=10, b=10),title=f"Daily Energy Generation Sunburst — {dates[0]}")

    return fig

def plot_sunburst_grid(df_daily, save = False, fmt = 'html'):
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

    # Decide mode
    if period > grid_max_days:
        fig = plot_sunburst_dropdown(df_daily)
        fig.update_layout(title="Daily Energy Generation Sunburst (Select Date)")
        if save:
            export_figure(fig, "Daily_Generation_Sunburst_Dropdown", fmt)
        return fig

    # Choose a stable automatic layout (no interactive input)
    cols = min(period, 5)
    rows = math.ceil(period / cols)
    fig = make_subplots(rows=rows,cols=cols,subplot_titles=df_daily["Date"].astype(str).tolist(),specs=[[{"type": "domain"}] * cols] * rows)
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

        sunburst = px.sunburst(names=labels + categories,parents=parents,values=values,branchvalues="total")
        fig.add_trace(sunburst.data[0],row=(i // cols) + 1,col=(i % cols) + 1)

    fig.update_layout(title="Daily Energy Generation Sunburst Chart")

    # Export the sunbrust figure if desired with given params
    if save:
        export_figure(fig,"Daily_Generation_Sunbrust_Plot",fmt)

    return fig

def plot_error_bars_by_type(df_daily, categories, title, ext = MWH_SUFFIX, save = False, fmt = 'html'):
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
        fig.add_trace(go.Bar(x=[name],y=[float(np.mean(data))],name=name,error_y=dict(type="data", array=[float(np.std(data, ddof=1))], visible=True)))

    fig.update_layout(title=title,xaxis_title="Type",yaxis_title="Energy [MWh]",barmode="group")

    # Export the daily energy generation with fluctuations figure if desired with given params
    if save:
        export_figure_name = title.replace(" ","_")
        export_figure(fig,export_figure_name,fmt)

    return fig

def plot_trends(df_daily, title = "Total Consumption and Production with Trend Lines", save=False, fmt='html'):
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
    fig.update_layout(title=title,xaxis_title="Date",yaxis_title="Energy [MWh]",hovermode="x unified",)

    # Export the trend figure if desired with given params
    if save:
        export_figure_name = title.replace(" ","_")
        export_figure(fig,export_figure_name,fmt)

    return fig

def plot_drilldown(df_daily,column_to_plot,title,yaxis_title,date_col="Date",percentage=False,):
    """
    Create an interactive Plotly figure showing monthly averages
    with a dropdown to inspect daily values for each month.
    """

    df = df_daily.copy()

    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)

    df = df.sort_index()
    df["Month"] = df.index.to_period("M").astype(str)
    monthly = (df.groupby("Month")[column_to_plot].mean().reset_index())
    unit = "%" if percentage else ""
    value_template = f"%{{y:.2f}}{unit}"
    fig = go.Figure()

    # Monthly overview trace
    fig.add_trace(go.Bar(x=monthly["Month"],y=monthly[column_to_plot],name="Monthly average",
                  visible=True,hovertemplate=("Month: %{x}"f"<br>{column_to_plot}: {value_template}""<extra></extra>")))

    months = monthly["Month"].tolist()

    # Daily traces
    for month in months:
        month_df = df[df["Month"] == month]
        fig.add_trace(go.Bar(x=month_df.index.strftime("%Y-%m-%d"),y=month_df[column_to_plot],name=f"Daily values: {month}",
                             visible=False,hovertemplate=("Date: %{x}"f"<br>{column_to_plot}: {value_template}""<extra></extra>"),))

    buttons = []

    # Monthly overview button
    buttons.append(dict(label="Monthly overview",method="update",
                   args=[{"visible": [True] + [False] * len(months)},{"title": f"Monthly Average {title}","xaxis": {"title": "Month"},"yaxis": {"title": yaxis_title}}]))

    # Daily month buttons
    for i, month in enumerate(months):
        visible = [False] * (len(months) + 1)
        visible[i + 1] = True

        buttons.append(dict(label=month,method="update",
                       args=[{"visible": visible},{"title": f"Daily {title} in {month}","xaxis": {"title": "Date"},"yaxis": {"title": yaxis_title}}]))

    fig.update_layout(title=f"Monthly Average {title}",xaxis_title="Month",yaxis_title=yaxis_title,template="plotly_white",
                      updatemenus=[dict(buttons=buttons,direction="down",showactive=True,x=1.02,y=1.0,xanchor="left",yanchor="top")],margin=dict(r=180))

    return fig

def plot_table(df, title, max_rows = None, round_digits = 2,):
    """
    Create a Plotly table figure from a pandas dataframe.

    Args:
        df: Input dataframe to display as a table.
        title: Title of the table figure.
        max_rows: Maximum number of rows to display. Defaults to None,
            which displays all rows.
        round_digits: Number of decimal places used for numeric columns.
            Defaults to 2.

    Returns:
        A Plotly figure containing the dataframe as a formatted table.
    """
    table_df = df.copy()

    if max_rows is not None:
        table_df = table_df.head(max_rows)

    for col in table_df.columns:
        if pd.api.types.is_numeric_dtype(table_df[col]):
            table_df[col] = table_df[col].round(round_digits)

    fig = go.Figure(data=[go.Table(header=dict(values=list(table_df.columns),align="left",font=dict(size=12)),
                                   cells=dict(values=[table_df[col] for col in table_df.columns],align="left",font=dict(size=11),height=28))])

    fig.update_layout(title=title,template="plotly_white",margin=dict(l=20, r=20, t=60, b=20))

    return fig
