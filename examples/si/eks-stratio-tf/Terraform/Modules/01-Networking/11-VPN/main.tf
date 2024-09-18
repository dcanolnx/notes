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
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

resource "random_password" "preshared_key" {
  length           = 16
  special          = false
  override_special = "_." // Only allow underscore and period as special characters
}
resource "aws_vpn_gateway" "vgw" {
  vpc_id = var.vpc_id
  tags = {
    Name = var.name
  }
}

resource "aws_customer_gateway" "cgw" {
  bgp_asn    = var.bgp_asn
  ip_address = var.customer_gateway_ip
  type       = "ipsec.1"
  tags = {
    Name = "TF Stratio"
  }
}

resource "aws_vpn_connection" "vpn" {
  customer_gateway_id = aws_customer_gateway.cgw.id
  vpn_gateway_id      = aws_vpn_gateway.vgw.id
  type                = "ipsec.1"
  static_routes_only  = true

  tunnel1_preshared_key                = random_password.preshared_key.result
  tunnel1_ike_versions                 = ["ikev2"]
  tunnel1_phase1_encryption_algorithms = ["AES256"]
  tunnel1_phase1_dh_group_numbers      = [20]
  tunnel1_phase1_integrity_algorithms  = ["SHA2-256"]
  tunnel1_phase2_dh_group_numbers      = [20]
  tunnel1_phase2_integrity_algorithms  = ["SHA2-256"]
  tunnel1_phase2_encryption_algorithms = ["AES256"]


  tunnel2_preshared_key                = random_password.preshared_key.result
  tunnel2_ike_versions                 = ["ikev2"]
  tunnel2_phase1_encryption_algorithms = ["AES256"]
  tunnel2_phase1_dh_group_numbers      = [20]
  tunnel2_phase1_integrity_algorithms  = ["SHA2-256"]
  tunnel2_phase2_dh_group_numbers      = [20]
  tunnel2_phase2_integrity_algorithms  = ["SHA2-256"]
  tunnel2_phase2_encryption_algorithms = ["AES256"]

  tags = {
    Name = var.name
  }
}




resource "fortios_vpnipsec_phase1interface" "vpn1_phase1" {
  name         = "${var.enviroment}T1F1"
  comments     = "${var.name}T1F1"
  interface    = "wan2"
  peertype     = "any"
  proposal     = "aes256-sha256"
  dhgrp        = 20
  ike_version  = 2
  nattraversal = "disable"
  keylife      = 28800
  remote_gw    = aws_vpn_connection.vpn.tunnel1_address
  psksecret    = random_password.preshared_key.result
  type         = "static"
}




resource "fortios_vpnipsec_phase1interface" "vpn2_phase1" {
  name         = "${var.enviroment}T2F1"
  comments     = "${var.name}T2F1"
  interface    = "wan2" #Si no estan las dos en Colt no va
  peertype     = "any"
  proposal     = "aes256-sha256"
  dhgrp        = 20
  ike_version  = 2
  nattraversal = "disable"
  keylife      = 28800
  remote_gw    = aws_vpn_connection.vpn.tunnel2_address
  psksecret    = random_password.preshared_key.result
  type         = "static"
}

#Fases 2 de ambas vpn y su parte en aws

#LABS
resource "aws_vpn_connection_route" "stratio-servers" {
  destination_cidr_block = "10.200.0.0/16"
  vpn_connection_id      = aws_vpn_connection.vpn.id
}

resource "fortios_vpnipsec_phase2interface" "vpn1_phase2_1" {
  name           = "${var.enviroment}T1F2-1 Labs"
  phase1name     = fortios_vpnipsec_phase1interface.vpn1_phase1.name
  depends_on     = [fortios_vpnipsec_phase1interface.vpn1_phase1]
  proposal       = "aes256-sha256"
  src_subnet     = "10.200.0.0 255.255.0.0"
  dst_subnet     = "10.120.204.0 255.255.254.0"
  dhgrp          = 20
  keylifeseconds = 3600
}


resource "fortios_vpnipsec_phase2interface" "vpn2_phase2_1" {
  name           = "${var.enviroment}T2F2-1 Labs"
  phase1name     = fortios_vpnipsec_phase1interface.vpn2_phase1.name
  depends_on     = [fortios_vpnipsec_phase1interface.vpn2_phase1]
  proposal       = "aes256-sha256"
  src_subnet     = "10.200.0.0 255.255.0.0"
  dst_subnet     = "10.120.204.0 255.255.254.0"
  dhgrp          = 20
  keylifeseconds = 3600
}

#VPN Employees

resource "aws_vpn_connection_route" "stratio-vpn" {
  destination_cidr_block = "10.110.0.0/24"
  vpn_connection_id      = aws_vpn_connection.vpn.id
}



resource "fortios_vpnipsec_phase2interface" "vpn1_phase2_2" {
  name           = "${var.enviroment}T1F2-2 VPN Employees"
  phase1name     = fortios_vpnipsec_phase1interface.vpn1_phase1.name
  depends_on     = [fortios_vpnipsec_phase1interface.vpn1_phase1]
  proposal       = "aes256-sha256"
  src_subnet     = "10.110.0.0 255.255.255.0"
  dst_subnet     = local.ip_and_mask
  dhgrp          = 20
  keylifeseconds = 3600
}
resource "fortios_vpnipsec_phase2interface" "vpn2_phase2_2" {
  name           = "${var.enviroment}T2F2-2 VPN Employees"
  phase1name     = fortios_vpnipsec_phase1interface.vpn2_phase1.name
  depends_on     = [fortios_vpnipsec_phase1interface.vpn2_phase1]
  proposal       = "aes256-sha256"
  src_subnet     = "10.110.0.0 255.255.255.0"
  dst_subnet     = local.ip_and_mask
  dhgrp          = 20
  keylifeseconds = 3600
}


locals {
  ip_address  = cidrhost(var.vpc_cidr, 0)                  // Obtiene la dirección IP base de la red CIDR.
  subnet_mask = cidrnetmask(var.vpc_cidr)                  // Calcula la máscara de subred a partir de la notación CIDR.
  ip_and_mask = "${local.ip_address} ${local.subnet_mask}" // Combina ambas en una sola cadena.
}

output "ip_and_subnet_mask" {
  value = local.ip_and_mask
}

resource "fortios_firewall_address" "address" {
  name    = "${var.enviroment} ADDRESS"
  subnet  = local.ip_and_mask
  type    = "ipmask"
  comment = var.name
}

resource "fortios_router_static" "static_route1" {
  dst     = fortios_firewall_address.address.subnet
  device  = fortios_vpnipsec_phase1interface.vpn1_phase1.name
  comment = "TF - ${var.enviroment} Route 1"
}

resource "fortios_router_static" "static_route2" {
  dst     = fortios_firewall_address.address.subnet
  device  = fortios_vpnipsec_phase1interface.vpn2_phase1.name
  comment = "TF - ${var.enviroment} Route 2"
}


resource "random_integer" "random_number1" {
  min = 500
  max = 1000
}
resource "random_integer" "random_number2" {
  min = 500
  max = 1000
}
resource "random_integer" "random_number3" {
  min = 500
  max = 1000
}
resource "random_integer" "random_number4" {
  min = 500
  max = 1000
}

resource "fortios_firewall_policy" "rule1" {
  action             = "accept"
  logtraffic         = "utm"
  name               = "TF - ${var.enviroment} T1 R1"
  policyid           = random_integer.random_number1.result
  schedule           = "always"
  wanopt             = "disable"
  wanopt_detection   = "active"
  wanopt_passive_opt = "default"
  wccp               = "disable"
  webcache           = "disable"
  webcache_https     = "disable"
  wsso               = "enable"

  dstaddr {
    name = "${var.enviroment} ADDRESS"
  }

  dstintf {
    name = fortios_vpnipsec_phase1interface.vpn1_phase1.name
  }

  service {
    name = "ALL"
  }
  srcaddr {
    name = "Net_VPN-SSL_Employees_10.110.0.0/22"
  }
  groups {
    name = "LDAP_Users"
  }

  srcintf {
    name = "wan2"
  }
}

resource "fortios_firewall_policy" "rule2" {
  action             = "accept"
  logtraffic         = "utm"
  name               = "TF - ${var.enviroment} T1 R2 "
  policyid           = random_integer.random_number2.result
  schedule           = "always"
  wanopt             = "disable"
  wanopt_detection   = "active"
  wanopt_passive_opt = "default"
  wccp               = "disable"
  webcache           = "disable"
  webcache_https     = "disable"
  wsso               = "enable"

  dstaddr {
    name = "${var.enviroment} ADDRESS"
  }

  dstintf {
    name = fortios_vpnipsec_phase1interface.vpn1_phase1.name
  }

  service {
    name = "ALL"
  }
  srcaddr {
    name = "IPs_VPN-SSL_Employees_10.110.0.102-199"
  }
  srcaddr {
    name = "Net_VPN-SSL_Employees-Sysadmin_10.110.0.0/27"
  }
  groups {
    name = "LDAP_Users"
  }
  groups {
    name = "LDAP_Sistemas"
  }
  srcintf {
    name = "ssl.root"
  }
}


resource "fortios_firewall_policy" "rule3" {
  action             = "accept"
  logtraffic         = "utm"
  name               = "TF - ${var.enviroment} T2 R1"
  policyid           = random_integer.random_number3.result
  schedule           = "always"
  wanopt             = "disable"
  wanopt_detection   = "active"
  wanopt_passive_opt = "default"
  wccp               = "disable"
  webcache           = "disable"
  webcache_https     = "disable"
  wsso               = "enable"

  dstaddr {
    name = "${var.enviroment} ADDRESS"
  }

  dstintf {
    name = fortios_vpnipsec_phase1interface.vpn2_phase1.name
  }

  service {
    name = "ALL"
  }
  srcaddr {
    name = "Net_VPN-SSL_Employees_10.110.0.0/22"
  }
  groups {
    name = "LDAP_Users"
  }

  srcintf {
    name = "wan2"
  }
}

resource "fortios_firewall_policy" "rule4" {
  action             = "accept"
  logtraffic         = "utm"
  name               = "TF - ${var.enviroment} T2 R2 "
  policyid           = random_integer.random_number4.result
  schedule           = "always"
  wanopt             = "disable"
  wanopt_detection   = "active"
  wanopt_passive_opt = "default"
  wccp               = "disable"
  webcache           = "disable"
  webcache_https     = "disable"
  wsso               = "enable"

  dstaddr {
    name = "${var.enviroment} ADDRESS"
  }

  dstintf {
    name = fortios_vpnipsec_phase1interface.vpn2_phase1.name
  }

  service {
    name = "ALL"
  }
  srcaddr {
    name = "IPs_VPN-SSL_Employees_10.110.0.102-199"
  }
  srcaddr {
    name = "Net_VPN-SSL_Employees-Sysadmin_10.110.0.0/27"
  }
  groups {
    name = "LDAP_Users"
  }
  groups {
    name = "LDAP_Sistemas"
  }
  srcintf {
    name = "ssl.root"
  }
}

