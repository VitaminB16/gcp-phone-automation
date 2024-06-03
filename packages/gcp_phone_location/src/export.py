import os
import pandas as pd
from gcp_pal import Firestore


def export_locations(device_id=None, start_date=None, end_date=None):
    """
    Export the location data from Firestore between the start and end dates.

    Args:
    - device_id (str): The device ID to export the location data for.
    - start_date (str): The start date to export the location data from (e.g. '2024-05-28T18:09:53+00:00').
    - end_date (str): The end date to export the location data to (e.g. '2024-05-28T18:09:53+00:00').

    Returns:
    - dict: The location data between the start and end dates.
    """
    if device_id is None:
        device_id = os.environ["FOLLOWMEE_DEVICE_ID"]
    col_ref = Firestore(f"device_locations/devices/{device_id}").get()
    # Query all documents between the start and end dates
    if start_date is None:
        start_date = "2010-05-28T18:09:53+00:00"
    if end_date is None:
        end_date = "2200-05-28T18:09:53+00:00"

    # Filter the documents between the start and end dates by the ID
    doc_ref = (
        col_ref.where("Date", ">=", start_date).where("Date", "<=", end_date).get()
    )
    output = {}
    keys_to_keep = ["Date", "Latitude", "Longitude"]
    for doc in doc_ref:
        doc_dict = doc.to_dict()
        doc_dict = {k: doc_dict[k] for k in keys_to_keep}
        output[doc.id] = doc_dict
    df = pd.DataFrame(output).T
    df = df.reset_index(drop=True)
    df.to_csv(f"output/location_export_{device_id}.csv", index=False)
    return output


if __name__ == "__main__":
    export_locations()