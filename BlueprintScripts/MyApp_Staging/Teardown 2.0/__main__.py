from cloudshell.workflow.orchestration.sandbox import Sandbox
from cloudshell.workflow.orchestration.teardown.default_teardown_orchestrator import DefaultTeardownWorkflow

sandbox = Sandbox()

DefaultTeardownWorkflow().register(sandbox)
api = sandbox.automation_api
api.WriteMessageToReservationOutput(reservationId=sandbox.id, message='Tearing down CloudFront Distribution...')
api.ExecuteCommand(sandbox.id, "AWS CloudFront", "Service", "disable_cf_dist")
api.ExecuteCommand(sandbox.id, "AWS CloudFront", "Service", "delete_cf_dist")
api.RemoveServicesFromReservation(sandbox.id, ["AWS CloudFront"])

api.WriteMessageToReservationOutput(reservationId=sandbox.id, message='Tearing down Elastic Load Balancer...')
api.ExecuteCommand(sandbox.id, "AWS Elastic Load Balancer", "Service", "delete_elb")
api.RemoveServicesFromReservation(sandbox.id, ["AWS Elastic Load Balancer"])

sandbox.execute_teardown()
