import pandas
import requests
import pandas as pd
import logging

logging.basicConfig(
    filename="forecast.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

url = "https://api.open-meteo.com/v1/forecast"

LOCATION = {"b": 49.082778, "l": 9.556667}  # Mainhardt Kirchstrasse 27
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
    try:
        logging.info("Lade Forecast Suedost...")

        r = requests.get(url, params=params_so, timeout=30)
        r.raise_for_status()
        data_so = r.json()

        df_so = json_to_dataframe(data_so)
        df_so["power"] = irradiance_to_power(df_so["irradiance"], PEAK_POWER_SO)

        date = df_so["datetime"].iloc[0].strftime("%Y%m%d")
        filename = f"data/{date}_open_meteo_so.csv"
        df_so.to_csv(filename, index=False)

        logging.info("Suedost gespeichert: %s (%d Zeilen)", filename, len(df_so))


        logging.info("Lade Forecast Suedwest...")

        r = requests.get(url, params=params_sw, timeout=30)
        r.raise_for_status()
        data_sw = r.json()

        df_sw = json_to_dataframe(data_sw)
        df_sw["power"] = irradiance_to_power(df_sw["irradiance"], PEAK_POWER_SW)

        filename = f"data/{date}_open_meteo_sw.csv"
        df_sw.to_csv(filename, index=False)

        logging.info("Suedwest gespeichert: %s (%d Zeilen)", filename, len(df_sw))


        df_power_complete = df_so.copy()
        df_power_complete["power"] += df_sw["power"]
        df_power_complete.drop(columns=["irradiance"], inplace=True)

        filename = f"data/{date}_open_meteo_complete.csv"
        df_power_complete.to_csv(filename, index=False)

        logging.info("Gesamtforecast gespeichert: %s", filename)

    except Exception:
        logging.exception("Fehler beim Abrufen oder Speichern des Forecasts")


if __name__ == '__main__':
    get_and_save_forcast()
