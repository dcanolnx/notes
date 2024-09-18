#/bin/bash

## Generate Kubeconfig
mkdir /.kube/
server="https://10.120.14.102:6443"
ca=$(cat /run/secrets/kubernetes.io/serviceaccount/ca.crt | base64 | tr -d '\n')
token=$(cat /run/secrets/kubernetes.io/serviceaccount/token)
namespace=$(cat /run/secrets/kubernetes.io/serviceaccount/namespace)


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