import plotly.express as px
import pandas as pd
import os

from pathlib import Path

from .config import(
    analysis_file_dir,
    figure_export_dir,
)

def export_analysis(analysis, export_file_name, echo = True, mode = 'a'):
    """
    Export analysis to a text file and optionally echo them to stdout.

    Args:
        analysis: Iterable of lines to write (newline will be added automatically).
        echo: If True, print each line after writing.
    """
    analysis_file_dir.mkdir(parents=True, exist_ok=True)
    analysis_file_path = analysis_file_dir/export_file_name
    with analysis_file_path.open(mode, encoding="utf-8") as analysis_file:
        for analyse in analysis:
            analysis_file.write(f"{analyse}\n")
            if echo:
                print(analyse)

def export_figure(figure, figure_name, fmt):
    """
    Export a Plotly figure and continue execution on failure.

    The figure is saved under a format-specific directory:
        <figure_export_dir>/Figures_<fmt>/

    If exporting fails (e.g., Kaleido/browser issues for image formats), the function
    prints a warning and returns False instead of raising, so the main program can
    continue running.

    Args:
        figure: Plotly figure object (e.g., `plotly.graph_objs.Figure`).
        figure_name: Base filename (without extension). Must be a non-empty string.
        fmt: Output format/extension (case-insensitive; leading '.' allowed), such as
            "html", "png", "svg", or "pdf".

    Returns:
        True if the export succeeded, otherwise False.

    Raises:
        ValueError: If `figure_name` is empty/blank.
        ValueError: If `fmt` is empty/blank after normalization.

    Notes:
        - Image exports (`png`, `svg`, `pdf`, ...) typically require `kaleido`.
        - Plotly determines the output format primarily from the file extension.
    """

    if not figure_name or not figure_name.strip():
        raise ValueError("figure_name must be a non-empty string")

    fmt = fmt.strip().lower().lstrip(".")
    if not fmt:
        raise ValueError("fmt must be a non-empty string (e.g., 'html', 'png')")

    figure_export_file_dir = Path(f"{figure_export_dir}/Figures_{fmt}")
    figure_export_file_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(figure_export_file_dir /f"{figure_name}.{fmt}")
    try:
        if fmt != "html":
            figure.write_image(output_path)
        else:
            figure.write_html(output_path)
        return True
    except Exception as e:
        print(f"[WARN] Export failed for {figure_name}.{fmt}: {e}")
        return False

def export_csv(data,export_file_name):
    """
    Export given DataFrame as a csv file into analysis directory
    """
    data.to_csv(analysis_file_dir/export_file_name,index=False)
    print(f"Data exported as {analysis_file_dir/export_file_name}")
