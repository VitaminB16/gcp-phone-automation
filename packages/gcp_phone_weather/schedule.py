from dotenv import load_dotenv

load_dotenv()

import os

from gcp_pal import CloudScheduler, CloudRun


def schedule_service():

    cloud_run_uri = CloudRun("phone-weather").uri()
    once_a_day_at_5_58_am = "58 5 * * *"
    service_account = os.environ["SERVICE_ACCOUNT"]
    CloudScheduler("phone-weather").create(
        target=cloud_run_uri,
        schedule=once_a_day_at_5_58_am,
        time_zone="UTC",
        payload='{"task": "weather"}',
        service_account=service_account,
    )
    status = CloudScheduler("phone-location").status()
    print(f"Status: {status}")
    return status
