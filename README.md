A scheduled GCP service which obtains the location of my phone and stores it in Google Cloud Firestore.

This service is deployed as a Cloud Function. The Cloud Scheduler triggers the Cloud Function every 2 minutes. The Cloud Function uses the FollowMee API to obtain the location of my phone. The location is then stored in Google Cloud Firestore.