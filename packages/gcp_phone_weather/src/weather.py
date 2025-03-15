from dotenv import load_dotenv

load_dotenv()

import os
import requests
import pandas as pd
from datetime import datetime


def query_weather_forecast(latitude, longitude, parse_output=True):
    """
    Query the weather forecast from the OpenWeatherMap API.

    Args:
    - latitude (float): The latitude of the location.
    - longitude (float): The longitude of the location.

    Returns:
    - dict: The weather forecast data.
    """
    metadata = None
    api_key = os.environ["OPENWEATHERMAP_API_KEY"]
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"lat": latitude, "lon": longitude, "appid": api_key}
    response = requests.get(url, params=params)
    output = response.json()
    if parse_output:
        output, metadata = parse_weather_forecast(output)
    return output, metadata


def parse_city_metadata(city):
    """
    Parse the city metadata.

    Args:
    - city (dict): The city metadata.

    Returns:
    - dict: The parsed city metadata.
    """
    timezone = city["timezone"] / 3600
    sunrise = city["sunrise"]
    sunset = city["sunset"]
    sunrise = datetime.fromtimestamp(sunrise).isoformat()
    sunset = datetime.fromtimestamp(sunset).isoformat()
    metadata = {
        "name": city["name"],
        "country": city["country"],
        "timezone": timezone,
        "sunrise": sunrise,
        "sunset": sunset,
    }
    return metadata


def parse_weather_forecast(weather_forecast):
    """
    Parse the weather forecast data.

    Args:
    - weather_forecast (dict): The weather forecast data.

    Returns:
    - dict: The parsed weather forecast data. Schema:
        - timestamp (datetime): The timestamp of the forecast (YYYY-MM-DD HH:MM:SS).
        - weather (str): The weather description (e.g. "light rain").
        - temp (float): The temperature in Celsius (°C).
        - temp_feels_like (float): The temperature feels like in Celsius (°C).
        - pressure (int): The atmospheric pressure in hPa (hectopascals).
        - humidity (int): The humidity in % (percentage).
        - wind_speed (float): The wind speed in km/h (kilometers per hour).
        - wind_gust (float): The wind gust in km/h (kilometers per hour).
        - wind_direction (float): The wind direction in degrees (°).
        - rain (float): The rain volume in mm (millimetres).
        - cloudiness (int): The cloudiness in % (percentage).
    """
    parsed_forecast = {}
    for forecast in weather_forecast["list"]:
        date = forecast["dt_txt"]
        weather = forecast["weather"][0]["description"]
        cloudiness = forecast["clouds"]["all"]
        prob_precip = forecast.get("pop", 0)
        temp = forecast["main"]["temp"] - 273.15
        temp_feels_like = forecast["main"]["feels_like"] - 273.15
        pressure = forecast["main"]["pressure"]
        humidity = forecast["main"]["humidity"]
        wind_speed = forecast["wind"]["speed"] * 3.6
        wind_gust = forecast["wind"].get("gust", 0) * 3.6
        wind_direction = forecast["wind"]["deg"]
        rain = forecast.get("rain", {}).get("3h", 0)
        snow = forecast.get("snow", {}).get("3h", 0)

        parsed_forecast[date] = {
            "weather": weather,
            "temp": temp,
            "temp_feels_like": temp_feels_like,
            "pressure": pressure,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "wind_gust": wind_gust,
            "wind_direction": wind_direction,
            "rain": rain,
            "snow": snow,
            "prob_precip": prob_precip,  # "pop" is the probability of precipitation, not the actual rain volume
            "cloudiness": cloudiness,
        }

    parsed_forecast = pd.DataFrame(parsed_forecast).T
    parsed_forecast = parsed_forecast.reset_index()
    parsed_forecast = parsed_forecast.rename(columns={"index": "timestamp"})
    parsed_forecast = parsed_forecast.reset_index(drop=True)
    parsed_forecast["timestamp"] = pd.to_datetime(parsed_forecast["timestamp"])
    # Get the granularity of the forecast
    current_time = pd.Timestamp.now()
    filter_time_min = current_time - pd.Timedelta(hours=1)
    filter_time_max = current_time + pd.Timedelta(hours=16)
    query_str = "timestamp >= @filter_time_min and timestamp <= @filter_time_max"
    parsed_forecast = parsed_forecast.query(query_str)

    metadata = parse_city_metadata(weather_forecast["city"])

    return parsed_forecast, metadata


def print_weather(weather_df):
    """
    Print the weather forecast for the LLM prompt.

    Args:
    - weather_df (pd.DataFrame): The weather forecast data.
    """
    print_strings = []
    weather_df["timestamp"] = pd.to_datetime(weather_df["timestamp"])
    for _, row in weather_df.iterrows():
        timestamp = row["timestamp"].strftime("%H:%M")
        weather = row["weather"]
        temp = round(row["temp"])
        temp_feels_like = round(row["temp_feels_like"])
        pressure = row["pressure"]
        humidity = row["humidity"]
        wind_speed = round(row["wind_speed"])
        wind_gust = round(row["wind_gust"])
        wind_direction = row["wind_direction"]
        rain = row["rain"]
        cloudiness = row["cloudiness"]
        print_string = (
            f"{timestamp}: {weather} | {temp}°C (feels like {temp_feels_like}°C) | "
            f"Pressure: {pressure} hPa | Humidity: {humidity}% | "
            f"Wind: {wind_speed} km/h (gust {wind_gust} km/h) {wind_direction}° | "
            f"Cloudiness: {cloudiness}% | Prob. precip: {row['prob_precip']}% | "
            f"Rain: {rain} mm | Snow: {row['snow']} mm"
        )
        print_strings.append(print_string)
    print_string = "\n".join(print_strings)
    return print_string


def get_message_for_weather(weather_df, metadata):
    """
    Get the message for the weather forecast.

    Args:
    - weather_df (pd.DataFrame): The weather forecast data.

    Returns:
    - str: The message for the weather forecast.
    """
    city = metadata["name"]
    country = metadata["country"]
    sunrise = metadata["sunrise"]
    sunset = metadata["sunset"]
    message = f"Here is the weather forecast for {city}, {country}:\n"
    message += print_weather(weather_df)
    message += f"\nSunrise: {sunrise}"
    message = f"\nSunset: {sunset}"
    return message
