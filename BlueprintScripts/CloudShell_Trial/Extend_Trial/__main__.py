from os import environ as parameter
from cloudshell.api.cloudshell_api import *
from cloudshelltrialutils.email_helper import SMTPClient
from cloudshelltrialutils.hubspot_helper import Hubspot_API_Helper
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

api = CloudShellAPISession(host=connectivityContext["serverAddress"], token_id=connectivityContext["adminAuthToken"], domain=reservationContext["domain"])

# Get SMTP Details from Resource
smtp_resource = api.FindResources('Mail Server', 'SMTP Server').Resources[0]
smtp_resource_details = api.GetResourceDetails(smtp_resource.FullPath)
smtp_attributes = {attribute.Name: attribute.Value if attribute.Type != "Password" else api.DecryptPassword(attribute.Value).Value for attribute in smtp_resource_details.ResourceAttributes}
smtp_client = SMTPClient(smtp_attributes["User"], smtp_attributes["Password"], smtp_resource_details.Address, smtp_attributes["Port"], "trial@quali.com")
admin_email = api.GetUserDetails("admin").Email

extension_period_in_days = "5"

api.ExtendReservation(reservationContext["id"], 24 * 60 * int(extension_period_in_days))
reservation_details = api.GetReservationDetails(reservationContext["id"]).ReservationDescription
try:
	reservation_end_date = datetime.datetime.strptime(reservation_details.EndTime, "%d/%m/%Y %H:%M").replace(hour=0, minute=0, second=0, microsecond=0)
except ValueError:
	reservation_end_date = datetime.datetime.strptime(reservation_details.EndTime, "%m/%d/%Y %H:%M").replace(hour=0, minute=0, second=0, microsecond=0)
reservation_end_time_in_ms = int((reservation_end_date - datetime.datetime.utcfromtimestamp(0)).total_seconds() * 1000)

hubspot_helper = Hubspot_API_Helper("cba66474-e4e4-4f5b-9b9b-35620577f343")
hubspot_helper.change_contact_property(email, "cloudshell_trial_end_date", str(reservation_end_time_in_ms))
hubspot_helper.enroll_contact_to_workflow(email, "2012345")

email_title = "CloudShell Trial: Trial Extension"
email_body = "The Trial for {user} has been extended by 5 days".format(user=email)
smtp_client.send_email(",".join([owner_email, admin_email]), email_title, email_body, False)

api.WriteMessageToReservationOutput(reservationContext["id"], "Trial Extended by " + extension_period_in_days + " days")
