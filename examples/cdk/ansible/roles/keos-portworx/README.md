Role Name
=========

This role is used to deploy portworx+pure flasharray on a keos cluster

Requirements
------------


Role Variables
--------------

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
  - keos-portworx
  vars:
    keos_kubeconfig_path: /root/.kube/config


License
-------

BSD

Author Information
------------------

Sysinternal
