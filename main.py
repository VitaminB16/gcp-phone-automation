from dotenv import load_dotenv

load_dotenv()

import os
import json
from gcp_pal.utils import log
from flask import Flask, jsonify, request as flask_request

app = Flask(__name__)


def main(task=None):
    """
    Stores the current location of all my devices.

    Args:
    - task (str): The task to run. Can be either "location" or "weather".
    """
    if task == "location":
        from packages.gcp_phone_location.main import main
    elif task == "weather":
        from packages.gcp_phone_weather.main import main
    else:
        raise ValueError(f"Invalid task: {task}")

    main()

    return {"status": "success"}


def entry_point(request):
    """
    Entry point for the Cloud Function.

    Args:
    - request (flask.Request): The flask request object, which (potentially) contains the payload.

    Returns:
    - dict: A dictionary containing the response.
    """
    task = request.args.get("task", "location")
    response = main(task=task)
    return response


@app.route("/", methods=["POST", "GET"])
def flask_entry_point():
    """
    Entry point for the Flask app. This is used by the Cloud Run services. The payload is passed in the request.

    Returns:
    - dict: A dictionary containing the response.
    """
    if flask_request.method == "POST":
        payload = flask_request.get_json(silent=True, force=True)
    else:
        payload = flask_request.args.to_dict()
    if isinstance(payload, str):
        payload = json.loads(payload)
    task = payload.get("task", None)
    if task is None:
        log("No task provided.")
        return {
            "status": "failure",
            "message": f"No task provided. Recieved: {flask_request.args}",
        }
    main(task=task)
    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    if os.getenv("ENV", None) == "dev":
        main(task="weather")
    else:
        port = int(os.environ.get("PORT", 8080))
        host = os.environ.get("HOST", "0.0.0.0")
        app.run(host=host, port=port)
