resource "aws_eip" "this" {
  instance = null # Asigna null para indicar que la IP no está asociada a ninguna instancia
  tags = {
    Name = var.name
  }
}