import datetime
from cloudshell.api.cloudshell_api import CloudShellAPISession, AttributeNameValue
from cloudshell.shell.core.context import ResourceCommandContext, InitCommandContext
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import httplib2
from quali_api_helper import QualiAPISession
from email_helper import SMTPClient

class GoogleAnalyticsService:
	def __init__(self):
		pass

	def initialize(self, context):
		"""
		:type context InitCommandContext
		:param context: 
		:return: 
		"""

	def cleanup(self):
		pass

	def _init_cs_api(self, context):
		"""
		:type context ResourceRemoteCommandContext
		"""
		return CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)

	def generate_ga_user_report(self, context, start_date, end_date, cloudshell_username):
		"""		
		:type context ResourceCommandContext
		:param context: 
		:param test_name: 
		:return: 
		"""
		scopes = ['https://www.googleapis.com/auth/analytics.readonly']
		key_file = r'c:\Quali\key_file.json'
		google_api_credentials = ServiceAccountCredentials.from_json_keyfile_name(key_file, scopes)
		authorized_credentials = google_api_credentials.authorize(httplib2.Http())
		service = build("analytics", "v3", authorized_credentials)

		ids = context.resource.attributes["Google Analytics View ID"]
		metrics = ','.join(["ga:timeOnPage"])
		dimensions = ','.join(["ga:browser", "ga:pageTitle", "ga:dimension1", "ga:date", "ga:dateHourMinute", "ga:pagePath"])
		filters="ga:dimension1=={}".format(cloudshell_username)
		query = service.data().ga().get(start_date=start_date, end_date=end_date, metrics=metrics, dimensions=dimensions, ids=ids, filters=filters, sort="ga:dateHourMinute")
		result = query.execute()

		#date_index = result["columnHeaders"].index(next(item for item in result["columnHeaders"] if "date" in item["name"]))
		#hour_index = result["columnHeaders"].index(next(item for item in result["columnHeaders"] if "hour" in item["name"]))
		#minute_index = result["columnHeaders"].index(next(item for item in result["columnHeaders"] if "minute" in item["name"]))
		#sorted_rows = sorted(result["rows"], key=lambda row: (row[date_index+1], row[hour_index+1], row[minute_index+1]))

		if "rows" in result:
			report = ''.join([header["name"].split(':')[-1] + "," if "dimension1" not in header["name"] else "username," for header in result["columnHeaders"]])
			report += "\n"
			report += ''.join(''.join([value + ',' for value in row]) + '\n' for row in result["rows"])
			return report
		else:
			return ""

	def attach_ga_user_report_to_reservation(self, context, start_date, end_date, cloudshell_username):
		"""		
		:type context ResourceCommandContext
		:param context: 
		:param test_name: 
		:return: 
		"""
		report_content = self.generate_ga_user_report(context, start_date, end_date, cloudshell_username)
		if report_content:
			quali_api = QualiAPISession(host=context.connectivity.server_address, domain='Global', token_id=context.connectivity.admin_auth_token, port=context.connectivity.quali_api_port)

			current_timestamp = datetime.datetime.strftime(datetime.datetime.now(), "%m-%d_%H-%M")
			filename = "GA_Report_" + current_timestamp + ".csv"
			with open(filename, 'w') as csv_file:
				csv_file.write(report_content)
			quali_api.AttachFileToReservation(context.reservation.reservation_id, filename, filename, True)
			return filename + " was attached to the reservation successfully, please refresh the page to view the attachment"
		else:
			return "No activity for user"
		

	def email_ga_user_report_to_contact(self, context, start_date, end_date, cloudshell_username, email_address, email_title):
		"""		
		:type context ResourceCommandContext
		:param context: 
		:param test_name: 
		:return: 
		"""
		api = CloudShellAPISession(host=context.connectivity.server_address, port=context.connectivity.cloudshell_api_port, token_id=context.connectivity.admin_auth_token, domain="Global")
		admin_email = api.GetUserDetails("admin").Email
		smtp_resource = api.FindResources('Mail Server', 'SMTP Server').Resources[0]
		smtp_resource_details = api.GetResourceDetails(smtp_resource.FullPath)
		smtp_attributes = {attribute.Name: attribute.Value if attribute.Type != "Password" else api.DecryptPassword(attribute.Value).Value for attribute in smtp_resource_details.ResourceAttributes}
		smtp_client = SMTPClient(smtp_attributes["User"], smtp_attributes["Password"], smtp_resource_details.Address, smtp_attributes["Port"])
		report_content = self.generate_ga_user_report(context, start_date, end_date, cloudshell_username)
		if report_content:
			current_timestamp = datetime.datetime.strftime(datetime.datetime.now(), "%m-%d_%H-%M")
			filename = "GA_Report_" + current_timestamp + ".csv"
			with open(filename, 'w') as csv_file:
				csv_file.write(report_content)
			smtp_client.send_email(",".join([email_address, admin_email]), email_title, "See attached user activity report", False, [filename])
			return "User activity report emailed successfully"
		else:
			smtp_client.send_email(",".join([email_address, admin_email]), email_title, "No activity reported to date for this user", False)



