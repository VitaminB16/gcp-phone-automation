import os
from gcp_pal import Firestore


def add_date_device_id_to_location(device_id=None):
    """
    Older entries in Firestore do not have the date and device ID in the location data.
    This data is redundant but is needed for querying the data.
    This function adds the date and device ID to the location data for all devices.

    Args:
    - device_id (str): The device ID to add the date and device ID to the location data for.

    Returns:
    - bool: True if the date and device ID were added to the location data successfully.
    """
    if device_id is None:
        device_id = os.environ["FOLLOWMEE_DEVICE_ID"]
    col_ref = Firestore(f"device_locations/devices/{device_id}").read()
    for date, doc in col_ref.items():
        doc["Date"] = date
        doc["DeviceID"] = device_id
        Firestore(f"device_locations/devices/{device_id}/{date}").write(doc)

    return True
