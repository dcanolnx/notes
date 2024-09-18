resource "aws_db_instance" "this" {
  allocated_storage       = var.allocated_storage
  identifier              = var.name
  db_name                 = var.db_name
  engine                  = var.engine
  engine_version          = var.engine_version
  instance_class          = var.instance_class
  username                = var.username
  password                = var.password
  skip_final_snapshot     = var.skip_final_snapshot
  backup_retention_period = var.backup_retention_period
  backup_window           = "01:00-02:00"
  publicly_accessible     = "false"

  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = [var.vpc_security_group_ids]

  tags = {
    Name = var.name
  }

}