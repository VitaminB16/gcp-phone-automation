from dotenv import load_dotenv

load_dotenv()

import os
import json
import requests

from packages.gcp_phone_weather.weather import print_weather


def get_llm_prompt(weather_df=None, metadata=None):
    """
    Query the OpenAI GPT-3 API.

    Args:
    - prompt (str): The prompt to query.

    Returns:
    - str: The response from the GPT-3 API.
    """
    weather_string = print_weather(weather_df)
    prompt = f"""It is 6am. The following is a weather forecast for today:
```
{weather_string}
```
Your task is to summarise this forecast in a digestible way, by giving advice on whether it is warm/cold.
The output will be sent as a text message at 6am and will be read first thing in the morning, so it should be very simple.
Write short sentences, (e.g. "Today will be rainy, cool and cloudy. Temperature 13.1°C-15.7°C. Wind speed high, gusts 12.8 m/s.").
Present information using tables, bullet points, or any other format that makes it easy to digest. Don't use markdown or HTML.
Give actionable sugestions. E.g. "Bring an umbrella.", "Wear a jacket.", "Go for a walk.", "Wear gloves.".
Make it short and informative. Use the same units as in the forecast. Round the numbers to integers.
Be as informative as possible, but keep it simple and concise.
Additional metadata:
{json.dumps(metadata)}
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
