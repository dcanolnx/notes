output "vpn_connection_id" {
  value = aws_vpn_connection.vpn.id
}

output "vgw_id" {
  value = aws_vpn_gateway.vgw.id
}

output "cgw_id" {
  value = aws_customer_gateway.cgw.id
}
output "aws_vpn_ip_address" {
  value = aws_vpn_connection.vpn.tunnel1_address
}

output "aws_vpn_preshared_key" {
  value = aws_vpn_connection.vpn.tunnel1_preshared_key
}
