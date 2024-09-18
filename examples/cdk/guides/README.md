# Guides

This file contains some guides to administrate CICD Keos: 

- ** Configure cron backup for vault and control-plane **

Next commands should be launch on docker cicd that is running on kubeboot.int.stratio.com . First one configure a backup that is executed every night for etcd-vault on workers:

```
keos backup schedule vault
```
This command configure backup for etc control-plane:

```
keos backup schedule control-plane
```

- ** Remove and restore vault **

This procedure has been executed some times because default local storage is LocalPath and when we loose one of the three workers that contains a etcd-vault pod the data disappears.

So the first thing we should do if all is working fine but one of the etcd-vault pods is failing is do a backup:
```
keos backup create vault 
```
Once this has been done we list it:
```
keos backup list vault
```
Uninstall etcd-vault helm:
```
helm uninstall etcd-vault -n keos-core
```
We get pvc of etcd-vault and delete it:
```
kubectl  get pvc -n keos-core
kubectl  delete pvc data-etcd-vault-0 -n keos-core
kubectl  delete pvc data-etcd-vault-1 -n keos-core
kubectl  delete pvc data-etcd-vault-2 -n keos-core
```
We list backups again and get timestamp:
```
keos backup list vault
```
Finally we execute restore command with timestamp:
```
keos backup restore vault $timestamp
```