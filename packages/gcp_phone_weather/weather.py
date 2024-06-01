from dotenv import load_dotenv

load_dotenv()

import os
import requests
import pandas as pd
from datetime import datetime
from gcp_pal import Firestore


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
    # current_time = pd.Timestamp.now()
    current_time = pd.Timestamp("2024-06-01 06:00:02")
    filter_time_min = current_time - pd.Timedelta(hours=1)
    filter_time_max = current_time + pd.Timedelta(hours=19)
    query_str = "timestamp >= @filter_time_min and timestamp <= @filter_time_max"
    parsed_forecast = parsed_forecast.query(query_str)

    metadata = parse_city_metadata(weather_forecast["city"])

    return parsed_forecast, metadata


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


def print_weather(weather_df):
    """
    Print the weather forecast for the LLM prompt.

    Args:
    - weather_df (pd.DataFrame): The weather forecast data.
    """
    print_strings = []
    weather_df["timestamp"] = pd.to_datetime(weather_df["timestamp"]) - pd.Timedelta(
        hours=9
    )
    for _, row in weather_df.iterrows():
        timestamp = row["timestamp"].strftime("%H:%M")
        weather = row["weather"]
        temp = round(row["temp"], 1)
        temp_feels_like = round(row["temp_feels_like"], 1)
        pressure = row["pressure"]
        humidity = row["humidity"]
        wind_speed = round(row["wind_speed"], 0)
        wind_gust = round(row["wind_gust"], 0)
        wind_direction = row["wind_direction"]
        rain = row["rain"]
        cloudiness = row["cloudiness"]
        print_string = (
            f"{timestamp}: {weather} | {temp}°C (feels like {temp_feels_like}°C) | "
            f"Pressure: {pressure} hPa | Humidity: {humidity}% | "
            f"Wind: {wind_speed} km/h (gust {wind_gust} km/h) {wind_direction}° | "
            f"Cloudiness: {cloudiness}% | % Precip: {row['prob_precip']}% | "
            f" | Rain: {rain} mm | Snow: {row['snow']} mm"
        )
        print_strings.append(print_string)
    print_string = "\n".join(print_strings)
    return print_string


def get_llm_prompt(weather_df=None):
    """
    Query the OpenAI GPT-3 API.

    Args:
    - prompt (str): The prompt to query.

    Returns:
    - str: The response from the GPT-3 API.
    """
    weather_string = print_weather(weather_df)
    prompt = f"""
It is 6am. The following is a weather forecast for today:
```
{weather_string}
```
Your task is to summarise this forecast in a digestible way, by giving advice on whether it is warm/cold or whether I should take an umbrella, etc. The output will be sent as a text message at 6am and will be read first thing in the morning, so it should be very simple. Write short sentences, (e.g. "Today will be rainy, cool and cloudy. Temperature 13.1°C-15.7°C. Wind speed high, gusts 12.8 m/s."). Make it short and informative. Use the same units as in the forecast.
"""
    return prompt


def query_openai_prompt(prompt, model="gpt-4-turbo"):
    api_key = os.environ["OPENAI_API_KEY"]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = "https://api.openai.com/v1/chat/completions"
    message = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    response = requests.post(url, headers=headers, json=message)
    output = response.json()
    output_message = output["choices"][0]["message"]["content"]
    return output_message


if __name__ == "__main__":
    latitude, longitude = obtain_recent_coordinates()
    weather, metadata = query_weather_forecast(latitude, longitude)
    prompt = get_llm_prompt(weather)
    response = query_openai_prompt(prompt)
    print(response)
