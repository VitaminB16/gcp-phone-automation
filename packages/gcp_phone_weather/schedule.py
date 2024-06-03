from gcp_pal import CloudScheduler, CloudRun


def schedule_service():
    """
    Schedules the phone weather service to run every day at 5:58 AM.
    It should run at 5:58 AM because the weather forecast for 6 AM is still available.

    Returns:
    - str: The status of the Cloud Scheduler job.
    """

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
