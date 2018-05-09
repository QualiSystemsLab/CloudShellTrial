from cloudshell.api.cloudshell_api import *
from os import environ as parameter
import json
import requests
import datetime

reservationContext = json.loads(parameter["reservationContext"])
connectivityContext = json.loads(parameter["qualiConnectivityContext"])

global_inputs = {in_param["parameterName"]:in_param["value"] for in_param in reservationContext["parameters"]["globalInputs"]}
first_name = global_inputs["First Name"]
last_name = global_inputs["Last Name"]
email = global_inputs["email"]
company = global_inputs["Company Name"]
phone = global_inputs["Phone number"]
owner_email = global_inputs["Quali Owner"]
username = email

new_owner = parameter["New_Owner"]

api = CloudShellAPISession(host=connectivityContext["serverAddress"], token_id=connectivityContext["adminAuthToken"], domain=reservationContext["domain"])

user_info = api.GetUserDetails(username)
group_name = user_info.Groups[0].Name
api.AddUsersToGroup([new_owner], group_name)

api.WriteMessageToReservationOutput(reservationContext["id"], """{0} was successfully added as an owner to {1}'s CloudShell VE Trial, 
please make sure to monitor any feedback or assistance that might be required from the Trial User""".format(new_owner, username))
