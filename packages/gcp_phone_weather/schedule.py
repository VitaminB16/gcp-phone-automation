from gcp_pal import CloudScheduler, CloudRun


def schedule_service():

    cloud_run_uri = CloudRun("phone-weather").uri()
    once_a_day_at_5_58_am = "58 5 * * *"
    CloudScheduler("phone-weather").create(
        target=cloud_run_uri,
        schedule=once_a_day_at_5_58_am,
        time_zone="UTC",
        payload='{"task": "weather"}',
        service_account="DEFAULT",
    )
    status = CloudScheduler("phone-weather").status()
    print(f"Status: {status}")
    return status
