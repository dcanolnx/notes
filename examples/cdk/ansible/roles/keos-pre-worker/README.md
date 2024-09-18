Role Name
=========

This role is used to create a disk on PureStorage and connect it with workers to be used with ceph. It should be running on workers before launch keos install.

Requirements
------------

Any pre-requisites that may not be covered by Ansible itself or the role should be mentioned here. For instance, if the role uses the EC2 module, it may be a good idea to mention in this section that the boto package is required.

Role Variables
--------------

- Pure API Token
- Location of file kube/.config

Dependencies
------------


Example Playbook
----------------
---

- hosts: hosts_example
  become: true
  become_user: root  
  roles:
  - keos-purestorage
  vars:
    pure_hostname:    "cabina.stratio.com"
    pure_api: "1111111-11111-11111-11111-1111111"
    pure_hostgroup: "Kubernetes"
    keos_kubeconfig_path: /root/.kube/config


License
-------

BSD

Author Information
------------------

Sysinternal
