from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow
from custom_configuration import config_web_servers
from cloudshelltrialutils.trial_utils import TrialUtils
from cloudshelltrialutils import Hubspot_API_Helper
import traceback

hubspot_helper = Hubspot_API_Helper("cba66474-e4e4-4f5b-9b9b-35620577f343")
sandbox = Sandbox()
sandbox.suppress_exceptions = False
if len(sandbox.components.apps) > 7:
	raise ValueError("Cannot setup a Sandbox with more than 7 apps in Trial Version, please remove some apps from the Blueprint and try again")

trial_utils = TrialUtils(sandbox.automation_api)
trial_owner = trial_utils.get_quali_owner(sandbox.reservationContextDetails.domain)
sandbox.automation_api.AddPermittedUsersToReservation(sandbox.id, [trial_owner])
DefaultSetupWorkflow().register(sandbox, enable_configuration=False)

sandbox.workflow.add_to_configuration(config_web_servers, sandbox.components)

if "@" in sandbox.reservationContextDetails.owner_user:
	hubspot_helper.increment_trial_sandbox_count(sandbox.reservationContextDetails.owner_user)
	hubspot_helper.update_contact_initial_login(sandbox.reservationContextDetails.owner_user, None)

try:
	sandbox.execute_setup()
except Exception as e:
	trial_utils.send_error_to_owner(e, traceback.format_exc(), sandbox.reservationContextDetails.owner_user, trial_owner, sandbox.id)
	raise RuntimeError("An error has occurred during setup of the sandbox, please contact your trial owner at {0} for assistance".format(trial_owner))
