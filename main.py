from dotenv import load_dotenv

load_dotenv()

from gcp_pal.utils import log


from src.location import get_current_location, store_location


def main():
    """
    Stores the current location of all my devices.
    """
    location_data = get_current_location()
    result = store_location(location_data)
    if result is True:
        log("Location data stored successfully.")
    else:
        raise Exception("Failed to store location data.")
    return


def entry_point(request):
    main()
    return {"status": "success"}


if __name__ == "__main__":
    main()
