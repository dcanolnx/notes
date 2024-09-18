#!/bin/bash

LAMBDA_FUNCTION_DIR="$HOME/sistemas-interna/terraform/compliance_users_aws"
LAMBDA_FUNCTION_FILE="lambda_function.js"

cd "$LAMBDA_FUNCTION_DIR"

npm install

zip -r lambda.zip "$LAMBDA_FUNCTION_FILE" node_modules/


echo "El paquete de despliegue 'lambda.zip' está listo y ubicado en $LAMBDA_FUNCTION_DIR"
