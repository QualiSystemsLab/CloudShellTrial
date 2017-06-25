import requests

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
		return requests.post(self.api_base + "/automation/v2/workflows/{w_id}/enrollments/contacts/{email}".format(w_id=workflow_id, email=contact_email), 
							params={"hapikey":self.api_key})

	def unenroll_contact_from_workflow(self, contact_email, workflow_id):
		return requests.delete(self.api_base + "/automation/v2/workflows/{w_id}/enrollments/contacts/{email}".format(w_id=workflow_id, email=contact_email), 
							params={"hapikey":self.api_key})		

	def change_contact_property(self, contact_email, property_name, property_value):
		post_result = requests.post(self.api_base + "/contacts/v1/contact/email/{email}/profile".format(email=contact_email), 
							params={"hapikey":self.api_key}, json={"properties":[{"property":property_name, "value":property_value}]})
