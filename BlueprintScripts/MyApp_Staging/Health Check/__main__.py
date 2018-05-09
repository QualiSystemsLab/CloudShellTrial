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
if elb_url.startswith("http://"): elb_url = elb_url[len("http://"):]

api.WriteMessageToReservationOutput(reservationContext["id"], "Attempting to reach Elastic Load Balancer...")
try:
	if not elb_url:
		api.WriteMessageToReservationOutput(reservationContext["id"], "No Elastic Load Balancer is deployed!")
		healthcheck_passed = False
	elif requests.get("http://" + elb_url).status_code != 200:
		api.WriteMessageToReservationOutput(reservationContext["id"], "Elastic Load Balancer is unreachable!")
		healthcheck_passed = False
except:
	api.WriteMessageToReservationOutput(reservationContext["id"], "An error occurred when trying to reach Elastic Load Balancer!")
	healthcheck_passed = False
	

cf_service = next(service for service in reservation_details.ReservationDescription.Services if service.ServiceName == "AWS CloudFront Distribution")
cf_url = next(attribute.Value for attribute in cf_service.Attributes if attribute.Name == "External_URL")
if cf_url.startswith("http://"): cf_url = cf_url[len("http://"):]

api.WriteMessageToReservationOutput(reservationContext["id"], "Attempting to reach CloudFront Distribution...")

try:
	if not cf_url:
		api.WriteMessageToReservationOutput(reservationContext["id"], "No CF Distribution is deployed!")
		healthcheck_passed = False
	elif requests.get("http://" + cf_url).status_code != 200:
		api.WriteMessageToReservationOutput(reservationContext["id"], "CloudFront Distribution is unreachable!")
		healthcheck_passed = False
except:
	api.WriteMessageToReservationOutput(reservationContext["id"], "An error occurred when trying to reach CloudFront Distribution!")
	healthcheck_passed = False

if healthcheck_passed:
	api.WriteMessageToReservationOutput(reservationContext["id"], "Sandbox Healthcheck passed!")
else:
	api.WriteMessageToReservationOutput(reservationContext["id"], "Sandbox Healthcheck failed!")
