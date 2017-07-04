from cloudshell.workflow.orchestration.sandbox import Sandbox, Components


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

	sandbox.apps_configuration.apply_apps_configurations(selenium_nodes )

	api.WriteMessageToReservationOutput(reservationId=sandbox.id, message='Sandbox setup finished successfully')