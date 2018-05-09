from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.setup.default_setup_orchestrator import DefaultSetupWorkflow
from cloudshelltrialutils.trial_utils import TrialUtils

sandbox = Sandbox()
trial_utils = TrialUtils(sandbox.automation_api)
print trial_utils.get_quali_owner(sandbox.reservationContextDetails.domain)