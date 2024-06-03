from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request as flask_request

from packages.gcp_phone_weather.src.weather import query_weather_forecast
from packages.gcp_phone_weather.src.utils import (
    compute_text_message,
    send_text_message,
    obtain_recent_coordinates,
)


def main():
    """
    Query the weather forecast for the most recent coordinates of the device and send a text message.

    Returns:
    - dict: A dictionary containing the response.
    """
    latitude, longitude = obtain_recent_coordinates()
    weather, metadata = query_weather_forecast(latitude, longitude)
    message = compute_text_message(weather, metadata, use_llm=True)
    status = send_text_message(message, metadata)
    return status


if __name__ == "__main__":
    main()
