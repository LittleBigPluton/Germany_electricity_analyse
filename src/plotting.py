import math
import plotly.graph_objs as go

from config import (
    CONSUMPTION_TRACE,
    HOURLY_SERIES,
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

    # Only include these Plotly params if they are meaningful (cleaner than passing None)
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
