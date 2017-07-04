from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow

sandbox = Sandbox()
if len(sandbox.components.apps) > 7:
	raise ValueError("Cannot setup a Sandbox with more than 7 apps in Trial Version, please remove some apps from the Blueprint and try again")

DefaultSetupWorkflow().register(sandbox)

sandbox.execute_setup()
