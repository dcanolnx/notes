resource "aws_route" "nat" {
  route_table_id         = var.route_table_id
  destination_cidr_block = var.destination_cidr_block
  nat_gateway_id         = var.nat_gateway_id
}

resource "aws_route" "vgw" {
  route_table_id         = var.route_table_id
  destination_cidr_block = "10.110.0.0/16" # Asegúrate de que el CIDR sea correcto
  gateway_id             = var.vgw_id
}
