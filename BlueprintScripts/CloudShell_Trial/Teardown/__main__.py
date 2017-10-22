from cloudshell.api.cloudshell_api import *
from hubspot_helper import Hubspot_API_Helper
from email_helper import SMTPClient
from os import environ as parameter
import json
import random
import string
import requests
import itertools

reservationContext = json.loads(parameter["reservationContext"])
connectivityContext = json.loads(parameter["qualiConnectivityContext"])

global_inputs = {in_param["parameterName"]:in_param["value"] for in_param in reservationContext["parameters"]["globalInputs"]}
first_name = global_inputs["First Name"]
last_name = global_inputs["Last Name"]
email = global_inputs["email"].lower()
company = global_inputs["Company Name"]
phone = global_inputs["Phone number"]
owner_email = global_inputs["Quali Owner"]

api = CloudShellAPISession(host=connectivityContext["serverAddress"], token_id=connectivityContext["adminAuthToken"], domain=reservationContext["domain"])
username = email
user_info = api.GetUserDetails(username)
group_name = user_info.Groups[0].Name
domain_name = group_name

# Get SMTP Details from Resource
smtp_resource = api.FindResources('Mail Server', 'SMTP Server').Resources[0]
smtp_resource_details = api.GetResourceDetails(smtp_resource.FullPath)
smtp_attributes = {attribute.Name: attribute.Value if attribute.Type != "Password" else api.DecryptPassword(attribute.Value).Value for attribute in smtp_resource_details.ResourceAttributes}
smtp_client = SMTPClient(smtp_attributes["User"], smtp_attributes["Password"], smtp_resource_details.Address, smtp_attributes["Port"], "trial@quali.com")
admin_email = api.GetUserDetails("admin").Email

# Send e-mail notifications
api.WriteMessageToReservationOutput(reservationContext["id"], "Sending 'Trial End' e-mails")
hubspot_helper = Hubspot_API_Helper("cba66474-e4e4-4f5b-9b9b-35620577f343")
hubspot_helper.enroll_contact_to_workflow(email, "1980444")

email_title = "CloudShell Trial: Trial has ended for {user}".format(user=username)
email_body = "The CloudShell trial for {user} has ended".format(user=username)
smtp_client.send_email(",".join([owner_email, admin_email]), email_title, email_body, False)

# Send end-of-trial activity report
trial_resource = next(resource for resource in api.GetReservationDetails(reservationContext["id"]).ReservationDescription.Resources if resource.ResourceModelName == "CloudShell VE Trial")
resource_details = api.GetResourceDetails(trial_resource.Name, True)
resource_atts_dict = {attribute.Name:attribute.Value for attribute in resource_details.ResourceAttributes}
command_inputs = {"start_date":"30daysAgo", "end_date":"today", "cloudshell_username":resource_atts_dict["email"], "email_address":resource_atts_dict["Quali Owner"], 
					"email_title": "End of Trial Activity Report for {0} {1}".format(resource_atts_dict["First Name"], resource_atts_dict["Last Name"]) }
api.ExecuteCommand(reservationContext["id"], "Admin-Google Analytics", "Service", "email_ga_user_report_to_contact", [InputNameValue(k,v) for k,v in command_inputs.items()], True)

# remove user from groups and deactivate
api.WriteMessageToReservationOutput(reservationContext["id"], "Deactivating user and removing permissions")
api.RemoveUsersFromGroup([username], group_name)
api.UpdateUser(username, email, isActive=False)

groups_in_domain = [group.Name for group in api.GetDomainDetails(domain_name).Groups if group.Name != "System Administrators"]
groups_in_domain_users = sum([group.Users for group in api.GetGroupsDetails().Groups if group.Name in groups_in_domain],[])
groups_in_domain_user_names = [user.Name for user in groups_in_domain_users]
api.ArchiveDomain(domain_name)



if username in groups_in_domain_user_names:
	email_title = "CloudShell Trial: Failed to remove user from domain"
	email_body = "Failed to remove {user} from trial domain!".format(user=username)
	smtp_client.send_email(",".join([owner_email, admin_email]), email_title, email_body, False)
	api.WriteMessageToReservationOutput(reservationContext["id"], "Critical error:User still has access to domain")
else:
	api.WriteMessageToReservationOutput(reservationContext["id"], "Trial ended successfully, thank you for using CloudShell Trial")
