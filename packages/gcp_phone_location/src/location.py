import os
import requests
from datetime import datetime, timezone

from gcp_pal import Firestore
from gcp_pal.utils import log


def get_current_location():
    """
    Get the current location of all devices being tracked by FollowMee.

    Returns:
    - dict: A dictionary where the keys are the device IDs and the values are the location data.
    """
    key = os.getenv("FOLLOWMEE_API_KEY")
    username = os.getenv("FOLLOWMEE_USERNAME")
    url = f"https://www.followmee.com/api/tracks.aspx"

    params = {
        "key": key,
        "username": username,
        "output": "json",
        "function": "currentforalldevices",
    }
    response = requests.get(url, params=params)
    response = response.json()
    devices_locations = response["Data"]
    irrelevant_keys = ["Altitude(ft)", "Speed(km/h)"]
    output = {}
    for device_location in devices_locations:
        device_id = device_location.get("DeviceID")
        for key in irrelevant_keys:
            device_location.pop(key)
        output[device_id] = device_location
    return output


def convert_time_to_utc(time):
    """
    Convert a time string (e.g. '2024-05-28T20:09:53+02:00') to UTC time string (e.g. '2024-05-28T18:09:53+00:00').

    Args:
    - time (str): The time string to convert.

    Returns:
    - str: The time string converted to UTC time.
    """
    time = datetime.fromisoformat(time)
    time = time.astimezone(timezone.utc)
    time = datetime.isoformat(time)
    return time


def parse_time_zone(time):
    """
    Parse the time zone from a time string.

    Args:
    - time (str): The time string to parse.

    Returns:
    - str: The time zone of the time string.
    """
    if "+" in time:
        time_zone = time.split("+")[1]
        sign = "+"
    elif "-" in time:
        time_zone = time.split("-")[1]
        sign = "-"
    # Remove leading zeros
    if time_zone == "00:00":
        return "UTC"
    if time_zone[0] == "0":
        time_zone = time_zone[1:]
    if time_zone.endswith(":00"):
        time_zone = time_zone.replace(":00", "")
    else:
        # There is little we can do for non-hour time zones (e.g. Kabul UTC+4:30)
        time_zone = time_zone.split(":")[0]
    # Archaic tz database format because Google Cloud Scheduler does not support UTC...
    time_zone = f"Etc/GMT{sign}{time_zone}"
    return time_zone


def store_location(location_data):
    """
    Store the location data in a file.

    Args:
    - location_data (dict): The location data to store.

    Returns:
    - bool: True if the location data was stored successfully, False otherwise.
    """
    default_updated_time = "1970-01-01T00:00:00Z"
    for device_id, location in location_data.items():
        last_updated_time_path = (
            f"device_locations/last_updated_times/{device_id}/last_updated_time"
        )
        last_updated_time = Firestore(last_updated_time_path).read(allow_empty=True)

        if last_updated_time == {}:
            last_updated_time = default_updated_time
        updated_time = location.get("Date")
        if convert_time_to_utc(updated_time) <= convert_time_to_utc(last_updated_time):
            log(f"No new location data for device {device_id}.")
            continue

        last_updated_time_zone = parse_time_zone(last_updated_time)
        current_time_zone = parse_time_zone(updated_time)
        if current_time_zone != last_updated_time_zone:
            # Time zone changed! We have to reschedule the weather service.
            log(f"Time zone changed for device {device_id}!")
            log("Rescheduling the weather service...")
            from packages.gcp_phone_weather.schedule import schedule_service
            try:
                schedule_service(time_zone=current_time_zone)
            except Exception as e:
                log(f"Failed to reschedule the weather service: {e}")

        # Only store the location if it is newer than the last stored location
        location_path = f"device_locations/devices/{device_id}/{updated_time}"
        Firestore(location_path).write(location)
        Firestore(last_updated_time_path).write({"data": updated_time})
    return True
