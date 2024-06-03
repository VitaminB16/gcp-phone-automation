from dotenv import load_dotenv

load_dotenv()

import os
import base64
import requests
from gcp_pal import Firestore
from selenium import webdriver
from selenium.webdriver.common.by import By

from packages.gcp_phone_weather.openai import get_llm_prompt, query_openai_prompt


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


def get_weather_image_icon(metadata):
    """
    Get the icon for today's weather forecast from the weather in Google Search.

    Args:
    - metadata (dict): The metadata of the location.

    Returns:
    - str: The URL of the weather image icon.
    """
    city = metadata["name"].replace(" ", "+")
    country = metadata["country"].replace(" ", "+")
    url = f"https://www.google.com/search?q=weather+in+{city}+{country}"
    headers = {"User-Agent": "Mozilla/5.0"}
    cookies = {"CONSENT": "YES+cb.20210720-07-p0.en+FX+410"}
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("window-size=1024,768")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    image_class = "wob_tci"
    image = driver.find_element(By.CLASS_NAME, image_class)
    image_url = image.get_attribute("src")
    driver.quit()
    image_data = requests.get(image_url, headers=headers, cookies=cookies).content
    return image_data


def send_text_message(message, metadata):
    """
    Send a notification to the phone using Pushover API.

    Args:
    - message (str): The message to send.
    - metadata (dict): The metadata of the location.
    """
    city = metadata["name"]
    message = f"{city} Weather:\n{message}"
    attachment_image = get_weather_image_icon(metadata)
    base64_image = base64.b64encode(attachment_image).decode("utf-8")
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": os.getenv("PUSHOVER_WEATHER_API_TOKEN", None),
        "user": os.getenv("PUSHOVER_USER_KEY", None),
        "title": "Weather Forecast",
        "message": message,
        "priority": 0,
        "attachment_base64": base64_image,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Notification sent.")
        return
    print("Failed to send notification.")
    return


def compute_text_message(weather_df, metadata, use_llm=True):
    if use_llm:
        prompt = get_llm_prompt(weather_df, metadata)
        message = query_openai_prompt(prompt)
    else:
        from packages.gcp_phone_weather.weather import get_message_for_weather

        message = get_message_for_weather(weather_df, metadata)
    return message
