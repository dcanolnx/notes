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


# Delete pods, services and pvcs older than 15 days
whitelist_file="/keoscicd-cleaner-whitelist/keoscicd-cleaner-whitelist"

kubectl get pods -n $namespace -o json | jq -r '.items[] | select((now - (.metadata.creationTimestamp | fromdateiso8601)) > 259200) | .metadata.name' | while IFS=$'\t' read -r name; do
	avoid=false
    while IFS= read -r linea; do
        # Comprueba si la cadena a buscar es una subcadena de la línea actual
        if [[ $name == *"$linea"* ]]; then
            avoid=true
			echo "ignore pod $name"
        fi
    done < "$whitelist_file"
	if [[ "$avoid" = "false"]]; then
		echo "kubectl delete --force pod $name -n $namespace"
	fi
done	

kubectl get pvc -n $namespace -o json | jq -r '.items[] | select((now - (.metadata.creationTimestamp | fromdateiso8601)) > 259200) | .metadata.name' | while IFS=$'\t' read -r name; do
	avoid=false
    while IFS= read -r linea; do
        # Comprueba si la cadena a buscar es una subcadena de la línea actual
        if [[ $name == *"$linea"* ]]; then
            avoid=true
			echo "ignore pvc $name"
        fi
    done < "$whitelist_file"
	if [[ "$avoid" = "false"]]; then
		echo "kubectl delete --force pvc $name -n $namespace"
	fi
done

kubectl get services -n $namespace -o json | jq -r '.items[] | select((now - (.metadata.creationTimestamp | fromdateiso8601)) > 259200) | .metadata.name' | while IFS=$'\t' read -r name; do
	avoid=false
    while IFS= read -r linea; do
        # Comprueba si la cadena a buscar es una subcadena de la línea actual
        if [[ $name == *"$linea"* ]]; then
            avoid=true
			echo "ignore service $name"
        fi
    done < "$whitelist_file"
	if [[ "$avoid" = "false"]]; then
		echo "kubectl delete --force service $name -n $namespace"
	fi
done