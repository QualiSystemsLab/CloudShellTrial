from cloudshell.workflow.orchestration.sandbox import Sandbox, Components


def config_web_servers(sandbox, components):
	"""
		:param Sandbox sandbox:
		:param Components components:
		:return:
	"""
	build_number = sandbox.global_inputs["Build Number"]
	app_colors = ["ffebd1", "ffd1d1", "d1fffb", "d1d9ff", "d1ffda", "ffffff"]
	api = sandbox.automation_api
	components.refresh_components(sandbox)
	application_db_address = components.get_apps_by_name_contains("MySQL DB")[0].deployed_app.FullAddress

	api.WriteMessageToReservationOutput(reservationId=sandbox.id, message="Configuring My App Web Servers with build {}...".format(build_number))

	web_servers = components.get_apps_by_name_contains("My App Web Server")
	for server, app_color in zip(web_servers, app_colors):
		sandbox.apps_configuration.set_config_param(server, 'database_server_address', application_db_address)
		sandbox.apps_configuration.set_config_param(server, 'app_color', app_color)

	sandbox.apps_configuration.apply_apps_configurations(web_servers)

	api.WriteMessageToReservationOutput(reservationId=sandbox.id, message='Configuring HA Proxy')

	ha_proxy = components.get_apps_by_name_contains('HA Proxy')[0]
	my_app_addresses = [web_server.deployed_app.FullAddress for web_server in web_servers]
	my_app_addresses_string = ",".join(my_app_addresses)
	sandbox.apps_configuration.set_config_param(ha_proxy, 'web_server_addresses', my_app_addresses_string)
	sandbox.apps_configuration.apply_apps_configurations([ha_proxy])

	api.WriteMessageToReservationOutput(reservationId=sandbox.id, message='Sandbox setup finished successfully')