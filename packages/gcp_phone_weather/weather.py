from dotenv import load_dotenv

load_dotenv()

import os
import requests
from gcp_pal import Firestore


def query_weather_forecast(latitude, longitude, length=1):
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
    return output


if __name__ == "__main__":
    latitude = 51.21341
    longitude = 3.22956
    query_weather_forecast(latitude, longitude)


