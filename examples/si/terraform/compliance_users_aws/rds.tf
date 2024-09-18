resource "aws_db_instance" "compliance_db" {
  allocated_storage    = 20
  storage_type         = "gp2"
  engine               = "mysql"
  engine_version       = "8.0" 
  instance_class       = "db.t3.micro"
  db_name              = "compliance"
  username             = var.db_username
  password             = var.db_password
  parameter_group_name = "default.mysql8.0"
  skip_final_snapshot  = true
  publicly_accessible  = true
  vpc_security_group_ids = [aws_security_group.my_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.my_db_subnet_group.name
}

resource "aws_db_subnet_group" "my_db_subnet_group" {
  name       = "my_db_subnet_group"
  subnet_ids = [aws_subnet.my_subnet1.id, aws_subnet.my_subnet2.id]

  tags = {
    Name = "my_db_subnet_group"
  }
}
