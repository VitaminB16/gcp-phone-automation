import os
from gcp_pal import CloudFunctions


def make_requirements():
    command = (
        "poetry export -f requirements.txt --without-hashes --output requirements.txt"
    )
    os.system(command)


def deploy():
    CloudFunctions("phone-location").deploy(path=".", entry_point="entry_point")


if __name__ == "__main__":
    make_requirements()
    deploy()
