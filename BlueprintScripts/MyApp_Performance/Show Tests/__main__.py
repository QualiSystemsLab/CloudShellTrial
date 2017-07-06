from cloudshell.api.cloudshell_api import *
from os import environ as parameter
import json

reservationContext = json.loads(parameter["reservationContext"])
connectivityContext = json.loads(parameter["qualiConnectivityContext"])

api = CloudShellAPISession(host=connectivityContext["serverAddress"], token_id=connectivityContext["adminAuthToken"], domain=reservationContext["domain"])

reservation_details = api.GetReservationDetails(reservationContext["id"])

jmeter_resource = next(resource.Name for resource in reservation_details.ReservationDescription.Resources if "JMeter" in resource.ResourceModelName)

print(api.ExecuteCommand(reservationContext["id"], jmeter_resource, "Resource", "show_available_tests").Output)
