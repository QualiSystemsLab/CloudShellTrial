from cloudshell.api.cloudshell_api import CloudShellAPISession
from email_helper import SMTPClient

class TrialUtils(object):
	def __init__(self, cs_api_session):
		self.cs_api = cs_api_session
		pass

	def get_quali_owner(self, domain_name):
		all_groups_details = self.cs_api.GetGroupsDetails()
		try:
			my_group_details = next(group for group in all_groups_details.Groups if group.Name == domain_name)
		except StopIteration:
			my_group_details = next(group for group in all_groups_details.Groups if group.Name == "System Administrators")
		quali_owner = next(user.Name for user in my_group_details.Users if "quali.com" in user.Name)		
		return quali_owner

	def get_smtp_client(self):
		# Get SMTP Details from Resource
		smtp_resource = self.cs_api.FindResources('Mail Server', 'SMTP Server').Resources[0]
		smtp_resource_details = self.cs_api.GetResourceDetails(smtp_resource.Name)
		smtp_attributes = {attribute.Name: attribute.Value if attribute.Type != "Password" else self.cs_api.DecryptPassword(attribute.Value).Value for attribute in smtp_resource_details.ResourceAttributes}
		smtp_client = SMTPClient(smtp_attributes["User"], smtp_attributes["Password"], smtp_resource_details.Address, smtp_attributes["Port"], "trial@quali.com")
		return smtp_client

	def send_error_to_owner(self, exception, exception_traceback, trial_user, trial_owner, sandbox_id):
		smtp_client = self.get_smtp_client()
		email_body = "{0}: {1}\nSee traceback below:\n\n{2}".format(type(exception).__name__, exception.message, exception_traceback)
		admin_email = self.cs_api.GetUserDetails("admin").Email
		smtp_client.send_email(",".join([trial_owner, admin_email]), "An error has occurred in {0}'s sandbox {1}".format(trial_user, sandbox_id), email_body, False)
		