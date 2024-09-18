terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.34.0"
    }

    fortios = {
      source  = "registry.terraform.io/fortinetdev/fortios"
      version = "1.19.0"
    }
  }
}

locals {
  enviroment = "AWS-PRE-"
}

provider "aws" {
  # Configuration options
  region = var.aws_credentials.aws_region
}

# Configure the FortiOS Provider
provider "fortios" {
  hostname = "deuterio.int.stratio.com"
  token    = "cfz4m1cjQ1bk8kk0z73j5ytwbQs3Qg"
  insecure = true
}

module "VPC" {
  source     = "./Modules/01-Networking/1-VPC"
  for_each   = var.vpc
  cidr_block = each.value.cidr_block
  name       = each.key
}

module "Private_Subnets" {
  source                  = "./Modules/01-Networking/2-Subnets"
  for_each                = var.private_subnets
  vpc_id                  = module.VPC[each.value.vpc_name].vpc_id
  cidr_block              = each.value.cidr_block
  availability_zone       = each.value.availability_zone
  map_public_ip_on_launch = each.value.map_public_ip_on_launch
  name                    = each.key
}
module "Public_Subnets" {
  source                  = "./Modules/01-Networking/2-Subnets"
  for_each                = var.public_subnets
  vpc_id                  = module.VPC[each.value.vpc_name].vpc_id
  cidr_block              = each.value.cidr_block
  availability_zone       = each.value.availability_zone
  map_public_ip_on_launch = each.value.map_public_ip_on_launch
  name                    = each.key
}


module "Elastic_IP" {
  source   = "./Modules/01-Networking/8-EIP"
  for_each = var.eip
  name     = each.key
}

module "Internet_Gateway" {
  source   = "./Modules/01-Networking/9-IGW"
  for_each = var.internet_gateway
  name     = each.key
  vpc_id   = module.VPC[each.value.vpc_name].vpc_id
}

module "vpn_connection" {
  source              = "./Modules/01-Networking/11-VPN"
  for_each            = var.vpn_connection
  vpc_id              = module.VPC[each.value.vpc_name].vpc_id
  vpc_cidr            = module.VPC[each.value.vpc_name].cidr_block
  name                = each.key
  customer_gateway_ip = each.value.customer_gateway_ip
  enviroment          = local.enviroment
  providers = {
    fortios = fortios
  }
}


module "NAT_Gateway" {
  source            = "./Modules/01-Networking/3-NGW"
  for_each          = var.nat
  connectivity_type = each.value.connectivity_type
  allocation_id     = module.Elastic_IP[each.value.allocation_id].eip_id
  subnet_id         = module.Public_Subnets[each.value.subnet_id].subnet_id
  name              = each.key
}

module "Route_Table" {
  source   = "./Modules/01-Networking/4-RT"
  for_each = var.route_table
  vpc_id   = module.VPC[each.value.vpc_name].vpc_id
  name     = each.key
}

module "private_routes" {
  source                 = "./Modules/01-Networking/5-Routes_Privates"
  for_each               = var.private_routes
  route_table_id         = module.Route_Table[each.key].route_table_id
  destination_cidr_block = each.value.destination_cidr_block
  nat_gateway_id         = module.NAT_Gateway[each.value.nat_gateway_name].nat_gateway_id
  vgw_id                 = module.vpn_connection[var.vpn_name_for_vgw].vgw_id
}
module "public_routes" {
  source                 = "./Modules/01-Networking/5-Routes_Public"
  for_each               = var.public_routes
  route_table_id         = module.Route_Table[each.key].route_table_id
  destination_cidr_block = each.value.destination_cidr_block
  gateway_id             = module.Internet_Gateway[each.value.igw_name].igw_id
}

module "route_table_association_private" {
  source         = "./Modules/01-Networking/6-Routes_Association"
  for_each       = var.route_table_association_pvt
  subnet_id      = module.Private_Subnets[each.value.subnet_name].subnet_id
  route_table_id = module.Route_Table[each.value.route_table_name].route_table_id
}

module "route_table_association_public" {
  source         = "./Modules/01-Networking/6-Routes_Association"
  for_each       = var.route_table_association_pub
  subnet_id      = module.Public_Subnets[each.value.subnet_name].subnet_id
  route_table_id = module.Route_Table[each.value.route_table_name].route_table_id
}

module "SG-EKS" {
  source           = "./Modules/03-SG/01-SG-EKS"
  for_each         = var.security_groups
  vpc_id           = module.VPC[each.value.vpc_name].vpc_id
  name             = each.key
  description_rule = each.value.description_rule
  #Ingress
  cidr_blocks_in = each.value.cidr_blocks_in
  from_port_in   = each.value.from_port_in
  to_port_in     = each.value.to_port_in
  protocol_in    = each.value.protocol_in
  #Egress
  from_port_out   = each.value.from_port_out
  to_port_out     = each.value.to_port_out
  protocol_out    = each.value.protocol_out
  cidr_blocks_out = each.value.cidr_blocks_out
}

resource "aws_iam_role" "eksPreproductionRole" {
  name = "eks-cluster-preproduction-stratio"

  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
POLICY
}

resource "aws_iam_role_policy_attachment" "eksPreproductionRole-AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eksPreproductionRole.name
}

module "EKS_Cluster" {
  source   = "./Modules/04-EKS/01-EKS_Cluster"
  for_each = var.eks
  name     = each.key
  role_arn = aws_iam_role.eksPreproductionRole.arn
  #vpc_id                    = module.VPC[each.value.vpc_name].vpc_id
  #cluster_security_group_id = module.SG-EKS[each.value.cluster_security_group_id].id
  endpoint_private_access = each.value.endpoint_private_access
  endpoint_public_access  = each.value.endpoint_public_access
  version-eks             = each.value.version-eks
  subnet_ids = [
    module.Private_Subnets[each.value.subnet_name-a.subnet_name].subnet_id,
    module.Private_Subnets[each.value.subnet_name-b.subnet_name].subnet_id,
  ]
  authentication_mode                         = each.value.authentication_mode
  bootstrap_cluster_creator_admin_permissions = each.value.bootstrap_cluster_creator_admin_permissions

  #depends_on = [module.SG-EKS]
}

module "EKS_Addon" {
  source       = "./Modules/04-EKS/02-EKS_Addon"
  for_each     = var.eks-addon
  cluster_name = each.value.cluster_name
  addon_name   = each.value.addon_name

  depends_on = [module.EKS_Cluster]

}



module "EKS_Node_Group" {
  source          = "./Modules/04-EKS/03-EKS-Nodes"
  for_each        = var.eks-nodes
  cluster_name    = each.value.cluster_name
  node_group_name = each.key

  ami_type        = each.value.ami_type
  capacity_type   = each.value.capacity_type
  disk_size       = each.value.disk_size
  instance_types  = each.value.instance_types
  desired_size    = each.value.desired_size
  max_size        = each.value.max_size
  min_size        = each.value.min_size
  max_unavailable = each.value.max_unavailable
  subnet_ids = [
    module.Private_Subnets[each.value.subnets_name.subnet_name-a.subnet_name].subnet_id,
    module.Private_Subnets[each.value.subnets_name.subnet_name-b.subnet_name].subnet_id,
  ]
}


#
#data "aws_iam_policy" "ebs_csi_policy" {
#arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
#}
#
#module "irsa-ebs-csi" {
#source  = "terraform-aws-modules/iam/aws//modules/iam-assumable-role-with-oidc"
#version = "4.7.0"
#
#create_role                   = true
#role_name                     = "AmazonEKSTFEBSCSIRole-${module.eks.cluster_name}"
#provider_url                  = module.eks.oidc_provider
#role_policy_arns              = [data.aws_iam_policy.ebs_csi_policy.arn]
#oidc_fully_qualified_subjects = ["system:serviceaccount:kube-system:ebs-csi-controller-sa"]
#}

