# Ansible Filters

Installation
===========
Added to file `ansible.cfg` the filters directory variable:
```
filter_plugins     = /etc/ansible/filters/
```

Overview
===========
### Collection Utilities
* includes - Tests if string contains a substring.
```
- name: includes(haystack, needle)
  assert:
    that: 
      - "'foobar' | includes('ob') == True"
      - "'foobar' | includes('qux') == False"
      - "'foobar' | includes('bar') == True"
      - "'foobar' | includes('buzz') == False"
      - "12345 | includes(34) == True"
```
