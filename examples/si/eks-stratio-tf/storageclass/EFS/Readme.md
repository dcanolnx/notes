## Instalar Storage Class EFS

### Agregar Repo Helm
`helm repo add aws-efs-csi-driver https://kubernetes-sigs.github.io/aws-efs-csi-driver/ `  

### Actualizar Repositorio
`helm repo update aws-efs-csi-driver`  

### Instalar Driver EFS
` helm upgrade --install aws-efs-csi-driver --namespace kube-system aws-efs-csi-driver/aws-efs-csi-driver`  

### Validar Repo
`kubectl get pod -n kube-system -l "app.kubernetes.io/name=aws-efs-csi-driver,app.kubernetes.io/instance=aws-efs-csi-driver"`  

### Desplegar Storageclass  
`kubectl apply -f ./kubernetes/Prod/wordpress/wordpress-storageclass-dynamic.yaml`  

### Desplegar PVC asociado al Storageclass  
`kubectl apply -f ./kubernetes/Prod/wordpress/wordpress-pvc.yaml`  