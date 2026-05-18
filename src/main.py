import pandas as pd

from io_utils import (
    normalize_data_headers,
    read_hourly_generation,
    read_hourly_consumption,
    read_daily_generation_df,
    )

from plotting import (
    plot_hourly_stacked_area,
    plot_sunburst_grid,
    plot_error_bars_by_type,
    plot_trends,
)

from config import (
    HOURLY_CONSUMPTION_FILE_RAW,
    HOURLY_GENERATION_FILE_RAW,
    DAILY_GENERATION_FILE_RAW,
    HOURLY_CONSUMPTION_FILE_PROC,
    HOURLY_GENERATION_FILE_PROC,
    DAILY_GENERATION_FILE_PROC,
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
    linear_trend,
    describe_trend,
)

from export_utils import(
    export_analysis,
)
def main():
    # ----------------------------
    # 0) Data processing
    # ----------------------------
    HOURLY_CONSUMPTION_FILE_PROC = normalize_data_headers(HOURLY_CONSUMPTION_FILE_RAW)
    HOURLY_GENERATION_FILE_PROC = normalize_data_headers(HOURLY_GENERATION_FILE_RAW)
    DAILY_GENERATION_FILE_PROC = normalize_data_headers(DAILY_GENERATION_FILE_RAW)

    # ----------------------------
    # 1) Hourly stacked area plot
    # ----------------------------
    try:
        timestamps, generation_series = read_hourly_generation(HOURLY_GENERATION_FILE_PROC)
        consumption = read_hourly_consumption(HOURLY_CONSUMPTION_FILE_PROC)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}")
        return 1

    fig1 = plot_hourly_stacked_area(timestamps, generation_series, consumption=consumption, save=True)
    fig1.show()

    # ----------------------------
    # 2) Daily sunburst plots
    # ----------------------------
    try:
        df_daily_raw = read_daily_generation_df(DAILY_GENERATION_FILE_PROC)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return 1

    # Sunburst expects Date column + category columns in the daily df
    fig2 = plot_sunburst_grid(df_daily_raw, save=True)
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
    df_hourly = pd.read_csv(HOURLY_CONSUMPTION_FILE_PROC, sep=CSV_SEPARATOR)
    df_hourly = df_hourly.replace(",", "", regex=True)

    # Add daily consumption by resampling hourly
    df_daily = add_daily_consumption_from_hourly(
        df_daily_indexed=df_daily,
        df_hourly_consumption=df_hourly,
        hourly_date_col="Date",
        hourly_value_col=DAILY_CONSUMPTION_COL,
    )

    # Print and save comparison analysis
    export_analysis(build_comparison_messages(df_daily), mode="w")

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
        production_fluctuation = [f"Fluctuation of Total Production: {prod_std:.5f} MWh (%{prod_cv:.2f})"]
        export_analysis(production_fluctuation)
        consumption_fluctuation = [f"Fluctuation of Total Consumption: {cons_std:.5f} MWh (%{cons_cv:.2f})"]
        export_analysis(consumption_fluctuation)

    # ----------------------------
    # 5) Error bar plots
    # ----------------------------
    fig3 = plot_error_bars_by_type(
        df_daily=df_daily,
        categories=ALL_DAILY_CATEGORIES,
        title="Daily Average Energy Generations with Fluctuations",
        ext=MWH_SUFFIX,
        save=True,
    )
    fig3.show()

    fig4 = plot_error_bars_by_type(
        df_daily=df_daily,
        categories=["Total Renewable", "Total Conventional", "Total Production", "Total Consumption"],
        title="Daily Average Energy Stats with Fluctuations",
        ext="",  # these columns are plain names
        save=True,
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
        export_analysis([sentence])

    # ----------------------------
    # 7) Trend messages + trend plot
    # ----------------------------
    tr_cons = linear_trend(df_daily["Total Consumption"])
    tr_prod = linear_trend(df_daily["Total Production"])
    consumption_trend = describe_trend("Total Consumption", tr_cons.slope)
    production_trend = describe_trend("Total Production", tr_prod.slope)

    # Print and save trend messages
    export_analysis([consumption_trend])
    export_analysis([production_trend])

    # Plot the trends
    fig5 = plot_trends(df_daily,save=True)
    fig5.show()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
