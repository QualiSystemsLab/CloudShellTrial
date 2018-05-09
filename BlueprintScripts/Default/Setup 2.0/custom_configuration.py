from cloudshell.workflow.orchestration.sandbox import Sandbox, Components
import requests
from time import sleep


def wait_for_webservers(sandbox, components):
	"""
		:param Sandbox sandbox:
		:param Components components:
		:return:
	"""
	build_number = sandbox.global_inputs["Build Number"]
	api = sandbox.automation_api
	components.refresh_components(sandbox)

	api.WriteMessageToReservationOutput(reservationId=sandbox.id, message="Configuring My App with build {}...".format(build_number))

	web_servers = components.get_apps_by_name_contains("My App")
	if web_servers:
		web_server_port = next(attribute.Value for attribute in web_servers[0].app_request.app_resource.LogicalResource.Attributes if attribute.Name == "WWW_Port")
		web_server_details = api.GetResourceDetails(web_servers[0].deployed_app.Name)
		web_server_public_ip = next(att.Value for att in web_server_details.ResourceAttributes if att.Name == "Public IP")
		wait_time = 0
		my_app_available = False
		while not my_app_available:
			try:
				get_result = requests.get("http://" + web_server_public_ip + ":" + web_server_port)
				my_app_available = (200 <= get_result.status_code < 300)
			except requests.ConnectionError:
				sleep(5)
				wait_time += 5

			if wait_time > 300:
				raise Exception("Timeout while waiting for My App availability")
