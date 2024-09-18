variable "db_username" {
  description = "Nombre de usuario de la base de datos RDS"
  type        = string
}

variable "db_password" {
  description = "Contraseña de la base de datos RDS"
  type        = string
  sensitive   = true
}
