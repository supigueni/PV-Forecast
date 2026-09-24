# PV Forecast

This Python script retrieves hourly solar irradiance forecasts from the Open-Meteo API for two PV array orientations (south-east and south-west), converts the irradiance into estimated PV power based on the installed peak capacity, and stores the results as CSV files.

## Features

- Downloads hourly `global_tilted_irradiance` forecasts from Open-Meteo
- Supports multiple PV array orientations
- Estimates PV power output (kW) from irradiance
- Generates separate CSV files for each roof orientation and the combined system
- Logs all operations and errors to a log file
- Designed to run automatically via Windows Task Scheduler

## Correction surface

Build a filtered elevation/azimuth correction surface from the combined measured
and forecast power data:

```text
python scripts/correction_surface.py
```

This writes `data/correction_surface.csv`. The surface excludes low-signal
samples, aggregates each 2-degree angle bin by its median correction factor,
and interpolates the result onto a regular 1-degree grid. For a later forecast
correction, load it with `load_correction_surface()` from
`scripts.correction_surface`; the returned interpolator accepts points as
`[elevation, azimuth]` and returns `NaN` outside the measured angle range.