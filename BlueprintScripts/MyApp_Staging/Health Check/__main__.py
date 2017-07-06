from cloudshell.api.cloudshell_api import *
from os import environ as parameter
import json
import requests

reservationContext = json.loads(parameter["reservationContext"])
connectivityContext = json.loads(parameter["qualiConnectivityContext"])

healthcheck_passed = True

api = CloudShellAPISession(host=connectivityContext["serverAddress"], token_id=connectivityContext["adminAuthToken"], domain=reservationContext["domain"])

reservation_details = api.GetReservationDetails(reservationContext["id"])

elb_service = next(service for service in reservation_details.ReservationDescription.Services if service.ServiceName == "AWS Elastic Load Balancer")
elb_url = next(attribute.Value for attribute in elb_service.Attributes if attribute.Name == "External_URL")
print("Attempting to reach Elastic Load Balancer...")

if not elb_url:
	print("No Elastic Load Balancer is deployed!")
	healthcheck_passed = False
elif requests.get("http://" + elb_url).status_code != 200:
	print("Elastic Load Balancer is unreachable!")
	healthcheck_passed = False

cf_service = next(service for service in reservation_details.ReservationDescription.Services if service.ServiceName == "AWS CloudFront Distribution")
cf_url = next(attribute.Value for attribute in cf_service.Attributes if attribute.Name == "External_URL")

print("Attempting to reach CloudFront Distribution...")

if not cf_url:
	print("No CF Distribution is deployed!")
	healthcheck_passed = False
elif requests.get("http://" + cf_url).status_code != 200:
	print("CloudFront Distribution is unreachable!")
	healthcheck_passed = False

if healthcheck_passed:
	print("Healthcheck performed successfully")
