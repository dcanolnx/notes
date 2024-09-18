resource "aws_backup_selection" "this" {
  iam_role_arn = var.iam_role_arn
  name         = var.name
  plan_id      = var.plan_id

  resources = [
    var.db_rds
  ]
}