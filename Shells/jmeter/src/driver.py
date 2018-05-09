from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadDetails, CancellationContext
from cloudshell.api.cloudshell_api import CloudShellAPISession
import os
import sys
import datetime
import requests
import shutil
import urllib
from paramiko import SSHClient, AutoAddPolicy
import traceback
from github import Github
from data_model import Jmeter # run 'shellfoundry generate' to generate data model classes


class JmeterDriver (ResourceDriverInterface):

	def __init__(self):
		"""
		ctor must be without arguments, it is created with reflection at run time
		"""
		pass

	def initialize(self, context):
		"""
		Initialize the driver session, this function is called everytime a new instance of the driver is created
		This is a good place to load and cache the driver configuration, initiate sessions etc.
		:param InitCommandContext context: the context the command runs on
		"""
		pass

	def cleanup(self):
		"""
		Destroy the driver session, this function is called everytime a driver instance is destroyed
		This is a good place to close any open sessions, finish writing to log files
		"""
		pass

	# <editor-fold desc="Discovery">

	def __initApiSession__(self, context):
		"""
		:param context: driver_context.ResourceCommandContext
		:return: 
		"""
		return CloudShellAPISession(host=context.connectivity.server_address, port=context.connectivity.cloudshell_api_port, token_id=context.connectivity.admin_auth_token, domain="Global")

	def _get_connected_entity_name(self, context):
		api = self.__initApiSession__(context)
		reservation_details = api.GetReservationDetails(context.reservation.reservation_id)
		connectors = reservation_details.ReservationDescription.Connectors
		connection = next(conn for conn in connectors if context.resource.name in conn.Source + conn.Target)
		target_name = connection.Source if connection.Target == context.resource.name else connection.Target
		api.WriteMessageToReservationOutput(context.reservation.reservation_id, "Found connected resource " + target_name)
		return target_name

	def run_test(self, context, test_name, target_resource_name, thread_count):
		"""		
		:type context ResourceCommandContext
		:param context: 
		:param test_name: 
		:return: 
		"""
		api = self.__initApiSession__(context)
		reservation_details = api.GetReservationDetails(context.reservation.reservation_id)
		jmeter_resource = Jmeter.create_from_context(context)
		current_timestamp = datetime.datetime.strftime(datetime.datetime.now(), "%m-%d_%H-%M")
		artifacts_folder_name = "artifacts-" + current_timestamp
		if not target_resource_name: target_resource_name = self._get_connected_entity_name(context)
		if target_resource_name in [res.Name for res in reservation_details.ReservationDescription.Resources]:
			target_resource_details = api.GetResourceDetails(target_resource_name)
			target_ip = target_resource_details.FullAddress
			target_port = next(attribute.Value for attribute in target_resource_details.ResourceAttributes if attribute.Name == "WWW_Port")
		else:
			target_service = next(service for service in reservation_details.ReservationDescription.Services if target_resource_name == service.Alias)
			target_service_attributes = {att.Name:att.Value for att in target_service.Attributes}
			target_ip = target_service_attributes["External_URL"]
			if target_ip.startswith("http://"): target_ip = target_ip[len("http://"):]
			target_port = 80
		
		test_url = jmeter_resource.tests_location + test_name + ".jmx"
		api.WriteMessageToReservationOutput(context.reservation.reservation_id, "Retrieving test: {0}".format(test_url))
		
		if os.path.isdir(artifacts_folder_name):
			shutil.rmtree(path=artifacts_folder_name, ignore_errors=True)

		os.mkdir(artifacts_folder_name)
		testfile = urllib.URLopener()
		testfile.retrieve(test_url, test_name + ".jmx")
		api.WriteMessageToReservationOutput(context.reservation.reservation_id, "Running Test '{0}' with {1} threads".format(test_name, thread_count))

		test_results_filename = None
		return_message = ""
		try:
			# Call the python executable running this driver to run the test.
			params_string = "target_ip,target_port\n{0},{1}".format(target_ip, target_port)
			with open(os.path.join(artifacts_folder_name, "config.csv"), mode="w") as config_file: config_file.write(params_string)

			ssh = SSHClient()
			ssh.load_system_host_keys()
			ssh.set_missing_host_key_policy(AutoAddPolicy())
			ssh.connect(hostname=context.resource.address, username=jmeter_resource.user, password=api.DecryptPassword(jmeter_resource.password).Value, timeout=300)
			sftp = ssh.open_sftp()
			sftp.put(os.path.join(artifacts_folder_name, "config.csv"), r"C:\JMeter\config.csv")
			sftp.put(test_name + ".jmx", r"C:\JMeter\{0}.jmx".format(test_name))
			stdin, stdout, stderr = ssh.exec_command(r"jmeter -Jparam_file=C:\JMeter\config.csv -Jthreads={0} -Jreport_file=C:\JMeter\report.csv -n -t c:\JMeter\{1}.jmx".format(thread_count, test_name))
			test_output = stdout.read()
			sftp.get(r"C:\JMeter\report.csv", os.path.join(artifacts_folder_name, "report.csv"))
			sftp.remove(r"C:\JMeter\report.csv")
			sftp.remove(r"C:\JMeter\config.csv")
			sftp.remove(r"C:\JMeter\{0}.jmx".format(test_name))
			sftp.close()
			ssh.close()

			with open(os.path.join(artifacts_folder_name, "test_output.txt"), mode="w") as output_file:
				output_file.write(test_output)
			
			return_message = "Test {test_name} Completed successfully, See report in Sandbox attachments".format(test_name=test_name)
		except Exception as ex:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			with open(os.path.join(artifacts_folder_name, "test_output.txt"), mode="w") as output_file:
				output_file.write("\n".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
			
			return_message = "Test {test_name} Exited with error, See report in Sandbox attachments".format(test_name=test_name)
		finally:
			test_results_filename = test_name + "-result-" + current_timestamp
			shutil.make_archive(base_name=test_results_filename, format="zip", root_dir=artifacts_folder_name)

			attach_file_result_code = self._attach_file_to_reservation(context, test_results_filename + ".zip", test_results_filename + ".zip")
			shutil.rmtree(path=artifacts_folder_name, ignore_errors=True)
			os.remove(test_name + ".jmx")
			if test_results_filename:
				os.remove(test_results_filename + ".zip")
			if not 200 <= attach_file_result_code < 300:
				return "Error Attaching File to reservation"
			else:
				return return_message

	def show_available_tests(self,context):
		jmeter_resource = Jmeter.create_from_context(context)
		if "github" in jmeter_resource.tests_location.lower():
			github_api = Github()
			test_location_path = jmeter_resource.tests_location.split(".com/")[1]
			(repo_name, container_name) = test_location_path.split("/master")
			container_name = container_name.replace('/','')
			repo = github_api.get_repo(repo_name)
			tests = repo.get_contents(container_name)
			return "<b>Available Tests:</b><br>" + "<br>".join((test.name.split('.')[0].encode("ascii") for test in tests))
		else:
			return "<b>Unable to retrieve test list for the current tests location</b>"

	def get_inventory(self, context):
		return AutoLoadDetails([],[])

	def _attach_file_to_reservation(self, context, filename, name_in_reservation):
		"""
		:type context ResourceCommandContext
		:param context: 
		:return: 
		"""
		api_base_url = "http://{0}:{1}/Api".format(context.connectivity.server_address, context.connectivity.quali_api_port)
		api = self.__initApiSession__(context)
		# DEBUG api.WriteMessageToReservationOutput(context.reservation.reservation_id, "api base url is " + api_base_url)

		login_result = requests.put(api_base_url + "/Auth/Login", {"token": context.connectivity.admin_auth_token, "domain": "Global"})
		authcode = "Basic " + login_result._content[1:-1]
		# DEBUG api.WriteMessageToReservationOutput(context.reservation.reservation_id, "Logged in with authcode" + authcode)

		attached_file = open(filename, "rb")
		attach_file_result = requests.post(api_base_url + "/Package/AttachFileToReservation", headers={"Authorization": authcode},
										   data={"reservationId": context.reservation.reservation_id, "saveFileAs": name_in_reservation, "overwriteIfExists": "True"},
										   files={'QualiPackage': attached_file})

		# DEBUG api.WriteMessageToReservationOutput(context.reservation.reservation_id, "Attach file result is " + str(attach_file_result.status_code))
		return attach_file_result.status_code
