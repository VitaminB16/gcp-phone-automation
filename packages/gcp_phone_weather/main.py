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
    latitude, longitude = obtain_recent_coordinates()
    weather, metadata = query_weather_forecast(latitude, longitude)
    message = compute_text_message(weather, metadata, use_llm=True)
    send_text_message(message, metadata)


def entry_point(request):
    main()
    return {"status": 200}


if __name__ == "__main__":
    main()
