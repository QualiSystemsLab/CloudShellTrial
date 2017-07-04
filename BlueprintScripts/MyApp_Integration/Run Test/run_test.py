from cloudshell.api.cloudshell_api import *
from os import environ as parameter
import json

reservationContext = json.loads(parameter["reservationContext"])
connectivityContext = json.loads(parameter["qualiConnectivityContext"])

test_name = parameter["Test_Name"]

api = CloudShellAPISession(host=connectivityContext["serverAddress"], token_id=connectivityContext["adminAuthToken"], domain=reservationContext["domain"])

reservation_details = api.GetReservationDetails(reservationContext["id"])
web_server_resource = next(resource.Name for resource in reservation_details.ReservationDescription.Resources if "My App Web Server" in resource.ResourceModelName)

selenium_hub_resource = next(resource.Name for resource in reservation_details.ReservationDescription.Resources if "Selenium Hub" in resource.ResourceModelName)

print(api.ExecuteCommand(reservationContext["id"], selenium_hub_resource, "Resource", "run_selenium_test", [InputNameValue("test_name", test_name), InputNameValue("target_resource_name", web_server_resource)]).Output)
