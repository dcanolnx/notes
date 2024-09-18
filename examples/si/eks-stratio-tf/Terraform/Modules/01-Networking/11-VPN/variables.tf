variable "vpc_id" {

}

variable "customer_gateway_ip" {
  description = "Public IP address of the customer gateway"
  type        = string
}

variable "bgp_asn" {
  description = "BGP ASN of the customer gateway (65000 by default)"
  type        = number
  default     = 65000
}

variable "name" {

}
variable "vpc_cidr" {
  description = "Public IP address of the customer gateway"
  type        = string
}

variable "enviroment" {

}