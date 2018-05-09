import requests
import json
import datetime

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

	def get_contact_property(self, contact_email, property_name):
		contact_details = requests.get(self.api_base + "/contacts/v1/contact/email/{email}/profile".format(email=contact_email), params={"hapikey":self.api_key})
		contact_details_json = json.loads(contact_details.content)
		return contact_details_json["properties"][property_name]["value"] if property_name in contact_details_json["properties"] else None

	def increment_trial_sandbox_count(self, trial_user_email):
		sandbox_count = self.get_contact_property(trial_user_email, "cloudshell_trial_sandbox_count")
		if sandbox_count:
			new_sandbox_count = int(sandbox_count) + 1
		else:
			new_sandbox_count = str(1)
		self.change_contact_property(trial_user_email, "cloudshell_trial_sandbox_count", new_sandbox_count)

	def update_contact_initial_login(self, contact_email, login_datetime):
		if not login_datetime:
			today = datetime.datetime.today()
			today_midnight = datetime.datetime(today.year, today.month, today.day)
			login_datetime_in_ms = int((today_midnight - datetime.datetime.utcfromtimestamp(0)).total_seconds() * 1000)
		else:
			login_datetime_in_ms = int((login_datetime - datetime.datetime.utcfromtimestamp(0)).total_seconds() * 1000)
		current_contact_initial_login_date = self.get_contact_property(contact_email, "cloudshell_trial_initial_login")
		if not current_contact_initial_login_date:
			self.change_contact_property(contact_email, "cloudshell_trial_initial_login", login_datetime_in_ms)

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
		