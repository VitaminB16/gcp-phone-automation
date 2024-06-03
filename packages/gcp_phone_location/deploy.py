from gcp_pal import CloudFunctions
from gcp_pal.utils import log

from packages.gcp_phone_location.schedule import schedule_service


def deploy_cloud_function():
    CloudFunctions("phone-location").deploy(
        path=".", entry_point="entry_point", runtime="python312"
    )
    status = CloudFunctions("phone-location").status()
    log(f"Status: {status}")
    return status


def deploy_phone_location():
    print("Deploying phone location cloud function..")
    deploy_cloud_function()
    print("Scheduling service...")
    schedule_service()
