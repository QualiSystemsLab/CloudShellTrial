from cloudshell.api.cloudshell_api import *
from os import environ as parameter
import json
from hubspot_helper import Hubspot_API_Helper

reservationContext = json.loads(parameter["reservationContext"])
connectivityContext = json.loads(parameter["qualiConnectivityContext"])

api = CloudShellAPISession(host=connectivityContext["serverAddress"], token_id=connectivityContext["adminAuthToken"], domain=reservationContext["domain"])
hb_helper = Hubspot_API_Helper("cba66474-e4e4-4f5b-9b9b-35620577f343")

api.WriteMessageToReservationOutput(reservationContext["id"], "Retrieving Trials data ")

find_resources_result = api.FindResources(resourceFamily="CloudShell Trial", showAllDomains=True)

active_trial_resources = [resource for resource in find_resources_result.Resources if resource.ReservedStatus == "Reserved"]

api.WriteMessageToReservationOutput(reservationContext["id"], "Sending Google Analytics Reports to Owners...")

for resource in active_trial_resources:
	resource_details = api.GetResourceDetails(resource.FullPath, True)
	resource_atts_dict = {attribute.Name:attribute.Value for attribute in resource_details.ResourceAttributes}
	trial_owner_email = hb_helper.get_contact_owner_email(resource_atts_dict["email"])
	email_to_address = ",".join([resource_atts_dict["Quali Owner"], trial_owner_email]) if trial_owner_email != "" else resource_atts_dict["Quali Owner"] 
	api.WriteMessageToReservationOutput(reservationContext["id"], "Sending trial report for {0} {1}'s trial to {2}".format(resource_atts_dict["First Name"], resource_atts_dict["Last Name"], email_to_address))
	command_inputs = {"start_date":"30daysAgo", "end_date":"today", "cloudshell_username":resource_atts_dict["email"], "email_address":email_to_address, 
					  "email_title": "Trial Activity Report for {0} {1}".format(resource_atts_dict["First Name"], resource_atts_dict["Last Name"]) }
	api.ExecuteCommand(reservationContext["id"], "Admin-Google Analytics", "Service", "email_ga_user_report_to_contact", [InputNameValue(k,v) for k,v in command_inputs.items()], True)

api.WriteMessageToReservationOutput(reservationContext["id"], "Done!")