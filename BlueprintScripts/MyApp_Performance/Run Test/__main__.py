from cloudshell.api.cloudshell_api import *
from os import environ as parameter
import json

reservationContext = json.loads(parameter["reservationContext"])
connectivityContext = json.loads(parameter["qualiConnectivityContext"])

test_name = parameter["Test_Name"]
thread_count = parameter["Thread_Count"]

api = CloudShellAPISession(host=connectivityContext["serverAddress"], token_id=connectivityContext["adminAuthToken"], domain=reservationContext["domain"])

reservation_details = api.GetReservationDetails(reservationContext["id"])
ha_proxy_resource = next(resource.Name for resource in reservation_details.ReservationDescription.Resources if "HA Proxy" in resource.ResourceModelName)

jmeter_resource = next(resource.Name for resource in reservation_details.ReservationDescription.Resources if "JMeter".lower() in resource.ResourceModelName.lower())

print(api.ExecuteCommand(reservationContext["id"], jmeter_resource, "Resource", "run_test", 
	[InputNameValue("test_name", test_name), InputNameValue("target_resource_name", ha_proxy_resource), InputNameValue("thread_count", thread_count)]).Output)
