import datetime
from cloudshell.api.cloudshell_api import CloudShellAPISession, AttributeNameValue
from cloudshell.shell.core.context import ResourceCommandContext, InitCommandContext
import boto3
from botocore.exceptions import ClientError
from time import sleep
import yaml

class ElasticLoadBalancer:
	def __init__(self):
		pass

	def initialize(self, context):
		"""
		:type context InitCommandContext
		:param context: 
		:return: 
		"""

	def cleanup(self):
		pass

	def _get_amazon_session(self, context):
		api = self._init_cs_api(context)

		aws_cp_details = api.GetResourceDetails(context.resource.attributes["Cloud Provider"], True)
		aws_cp_attributes_dict = {attribute.Name: attribute.Value for attribute in aws_cp_details.ResourceAttributes}
		access_key = api.DecryptPassword(aws_cp_attributes_dict["AWS Access Key ID"]).Value
		secret_access_key = api.DecryptPassword(aws_cp_attributes_dict["AWS Secret Access Key"]).Value
		session = boto3.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_access_key, region_name=aws_cp_attributes_dict["Region"])

		return session

	def _init_cs_api(self, context):
		"""
		:type context ResourceRemoteCommandContext
		"""
		return CloudShellAPISession(context.connectivity.server_address, domain="Global", token_id=context.connectivity.admin_auth_token, port=context.connectivity.cloudshell_api_port)

	def _get_instance_subnets(self, context, instance_ids):
		ec2_client = self._get_amazon_session(context).client("ec2")
		describe_result = ec2_client.describe_instances(InstanceIds=instance_ids)
		return [reservation["Instances"][0]["SubnetId"] for reservation in describe_result["Reservations"]]

	def _get_instance_vpc(self, context, instance_id):
		ec2_client = self._get_amazon_session(context).client("ec2")
		describe_result = ec2_client.describe_instances(InstanceIds=[instance_id])
		return describe_result["Reservations"][0]["Instances"][0]["VpcId"]

	def create_elb(self, context, elb_name, listeners, use_cookie, instance_ids):
		"""
		listeners: comma separated list of from_protocol:from_port->to_protocol:to_port (e.g. "HTTP:80->HTTP:8000,HTTPS:443->HTTPS:443"
		instance_ids: comma separated list of instance_ids to add to the ELB
		:type context: ResourceCommandContext
		:return: 
		"""
		api = self._init_cs_api(context)
		elb_client = self._get_amazon_session(context).client("elb")
		ec2_client = self._get_amazon_session(context).client("ec2")

		listeners_list = []
		instance_ids = instance_ids.split(',')
		for listener_request in listeners.split(','):
			(request_from, request_to) = listener_request.split('->')
			(request_from_protocol, request_from_port) = request_from.split(':')
			(request_to_protocol, request_to_port) = request_to.split(':')
			listeners_list.append({"Protocol":request_from_protocol, "LoadBalancerPort":int(request_from_port), "InstanceProtocol":request_to_protocol, "InstancePort":int(request_to_port)})

		subnets_in_elb = self._get_instance_subnets(context, instance_ids)

		reservation_tags =		[{"Key":"CreatedBy",	"Value":"Cloudshell"}]
		reservation_tags.append( {"Key":"ReservationId","Value":context.reservation.reservation_id})
		reservation_tags.append( {"Key":"Owner",		"Value":context.reservation.owner_user})
		reservation_tags.append( {"Key":"Domain",		"Value":context.reservation.domain})
		reservation_tags.append( {"Key":"Blueprint",	"Value":context.reservation.environment_name})

		creation_result = elb_client.create_load_balancer(LoadBalancerName=elb_name,Listeners=listeners_list, Subnets=subnets_in_elb, Tags=reservation_tags)
		register_result = elb_client.register_instances_with_load_balancer(LoadBalancerName=elb_name, Instances=[{"InstanceId":instance_id} for instance_id in instance_ids])
		elb_healthcheck_config = {"Target":"TCP:" + str(listeners_list[0]["InstancePort"]), "Interval":30, "Timeout":5, "UnhealthyThreshold":2, "HealthyThreshold":10 }
		configure_result = elb_client.configure_health_check(LoadBalancerName=elb_name, HealthCheck=elb_healthcheck_config)

		create_sg_result = ec2_client.create_security_group(GroupName=elb_name + "SG", VpcId=self._get_instance_vpc(context, instance_ids[0]), Description="SG for ELB HTTP Access")
		group_available = False
		while not group_available:
			try:
				sg_description = ec2_client.describe_security_groups(GroupIds=[create_sg_result["GroupId"]])
				group_available = True
			except ClientError as error:
				sleep(2)
		create_tags_result = ec2_client.create_tags(Resources=[create_sg_result["GroupId"]], Tags=reservation_tags)
		for listener in listeners_list:
			auth_in_result = ec2_client.authorize_security_group_ingress(GroupId=create_sg_result["GroupId"], IpProtocol="tcp", FromPort=listener["LoadBalancerPort"], ToPort=listener["LoadBalancerPort"], CidrIp="0.0.0.0/0")

		apply_result = elb_client.apply_security_groups_to_load_balancer(LoadBalancerName=elb_name, SecurityGroups=[create_sg_result["GroupId"]])

		if use_cookie.lower() == "true":
			elb_client.create_lb_cookie_stickiness_policy(LoadBalancerName=elb_name, PolicyName="StickinessPolicy")
			for listener in listeners_list:
				elb_client.set_load_balancer_policies_of_listener(LoadBalancerName=elb_name, LoadBalancerPort=listener["LoadBalancerPort"], PolicyNames=["StickinessPolicy"])
		
		api.SetServiceLiveStatus(context.reservation.reservation_id, context.resource.name, "Online", "Load Balancer Created Successfully")
		api.SetServiceAttributesValues(context.reservation.reservation_id, context.resource.name, 
			[AttributeNameValue("AWS ELB Name", elb_name), AttributeNameValue("External_URL", creation_result["DNSName"])])
		return "Elastic Load Balancer created successfully at:\n" + "http://" + creation_result["DNSName"] + "\nThis address may take a few minutes to become available due to DNS propagation"

	def get_elb_dns(self, context):
		elb_client = self._get_amazon_session(context).client("elb")
		elb_details = elb_client.describe_load_balancers(LoadBalancerNames=[context.resource.attributes["AWS ELB Name"]])
		return "http://" + elb_details["LoadBalancerDescriptions"][0]["DNSName"]
	
	def add_instances_to_elb(self, context, instance_ids):
		elb_client = self._get_amazon_session(context).client("elb")
		register_result = elb_client.register_instances_with_load_balancer(LoadBalancerName=elb_name, Instances=[{"InstanceId":instance_id} for instance_id in instance_ids.split(',')])
		return "Load Balancer instance registration result:\n" + yaml.safe_dump(register_result, default_flow_style=False)

	def get_elb_details(self, context):
		elb_client = self._get_amazon_session(context).client("elb")
		elb_details = elb_client.describe_load_balancers(LoadBalancerNames=[context.resource.attributes["AWS ELB Name"]])
		return "Load Balancer Details:\n" + yaml.safe_dump(elb_details["LoadBalancerDescriptions"][0], default_flow_style=False)

	def delete_elb(self, context):
		api = self._init_cs_api(context)
		elb_client = self._get_amazon_session(context).client("elb")
		delete_response = elb_client.delete_load_balancer(LoadBalancerName=context.resource.attributes["AWS ELB Name"])
		api.SetServiceLiveStatus(context.reservation.reservation_id, context.resource.name, "Offline", "Load Balancer Delted Successfully")
		api.SetServiceAttributesValues(context.reservation.reservation_id, context.resource.name, [AttributeNameValue("AWS ELB Name", "")])
		return "Delete Load Balancer Response:\n" + yaml.safe_dump(delete_response, default_flow_style=False)