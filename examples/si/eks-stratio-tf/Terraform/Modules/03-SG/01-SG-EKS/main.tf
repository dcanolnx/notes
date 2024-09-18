resource "aws_security_group" "this" {
  vpc_id = var.vpc_id

  ingress {
    description = var.description_rule
    cidr_blocks = var.cidr_blocks_in
    from_port   = var.from_port_in
    to_port     = var.to_port_in
    protocol    = var.protocol_in
  }
  egress {
    from_port   = var.from_port_out
    to_port     = var.to_port_out
    protocol    = var.protocol_out
    cidr_blocks = var.cidr_blocks_out
  }

  tags = {
    Name = var.name
  }
}