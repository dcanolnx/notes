resource "aws_nat_gateway" "this" {
  connectivity_type = var.connectivity_type
  allocation_id     = var.allocation_id
  subnet_id         = var.subnet_id
  tags = {
    Name = var.name
  }
}