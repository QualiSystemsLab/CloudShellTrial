from cloudshell.workflow.orchestration.sandbox import Sandbox, Components
import requests
from time import sleep


def config_web_servers(sandbox, components):
	"""
	    :param Sandbox sandbox:
	    :param Components components:
	    :return:
    """
	build_number = sandbox.global_inputs["Build Number"]
	api = sandbox.automation_api
	components.refresh_components(sandbox)
	application_db_address = components.get_apps_by_name_contains("MySQL DB")[0].deployed_app.FullAddress

	api.WriteMessageToReservationOutput(reservationId=sandbox.id, message="Configuring My App Web Servers with build {}...".format(build_number))

	web_servers = components.get_apps_by_name_contains("My App Web Server")
	for server in web_servers:
		sandbox.apps_configuration.set_config_param(server, 'database_server_address', application_db_address)

	sandbox.apps_configuration.apply_apps_configurations(web_servers)

	api.WriteMessageToReservationOutput(reservationId=sandbox.id, message='Configuring Selenium Grid...')

	selenium_hub_address = components.get_apps_by_name_contains('Selenium Hub')[0].deployed_app.FullAddress
	selenium_nodes = components.get_apps_by_name_contains("Selenium Node")
	for selenium_node in selenium_nodes:
		sandbox.apps_configuration.set_config_param(selenium_node, 'hub_server_address', selenium_hub_address)

	sandbox.apps_configuration.apply_apps_configurations(selenium_nodes)
	web_server_port = next(attribute.Value for attribute in web_servers[0].app_request.app_resource.LogicalResource.Attributes if attribute.Name == "WWW_Port")
	wait_time = 0
	while not (200 <= requests.get("http://" + web_servers[0].deployed_app.FullAddress + ":" + web_server_port).status_code < 300):
		sleep(5)
		wait_time += 5
		if wait_time > 300:
			raise Exception("Timeout while waiting for My App availability")
