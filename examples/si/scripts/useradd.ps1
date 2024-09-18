# Variables
$username = "Sistemas"
$description = "Usuario para gestion remota"
$password = ConverTo-SecureString "SupePassword123!" -AsPlainText -Force

# Crear usuario
New-LocalUser -Name $username -Password $password -FullName &username -Description $description

# Añadir grupo administradores, revisar si el idioma de la instalacion
Add-LocalGroupMember -Groups "Administadores" -Member $username
