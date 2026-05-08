import pandas as pd

from io_utils import (
    read_hourly_generation,
    read_hourly_consumption,
    read_daily_generation_df,
    )

from plotting import (
    plot_hourly_stacked_area,
    plot_sunburst_grid,
    plot_error_bars_by_type,
)

from config import (
    HOURLY_CONSUMPTION_FILE,
    HOURLY_GENERATION_FILE,
    DAILY_GENERATION_FILE,
    CSV_SEPARATOR,
    DAILY_CONSUMPTION_COL,
    ALL_DAILY_CATEGORIES,
    MWH_SUFFIX,
)

from analysis import (
    add_daily_totals,
    set_date_index,
    add_daily_consumption_from_hourly,
    build_comparison_messages,
    compute_stats_table,
    rank_stability,
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

    # Load hourly consumption into a dataframe so it can be resampled to daily
    # The original hourly consumption file uses columns: Date, Start, End, Total (grid load)...
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

    # ----------------------------
    # 4) Stats table (separate, professional)
    # ----------------------------
    daily_category_cols =  [f"{c}{MWH_SUFFIX}" for c in ALL_DAILY_CATEGORIES]
    stats_df = compute_stats_table(df_daily, category_columns=daily_category_cols)

    # Print two key fluctuations
    if "Total Production" in stats_df.index and "Total Consumption" in stats_df.index:
        prod_std = stats_df.loc["Total Production", "std"]
        prod_cv = stats_df.loc["Total Production", "cv_percent"]
        cons_std = stats_df.loc["Total Consumption", "std"]
        cons_cv = stats_df.loc["Total Consumption", "cv_percent"]

        print(f"Fluctuation of Total Production: {prod_std:.5f} MWh (%{prod_cv:.2f})")
        print(f"Fluctuation of Total Consumption: {cons_std:.5f} MWh (%{cons_cv:.2f})")

    # ----------------------------
    # 5) Error bar plots
    # ----------------------------
    fig3 = plot_error_bars_by_type(
        df_daily=df_daily,
        categories=ALL_DAILY_CATEGORIES,
        title="Daily Average Energy Generations with Fluctuations",
        ext=MWH_SUFFIX,
    )
    fig3.show()

    fig4 = plot_error_bars_by_type(
        df_daily=df_daily,
        categories=["Total Renewable", "Total Conventional", "Total Production", "Total Consumption"],
        title="Daily Average Energy Stats with Fluctuations",
        ext="",  # these columns are plain names
    )
    fig4.show()

    # ----------------------------
    # 6) Stability ranking
    # ----------------------------
    stability_sorted_cols = rank_stability(df_daily, daily_category_cols)
    # Convert to clean names
    cleaned_methods = [c.replace(MWH_SUFFIX, "") for c in stability_sorted_cols]
    if cleaned_methods:
        if len(cleaned_methods) == 1:
            sentence = f"Stability of energy generation methods: {cleaned_methods[0]}."
        else:
            sentence = (
                "Stability of energy generation methods in ascending order is: "
                + ", ".join(cleaned_methods[:-1])
                + " and "
                + cleaned_methods[-1]
                + "."
            )
        # Print and save comparison analysis
        try :
            with open("analysis.txt","a") as analysis_file:
                analysis_file.write(sentence+"\n")
                print(sentence)
        except:
            with open("analysis.txt","w") as analysis_file:
                analysis_file.write(sentence+"\n")
                print(sentence)

    return 0
if __name__ == "__main__":
    raise SystemExit(main())
