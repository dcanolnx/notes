resource "aws_backup_plan" "this" {
  name = var.name

  rule {
    rule_name         = var.rule_name
    target_vault_name = var.target_vault_name
    schedule          = var.schedule

    lifecycle {
      delete_after = var.delete_after
    }
  }
}