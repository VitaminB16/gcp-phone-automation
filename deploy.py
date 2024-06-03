from dotenv import load_dotenv

load_dotenv()

from packages.utils import make_requirements
from packages.gcp_phone_location.deploy import deploy_phone_location
from packages.gcp_phone_weather.deploy import deploy_phone_weather


if __name__ == "__main__":
    make_requirements()
    deploy_phone_location()
    deploy_phone_weather()
