resource "aws_backup_vault" "this" {
  name        = var.name
  kms_key_arn = var.kms_key_arn
}