from cloudshell.api.cloudshell_api import CloudShellAPISession

class TrialUtils(object):
	def __init__(self, cs_api_session):
		self.cs_api = cs_api_session
		pass

	def get_quali_owner(self, domain_name):
		all_groups_details = self.api.GetGroupsDetails()
		my_group_details = next(group for group in all_groups_details.Groups if group.Name == domain_name)
		quali_owner = next(user.Name for user in my_group_details.Users if "quali.com" in user.Name)		
		return quali_owner
