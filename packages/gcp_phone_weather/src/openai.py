from dotenv import load_dotenv

load_dotenv()

import os
import json
import requests

from packages.gcp_phone_weather.src.weather import print_weather


PROMPT_1 = """You are presented with a weather forecast for the day.
Your task is to give actionable sugestions. E.g. "- Bring an umbrella.", "Wear gloves.".
Do not include anything else in your message.
For example:
Example message: - Dress warmly.\n- Take umbrella.
Example message: - Dress warmly.\n- Feels colder than actual temperature.
Example message: - Dress light.\n- Take sunglasses.
"""

PROMPT_2 = """Your task is to summarise this forecast in a digestible way, by stating the weather conditions and temperature.
The output will be sent as a text message at 6am and will be read first thing in the morning, so it should be very simple.
E.g. "Temperature 12°C-17°C-14°C. Wind speed 13 km/h. Rain probability 50% over 6 hours. Take umbrella (if applicable)."."""


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
{PROMPT_1}
Additional metadata:
{json.dumps(metadata)}
"""
    return prompt


def query_openai_prompt(prompt, model="gpt-4-turbo"):
    """
    Query the OpenAI API with the given prompt.

    Args:
    - prompt (str): The prompt to query.
    - model (str): The model to use. Defaults to "gpt-4-turbo".

    Returns:
    - str: The response from the LLM model.
    """
    api_key = os.environ["OPENAI_API_KEY"]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = "https://api.openai.com/v1/chat/completions"
    message = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    print("Querying OpenAI API...")
    response = requests.post(url, headers=headers, json=message)
    output = response.json()
    output_message = output["choices"][0]["message"]["content"]
    return output_message
