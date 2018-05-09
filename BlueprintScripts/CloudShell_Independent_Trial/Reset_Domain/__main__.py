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

username = email

api = CloudShellAPISession(host=connectivityContext["serverAddress"], token_id=connectivityContext["adminAuthToken"], domain=reservationContext["domain"])

user_info = api.GetUserDetails(username)
group_name = user_info.Groups[0].Name
domain_name = group_name
domain_details = api.GetDomainDetails(domain_name)
domain_topologies_folder = "\\".join(domain_details.TopologiesFolder.split("\\")[1:])
master_domain_details = api.GetDomainDetails("Lead Master")
master_topologies_folder = "\\".join(master_domain_details.TopologiesFolder.split("\\")[1:])

blueprints_in_domain = [blueprint.Name for blueprint in domain_details.Topologies]
blueprints_in_master_domain = [blueprint.Name for blueprint in master_domain_details.Topologies]


# Necessary to comply with "RemoveTopologiesFromDomain" API - chain the topology full path to the topology name.
blueprints_to_remove = [master_topologies_folder + "\\" + blueprint_name if blueprint_name in blueprints_in_master_domain else domain_topologies_folder + "\\" + blueprint_name
						for blueprint_name in blueprints_in_domain]

api.RemoveTopologiesFromDomain(domain_name, blueprints_to_remove)

api_root_url = 'http://{0}:{1}/Api'.format(connectivityContext["serverAddress"], connectivityContext["qualiAPIPort"])
blueprints_to_export = [blueprint.Name for blueprint in api.GetDomainDetails("Lead Master").Topologies]
blueprints_to_export_full_names = ["Lead Master topologies\\" + blueprint for blueprint in blueprints_to_export]

api.AddTopologiesToDomain(domain_name, blueprints_to_export_full_names)

login_result = requests.put(api_root_url + "/Auth/Login", {"token": connectivityContext["adminAuthToken"], "domain": "Lead Master"})
master_domain_authcode = "Basic " + login_result.content[1:-1]

export_result = requests.post(api_root_url + "/Package/ExportPackage", {"TopologyNames": blueprints_to_export}, headers={"Authorization": master_domain_authcode})

login_result = requests.put(api_root_url + "/Auth/Login", {"token": connectivityContext["adminAuthToken"], "domain": domain_name})
new_domain_authcode = "Basic " + login_result.content[1:-1]

import_result = requests.post(api_root_url + "/Package/ImportPackage", headers={"Authorization": new_domain_authcode}, files={'QualiPackage': export_result.content})
topologies_in_new_domain = [blueprint.Name for blueprint in api.GetDomainDetails(domain_name).Topologies]
api.RemoveTopologiesFromDomain(domain_name, ["Master topologies/Vanilla Operating Systems"])
if topologies_in_new_domain != blueprints_to_export:
	# TODO: send e-mail to owner & admin
	api.WriteMessageToReservationOutput(reservationContext["id"], "Topologies not imported successfully, aborting trial creation")
	api.EndReservation(reservationContext["id"])

api.WriteMessageToReservationOutput(reservationContext["id"], "Trial Domain reset")
