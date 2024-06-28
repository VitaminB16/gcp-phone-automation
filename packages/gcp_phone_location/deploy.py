from gcp_pal import CloudFunctions
from gcp_pal.utils import log

from packages.gcp_phone_location.schedule import schedule_service


def deploy_cloud_function():
    """
    Deploys the phone location cloud function.

    Returns:
    - str: The status of the cloud function.
    """
    CloudFunctions("phone-location").deploy(
        path=".", entry_point="entry_point", runtime="python312", environment=1
    )
    status = CloudFunctions("phone-location").status()
    log(f"Status: {status}")
    return status


def deploy_phone_location():
    """
    Deploys the phone location service - the cloud function and the scheduler.

    Returns:
    - str: The status of the cloud function.
    """
    print("Deploying phone location cloud function..")
    deploy_cloud_function()
    print("Scheduling service...")
    status = schedule_service()
    return status
