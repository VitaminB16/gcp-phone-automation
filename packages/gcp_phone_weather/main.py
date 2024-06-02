from dotenv import load_dotenv

load_dotenv()

from packages.gcp_phone_weather.weather import query_weather_forecast
from packages.gcp_phone_weather.openai import get_llm_prompt, query_openai_prompt
from packages.gcp_phone_weather.utils import (
    send_text_message,
    obtain_recent_coordinates,
)


if __name__ == "__main__":
    latitude, longitude = obtain_recent_coordinates()
    weather, metadata = query_weather_forecast(latitude, longitude)
    prompt = get_llm_prompt(weather, metadata)
    response = query_openai_prompt(prompt)
    send_text_message(response, metadata)
