from cloudshell.api.cloudshell_api import *
from os import environ as parameter
import json
import random
import string
import requests

reservationContext = json.loads(parameter["reservationContext"])
connectivityContext = json.loads(parameter["qualiConnectivityContext"])

global_inputs = {in_param["parameterName"]:in_param["value"] for in_param in reservationContext["parameters"]["globalInputs"]}
first_name = global_inputs["First Name"]
last_name = global_inputs["Last Name"]
email = global_inputs["email"]
company = global_inputs["Company Name"]
phone = global_inputs["Phone number"]
owner_email = global_inputs["Quali Owner"]

extension_period_in_days = parameter["Extension Period"]
api = CloudShellAPISession(host=connectivityContext["serverAddress"], token_id=connectivityContext["adminAuthToken"], domain=reservationContext["domain"])

api.ExtendReservation(reservationContext["id"], 24 * 60 * int(extension_period_in_days))
# TODO: Extend trial campaign in hubspot and send relevant e-mail
# Todo send "Extended Trial" e-mail to owner + admin

api.WriteMessageToReservationOutput(reservationContext["id"], "Trial Extended by " + extension_period_in_days + " days")
