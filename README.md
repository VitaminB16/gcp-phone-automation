This repository contains a set of Google Cloud Platform (GCP) services that I use to automate some of my daily tasks.

---

## Phone location

_I need to always know my current location, and I always have my phone with me._

A scheduled GCP service which obtains the location of my phone and stores it in Google Cloud Firestore.

This service is deployed as a Cloud Function. The Cloud Scheduler triggers the Cloud Function every 2 minutes. The Cloud Function uses the FollowMee API to obtain the location of my phone. The location is then stored in Google Cloud Firestore.

This data can be used by other services to provide location-based services.

---

## Weather forecast

_Every day I search "weather [city name]" on Google. I should automate this._

A scheduled GCP service which obtains the location of my phone and sends me a text message with the weather forecast for that location.

This service runs once a day at 6:00 AM (local time). The Cloud Scheduler triggers the Cloud Function, which does the following:
1. Grabs latest saved location of my phone from Firestore
2. Queries the OpenWeatherMap API for the weather forecast
3. Generates an appropriate message using OpenAI's GPT-4 API to let me know if I should take an umbrella
4. Sends the notification to my phone using Pushover API
