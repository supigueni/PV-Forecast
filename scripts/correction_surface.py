"""Build and query a filtered correction-factor surface."""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from pvlib.solarposition import get_solarposition
from scipy.interpolate import RegularGridInterpolator, griddata

LOCATION = {"lat": 49.082778, "lon": 9.556667}
TIME_ZONE = "Europe/Berlin"
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PLOT_DIR = BASE_DIR / "plots"
DEFAULT_INPUT = DATA_DIR / "_combined_complete.csv"
DEFAULT_OUTPUT = DATA_DIR / "correction_surface.csv"
DEFAULT_PLOT = PLOT_DIR / "correction_surface.png"
DEFAULT_RAW_PLOT = PLOT_DIR / "correction_raw_data.png"


def add_solar_angles(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return the correction data with solar azimuth and elevation columns."""
    result = dataframe.copy()
    times = pd.DatetimeIndex(pd.to_datetime(result["datetime"]))
    if times.tz is None:
        times = times.tz_localize(TIME_ZONE)
    else:
        times = times.tz_convert(TIME_ZONE)

    solar_position = get_solarposition(
        times, LOCATION["lat"], LOCATION["lon"]
    )
    result["azimuth"] = solar_position["azimuth"].to_numpy()
    result["elevation"] = solar_position["elevation"].to_numpy()
    return result


def raw_correction_points(
    dataframe: pd.DataFrame,
    minimum_elevation: float = 5.0,
    minimum_open_meteo_power: float = 0.2,
) -> pd.DataFrame:
    """Return valid individual correction-factor samples."""
    data = add_solar_angles(dataframe)
    data["fenecon_power"] = pd.to_numeric(data["fenecon_power"], errors="coerce")
    data["open_meteo_power"] = pd.to_numeric(
        data["open_meteo_power"], errors="coerce"
    )
    data["correction_factor"] = data["fenecon_power"].div(
        data["open_meteo_power"].replace(0, np.nan)
    )
    data["correction_factor"] = data["correction_factor"].clip(0, 1)

    valid = data.dropna(
        subset=["azimuth", "elevation", "correction_factor"]
    ).loc[
        lambda frame: (frame["elevation"] >= minimum_elevation)
        & (frame["open_meteo_power"] >= minimum_open_meteo_power)
    ].copy()
    return valid[["azimuth", "elevation", "correction_factor"]]


def filtered_correction_points(
    dataframe: pd.DataFrame,
    minimum_elevation: float = 5.0,
    minimum_open_meteo_power: float = 0.2,
    angle_bin_size: float = 2.0,
) -> pd.DataFrame:
    """Filter samples and return median correction values per angle bin."""
    valid = raw_correction_points(
        dataframe,
        minimum_elevation=minimum_elevation,
        minimum_open_meteo_power=minimum_open_meteo_power,
    ).copy()

    valid["azimuth_bin"] = (
        np.floor(valid["azimuth"] / angle_bin_size) * angle_bin_size
        + angle_bin_size / 2
    )
    valid["elevation_bin"] = (
        np.floor(valid["elevation"] / angle_bin_size) * angle_bin_size
        + angle_bin_size / 2
    )
    return (
        valid.groupby(["azimuth_bin", "elevation_bin"], as_index=False)[
            "correction_factor"
        ]
        .median()
        .rename(columns={"azimuth_bin": "azimuth", "elevation_bin": "elevation"})
    )


def build_correction_surface(
    points: pd.DataFrame,
    angle_grid_size: float = 1.0,
) -> pd.DataFrame:
    """Interpolate filtered points onto a regular azimuth/elevation grid."""
    azimuth = np.arange(
        points["azimuth"].min(), points["azimuth"].max() + angle_grid_size,
        angle_grid_size,
    )
    elevation = np.arange(
        points["elevation"].min(), points["elevation"].max() + angle_grid_size,
        angle_grid_size,
    )
    azimuth_grid, elevation_grid = np.meshgrid(azimuth, elevation)
    coordinates = points[["azimuth", "elevation"]].to_numpy()
    values = points["correction_factor"].to_numpy()
    surface = griddata(
        coordinates,
        values,
        (azimuth_grid, elevation_grid),
        method="linear",
    )
    nearest = griddata(
        coordinates,
        values,
        (azimuth_grid, elevation_grid),
        method="nearest",
    )
    surface = np.where(np.isnan(surface), nearest, surface)
    return pd.DataFrame(
        {
            "azimuth": azimuth_grid.ravel(),
            "elevation": elevation_grid.ravel(),
            "correction_factor": np.clip(surface.ravel(), 0, 1),
        }
    )


def plot_correction_surface(
    surface: pd.DataFrame,
    output_path: Path = DEFAULT_PLOT,
) -> None:
    """Save a 2D heatmap of correction factor by solar angle."""
    grid = surface.pivot(
        index="elevation", columns="azimuth", values="correction_factor"
    ).sort_index()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 6))
    image = ax.pcolormesh(
        grid.columns,
        grid.index,
        grid.to_numpy(),
        shading="auto",
        cmap="coolwarm",
        vmin=0,
        vmax=1,
    )
    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("Correction factor")
    ax.set_xlabel("Azimuth (degrees)")
    ax.set_ylabel("Elevation (degrees)")
    ax.set_title("Correction Factor Surface")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_raw_correction_data(
    points: pd.DataFrame,
    output_path: Path = DEFAULT_RAW_PLOT,
) -> None:
    """Save a 2D scatter plot of the filtered raw correction datapoints."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 6))
    image = ax.scatter(
        points["azimuth"],
        points["elevation"],
        c=points["correction_factor"],
        cmap="coolwarm",
        vmin=0,
        vmax=1,
        s=12,
        alpha=0.7,
        edgecolors="none",
    )
    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("Correction factor")
    ax.set_xlabel("Azimuth (degrees)")
    ax.set_ylabel("Elevation (degrees)")
    ax.set_title("Raw Correction Data")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def load_correction_surface(path: Path = DEFAULT_OUTPUT) -> RegularGridInterpolator:
    """Load a saved surface and return an interpolator for (azimuth, elevation)."""
    surface = pd.read_csv(path)
    azimuth = np.sort(surface["azimuth"].unique())
    elevation = np.sort(surface["elevation"].unique())
    values = surface.pivot(
        index="elevation", columns="azimuth", values="correction_factor"
    ).reindex(index=elevation, columns=azimuth).to_numpy()
    return RegularGridInterpolator(
        (elevation, azimuth),
        values,
        bounds_error=False,
        fill_value=np.nan,
    )


def create_surface(
    input_path: Path = DEFAULT_INPUT,
    output_path: Path = DEFAULT_OUTPUT,
) -> pd.DataFrame:
    """Build the surface from combined power data and save it as CSV."""
    data = pd.read_csv(input_path)
    points = filtered_correction_points(data)
    surface = build_correction_surface(points)
    surface.to_csv(output_path, index=False)
    return surface


if __name__ == "__main__":
    result = create_surface()
    raw_points = raw_correction_points(pd.read_csv(DEFAULT_INPUT))
    plot_correction_surface(result)
    plot_raw_correction_data(raw_points)
    print(f"Saved {len(result)} surface points to {DEFAULT_OUTPUT}")
    print(f"Saved correction surface plot to {DEFAULT_PLOT}")
    print(f"Saved raw correction data plot to {DEFAULT_RAW_PLOT}")