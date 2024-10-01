#!/usr/bin/env python3.6
import configparser
import paramiko
import getpass
import os
import sys
import json
import ipaddress
import re
NAME_INI = "labs_environment.ini"
PATH_DIR = os.path.dirname(__file__)
PATH_INI = PATH_DIR + "/" + NAME_INI
#REDIRECT_ERROR = "2> /dev/null"
REDIRECT_ERROR = ""
DEFAULTS = {
    'hostname': 'helio.int.stratio.com',
    'port': '22',
    'timeout': '10',
    'username': getpass.getuser(),
    'user_password': '',
    'user_private_key': '/home/' + getpass.getuser() + '/.ssh/id_rsa',
    'path_environments': '/opt',
    'ignore': '[]'
}
class LabsInventory(object):
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
        self.command_ips = """sudo grep -ir --include="db.*.labs.stratio.com" '^[a-z0-9].*IN.*A.*10\.200\.[0-9]*\.[0-9]*'"""
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
            config.add_section('helio')
        except configparser.DuplicateSectionError:
            pass
    
        # Get Configs variables
        self.hostname = config.get('helio', 'hostname')
        self.host_port = config.getint('helio', 'port')
        self.host_timeout = config.getint('helio', 'timeout')
        self.host_user = config.get('helio', 'username')
        self.host_user_password = config.get('helio', 'user_password')
        self.host_user_private_key = config.get('helio', 'user_private_key')
        self.path_environments = config.get('helio', 'path_environments')
        self.ignore_environments = config.get('helio', 'ignore')
    
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
        self.command_ips = self.command_ips + " " + self.path_environments + " | grep -v SOA " + REDIRECT_ERROR
        try:
            stdin, stdout, stderr = self.client.exec_command(self.command_ips,timeout=self.host_timeout)
            self.ssh_output_ips = stdout.read()
            self.ssh_error = stderr.read()
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
        all_hosts=self.ssh_output_ips.decode().splitlines()
        # From stdout we create a list with [environment_name,machine_name,machine_ip]
        list_hosts=[]
        for host in all_hosts:
            if( ':' in host):
                if(len(str(host).split(':')) == 2):
                    environment_name=str(host).split(':')[0]
                    environment_name=str(environment_name.split('.')[-4])
                    machine_name=str(host).split(':')[1].split()[0]
                    machine_ip=host.split()[-1]
                    list_hosts.append([machine_name,environment_name,machine_ip])
        # Populate inventory from previus list
        for h in list_hosts:
            # Generate space
            self.inventory["_meta"]["hostvars"][h[0]+'-'+h[1]] = {}
            # Add Host
            self.inventory["_meta"]["hostvars"][h[0]+'-'+h[1]]["ansible_ssh_host"] = h[0]+'.'+h[1]+".labs.stratio.com"
            # Add Ip addr
            self.inventory["_meta"]["hostvars"][h[0]+'-'+h[1]]["ansible_host"] = h[2]
            # Add ssh common args
            self.inventory["_meta"]["hostvars"][h[0]+'-'+h[1]]["ansible_ssh_common_args"] = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        for h in list_hosts:
            self.inventory[h[1]] = {}
            self.inventory[h[1]]["hosts"] = []
        for h in list_hosts:
            self.inventory[h[1]]["hosts"].append(h[0]+'-'+h[1])
    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted string '''
        if pretty:
            return json.dumps(data, sort_keys=True, indent=4)
        else:
            return json.dumps(data)
if __name__ == '__main__':
    # Run the script
    LabsInventory()
