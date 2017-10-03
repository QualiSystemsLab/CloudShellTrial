from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow
from custom_configuration import config_web_servers

sandbox = Sandbox()
if len(sandbox.components.apps) > 7:
	raise ValueError("Cannot setup a Sandbox with more than 7 apps in Trial Version, please remove some apps from the Blueprint and try again")


DefaultSetupWorkflow().register(sandbox, enable_configuration=False)

sandbox.workflow.add_to_configuration(config_web_servers, sandbox.components)
sandbox.execute_setup()

