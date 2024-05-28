import os
from gcp_pal import CloudFunctions
from gcp_pal.utils import log


def make_requirements():
    command = (
        "poetry export -f requirements.txt --without-hashes --output requirements.txt"
    )
    os.system(command)


def deploy():
    CloudFunctions("phone-location").deploy(path=".", entry_point="entry_point", runtime="python312")
    status = CloudFunctions("phone-location").status()
    log(f"Status: {status}")
    return status


if __name__ == "__main__":
    make_requirements()
    deploy()
