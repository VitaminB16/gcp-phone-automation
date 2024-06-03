from dotenv import load_dotenv

load_dotenv()

import os
from gcp_pal import CloudScheduler, CloudRun, Firestore


def obtain_latest_time_zone():
    """
    Obtains the latest time zone from the Cloud Run service.

    Returns:
    - str: The time zone.
    """
    from packages.gcp_phone_location.src.location import parse_time_zone

    device_id = os.getenv("FOLLOWMEE_DEVICE_ID")
    if device_id is None:
        return "UTC"
    path = f"device_locations/last_updated_times/{device_id}/last_updated_time"
    last_updated_time = Firestore(path).read(allow_empty=True)
    time_zone = parse_time_zone(last_updated_time)
    print(f"Obtained latest time zone: {time_zone}")

    return time_zone


def schedule_service(time_zone=None):
    """
    Schedules the phone weather service to run every day at 5:58 AM.
    It should run at 5:58 AM because the weather forecast for 6 AM is still available.

    Returns:
    - str: The status of the Cloud Scheduler job.
    """
    if time_zone is None:
        time_zone = obtain_latest_time_zone()

    cloud_run_uri = CloudRun("phone-weather").uri()
    once_a_day_at_5_58_am = "58 5 * * *"
    CloudScheduler("phone-weather").create(
        target=cloud_run_uri,
        schedule=once_a_day_at_5_58_am,
        time_zone=time_zone,
        payload='{"task": "weather"}',
        service_account="DEFAULT",
    )
    status = CloudScheduler("phone-weather").status()
    print(f"Status: {status}")
    return status
