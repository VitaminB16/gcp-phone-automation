from gcp_pal import CloudRun

from packages.gcp_phone_weather.schedule import schedule_service


def deploy_phone_weather():
    print("Deploying phone weather cloud run..")
    CloudRun("phone-weather").deploy(
        path=".", dockerfile="packages/gcp_phone_weather/Dockerfile", memory="2048Mi"
    )
    status = CloudRun("phone-weather").status()
    print("Scheduling service...")
    schedule_service()
    print(f"Status: {status}")
