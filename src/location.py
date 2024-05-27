import os
import requests

from gcp_pal import Firestore


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
        device_id = device_location.pop("DeviceID")
        for key in irrelevant_keys:
            device_location.pop(key)
        output[device_id] = device_location
    return output


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
        updated_time = location.pop("Date")
        if updated_time <= last_updated_time:
            print(f"No new location data for device {device_id}.")
            continue
        # Only store the location if it is newer than the last stored location
        location_path = f"device_locations/devices/{device_id}/{updated_time}"
        Firestore(location_path).write(location)
        Firestore(last_updated_time_path).write({"data": updated_time})
    return True
