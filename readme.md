# PV Forecast

This Python script retrieves hourly solar irradiance forecasts from the Open-Meteo API for two PV array orientations (south-east and south-west), converts the irradiance into estimated PV power based on the installed peak capacity, and stores the results as CSV files.

## Features

- Downloads hourly `global_tilted_irradiance` forecasts from Open-Meteo
- Supports multiple PV array orientations
- Estimates PV power output (kW) from irradiance
- Generates separate CSV files for each roof orientation and the combined system
- Logs all operations and errors to a log file
- Designed to run automatically via Windows Task Scheduler