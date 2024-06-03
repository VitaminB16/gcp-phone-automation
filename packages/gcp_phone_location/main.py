from gcp_pal.utils import log

from packages.gcp_phone_location.src.location import (
    get_current_location,
    store_location,
)


def main():
    """
    Obtains the most recent location data and stores it in Firestore.
    """
    location_data = get_current_location()
    result = store_location(location_data)
    if result is True:
        log("Location data stored successfully.")
    else:
        raise Exception("Failed to store location data.")
    return {"status": "success"}


if __name__ == "__main__":
    main()
