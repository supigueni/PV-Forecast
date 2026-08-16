# plotting the power vs sun angles (azimuth and elevation)

from pathlib import Path

import matplotlib

matplotlib.use("TkAgg", force=True)

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime as dt
from pvlib.solarposition import get_solarposition

LOCATION = {"lat": 49.082778, "lon": 9.556667}  # Mainhardt Kirchstrasse 27

TIME_ZONE = "Europe/Berlin"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PLOT_DIR = BASE_DIR / "plots"
PLOT_DIR.mkdir(exist_ok=True)

combined_csv_path = DATA_DIR / "_combined_complete.csv"

if combined_csv_path.exists():
    df = pd.read_csv(combined_csv_path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    # ensure datetimes are timezone-aware (pvlib expects tz-aware times)
    times = pd.DatetimeIndex(df["datetime"])
    if times.tz is None:
        try:
            times = times.tz_localize(TIME_ZONE)
        except Exception:
            # fallback: assume UTC
            times = times.tz_localize("UTC")
    else:
        times = times.tz_convert(TIME_ZONE)

    # calculate azimuth and elevation angles from datetime
    solar_position = get_solarposition(times, LOCATION["lat"], LOCATION["lon"]) 
    # assign by position to avoid index misalignment between df and solar_position
    df["azimuth"] = solar_position["azimuth"].values
    df["elevation"] = solar_position["elevation"].values
    # ensure numeric types for plotting (convert any NA-like values to NaN)
    df["azimuth"] = pd.to_numeric(df["azimuth"], errors="coerce")
    df["elevation"] = pd.to_numeric(df["elevation"], errors="coerce")

    # ensure power columns are numeric and drop rows with missing positions or power
    df["fenecon_power"] = pd.to_numeric(df["fenecon_power"], errors="coerce")
    df["open_meteo_power"] = pd.to_numeric(df["open_meteo_power"], errors="coerce")
    plot_df = df.dropna(subset=["azimuth", "elevation", "fenecon_power"]).copy()

    # plot power (z) vs azimuth (x) and elevation (y) angles
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(plot_df["azimuth"].to_numpy(dtype=float), plot_df["elevation"].to_numpy(dtype=float), plot_df["fenecon_power"].to_numpy(dtype=float), c=plot_df["fenecon_power"].to_numpy(dtype=float), cmap="viridis")
    ax.set_xlabel("Azimuth (degrees)")
    ax.set_ylabel("Elevation (degrees)")
    ax.set_zlabel("Power (kW)")

    plt.title("Power vs Sun Angles")
    plt.savefig(PLOT_DIR / "fenecon_power_vs_sun_angles.png")
    print(f"Saved plot to {PLOT_DIR / 'fenecon_power_vs_sun_angles.png'}")

    # same for open_meteo_power (drop rows with missing power/positions)
    plot_df2 = df.dropna(subset=["azimuth", "elevation", "open_meteo_power"]).copy()
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(plot_df2["azimuth"].to_numpy(dtype=float), plot_df2["elevation"].to_numpy(dtype=float), plot_df2["open_meteo_power"].to_numpy(dtype=float), c=plot_df2["open_meteo_power"].to_numpy(dtype=float), cmap="plasma")
    ax.set_xlabel("Azimuth (degrees)")
    ax.set_ylabel("Elevation (degrees)")
    ax.set_zlabel("Power (kW)")
    plt.title("Open Meteo Power vs Sun Angles")
    plt.savefig(PLOT_DIR / "open_meteo_power_vs_sun_angles.png")
    print(f"Saved plot to {PLOT_DIR / 'open_meteo_power_vs_sun_angles.png'}")

    # calculate relative error between fenecon_power and open_meteo_power
    # - avoid division by zero
    # - relative error: e = (fenecon - open_meteo) / fenecon
    # corrected_forecast = open_meteo * correction_factor
    # - forecast correction correction_factor = fenecon / open_meteo (limit between 0 and 1)

    df["relative_error"] = (df["fenecon_power"] - df["open_meteo_power"]) / df["fenecon_power"].replace(0, pd.NA)
    df["relative_error"] = pd.to_numeric(df["relative_error"], errors="coerce")
    df["correction_factor"] = pd.to_numeric(df["fenecon_power"] / df["open_meteo_power"].replace(0, pd.NA), errors="coerce")
    df["correction_factor"] = df["correction_factor"].clip(0, 1)  # Limit correction factor between 0 and 1
    # plot relative error vs azimuth and elevation angles (drop NA)
    plot_df3 = df.dropna(subset=["azimuth", "elevation", "relative_error"]).copy()
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(plot_df3["azimuth"].to_numpy(dtype=float), plot_df3["elevation"].to_numpy(dtype=float), plot_df3["correction_factor"].to_numpy(dtype=float), c=plot_df3["correction_factor"].to_numpy(dtype=float), cmap="coolwarm")
    # show also the color bar for correction factor
    cbar = plt.colorbar(ax.collections[0], ax=ax, shrink=0.5, aspect=10)
    cbar.set_label("Correction Factor")
    ax.set_xlabel("Azimuth (degrees)")
    ax.set_ylabel("Elevation (degrees)")
    ax.set_zlabel("Correction Factor")
    plt.title("Correction Factor vs Sun Angles")
    plt.savefig(PLOT_DIR / "correction_factor_vs_sun_angles.png")
    print(f"Saved plot to {PLOT_DIR / 'correction_factor_vs_sun_angles.png'}")

    print(df.head(80))
    plt.show()
else:
    print(f"Combined CSV file not found at {combined_csv_path}. Please run the data combination script first.")