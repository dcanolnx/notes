#/bin/bash

## Generate Kubeconfig
mkdir /.kube/
server="https://10.120.14.102:6443"
ca=$(cat /run/secrets/kubernetes.io/serviceaccount/ca.crt | base64 | tr -d '\n')
token=$(cat /run/secrets/kubernetes.io/serviceaccount/token)
namespace=$(cat /run/secrets/kubernetes.io/serviceaccount/namespace)
psqlPass=$PSQL_PASS
litioPass=$SSH_PASS_BACKUPSONAR

echo "
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: ${ca}
    server:     ${server}
  name: stratiocicd
contexts:
- context:
    cluster: stratiocicd
    user: jenkins
    namespace: ${namespace}
  name: jenkins@stratiocicd
current-context: jenkins@stratiocicd
kind: Config
preferences: {}
users:
- name: jenkins
  user:
    token: ${token}
" > /.kube/config


# Create new backup
echo "kubectl exec --container sonarqube-postgresql -i sonarqube-postgresql-0 -n keos-ci -- bash -c \"/opt/bitnami/postgresql/bin/pg_dump --dbname=postgresql://sonarUser:password@127.0.0.1:5432/sonarDB > /tmp/backup_$(date +"%d-%m-%Y").sql\""
kubectl exec --container sonarqube-postgresql -i sonarqube-postgresql-0 -n keos-ci -- bash -c "/opt/bitnami/postgresql/bin/pg_dump --dbname=postgresql://sonarUser:"$psqlPass"@127.0.0.1:5432/sonarDB > /tmp/backup_$(date +"%d-%m-%Y").sql"
# Get backup.sql file
echo "kubectl cp keos-ci/sonarqube-postgresql-0:/tmp/backup_$(date +"%d-%m-%Y").sql /tmp/backup_$(date +%d-%m-%Y).sql"
kubectl cp keos-ci/sonarqube-postgresql-0:/tmp/backup_$(date +"%d-%m-%Y").sql /tmp/backup_$(date +%d-%m-%Y).sql
# Copy to litio
echo "SCP to litio"
sshpass -p $litioPass scp -o ConnectTimeout=1800 -o StrictHostKeyChecking=no /tmp/backup_$(date +"%d-%m-%Y").sql backup-sonar@litio.int.stratio.com:/backups/sonar/sonar/


