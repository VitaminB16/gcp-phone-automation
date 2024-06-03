from gcp_pal import CloudFunctions

if __name__ == "__main__":
    CloudFunctions("phone-weather").call({"task": "weather"})
