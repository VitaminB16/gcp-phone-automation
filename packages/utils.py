import os
import glob


def copy_requirements(packages=None):
    if packages is None:
        docker_files = glob.glob("packages/*/Dockerfile")
        packages = [os.path.dirname(docker_file) for docker_file in docker_files]

    for package in packages:
        os.system(f"cp requirements.txt {package}/requirements.txt")


def make_requirements():
    command = (
        "poetry export -f requirements.txt --without-hashes --output requirements.txt"
    )
    os.system(command)

    copy_requirements()
