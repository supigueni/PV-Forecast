import pandas
import requests
import pandas as pd

url = "https://api.open-meteo.com/v1/forecast"

LOCATION = {"b": 49.08, "l": 9.59}  # Mainhardt
PEAK_POWER_SO = 5.0  # kW
PEAK_POWER_SW = 6.0  # kW

params_so = {
    "latitude": LOCATION["b"],
    "longitude": LOCATION["l"],
    "tilt": 45,
    "azimuth": -45,
    "hourly": "global_tilted_irradiance",
    "forecast_days": 2,
    "timezone": "Europe/Berlin"
}

params_sw = {
    "latitude": LOCATION["b"],
    "longitude": LOCATION["l"],
    "tilt": 45,
    "azimuth": 45,
    "hourly": "global_tilted_irradiance",
    "forecast_days": 2,
    "timezone": "Europe/Berlin"
}


def irradiance_to_power(gti, peak_power):
    # power in kW
    return peak_power * gti / 1000 * 0.9


def json_to_dataframe(json) -> pandas.DataFrame:
    df = pd.DataFrame({
        "datetime": pd.to_datetime(json["hourly"]["time"]),
        "irradiance": json["hourly"]["global_tilted_irradiance"]
    })
    return df


def print_data(data):
    for t, p in zip(data["hourly"]["time"],
                    data["hourly"]["global_tilted_irradiance"]):
        print(t, p)


def get_and_save_forcast():
    r = requests.get(url, params=params_so)
    data_so = r.json()

    print("\n\n******************\ndata so:")
    df_so = json_to_dataframe(data_so)
    df_so["power"] = irradiance_to_power(df_so["irradiance"], PEAK_POWER_SO)
    print(df_so)
    date = df_so["datetime"].iloc[0].strftime("%Y%m%d")
    df_so.to_csv(f"data/{date}_open_meteo_so.csv")

    r = requests.get(url, params=params_sw)
    data_sw = r.json()
    print("\n\n******************\ndata sw:")
    df_sw = json_to_dataframe(data_sw)
    df_sw["power"] = irradiance_to_power(df_sw["irradiance"], PEAK_POWER_SW)
    print(df_sw)
    date = df_sw["datetime"].iloc[0].strftime("%Y%m%d")
    df_sw.to_csv(f"data/{date}_open_meteo_sw.csv")

    df_power_complete = df_so
    df_power_complete["power"] += df_sw["power"]
    df_power_complete.drop(["irradiance"], axis=1)
    date = df_power_complete["datetime"].iloc[0].strftime("%Y%m%d")
    df_power_complete.to_csv(f"data/{date}_open_meteo_complete.csv")


if __name__ == '__main__':
    get_and_save_forcast()
