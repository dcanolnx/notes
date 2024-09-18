#!/usr/bin/python3

'''
Hetzner enviroment  external inventory script
=============================================

Generates inventory that Ansible can understand by parsing dhcpd.conf
You must have connection ssh with The Master Cluser (Hetzner27)
'''

# (c) 2012, Peter Sankauskas
#
# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

######################################################################

import configparser
import paramiko
import getpass
import os
import sys
import json
import ipaddress
import re

NAME_INI = "hetzner_environment.ini"
PATH_DIR = os.path.dirname(__file__)
PATH_INI = PATH_DIR + "/" + NAME_INI
REDIRECT_ERROR = "2> /dev/null"
DEFAULTS = {
    'hostname': 'localhost',
    'port': '22',
    'timeout': '10',
    'username': getpass.getuser(),
    'user_password': '',
    'user_private_key': '/home/' + getpass.getuser() + '/.ssh/id_rsa',
    'path_environments': '/opt',
    'path_environments_physical': '/etc/named/zones',
    'ignore': '[]'
}


class HetznerInventory(object):

    def _empty_inventory(self):
        return {"_meta": {"hostvars": {}}}

    def __init__(self):
        ''' Main execution path '''

        # Inventory grouped by environments
        self.inventory = self._empty_inventory()

        # Define Host Variables
        self.hostname = ''
        self.host_port = None
        self.host_timeout = None
        self.host_user = ''
        self.host_user_password = ''
        self.host_user_private_key = ''
        self.path_environments = ''
        self.path_environments_physical = ''
        self.ignore_environments = ''

        # Read settings and parse CLI arguments
        # self.parse_cli_args()
        self.read_settings()

        # Define SSH session variables
        self.client = None
        self.ssh_output_ips = None
        self.ssh_output_mask = None
        self.ssh_output_domain_name = None
        self.ssh_output_hostname = None
        self.ssh_output_hostname_ip = None
        self.ssh_output_hostname_ip_physical = None
        self.command_ips = """grep -ir --include="*.conf" 'fixed-address'"""
        self.command_mask = """grep -ir --include="*.conf" 'option subnet-mask '"""
        self.command_domain_name = """grep -ir --include="*.conf" 'option domain-name '"""
        self.command_hostname = """grep -ir --include="*.conf" 'host '"""
        self.command_hostname_ip = """grep -A4 -ir --include="*.conf" 'host '"""
        self.command_hostname_ip_physical = """sudo egrep -ir --include='db.*.hetzner.stratio.com' """ + \
                                            """'hetzner[0-9]{1,3}\..*\.hetzner\.stratio\.com\.'"""

        # Connect to host
        self.host_get_ips_environments()

        # Define inventory variables
        self.environments = []

        # Create inventory
        self.create_inventory()

        print(self.json_format_dict(self.inventory, True))

    def read_settings(self):
        ''' Reads the settings from the path_ini file '''

        config = configparser.ConfigParser(DEFAULTS)
        config.read(PATH_INI)

        # Add empty sections
        #  if they don't exist
        try:
            config.add_section('master-gw')
        except configparser.DuplicateSectionError:
            pass

        # Get Configs variables
        self.hostname = config.get('master-gw', 'hostname')
        self.host_port = config.getint('master-gw', 'port')
        self.host_timeout = config.getint('master-gw', 'timeout')
        self.host_user = config.get('master-gw', 'username')
        self.host_user_password = config.get('master-gw', 'user_password')
        self.host_user_private_key = config.get('master-gw', 'user_private_key')
        self.path_environments = config.get('master-gw', 'path_environments')
        self.path_environments_physical = config.get('master-gw', 'path_environments_physical')
        self.ignore_environments = config.get('master-gw', 'ignore')

    def host_get_ips_environments(self):
        ''' Connect with ssh to the machine '''

        try:
            # Paramiko.SSHClient can be used to make connections to the remote server and transfer files
            self.client = paramiko.SSHClient()

            # Parsing an instance of the AutoAddPolicy to set_missing_host_key_policy() changes it to allow any host.
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the server
            if self.host_user_password == '':
                private_key = paramiko.RSAKey.from_private_key_file(self.host_user_private_key)
                self.client.connect(hostname=self.hostname, port=self.host_port, username=self.host_user,
                                    pkey=private_key, timeout=self.host_timeout, allow_agent=False,
                                    look_for_keys=False)
            else:
                self.client.connect(hostname=self.hostname, port=self.host_port, username=self.host_user,
                                    password=self.host_user_password, timeout=self.host_timeout, allow_agent=False,
                                    look_for_keys=False)

        except paramiko.AuthenticationException:
            print("Authentication failed, please verify your credentials")
            sys.exit(1)
        except paramiko.SSHException as sshException:
            print("Could not establish SSH connection: %s" % sshException)
            sys.exit(1)
        except Exception as e:
            print("Exception in connecting to the server")
            print("PYTHON SAYS:", e)
            self.client.close()
            sys.exit(1)


        ''' Get all environments with their IPs '''
        self.command_ips = self.command_ips + " " + self.path_environments + " " + REDIRECT_ERROR
        self.command_mask = self.command_mask + " " + self.path_environments + " " + REDIRECT_ERROR
        self.command_domain_name = self.command_domain_name + " " + self.path_environments + " " + REDIRECT_ERROR
        self.command_hostname = self.command_hostname + " " + self.path_environments + " " + REDIRECT_ERROR
        self.command_hostname_ip = self.command_hostname_ip + " " + self.path_environments + " " + REDIRECT_ERROR
        self.command_hostname_ip_physical = self.command_hostname_ip_physical + " " + self.path_environments_physical \
                                            + " " + REDIRECT_ERROR
        try:
            stdin, stdout, stderr = self.client.exec_command(self.command_ips, timeout=self.host_timeout)
            self.ssh_output_ips = stdout.read()
            self.ssh_error = stderr.read()

            stdin, stdout, stderr = self.client.exec_command(self.command_mask, timeout=self.host_timeout)
            self.ssh_output_mask = str(stdout.read())
            self.ssh_error = stderr.read()

            stdin, stdout, stderr = self.client.exec_command(self.command_domain_name, timeout=self.host_timeout)
            self.ssh_output_domain_name = str(stdout.read())
            self.ssh_error = stderr.read()

            stdin, stdout, stderr = self.client.exec_command(self.command_hostname, timeout=self.host_timeout)
            self.ssh_output_hostname = str(stdout.read())
            self.ssh_error = stderr.read()

            stdin, stdout, stderr = self.client.exec_command(self.command_hostname_ip, timeout=self.host_timeout)
            self.ssh_output_hostname_ip = str(stdout.read())
            self.ssh_error = stderr.read()

            stdin, stdout, stderr = self.client.exec_command(self.command_hostname_ip_physical,
                                                             timeout=self.host_timeout)
            self.ssh_output_hostname_ip_physical = str(stdout.read())
            self.ssh_error = stderr.read()

            if self.ssh_error:
                print("Problem occurred while running command:" + self.command_ips + " The error is " + self.ssh_error)

            self.client.close()

        except paramiko.SSHException:
            print("Failed to execute the command!", self.command_ips)
            self.client.close()
            sys.exit(1)
        except Exception as e:
            print("Exception in executing the command")
            print("PYTHON SAYS:", e)
            self.client.close()
            sys.exit(1)

    def create_inventory(self):
        ''' Create the inventory from stdout '''

        all_hosts = self.ssh_output_ips.decode().split(';')
        ignore_environments = json.loads(self.ignore_environments)
        environments = []

        # Get all environments with variables
        for host in all_hosts:
            if self.path_environments in host:
                environment = host.split('/')[2]

                # Hostvars
                if (environment not in environments) and (environment not in ignore_environments):
                    environments.append(environment)
                    self.inventory["_meta"]["hostvars"][environment] = {}

                    # Get Domain Name
                    looking = True
                    for domain in self.ssh_output_domain_name.split(';'):
                        if environment in domain and looking:
                            self.inventory["_meta"]["hostvars"][environment]["domain-name"] = domain.split('"')[1]
                            looking = False

                    # Get Netmask
                    looking = True
                    for mask in self.ssh_output_mask.split(';'):
                        if environment in mask and looking:

                            ip_host_string = host.split('fixed-address ')[1]
                            mask_environment = mask.split(" ")[-1]
                            net = ipaddress.IPv4Network(ip_host_string + '/' + mask_environment, False)

                            self.inventory["_meta"]["hostvars"][environment]["subnet"] = \
                                str(ipaddress.IPv4Address(int(ipaddress.IPv4Address(ip_host_string)) & int(net.netmask))) \
                                + '/' + mask.split(" ")[-1]
                            looking = False

        # Get all hostnames
        ips_environment = []
        ips_environment_physical = []
        for environment in environments:
            for hostname in self.ssh_output_hostname.split(' {'):
                if (environment in hostname) and (environment not in ignore_environments):
                    ips_environment.append(hostname.split('host ')[1] + '-' + environment)

                    # Get vars for the host
                    for host_ip in self.ssh_output_hostname_ip.split('}'):
                        if environment in host_ip and hostname in host_ip:
                            # Generate space
                            self.inventory["_meta"]["hostvars"][hostname.split('host ')[1] + '-' + environment] = {}
                            # Add Host
                            self.inventory["_meta"]["hostvars"][hostname.split('host ')[1] + '-' +
                                                                environment]["ansible_ssh_host"] = \
                                hostname.split('host ')[1] + '.' + \
                                self.inventory["_meta"]["hostvars"][environment]["domain-name"]
                            # Add Ip addr
                            self.inventory["_meta"]["hostvars"][hostname.split('host ')[1] + '-' +
                                                                environment]["ansible_host"] = \
                                host_ip.split('fixed-address')[1].split(';')[0].replace(' ', '')
                            # Add ssh common args
                            self.inventory["_meta"]["hostvars"][hostname.split('host ')[1] + '-' +
                                                                environment]["ansible_ssh_common_args"] = \
                                "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

            self.inventory[environment] = {}
            self.inventory[environment]["hosts"] = ips_environment
            ips_environment = []

            # Get all physical hostnames
            for hostname in self.ssh_output_hostname_ip_physical.split('\\n'):
                if environment in hostname:
                    # Add host to environment physical group
                    hostname_name = hostname.split()[0].split(':')[1].split('.')[0] + '-' + environment
                    ips_environment_physical.append(hostname_name)
                    # Generate space
                    self.inventory["_meta"]["hostvars"][hostname_name] = {}
                    # Add host
                    self.inventory["_meta"]["hostvars"][hostname_name]["ansible_ssh_host"] = \
                        re.search('hetzner[0-9]{1,3}\..*\.hetzner\.stratio\.com\.',
                                  hostname.split()[0].split(':')[1]).group(0)[:-1]
                    # Add Ip addr
                    self.inventory["_meta"]["hostvars"][hostname_name]["ansible_host"] = \
                        re.search('(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' +\
                                  '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' +\
                                  '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.' +\
                                  '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)', hostname).group(0)
                    # Add ssh common args
                    self.inventory["_meta"]["hostvars"][hostname_name]["ansible_ssh_common_args"] = \
                        "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

            self.inventory[environment+"-physical"] = {}
            self.inventory[environment+"-physical"]["hosts"] = ips_environment_physical
            ips_environment_physical = []

    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=4)
        else:
            return json.dumps(data)


if __name__ == '__main__':
    # Run the script
    HetznerInventory()
