import datetime
from time import sleep
from cloudshell.api.cloudshell_api import CloudShellAPISession, AttributeNameValue
from cloudshell.shell.core.driver_context import *
import boto3
import yaml

class CloudFront:
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

	def _wait_for_distribution_deployed(self, dist_id, cf_client):
		dist_details = cf_client.get_distribution(Id=dist_id)
		while dist_details["Distribution"]["Status"] == "InProgress":
			dist_details = cf_client.get_distribution(Id=dist_id)
			sleep(10)
		return

	def create_dist(self, context, elb_name):
		"""
		listeners: comma separated list of from_protocol:from_port->to_protocol:to_port (e.g. "HTTP:80->HTTP:8000,HTTPS:443->HTTPS:443"
		instance_ids: comma separated list of instance_ids to add to the ELB
		:type context: ResourceCommandContext
		:return: 
		"""
		api = self._init_cs_api(context)
		cf_client = self._get_amazon_session(context).client("cloudfront")
		elb_client = self._get_amazon_session(context).client("elb")

		reservation_tags =		[{"Key":"CreatedBy",	"Value":"Cloudshell"}]
		reservation_tags.append( {"Key":"ReservationId","Value":context.reservation.reservation_id})
		reservation_tags.append( {"Key":"Owner",		"Value":context.reservation.owner_user})
		reservation_tags.append( {"Key":"Domain",		"Value":context.reservation.domain})
		reservation_tags.append( {"Key":"Blueprint",	"Value":context.reservation.environment_name})
		
		elb_details = elb_client.describe_load_balancers(LoadBalancerNames=[elb_name])["LoadBalancerDescriptions"][0]

		call_ref = str(datetime.datetime.now())
		create_response = cf_client.create_distribution(DistributionConfig=
		{
			"CallerReference": call_ref, 
			"DefaultRootObject": "", 
			"Origins": 
			{ 
				"Quantity": 1, 
				"Items": [
				{
					"Id": elb_details["DNSName"].split('.')[0],
					"DomainName": elb_details["DNSName"], 
					"CustomOriginConfig": 
					{ 
						"HTTPPort": 80, 
						"HTTPSPort": 443, 
						"OriginProtocolPolicy": "http-only", 
						"OriginSslProtocols": { "Quantity": 4, "Items": ["SSLv3", "TLSv1", "TLSv1.1", "TLSv1.2"] }, 
						"OriginReadTimeout": 30, "OriginKeepaliveTimeout": 5 
					} 
				}, ] 
			}, 
			"DefaultCacheBehavior": 
			{ 
				"TargetOriginId": elb_details["DNSName"].split('.')[0], 
				"ForwardedValues": { "QueryString": True, "Cookies": {"Forward": "all"}, "Headers": {"Quantity": 0}, "QueryStringCacheKeys": {"Quantity": 1,"Items": ["*",]} }, 
				"TrustedSigners": {"Enabled":False, "Quantity": 0}, 
				"ViewerProtocolPolicy": "allow-all", 
				"MinTTL": 0, 
				"AllowedMethods": {"Quantity": 7, "Items": ["GET", "HEAD", "POST", "PUT", "PATCH", "OPTIONS", "DELETE"], "CachedMethods": {"Quantity": 3,"Items": ["GET", "HEAD", "OPTIONS"]}}, 
				"SmoothStreaming": False, 
				"DefaultTTL": 86400, 
				"MaxTTL": 31536000, 
				"Compress": True, 
			}, 
			"Comment": "", 
			"Logging": { "Enabled": False, "IncludeCookies": False, "Bucket": "", "Prefix": "" }, 
			"PriceClass": "PriceClass_All", 
			"Enabled": True, 
			"ViewerCertificate": 
			{ 
				"CloudFrontDefaultCertificate": True, 
				"SSLSupportMethod": "vip", 
				"MinimumProtocolVersion": "TLSv1", 
				"Certificate": "CloudFrontDefaultCertificatetrueCloudFrontDefaultCertificate", 
				"CertificateSource": "cloudfront" 
			}, 
			"Restrictions": { "GeoRestriction": { "RestrictionType": "none", "Quantity": 0, "Items": [] } }, 
			"IsIPV6Enabled": False 
			})

		api.WriteMessageToReservationOutput(context.reservation.reservation_id, "Waiting for CloudFront distribution to finish deployment, this may take up to 15 minutes...")
		api.SetServiceLiveStatus(context.reservation.reservation_id, context.resource.name, "In Progress", "Deployment in progress")
		self._wait_for_distribution_deployed(create_response["Distribution"]["Id"], cf_client)
		api.SetServiceLiveStatus(context.reservation.reservation_id, context.resource.name, "Online", "Deployment Complete")
		api.SetServiceAttributesValues(context.reservation.reservation_id, context.resource.name, 
			[AttributeNameValue("AWS CF ID", create_response["Distribution"]["Id"]), AttributeNameValue("External_URL", "http://" + create_response["Distribution"]["DomainName"])])
		return "CloudFront Distriubtion deployed successfully at:\n" + "http://" + create_response["Distribution"]["DomainName"]

	def get_cf_dist_details(self, context):
		cf_client = self._get_amazon_session(context).client("cloudfront")
		cf_details = cf_client.get_distribution(Id=context.resource.attributes["AWS CF ID"])
		return "CloudFront Distribution Details:\n" + yaml.safe_dump(cf_details["Distribution"], default_flow_style=False)

	def get_cf_access_details(self, context):
		cf_client = self._get_amazon_session(context).client("cloudfront")
		cf_details = cf_client.get_distribution(Id=context.resource.attributes["AWS CF ID"])
		return "http://" + cf_details["Distribution"]["DomainName"]

	def disable_cf_dist(self, context):
		api = self._init_cs_api(context)
		cf_client = self._get_amazon_session(context).client("cloudfront")
		dist_config = cf_client.get_distribution_config(Id=context.resource.attributes["AWS CF ID"])
		if dist_config["DistributionConfig"]["Enabled"] == False:
			return "The CloudFront Distribution is already disabled"
		else:
			dist_config["DistributionConfig"]["Enabled"] = False
			api.SetServiceLiveStatus(context.reservation.reservation_id, context.resource.name, "In Progress", "Disabling Distribution")
			update_request = cf_client.update_distribution(Id=context.resource.attributes["AWS CF ID"], IfMatch=dist_config["ETag"], DistributionConfig=dist_config["DistributionConfig"])
			self._wait_for_distribution_deployed(context.resource.attributes["AWS CF ID"], cf_client)
			api.SetServiceLiveStatus(context.reservation.reservation_id, context.resource.name, "Offline", "Distribution Disabled")
			return "Distribution disabled successfully"

	def enable_cf_dist(self, context):
		api = self._init_cs_api(context)
		cf_client = self._get_amazon_session(context).client("cloudfront")
		dist_config = cf_client.get_distribution_config(Id=context.resource.attributes["AWS CF ID"])
		if dist_config["DistributionConfig"]["Enabled"] == True:
			return "The CloudFront Distribution is already enabled"
		else:
			dist_config["DistributionConfig"]["Enabled"] = True
			update_request = cf_client.update_distribution(Id=context.resource.attributes["AWS CF ID"], IfMatch=dist_config["ETag"], DistributionConfig=dist_config["DistributionConfig"])
			api.SetServiceLiveStatus(context.reservation.reservation_id, context.resource.name, "In Progress", "Enabling Distribution")
			self._wait_for_distribution_deployed(context.resource.attributes["AWS CF ID"], cf_client)
			api.SetServiceLiveStatus(context.reservation.reservation_id, context.resource.name, "Online", "Distribution Enabled")
			return "Distribution enabled successfully"

	def delete_cf_dist(self, context):
		api = self._init_cs_api(context)
		cf_client = self._get_amazon_session(context).client("cloudfront")
		dist_config = cf_client.get_distribution_config(Id=context.resource.attributes["AWS CF ID"])
		delete_response = cf_client.delete_distribution(Id=context.resource.attributes["AWS CF ID"], IfMatch=dist_config["ETag"])
		api.SetServiceAttributesValues(context.reservation.reservation_id, context.resource.name, [AttributeNameValue("AWS CF ID", "")])
		return "Delete Load Balancer Response:\n" + yaml.safe_dump(delete_response, default_flow_style=False)