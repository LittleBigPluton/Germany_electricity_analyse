# Germany Electricity Analysis 2025

A Python-based data analysis project for exploring Germany's electricity generation and consumption patterns using SMARD electricity data. The project focuses on hourly and daily electricity generation, total consumption, renewable share, residual load, source-level variability, monthly summaries and exported interactive Plotly visualizations. Interactive figures are available through GitHub Pages, while the notebook and Medium article provide a more detailed walkthrough of the analysis.

---

## Links

- **Interactive figure gallery:** https://www.umutgokdemir.com/Germany_electricity_analyse/
- **Notebook:** https://nbviewer.org/github/LittleBigPluton/Germany_electricity_analyse/blob/main/notebooks/electricity_analysis_notebook.ipynb
- **Medium article:** https://medium.com/@ckmzyol/germanys-electricity-in-2025-what-a-full-year-of-data-shows-6f5e6708681d

---

## Project Overview

This repository analyzes Germany's electricity generation and consumption data for 2025. The analysis compares renewable and conventional electricity generation, investigates how well production follows demand and studies residual load, which is the part of electricity demand that remains after renewable generation is taken into account.

The project is structured as a small Python package with a command-line entry point. The full workflow can be run from the terminal using the package script defined in `pyproject.toml`.

Main analysis goals:

- Compare hourly electricity generation by source with total consumption
- Analyze daily renewable and conventional electricity generation
- Calculate renewable share and residual load
- Identify days when generation exceeded demand
- Identify days when renewable generation alone exceeded total consumption
- Summarize monthly electricity production, consumption, net balance and residual load
- Export interactive Plotly figures, PNG previews, CSV summaries and text reports

---

## Repository Structure

```text
Germany_electricity_analyse/
├── data/
│   └── yearly/
│       └── energy/
│           └── 2025/
│               ├── raw/
│               └── processed/
├── docs/
│   ├── Analysis/
│   │   ├── analysis.txt
│   │   ├── key_findings_2025.txt
│   │   ├── Monthly_based_summary_stats.csv
│   │   ├── Top_Consumption_Days.csv
│   │   ├── Top_Production_Days.csv
│   │   ├── Top_Renewable_days.csv
│   │   └── Top_Residual_Load_Days.csv
│   ├── Figures_html/
│   ├── Figures_png/
│   ├── index.html
│   └── .nojekyll
├── notebooks/
│   └── electricity_analysis_notebook.ipynb
├── src/
│   └── electricity_analyse/
│       ├── __init__.py
│       ├── analysis.py
│       ├── cli.py
│       ├── config.py
│       ├── export_utils.py
│       ├── io_utils.py
│       ├── plotting.py
│       └── stats_utils.py
├── pyproject.toml
└── README.md
````

---

## Installation

This project uses `pyproject.toml` for package metadata, dependencies and command-line configuration.

Clone the repository:

```bash
git clone https://github.com/LittleBigPluton/Germany_electricity_analyse.git
cd Germany_electricity_analyse
```

Create and activate a virtual environment:

```bash
python3 -m venv venv_Germany_Electricity_Analyse/
source venv/bin/activate
```

Install the project in editable mode:

```bash
pip install -e .
```

For development tools such as testing, linting and notebook support, install with:

```bash
pip install -e ".[dev]"
```

---

## Using `pyproject.toml`

The `pyproject.toml` file defines the project as an installable Python package.

Important parts:

```toml
[project]
name = "electricity-analyse"
version = "1.0.0"
requires-python = ">=3.10"
```

The package name is:

```text
electricity-analyse
```

The importable Python package is:

```python
electricity_analyse
```

The command-line script is defined here:

```toml
[project.scripts]
electricity-analyse = "electricity_analyse.cli:main"
```

After installation, the full analysis workflow can be run from the terminal with:

```bash
electricity-analyse
```

---

## Configuration with `config.py`

The file `src/electricity_analyse/config.py` stores the main project configuration.

It defines:

* Project root directory
* Raw input file paths
* Processed output paths
* Analysis output directory
* Figure export directory
* CSV separator
* Expected datetime formats
* Hourly generation column positions
* Energy source categories
* Renewable and conventional source groups
* Plot styling options

Example configuration sections include:

```python
HOURLY_GENERATION_FILE_RAW
HOURLY_CONSUMPTION_FILE_RAW
DAILY_GENERATION_FILE_RAW
```

These point to the raw SMARD CSV files under:

```text
data/yearly/energy/2025/raw/
```

The processed files are generated automatically into:

```text
data/yearly/energy/2025/processed/
```

The analysis outputs are exported to:

```text
docs/Analysis/
```

The interactive figures are exported to:

```text
docs/Figures_html/
```

PNG previews for the GitHub Pages gallery are stored in:

```text
docs/Figures_png/
```

To analyze a different year or a different SMARD export, update the input file paths in `config.py`.

---

## Running the CLI Workflow

The file `src/electricity_analyse/cli.py` is the main workflow entry point.

It performs the following steps:

1. Normalize raw SMARD CSV headers
2. Load hourly generation and consumption data
3. Create the hourly stacked generation and consumption figure
4. Load daily generation data
5. Calculate renewable, conventional and total production
6. Resample hourly consumption into daily consumption
7. Calculate renewable share
8. Calculate residual load
9. Export comparison messages to `analysis.txt`
10. Create the monthly summary table
11. Export top-day CSV files
12. Compute fluctuation and stability statistics
13. Generate key findings
14. Export interactive Plotly HTML figures

Run the full workflow with:

```bash
electricity-analyse
```

The workflow regenerates the processed data, analysis reports, CSV summaries and exported figures.

---

## Generated Outputs

The project generates three main types of outputs.

### 1. Analysis Reports

Located in:

```text
docs/Analysis/
```

Important files:

```text
analysis.txt
key_findings_2025.txt
Monthly_based_summary_stats.csv
Top_Consumption_Days.csv
Top_Production_Days.csv
Top_Renewable_days.csv
Top_Residual_Load_Days.csv
```

### 2. Interactive HTML Figures

Located in:

```text
docs/Figures_html/
```

Main figures:

```text
Hourly_Stacked_Plot.html
Daily_Generation_Sunburst_Dropdown.html
Renewable_Share_Drilldown.html
Residual_Load_Drilldown.html
Monthly_Energy_Summary_Table.html
Daily_Average_Energy_Generations_with_Fluctuations.html
Daily_Average_Energy_Stats_with_Fluctuations.html
Total_Consumption_and_Production_with_Trend_Lines.html
```

### 3. PNG Figure Previews

Located in:

```text
docs/Figures_png/
```

These are used by the GitHub Pages landing page.

---

## Short Analysis Summary

The analysis shows that Germany's electricity system in 2025 had strong renewable contributions, but also clear variability across days and months.

Key results from the generated reports:

* Total electricity generation exceeded total consumption on **82 out of 365 days**.
* Renewable generation was higher than conventional generation on **274 out of 365 days**.
* Renewable electricity generation alone exceeded total electricity consumption on **2 days**: **2025-10-05** and **2025-10-26**.
* The highest daily renewable share occurred on **2025-10-26**, reaching **86.76%**.
* The lowest daily renewable share occurred on **2025-11-08**, reaching **22.80%**.
* The highest monthly renewable share occurred in **June 2025**, with **73.30%**.
* The month with the highest total consumption was **January 2025**.
* The month with the highest residual load was **February 2025**.

These results show both the progress and the challenge of the energy transition: renewable generation can dominate the electricity mix on many days and on some days it can even meet total demand, but residual load remains important during periods of lower renewable output.

For a more detailed interpretation, see the notebook and Medium article:

* Notebook: [https://nbviewer.org/github/LittleBigPluton/Germany_electricity_analyse/blob/main/notebooks/electricity_analysis_notebook.ipynb](https://nbviewer.org/github/LittleBigPluton/Germany_electricity_analyse/blob/main/notebooks/electricity_analysis_notebook.ipynb)
* Medium article: [https://medium.com/@ckmzyol/germanys-electricity-in-2025-what-a-full-year-of-data-shows-6f5e6708681d](https://medium.com/@ckmzyol/germanys-electricity-in-2025-what-a-full-year-of-data-shows-6f5e6708681d)

---

## Main Figures

The interactive figures can be explored through the GitHub Pages gallery:

[https://www.umutgokdemir.com/Germany_electricity_analyse/](https://www.umutgokdemir.com/Germany_electricity_analyse/)

The main visualizations include:

* Hourly electricity generation mix and total consumption
* Daily generation mix sunburst chart
* Renewable share drilldown
* Residual load drilldown
* Monthly energy summary table
* Daily average generation by source with fluctuations
* Daily average energy statistics with fluctuations
* Total consumption and production with trend lines

---

## Data Source

The raw electricity data used in this project comes from SMARD, the electricity market data platform of the German Federal Network Agency. It can be accessed via [SMARD website](https://www.smard.de/home/downloadcenter/download-marktdaten/)

The analysis uses exported CSV files for:

* Hourly electricity generation by source
* Hourly electricity consumption
* Daily electricity generation by source

The raw files are stored in:

```text
data/yearly/energy/2025/raw/
```

Processed files are generated in:

```text
data/yearly/energy/2025/processed/
```

---

## Technical Details

Main technologies used:

* Python
* pandas
* NumPy
* Plotly
* Matplotlib
* statsmodels
* Jupyter Notebook
* pyproject.toml package structure
* GitHub Pages

Main package modules:

```text
analysis.py      # Derived metrics, statistics, rankings, key findings
cli.py           # Main command-line workflow
config.py        # File paths, categories, constants, date formats
export_utils.py  # Export helpers for figures, CSV files and text reports
io_utils.py      # CSV loading, cleaning and preprocessing
plotting.py      # Plotly and Matplotlib visualization functions
stats_utils.py   # Additional statistical helper functions
```

---

## Notes on Interpretation

This project analyzes electricity generation and consumption from the available SMARD data exports. It does not model electricity prices, grid constraints, imports, exports, storage behavior or forecasting uncertainty.

The result that renewable generation exceeded total consumption on two days should be interpreted at the aggregated daily level. It does not imply that every hour of those days was fully renewable nor does it remove the need for balancing, storage, grid management, imports or dispatchable capacity.

---

## License

This project is released under the MIT License.

---

## Author

**Ahmet Umut Gökdemir**

GitHub: [https://github.com/LittleBigPluton](https://github.com/LittleBigPluton)
Medium: [https://medium.com/@ckmzyol](https://medium.com/@ckmzyol)
