import subprocess
import sys
import os
import datetime
import requests
import shutil
import urllib
from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.shell.core.context import ResourceCommandContext, InitCommandContext


class SeleniumHub:
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

	def __initApiSession__(self, context):
		"""
		
		:param context: ResourceCommandContext
		:return: 
		"""
		return CloudShellAPISession(host=context.connectivity.server_address, port=context.connectivity.cloudshell_api_port, token_id=context.connectivity.admin_auth_token, domain="Global")

	def run_selenium_test(self, context, test_name, target_resource_name):
		"""
		
		:type context ResourceCommandContext
		:param context: 
		:param test_name: 
		:return: 
		"""
		api = self.__initApiSession__(context)
		target_resource_details = api.GetResourceDetails(target_resource_name)
		target_url = target_resource_details.FullAddress + ':' + next(attribute.Value for attribute in target_resource_details.ResourceAttributes if attribute.Name == "WWW_Port")
		test_url = context.resource.attributes["Tests Location"] + test_name + ".py"
		api.WriteMessageToReservationOutput(context.reservation.reservation_id, "About to retrieve {0}".format(test_url))

		os.mkdir('artifacts')
		testfile = urllib.URLopener()
		testfile.retrieve(test_url, test_name + ".py")
		api.WriteMessageToReservationOutput(context.reservation.reservation_id, "Running Test script {1} with parameters {2}".format(
			 sys.executable, test_name + '.py', 'hub={0}'.format(context.resource.address) + ' target={0}'.format(target_url)))

		test_results_filename = None
		try:
			test_output = subprocess.check_output([sys.executable, test_name + ".py", "hub={0}".format(context.resource.address), "target={0}".format(target_url)], stderr=subprocess.STDOUT)
			with open(os.path.join("artifacts", "test_output.txt"), mode="w") as output_file:
				output_file.write(test_output)
			
			return_message = "Test passed, check attachments for output"
		except subprocess.CalledProcessError as error:
			with open(os.path.join("artifacts", "test_output.txt"), mode="w") as output_file:
				output_file.write("[{0}] {1}:\n{2}".format(error.returncode, error.message + '\n' + error.output))
			
			return_message = "Test failed, check attachment for output" 
		finally:
			test_results_filename = test_name + "-result-" + datetime.datetime.strftime(datetime.datetime.now(), "%m-%d_%H-%M")
			shutil.make_archive(base_name=test_results_filename, format="zip", root_dir='artifacts')

			attach_file_result_code = self._attach_file_to_reservation(context, test_results_filename + ".zip", test_results_filename + ".zip")
			shutil.rmtree(path="artifacts", ignore_errors=True)
			os.remove(test_name + ".py")
			if test_results_filename:
				os.remove(test_results_filename + ".zip")
			if not 200 <= attach_file_result_code < 300:
				return "Error Attaching File to reservation"
			else:
				return return_message

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
