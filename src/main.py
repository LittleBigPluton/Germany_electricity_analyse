import pandas as pd

from io_utils import (
    read_hourly_generation,
    read_hourly_consumption,
    read_daily_generation_df,
    )

from plotting import (
    plot_hourly_stacked_area,
    plot_sunburst_grid,
)

from config import (
    HOURLY_CONSUMPTION_FILE,
    HOURLY_GENERATION_FILE,
    DAILY_GENERATION_FILE,
    CSV_SEPARATOR,
    DAILY_CONSUMPTION_COL,
)

from analysis import (
    add_daily_totals,
    set_date_index,
    add_daily_consumption_from_hourly,
    build_comparison_messages,
)

def main():
    # ----------------------------
    # 1) Hourly stacked area plot
    # ----------------------------
    try:
        timestamps, generation_series = read_hourly_generation(HOURLY_GENERATION_FILE)
        consumption = read_hourly_consumption(HOURLY_CONSUMPTION_FILE)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}")
        return 1

    fig1 = plot_hourly_stacked_area(timestamps, generation_series, consumption=consumption)
    fig1.show()

    # ----------------------------
    # 2) Daily sunburst plots
    # ----------------------------
    try:
        df_daily_raw = read_daily_generation_df(DAILY_GENERATION_FILE)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return 1

    # Sunburst expects Date column + category columns in the daily df
    fig2 = plot_sunburst_grid(df_daily_raw)
    fig2.show()

    # ----------------------------
    # 3) Daily analysis: totals + consumption + comparisons
    # ----------------------------
    # Add totals (renewable / conventional / production)
    df_daily = add_daily_totals(df_daily_raw)
    df_daily = set_date_index(df_daily, date_col="Date")

    # Load hourly consumption into a dataframe so we can resample to daily
    # Your original hourly consumption file uses columns: Date, Start, End, Total (grid load)...
    # We'll read it via pandas here (simple + robust).
    df_hourly = pd.read_csv(HOURLY_CONSUMPTION_FILE, sep=CSV_SEPARATOR)
    df_hourly = df_hourly.replace(",", "", regex=True)

    # Add daily consumption by resampling hourly
    df_daily = add_daily_consumption_from_hourly(
        df_daily_indexed=df_daily,
        df_hourly_consumption=df_hourly,
        hourly_date_col="Date",
        hourly_value_col=DAILY_CONSUMPTION_COL,
    )

    # Print and save comparison analysis
    try :
        with open("analysis.txt","x") as analysis_file:
            for msg in build_comparison_messages(df_daily):
                print(msg)
                analysis_file.write(msg+"\n")
    except:
        with open("analysis.txt","w") as analysis_file:
            for msg in build_comparison_messages(df_daily):
                print(msg)
                analysis_file.write(msg+"\n")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
