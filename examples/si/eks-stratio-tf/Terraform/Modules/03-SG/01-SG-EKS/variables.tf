variable "vpc_id" {
  description = "VPC ID"
  type        = any
}

## ingress
variable "description_rule" {
  description = "protocol traffic in"
  type        = string
}
variable "cidr_blocks_in" {
  description = "cidr_blocks_out"
  type        = list(string)
}
variable "from_port_in" {
  description = "from port traffic in"
  type        = number
}
variable "to_port_in" {
  description = "to port traffic in"
  type        = number
}
variable "protocol_in" {
  description = "protocol traffic in"
  type        = string
}

## Egress

variable "from_port_out" {
  description = "from port traffic out"
  type        = number
}
variable "to_port_out" {
  description = "to port traffic out"
  type        = number
}
variable "protocol_out" {
  description = "protocol traffic out"
  type        = string
}
variable "cidr_blocks_out" {
  description = "cidr_blocks_out"
  type        = list(string)
}

variable "name" {
  description = "SG EKS"
  type        = string
}