from dotenv import load_dotenv

load_dotenv()

import os
import requests
import pandas as pd
from gcp_pal import Firestore


def query_weather_forecast(latitude, longitude, length=1, parse_output=True):
    """
    Query the weather forecast from the OpenWeatherMap API.

    Args:
    - latitude (float): The latitude of the location.
    - longitude (float): The longitude of the location.
    - length (int): The number of days to forecast.

    Returns:
    - dict: The weather forecast data.
    """
    api_key = os.environ["OPENWEATHERMAP_API_KEY"]
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"lat": latitude, "lon": longitude, "appid": api_key}
    response = requests.get(url, params=params)
    output = response.json()
    if parse_output:
        output = parse_weather_forecast(output)
    return output


def parse_weather_forecast(weather_forecast):
    """
    Parse the weather forecast data.

    Args:
    - weather_forecast (dict): The weather forecast data.

    Returns:
    - dict: The parsed weather forecast data.
    """
    parsed_forecast = {}
    for forecast in weather_forecast["list"]:
        date = forecast["dt_txt"]
        weather = forecast["weather"][0]["description"]
        temp = forecast["main"]["temp"] - 273.15
        temp_feels_like = forecast["main"]["feels_like"] - 273.15
        pressure = forecast["main"]["pressure"]
        humidity = forecast["main"]["humidity"]
        wind_speed = forecast["wind"]["speed"]
        wind_direction = forecast["wind"]["deg"]
        rain = forecast.get("rain", {}).get("3h", 0)

        parsed_forecast[date] = {
            "weather": weather,
            "temp": temp,
            "temp_feels_like": temp_feels_like,
            "pressure": pressure,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "rain": rain,
        }

    parsed_forecast = pd.DataFrame(parsed_forecast).T
    parsed_forecast = parsed_forecast.reset_index()
    parsed_forecast = parsed_forecast.rename(columns={"index": "timestamp"})
    parsed_forecast = parsed_forecast.reset_index(drop=True)
    parsed_forecast["timestamp"] = pd.to_datetime(parsed_forecast["timestamp"])

    return parsed_forecast


def obtain_recent_coordinates(device_id=None):
    """
    Obtain the most recent coordinates of the device from Firestore.

    Args:
    - device_id (str): The device ID.

    Returns:
    - tuple: The latitude and longitude of the device.
    """
    if device_id is None:
        device_id = os.environ["FOLLOWMEE_DEVICE_ID"]

    firestore_time_path = (
        f"device_locations/last_updated_times/{device_id}/last_updated_time"
    )
    last_updated_time = Firestore(firestore_time_path).read()
    firestore_location_path = (
        f"device_locations/devices/{device_id}/{last_updated_time}"
    )
    last_location = Firestore(firestore_location_path).read()
    latitude = last_location["Latitude"]
    longitude = last_location["Longitude"]
    return latitude, longitude


if __name__ == "__main__":
    latitude, longitude = obtain_recent_coordinates()
    weather = query_weather_forecast(latitude, longitude)
    breakpoint()
