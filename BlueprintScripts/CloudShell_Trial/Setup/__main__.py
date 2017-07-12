from cloudshell.api.cloudshell_api import CloudShellAPISession, UserUpdateRequest
from email_helper import SMTPClient
from hubspot_helper import Hubspot_API_Helper
from os import environ as parameter
import json
import random
import string
import requests
import datetime

reservationContext = json.loads(parameter["reservationContext"])
connectivityContext = json.loads(parameter["qualiConnectivityContext"])

global_inputs = {in_param["parameterName"]:in_param["value"] for in_param in reservationContext["parameters"]["globalInputs"]}
first_name = global_inputs["First Name"]
last_name = global_inputs["Last Name"]
email = global_inputs["email"].lower()
company = global_inputs["Company Name"]
phone = global_inputs["Phone number"]
owner_email = global_inputs["Quali Owner"]

new_username = email

api = CloudShellAPISession(host=connectivityContext["serverAddress"], token_id=connectivityContext["adminAuthToken"], domain=reservationContext["domain"])

# Get SMTP Details from Resource
smtp_resource = api.FindResources('Mail Server', 'SMTP Server').Resources[0]
smtp_resource_details = api.GetResourceDetails(smtp_resource.FullPath)
smtp_attributes = {attribute.Name: attribute.Value if attribute.Type != "Password" else api.DecryptPassword(attribute.Value).Value for attribute in smtp_resource_details.ResourceAttributes}
smtp_client = SMTPClient(smtp_attributes["User"], smtp_attributes["Password"], smtp_resource_details.Address, smtp_attributes["Port"], "trial@quali.com")
admin_email = api.GetUserDetails("admin").Email

# Create Domain
api.WriteMessageToReservationOutput(reservationContext["id"], "Creating New Domain")
domain_name = '.'.join(new_username.split('.')[:-1]).replace('@', '-')
if domain_name in [domain.Name for domain in api.GetGroupDomains("System Administrators").TestShellDomains]:
	id_suffix = 1
	while domain_name + str(id_suffix) in [domain.Name for domain in api.GetGroupDomains("System Administrators").TestShellDomains]: 
		id_suffix += 1
	domain_name = domain_name + str(id_suffix)
	api.WriteMessageToReservationOutput(reservationContext["id"], "The requested domain already exists, appending {} to new domain name, please contact system admin at trial@quali.com".format(id_suffix))
	api.AddNewDomain(domainName=domain_name, description="Domain for {0} {1}'s Trial".format(first_name, last_name))
else:
	api.AddNewDomain(domainName=domain_name, description="Domain for {0} {1}'s Trial".format(first_name, last_name))

# Create User Account
api.WriteMessageToReservationOutput(reservationContext["id"], "Creating trial user")
if new_username in [user.Name.lower() for user in api.GetAllUsersDetails().Users]:
	generated_password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
	api.UpdateUser(username=new_username, email=email, isActive=True)
	api.UpdateUserPassword(username=new_username, password=generated_password)
	api.WriteMessageToReservationOutput(reservationContext["id"], "This user already had a trial, please contact system admin at trial@quali.com")
else:
	generated_password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
	api.AddNewUser(username=new_username, password=generated_password, email=email, isActive=True)

api.UpdateUsersLimitations([UserUpdateRequest(Username=email, MaxConcurrentReservations="2", MaxReservationDuration=str(4*60))])

# Create Group and add to domain
api.WriteMessageToReservationOutput(reservationContext["id"], "Configuring new domain permissions")
new_group_name = domain_name
api.AddNewGroup(groupName=new_group_name, description="Regular Users Group for " + domain_name + " domain", groupRole="Regular")
api.AddUsersToGroup(usernames=[new_username], groupName=new_group_name)
api.AddGroupsToDomain(domainName=domain_name, groupNames=[new_group_name])

# Import content
api.WriteMessageToReservationOutput(reservationContext["id"], "Importing Content to new domain")
api_root_url = 'http://{0}:{1}/Api'.format(connectivityContext["serverAddress"], connectivityContext["qualiAPIPort"])

blueprints_to_export = [blueprint.Name for blueprint in api.GetDomainDetails("Master").Topologies]
blueprints_to_export_full_names = ["Master topologies\\" + blueprint for blueprint in blueprints_to_export]

api.AddTopologiesToDomain(domain_name, blueprints_to_export_full_names)
# TODO: Change hardcoded CP name to dynamically assumed name
api.AddResourcesToDomain(domain_name, ["AWS us-east-1"])

login_result = requests.put(api_root_url + "/Auth/Login", {"token": connectivityContext["adminAuthToken"], "domain": "Master"})
master_domain_authcode = "Basic " + login_result.content[1:-1]
export_result = requests.post(api_root_url + "/Package/ExportPackage", {"TopologyNames": blueprints_to_export}, headers={"Authorization": master_domain_authcode})

login_result = requests.put(api_root_url + "/Auth/Login", {"token": connectivityContext["adminAuthToken"], "domain": domain_name})
new_domain_authcode = "Basic " + login_result.content[1:-1]

import_result = requests.post(api_root_url + "/Package/ImportPackage", headers={"Authorization": new_domain_authcode}, files={'QualiPackage': export_result.content})
topologies_in_new_domain = [blueprint.Name for blueprint in api.GetDomainDetails(domain_name).Topologies]
api.RemoveTopologiesFromDomain(domain_name, ["Master topologies/Vanilla Operating Systems"])
if topologies_in_new_domain != blueprints_to_export:
	email_title = "CloudShell Trial: Failed to setup trial"
	email_body = "Failed to setup trail for {user} because there was an error during import of blueprints to the new domain".format(user=new_username)
	smtp_client.send_email(",".join([owner_email, admin_email]), email_title, email_body, False)
	api.WriteMessageToReservationOutput(reservationContext["id"], "Topologies not imported successfully, aborting trial creation")
	api.EndReservation(reservationContext["id"])

# Send Trial start notifications
api.WriteMessageToReservationOutput(reservationContext["id"], "Sending trial start notifications")

# Calculate reservation end time in miliseconds
reservation_details = api.GetReservationDetails(reservationContext["id"]).ReservationDescription
try:
	reservation_end_date = datetime.datetime.strptime(reservation_details.EndTime, "%d/%m/%Y %H:%M").replace(hour=0, minute=0, second=0, microsecond=0)
except ValueError:
	reservation_end_date = datetime.datetime.strptime(reservation_details.EndTime, "%m/%d/%Y %H:%M").replace(hour=0, minute=0, second=0, microsecond=0)
reservation_end_time_in_ms = int((reservation_end_date - datetime.datetime.utcfromtimestamp(0)).total_seconds() * 1000)

# Create Hubspot contact and enroll to Hubspot Workflow

hubspot_helper = Hubspot_API_Helper("cba66474-e4e4-4f5b-9b9b-35620577f343")
hubspot_helper.create_contact(first_name, last_name, email, company, phone)
hubspot_helper.change_contact_property(email, "cloudshell_trial_password", generated_password)
hubspot_helper.change_contact_property(email, "cloudshell_trial_end_date", str(reservation_end_time_in_ms))
hubspot_helper.change_contact_property(email, "cloudshell_trial_owner", owner_email)
hubspot_helper.enroll_contact_to_workflow(email, "1980406")

# Send E-mail to owner + admin
email_title = "CloudShell Trial: Trial setup complete"
email_body = "Setup of trial for {user} has been completed successfully".format(user=new_username)
smtp_client.send_email(",".join([owner_email, admin_email]), email_title, email_body, False)

api.AddPermittedUsersToReservation(reservationContext["id"], [owner_email])

api.WriteMessageToReservationOutput(reservationContext["id"], "Trial Started successfully!")
