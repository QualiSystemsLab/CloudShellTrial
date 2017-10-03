from cloudshell.api.cloudshell_api import InputNameValue
from cloudshell.workflow.orchestration.sandbox import Sandbox, Components
import datetime
import requests
from time import sleep


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

	api.WriteMessageToReservationOutput(reservationId=sandbox.id, message="Configuring Elastic Load Balancer...")
	web_servers = components.get_apps_by_name_contains("My App Web Server")
	my_app_instance_ids = ','.join([my_app.deployed_app.VmDetails.UID for my_app in web_servers])

	elb_name = "My-App-ELB" + datetime.datetime.strftime(datetime.datetime.now(), "%H-%M-%S")
	command_inputs = {"elb_name":elb_name, "listeners":"HTTP:80->HTTP:8000", "instance_ids":my_app_instance_ids, "use_cookie":"True"}
	command_inputs = [InputNameValue(k, v) for k, v in command_inputs.items()]
	api.ExecuteCommand(sandbox.id, "AWS Elastic Load Balancer", "Service", "create_elb", command_inputs, True)

	api.WriteMessageToReservationOutput(reservationId=sandbox.id, message="Configuring My App Web Servers with build {}...".format(build_number))
	for server, app_color in zip(web_servers, app_colors):
		sandbox.apps_configuration.set_config_param(server, 'database_server_address', application_db_address)
		sandbox.apps_configuration.set_config_param(server, 'app_color', app_color)

	sandbox.apps_configuration.apply_apps_configurations(web_servers)

	api.WriteMessageToReservationOutput(reservationId=sandbox.id, message="Configuring CloudFront Distribution...")
	api.ExecuteCommand(sandbox.id, "AWS CloudFront", "Service", "create_dist", [InputNameValue("elb_name", elb_name)], True)
	sandbox.components.refresh_components(sandbox)
	cf_url = next(attribute.Value for attribute in sandbox.components.services["AWS CloudFront"].Attributes if attribute.Name == "External_URL")
	wait_time = 0
	while not (200 <= requests.get("http://" + cf_url).status_code < 300):
		sleep(5)
		wait_time += 5
		if wait_time > 300:
			raise Exception("Timeout while waiting for My App availability")
