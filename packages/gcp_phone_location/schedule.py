from gcp_pal import CloudScheduler, CloudFunctions


def schedule_service():
    """
    Schedules the phone location service to run every 2 minutes.

    Returns:
    - str: The status of the Cloud Scheduler job.
    """
    cloud_function_uri = CloudFunctions("phone-location").uri()
    # Create a Cloud Scheduler job that runs every 2 minutes
    CloudScheduler("phone-location-2-min").create(
        schedule="*/2 * * * *",
        time_zone="UTC",
        payload={},
        target=cloud_function_uri,
        service_account="DEFAULT",
    )
    status = CloudScheduler("phone-location-2-min").status()
    return status


if __name__ == "__main__":
    schedule_service()
