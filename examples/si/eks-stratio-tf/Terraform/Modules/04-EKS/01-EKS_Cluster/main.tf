resource "aws_eks_cluster" "this" {
  name     = var.name
  role_arn = var.role_arn
  vpc_config {
    #    vpc_id                    = var.vpc_id
    #cluster_security_group_id = var.cluster_security_group_id
    endpoint_private_access = var.endpoint_private_access
    endpoint_public_access  = var.endpoint_public_access
    subnet_ids              = var.subnet_ids
  }
  version = var.version-eks
  access_config {
    authentication_mode                         = var.authentication_mode
    bootstrap_cluster_creator_admin_permissions = var.bootstrap_cluster_creator_admin_permissions
  }
}

