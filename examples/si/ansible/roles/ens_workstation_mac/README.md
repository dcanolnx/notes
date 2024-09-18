ENS Workstation MAC
=========

Role to apply the ENS workstation configuration to a MAC.

How to Run
----------------

- Install Python3
Run on terminal:
```
python3
```
Click on Install, Agree the License and wait for the installation to finish.
- Login as root on terminal
- Install Ansible:
```
python3 -m pip install ansible
```
- Run Ansible:
```
python3 -m ansible playbook /path/to/ens_woorkstation_mac/playbook.yml
```


Requirements
------------

- Ansible 3.0.0 or higher

Role Variables
--------------

- password_minimum_age_days: User password minimum age in days
- password_maximum_age_days: User password maximum age in days
- password_minimum_length: User password minimum length
- password_complexity_digit: User password minimum number of digit
- password_complexity_uperchar: User password minimum number of upper case character
- password_complexity_lowerchar: User password minimum number of lower case character
- password_complexity_otherchar: User password minimum number of other character
- password_history_size: User password history size
- account_lock_inactivity_seconds: User account lock inactivity in seconds
- accout_lockout_count: User account lockout tries count
- accout_lockout_reset: User account lockout reset in seconds
- accout_lockout_duration_seconds: User account lockout idle duration in seconds
- ntp_url: NTP server URL

