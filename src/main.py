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
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
