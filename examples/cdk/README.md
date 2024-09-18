# continuous-delivery-keos

This repository has necessary steps and files to deploy Stratio KEOS CICD (PRO and DEV) architecture.

- **Prepare workers to be integrated with PureStorage**

We have created a role called keos-pre-worker in order to prepare workers to work with PureStorage installing all necessary dependencies. If you want to install Ceph you should modify; install_ceph=True it would create a volume on PureStorage and neccesary configuration on keos workers to mount a disk to be used by Ceph.
```
ansible-playbook keos-pre-workerpure.yml --vault-password-file ansible-vault-pass.txt
```

- **Install KEOS**

Execute:
```
docker run -ti --net host -v /var/run/docker.sock:/var/run/docker.sock -v $REPO_PATH/keos/workspace:/workspace qa.int.stratio.com/stratio/keos-installer:0.2.0-a2e020c
```
Inside the container execute:
```
ansible all -b -m shell -a "yum remove buildah podman -y"
keos install --skip-tags "command-center, falco, gosec, idp, keos-auth, kerberos-vault, oauth2-proxy, postgres, sis, sis-api, vault_kerberos,rook-ceph, install-rook-ceph

# If you want to install Ceph you should exec this instead of the previous command
keos install --skip-tags "command-center, falco, gosec, idp, keos-auth, kerberos-vault, oauth2-proxy, postgres, sis, sis-api, vault_kerberos"
```

- **PureStorage on KEOS**

We have created a role called keos-purestorage to integrate pure-cso with keos:
```
ansible-playbook keos-purestorage.yml --vault-password-file ansible-vault-pass.txt
```

- **Portworx + Pure FlashArray on KEOS**

We have created a role called keos-portworx to integrate; pure flasharray + portworx + keos:
```
ansible-playbook keos-portworx.yml --vault-password-file ansible-vault-pass.txt
```

On last Steps you should access manually to; https://central.portworx.com/specGen/wizard (sysinternal@stratio.com user for Production cluster). Select; Porworx Enterprise > Portworx CSI for FlashArray and FlashBlade  > Cloud (PureFlash Array)

- **CI Services**

We have created a role called keos-ci to launch all neccesary services: 
```
ansible-playbook keos-ci.yml --vault-password-file ansible-vault-pass.txt

```
# NOTES

To avoid passwords in plain text all sensible files are encrypted using ansible-vault.

This repository contains neccesary files to deploy PROD and DEV environments.

# REFERENCES

https://docs.portworx.com/cloud-references/auto-disk-provisioning/pure-flash-array/

https://github.com/jenkinsci/helm-charts/tree/main/charts/jenkins

https://github.com/twuni/docker-registry.helm

https://github.com/Stratio/keos-installer
