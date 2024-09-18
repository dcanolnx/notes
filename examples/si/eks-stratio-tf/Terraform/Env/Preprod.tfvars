### Providers ###
aws_credentials = {
  aws_region = "eu-west-3"
  path       = "terraform-preprod.tfstate"
}


### Networking ###

vpc = {
  vpc-stratio-preprod = {
    cidr_block = "10.120.204.0/23"
  }
}

private_subnets = {
  subnet-stratio-preprod-pvt-a = {
    vpc_name                = "vpc-stratio-preprod"
    cidr_block              = "10.120.204.0/25"
    availability_zone       = "eu-west-3a"
    map_public_ip_on_launch = false
  }
  subnet-stratio-preprod-pvt-b = {
    vpc_name                = "vpc-stratio-preprod"
    cidr_block              = "10.120.204.128/25"
    availability_zone       = "eu-west-3b"
    map_public_ip_on_launch = false
  }
  #subnet-stratio-preprod-pvt-c = {
  #vpc_name            = "vpc-preprod"
  #cidr_block         = "10.120.222.0/24"
  #availability_zone   = "eu-south-2c"
  #map_public_ip_on_launch = false
  #}
}

public_subnets = {
  subnet-stratio-preprod-pub-a = {
    vpc_name                = "vpc-stratio-preprod"
    cidr_block              = "10.120.205.0/25"
    availability_zone       = "eu-west-3a"
    map_public_ip_on_launch = true
  }
  subnet-stratio-preprod-pub-b = {
    vpc_name                = "vpc-stratio-preprod"
    cidr_block              = "10.120.205.128/25"
    availability_zone       = "eu-west-3b"
    map_public_ip_on_launch = false
  }
  #subnet-stratio-preprod-public-c = {
  #  vpc_name            = "vpc-preprod"
  #  cidr_block         = "10.120.222.0/24"
  #  availability_zone   = "eu-south-2c"
  #  map_public_ip_on_launch = false
  #}
}

eip = {
  eip-stratio-preprod-nat-prod-a = {}
}

internet_gateway = {
  igw-stratio-preprod = {
    vpc_name = "vpc-stratio-preprod"
  }
}


vpn_connection = {
  vpn-stratio-preprod = {
    vpc_name            = "vpc-stratio-preprod"
    customer_gateway_ip = "62.97.72.54"
  }
}


nat = {
  nat-stratio-preprod-pvt-a = {
    connectivity_type = "public"
    allocation_id     = "eip-stratio-preprod-nat-prod-a"
    subnet_id         = "subnet-stratio-preprod-pub-a"
  }
}

route_table = {
  rtbl-stratio-preprod-pvt-subnets = {
    vpc_name         = "vpc-stratio-preprod"
    route_table_name = "rtbl-stratio-preprod-pvt-subnets"
  }
  rtbl-stratio-preprod-pub-subnets = {
    vpc_name         = "vpc-stratio-preprod"
    route_table_name = "rtbl-stratio-preprod-pub-subnets"
  }
}

private_routes = {
  rtbl-stratio-preprod-pvt-subnets = {
    destination_cidr_block = "0.0.0.0/0"
    nat_gateway_name       = "nat-stratio-preprod-pvt-a"
  }
}
vpn_name_for_vgw = "vpn-stratio-preprod"

public_routes = {
  rtbl-stratio-preprod-pub-subnets = {
    destination_cidr_block = "0.0.0.0/0"
    igw_name               = "igw-stratio-preprod"
  }
}

route_table_association_pvt = {
  association_1 = {
    subnet_name      = "subnet-stratio-preprod-pvt-a"
    route_table_name = "rtbl-stratio-preprod-pvt-subnets"
  }
  association_2 = {
    subnet_name      = "subnet-stratio-preprod-pvt-b"
    route_table_name = "rtbl-stratio-preprod-pvt-subnets"
  }
}

route_table_association_pub = {
  association_1 = {
    subnet_name      = "subnet-stratio-preprod-pub-a"
    route_table_name = "rtbl-stratio-preprod-pub-subnets"
  }
  association_2 = {
    subnet_name      = "subnet-stratio-preprod-pub-b"
    route_table_name = "rtbl-stratio-preprod-pub-subnets"
  }
}
### SG EKS ###

security_groups = {
  sg_eks_preprod_genia = {
    vpc_name         = "vpc-stratio-preprod"
    description_rule = "Security group Cluster EKS"
    cidr_blocks_in   = ["0.0.0.0/0"]
    from_port_in     = 443
    to_port_in       = 443
    protocol_in      = "tcp"
    from_port_out    = 0
    to_port_out      = 0
    protocol_out     = "-1"
    cidr_blocks_out  = ["0.0.0.0/0"]
  }

}

### EKS Cluster ###

eks = {
  eksPreProductionCluster = {
    name                      = "eks-stratio-preprod"
    vpc_name                  = "vpc-stratio-preprod"
    cluster_security_group_id = "sg_stratio_cluster_eks"
    endpoint_private_access   = "true"
    endpoint_public_access    = "false"
    version-eks               = "1.28"
    subnet_name-a = {
      subnet_name = "subnet-stratio-preprod-pvt-a"
    }
    subnet_name-b = {
      subnet_name = "subnet-stratio-preprod-pvt-b"
    }
    subnet_name-c = {
      subnet_name = "subnet-stratio-preprod-pvt-c"
    }
    authentication_mode                         = "API_AND_CONFIG_MAP"
    bootstrap_cluster_creator_admin_permissions = "true"

  }
}

eks-addon = {
  addon_1 = {
    addon_name   = "vpc-cni"
    cluster_name = "eksPreProductionCluster"
  }
  addon_2 = {
    addon_name   = "coredns"
    cluster_name = "eksPreProductionCluster"
  }
  addon_3 = {
    addon_name   = "kube-proxy"
    cluster_name = "eksPreProductionCluster"
  }
  addon_4 = {
    addon_name   = "eks-pod-identity-agent"
    cluster_name = "eksPreProductionCluster"
  }
  addon_5 = {
    addon_name   = "aws-mountpoint-s3-csi-driver"
    cluster_name = "eksPreProductionCluster"
  }
  addon_6 = {
    addon_name   = "aws-ebs-csi-driver"
    cluster_name = "eksPreProductionCluster"
  }
}

eks-nodes = {
  t3_xlarge = {
    cluster_name = "eksPreProductionCluster"
    #node_group_name = "eks-preprod-genaia-nodes"
    ami_type       = "AL2_x86_64" #Amazon Linux 2
    capacity_type  = "ON_DEMAND"
    disk_size      = "50"
    instance_types = ["t3.xlarge"]
    labels = {
      environment = "stratio-prepro"
    }
    tags = {
      Environment = "stratio-prepro"
    }
    subnets_name = {
      subnet_name-a = {
        subnet_name = "subnet-stratio-preprod-pvt-a"
      }
      subnet_name-b = {
        subnet_name = "subnet-stratio-preprod-pvt-b"
      }
      subnet_name-c = {
        subnet_name = "subnet-stratio-preprod-pvt-c"
      }
    }
    desired_size    = 3
    max_size        = 4
    min_size        = 2
    max_unavailable = 1
  }
}



subnet_group = {
  db_subnet_preprod_pvt = {
    subnets_name = {
      subnet_name-a = {
        subnet_name = "subnet-stratio-preprod-pvt-a"
      }
      subnet_name-b = {
        subnet_name = "subnet-stratio-preprod-pvt-b"
      }
      subnet_name-c = {
        subnet_name = "subnet-stratio-preprod-pvt-c"
      }
    }
  }
}

