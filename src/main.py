from io_utils import (
    read_hourly_generation,
    read_hourly_consumption,
    )

from plotting import plot_hourly_stacked_area

from config import (
    HOURLY_CONSUMPTION_FILE,
    HOURLY_GENERATION_FILE,
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

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
