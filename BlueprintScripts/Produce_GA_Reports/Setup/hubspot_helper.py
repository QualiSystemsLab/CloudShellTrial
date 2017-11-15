import requests
import json

class Hubspot_API_Helper:
	def __init__(self, api_key):
		self.api_key = api_key
		self.api_base = "https://api.hubapi.com"

	def create_contact(self, fname, lname, email, company, phone):
		post_result = requests.post(self.api_base + "/contacts/v1/contact", params={"hapikey":self.api_key}, 
									json={"properties":[{"property":"email", "value":email}, 
														{"property":"firstname", "value":fname}, 
														{"property":"lastname", "value":lname}, 
														{"property":"company", "value":company}, 
														{"property":"phone", "value":phone}]})
		return post_result

	def enroll_contact_to_workflow(self, contact_email, workflow_id):
		return requests.post(self.api_base + "/automation/v2/workflows/{w_id}/enrollments/contacts/{email}".format(w_id=workflow_id, email=contact_email), params={"hapikey":self.api_key})

	def unenroll_contact_from_workflow(self, contact_email, workflow_id):
		return requests.delete(self.api_base + "/automation/v2/workflows/{w_id}/enrollments/contacts/{email}".format(w_id=workflow_id, email=contact_email), params={"hapikey":self.api_key})		

	def change_contact_property(self, contact_email, property_name, property_value):
		return requests.post(self.api_base + "/contacts/v1/contact/email/{email}/profile".format(email=contact_email), params={"hapikey":self.api_key}, 
				json={"properties":[{"property":property_name, "value":property_value}]})

	def get_contact_owner_email(self, contact_email):
		get_result = requests.get(self.api_base + "/contacts/v1/contact/email/" + contact_email + "/profile", params={"hapikey":self.api_key})
		json_result = json.loads(get_result.content)
		hubspot_owner_email = ""
		if "hubspot_owner_id" in json_result["properties"]:
			hubspot_owner_id = int(json_result["properties"]["hubspot_owner_id"]["value"])
			get_owners_result = requests.get(self.api_base + "/owners/v2/owners", params={"hapikey":self.api_key})
			owner_json_result = json.loads(get_owners_result.content)
			hubspot_owner_infos = [owner for owner in owner_json_result if owner["ownerId"] == hubspot_owner_id]
			if hubspot_owner_infos:
				hubspot_owner_email = hubspot_owner_infos[0]["email"]

		return hubspot_owner_email
		