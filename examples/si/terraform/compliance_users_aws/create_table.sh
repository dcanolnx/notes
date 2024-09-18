#!/bin/bash

# Configuración de la base de datos
DB_HOST="terraform-20240312111052491700000003.cfnzdjkdnxha.eu-west-2.rds.amazonaws.com" #Change after terraform apply
DB_USER="stratioadmin"
DB_PASS="" # PASSBOLT
DB_NAME="compliance"
DB_TABLE="compliance_info"

# SQL command to create the table with the appropriate columns
SQL_COMMAND="CREATE TABLE IF NOT EXISTS $DB_TABLE (
  id INT AUTO_INCREMENT PRIMARY KEY,
  hostname VARCHAR(255),
  uptime_system VARCHAR(255),
  uptime_system_minutes INT,
  status_eea VARCHAR(50),
  uptime_eea INT,
  status_eraagent VARCHAR(50),
  uptime_eraagent INT,
  status_wazuh VARCHAR(50),
  uptime_wazuh INT,
  date_collected DATETIME
);"

# Execute the MySQL command
mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME -e "$SQL_COMMAND"