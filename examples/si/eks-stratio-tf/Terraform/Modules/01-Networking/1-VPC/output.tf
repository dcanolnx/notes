output "vpc_id" {
  value = aws_vpc.this.id
}

output "cidr_block" {
  description = "The CIDR block of the VPC"
  value       = aws_vpc.this.cidr_block # Assuming `aws_vpc.this` is how your VPC resource is defined
}
