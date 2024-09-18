import sys
import argparse
import logging.handlers
import atexit
import datetime
from calendar import monthrange
import sqlite3
import smtplib
import requests
import json
import ssl

from pyVim.connect import SmartConnect, Disconnect

import keystoneauth1.identity
import keystoneclient.v3
import novaclient.client as novaclient
import cinderclient.client as cinderclient
import ovirtsdk4 as sdk


# Class definition for a VM
class VM(object):
    def __init__(self, name):
        self.name = name
        self.description = "No description"
        self.owner = "Unknown"
        self.email = "sysinternal@stratio.com"
        self.expiration = datetime.datetime.today() + datetime.timedelta(weeks=1)
        self.state = 0
        self.cpus = 0
        self.mem = 0
        self.disk = 0
        self.provider = None
        self.server = None
        self.dc = None

    def update_metadata(self, owner, email, description, expiration):
        self.owner = owner
        self.email = email
        self.description = description
        self.expiration = expiration

    def update_state(self, state):
        self.state = state

    def update_from_vmware(self, virtualmachine):
        self.state = virtualmachine.runtime.powerState == "poweredOn"
        self.cpus = virtualmachine.summary.config.numCpu
        self.mem = virtualmachine.summary.config.memorySizeMB / 1024
        self.disk = (virtualmachine.summary.storage.committed + virtualmachine.summary.storage.unshared) / 1073741824
        self.provider = "VMware"

    def update_from_ovirt(self, virtualmachine):
        self.state = virtualmachine.status == "up"
        self.cpus = virtualmachine.cpu.topology.sockets
        self.mem = virtualmachine.memory / (1024*1024)
        self.disk = 0
        self.provider = "oVirt"

    def update_from_openstack(self, virtualmachine, nova_conn, cinder_conn):
        flavors = nova_conn.flavors
        cinder_vols = cinder_conn.volumes
        flavor = flavors.get(virtualmachine.flavor["id"])
        vol_size = flavor.disk
        vols = virtualmachine._info['os-extended-volumes:volumes_attached']
        for v in vols:
            vol_size += cinder_vols.get(v["id"]).size
        self.cpus = flavor.vcpus
        self.mem = flavor.ram / 1024
        self.disk = vol_size
        self.state = virtualmachine._info["OS-EXT-STS:power_state"]
        self.provider = "Openstack"

    # def update_from_hetzner(self, servertype, dc):
    #     self.state = True
    #     self.provider = "Hetzner"
    #     self.server = servertype
    #     self.dc = dc.split("-")[0]

    def get_cpus(self):
        return self.cpus

    def get_mem(self):
        return self.mem

    def get_disk(self):
        return self.disk

    def get_owner(self):
        return self.owner

    def get_description(self):
        return self.description

    def get_email(self):
        return self.email

    def get_expiration(self):
        return self.expiration

    def get_state(self):
        return self.state


# Some defaults
default_log_level = "INFO"
default_database = "vnotifier.db"
default_database_path = "/var/vnotifier"
default_log_file = "/var/log/stratio/vnotifier.log"
default_email_from = "sysinternal@stratio.com"
default_email_username = "sistemas@stratio.com"

# List of all the VMs hosted in VMware
vms = []
# Orphan VMs
unknown_vms = []
# Expired VMs owned by each user
expired = {}
# The accounting info of VMs belonging to owners
owner_accounting = {}
# Today
today = datetime.datetime.today()


def read_config(json_file):
    """ Reads the configuration file

    Reads the file received as argument and parses its contents

    Returns:
        The configuration read from file
    """
    f = open(json_file, "r", encoding="utf-8")
    json_config = json.load(f)
    f.close()
    return json_config


def destroy_vm_database(db_conn):
    """Destroys an existing database

    This function destroys a database and it's associated indexes

    Returns:
        n/a
    """
    logging.info("Destroying database")
    c = db_conn.cursor()
    transaction = 'DROP INDEX IF EXISTS vm_index'
    c.execute(transaction)
    transaction = 'DROP TABLE IF EXISTS vms'
    c.execute(transaction)
    db_conn.commit()


def create_vm_database(db_conn):
    """Creates a blank database

    This function creates a blank database and its related indexes

    Returns:
        n/a
    """
    logging.info("Creating VM database schema")
    c = db_conn.cursor()
    transaction = '''CREATE TABLE IF NOT EXISTS vms (
            vmname TEXT NOT NULL PRIMARY KEY,
            provider TEXT NOT NULL,
            description TEXT NOT NULL,
            user TEXT,
            email TEXT NOT NULL,
            expdate TIMESTAMP NOT NULL)'''
    c.execute(transaction)
    transaction = 'CREATE INDEX IF NOT EXISTS vm_index ON vms (vmname)'
    c.execute(transaction)
    db_conn.commit()


def populate_initial_vm_database(db_conn, vm_list):
    """Populates a blank database

    This function populates the database with initial data from the VM list:
     - vmname
     - Blank description
     - Unknown user
     - sysinternal@stratio.com as email
     - a week in the future as the expiry date

    Returns:
        n/a
    """
    logging.info("Populating initial VM database")
    today = datetime.datetime.today()
    week = datetime.timedelta(weeks=1)
    expdate = today + week
    logging.debug("Iterating over the VMs")
    for vm in vm_list:
        create_new_vm(db_conn, vm)


def destroy_account_database(db_conn):
    """Destroys an existing database

    This function destroys a database and it's associated indexes

    Returns:
        n/a
    """
    logging.info("Destroying accounting database")
    c = db_conn.cursor()
    transaction = 'DROP TABLE IF EXISTS accounting'
    c.execute(transaction)
    db_conn.commit()


def create_account_database(db_conn):
    """Creates a blank database

    This function creates a blank database and its related indexes

    Returns:
        n/a
    """
    logging.info("Creating accounting database schema")
    c = db_conn.cursor()
    transaction = '''CREATE TABLE IF NOT EXISTS accounting (
            vmname TEXT NOT NULL PRIMARY KEY,
            total REAL)'''
    c.execute(transaction)
    db_conn.commit()


def populate_initial_account_database(db_conn, vm_list):
    """Populates a blank database

    This function retrieves info from the vCenter and populates the database with initial data:
     - vmname
     - no weekly cost
     - current date

    Returns:
        n/a
    """
    logging.info("Populating initial VM accounting database")
    logging.debug("Iterating over the VMs")
    for vm in vm_list:
        create_new_account_vm(db_conn, vm)


# def destroy_hetzner_prices_database(db_conn):
#     """Destroys an existing database

#     This function destroys a database and it's associated indexes

#     Returns:
#         n/a
#     """
#     logging.info("Destroying Hetzner prices database")
#     c = db_conn.cursor()
#     transaction = 'DROP TABLE IF EXISTS hetzner_prices'
#     c.execute(transaction)
#     db_conn.commit()


# def create_hetzner_prices_database(db_conn):
#     """Creates a blank database

#     This function creates a blank database and its related indexes

#     Returns:
#         n/a
#     """
#     logging.info("Creating Hetzner pricing database schema")
#     c = db_conn.cursor()
#     transaction = '''CREATE TABLE IF NOT EXISTS hetzner_prices (
#             servertype TEXT NOT NULL,
#             dc TEXT NOT NULL,
#             price REAL,
#             PRIMARY KEY (servertype, dc))'''
#     c.execute(transaction)
#     db_conn.commit()


# def update_hetzner_prices_database(db_conn, prices):
#     """Updates the hetzner prices database

#     This function receives hetzner prices and updates the database with new data:

#     Returns:
#         n/a
#     """
#     logging.info("Populating initial Hetzner pricing database")
#     c = db_conn.cursor()
#     logging.debug("Iterating over the Hetzner server types")
#     for servertype in prices:
#         logging.debug("Creating Hetzner server {0} in SQLite".format(servertype["server"]))
#         transaction = '''INSERT OR REPLACE INTO hetzner_prices (servertype, dc, price)
#          VALUES ("{0}", "{1}", "{2}")'''.format(servertype["server"], servertype["dc"], servertype["price"])
#         c.execute(transaction)
#     db_conn.commit()


def create_vmware_list(folder, maxd, current_depth=1):
    """Creates an array with the VMs

    Gathers from the vCenter all the VMs and populates an array with their names and references.

    Returns:
        Array with all the VMs
    """
    vm_list = []

    if current_depth > maxd:
        logging.debug("Surpassed max depth")
        return vm_list
    if len(folder) == 0:
        return vm_list
    for item in folder:
        # We check if it's another folder
        if hasattr(item, 'childEntity'):
            logging.debug("Reached vSphere folder " + item.name)
            vm_list += create_vmware_list(item.childEntity, maxd, current_depth + 1)
        else:
            logging.debug("Reached vSphere VM " + item.name)
            virtualmachine = VM(item.summary.vm.name)
            virtualmachine.update_from_vmware(item)
            vm_list.append(virtualmachine)
    return vm_list

def create_ovirt_list(ovirt_vms):
    """Creates an array with the VMs

    Gathers from the oVirt Engine all the VMs and populates an array with their names and references.

    Returns:
        Array with all the VMs
    """
    vm_list = []

    if len(ovirt_vms) == 0:
        return vm_list
    for item in ovirt_vms:
        # We check if it's another folder
        logging.debug("Reached oVirt VM " + item.name)
        virtualmachine = VM(item.name)
        virtualmachine.update_from_ovirt(item)
        vm_list.append(virtualmachine)
    return vm_list


def clean_orphaned_vms(db_conn, vms):
    """Deletes from SQLite references to non-existent VMs

    In case a VM has been deleted from vSphere, Openstack, etc., there will be obsolete references in SQLite.
    This function is meant to clean up a little. IT IS VERY UNEFFICIENT!!

    Returns:
        n/a
    """
    logging.info("Cleaning orphaned VMs")
    # We retrieve all the VMs
    c = db_conn.cursor()
    transaction = 'SELECT * FROM vms'
    c.execute(transaction)
    vm_list = c.fetchall()
    # We check if any of them is not in vSphere
    for vm_data in vm_list:
        vm_name = vm_data[0]
        # We look for the VM in the VM list
        found = False
        for vm in vms:
            if vm.name == vm_name:
                found = True
                break
        if not found:
            logging.info("Found an orphan: " + vm_name)
            delete_vm(db_conn, vm_name)
            # We don't delete from the accounting database because we must still charge the owner at the end of month


def update_vm_owner(db_conn, vm_id, vm_user, vm_email):
    """Updates a VM's owner

    This function sets the received owner to the given vm in the SQLite database

    Returns:
        n/a
    """
    c = db_conn.cursor()
    transaction = 'UPDATE vms SET user = {0}, email = {1}  WHERE vmname={2}'.format(vm_user, vm_email, vm_id)
    c.execute(transaction)
    db_conn.commit()

def update_vm_provider(db_conn, vm_id, vm_provider):
    """Updates a VM's provider

    This function sets the received provider to the given vm in the SQLite database

    Returns:
        n/a
    """
    c = db_conn.cursor()
    transaction = 'UPDATE vms SET provider = "{0}" WHERE vmname="{1}"'.format(vm_provider, vm_id)
    c.execute(transaction)
    db_conn.commit()

def update_vm_expdate(db_conn, vm_id, expdate):
    """Updates a VM's expiry date

    This function sets the received expiry date to the given vm in the SQLite database

    Returns:
        n/a
    """
    c = db_conn.cursor()
    transaction = 'UPDATE vms SET expdate = {0} WHERE vmname={1}'.format(expdate, vm_id)
    c.execute(transaction)
    db_conn.commit()


def create_new_vm(db_conn, vm):
    """Adds a new VM

    This function adds a new VM to the SQLite database

    Returns:
        n/a
    """
    c = db_conn.cursor()
    logging.debug("Creating VM {0} in SQLite".format(vm.name))
    transaction = '''INSERT OR REPLACE INTO vms (vmname, provider, description, user, email, expdate)
            VALUES ("{0}", "{1}", "{2}", "{3}", "{4}", "{5}")'''.format(vm.name, vm.provider, vm.description, vm.owner,
                                                                        vm.email, vm.expiration)
    c.execute(transaction)
    db_conn.commit()


def delete_vm(db_conn, vm_id):
    """Deletes a VM

    This function deletes an existing VM from the SQLite database

    Returns:
        n/a
    """
    c = db_conn.cursor()
    logging.debug("Deleting VM {0} from SQLite".format(vm_id))
    transaction = 'DELETE FROM vms WHERE vmname = "{0}"'.format(vm_id)
    c.execute(transaction)
    db_conn.commit()


def query_vm(db_conn, vm_id):
    """Retrieves vm related data

    This function retrieves info from the SQLite database related to a vm

    Returns:
        A string including all the info
    """
    c = db_conn.cursor()
    transaction = 'SELECT * FROM vms WHERE vmname="{0}"'.format(vm_id)
    c.execute(transaction)
    data = c.fetchone()
    return data


def create_new_account_vm(db_conn, vm):
    """Adds a new VM in the accounting database

    This function adds a new VM to the accounting SQLite database

    Returns:
        n/a
    """
    c = db_conn.cursor()
    logging.debug("Creating VM {0} in SQLite".format(vm.name))
    transaction = '''INSERT OR REPLACE INTO accounting (vmname, total)
            VALUES ("{0}", "{1}")'''.format(vm.name, 0.0)
    c.execute(transaction)
    db_conn.commit()


def delete_account_vm(db_conn, vm_id):
    """Deletes a VM from the accounting database

    This function deletes an existing VM from the accounting SQLite database

    Returns:
        n/a
    """
    c = db_conn.cursor()
    logging.debug("Deleting VM {0} from SQLite".format(vm_id))
    transaction = 'DELETE FROM vms WHERE vmname = "{0}"'.format(vm_id)
    c.execute(transaction)
    db_conn.commit()


def update_account_vm_cost(db_conn, vm_id, cost):
    """Updates a VM's cost

    This function adds the received cost to the stored one for the given vm in the SQLite database

    Returns:
        The new cost stored in the database
    """
    # We check if the VM already exists
    c = db_conn.cursor()
    transaction = 'SELECT * FROM accounting WHERE vmname="{0}"'.format(vm_id)
    c.execute(transaction)
    data = c.fetchone()
    if data:
        vm = query_account_vm(db_conn, vm_id)
        new_total = vm[1] + cost
        transaction = 'UPDATE accounting SET total = "{0}" WHERE vmname="{1}"'.format(new_total, vm_id)
        c.execute(transaction)
    else:
        new_total = cost
        transaction = '''INSERT OR REPLACE INTO accounting(vmname, total)
        VALUES("{0}", "{1}")'''.format(vm_id, new_total)
        c.execute(transaction)
    db_conn.commit()
    return new_total


def query_account_vm(db_conn, vm_id):
    """Retrieves vm accounting related data

    This function retrieves info from the SQLite database related to a vm

    Returns:
        A string including all the info
    """
    c = db_conn.cursor()
    transaction = 'SELECT * FROM accounting WHERE vmname="{0}"'.format(vm_id)
    c.execute(transaction)
    data = c.fetchone()
    return data


def retrieve_accounting_db(db_conn):
    # We retrieve all the VMs
    c = db_conn.cursor()
    transaction = 'SELECT * FROM accounting'
    c.execute(transaction)
    vm_list = c.fetchall()
    return vm_list


# def query_hetzner_price(db_conn, server_type, dc):
#     """Retrieves hetzner server price

#     This function retrieves info from the SQLite database related to a hetzner server type

#     Returns:
#         The hetzner server price data
#     """
#     c = db_conn.cursor()
#     transaction = 'SELECT * FROM hetzner_prices WHERE servertype="{0}" AND dc="{1}"'.format(server_type, dc)
#     c.execute(transaction)
#     data = c.fetchone()
#     return data


def calculate_vm_cost(db_conn, vm, accounting):
    """Calculates the cost of a VM or server

    This function calculates the cost of a VM depending of the uptime of such virtual machine/server

    Returns:
        A real with the cost of a VM
    """
    # if vm.provider == "Hetzner":
    #     server_info = query_hetzner_price(db_conn, vm.server, vm.dc)
    #     server_cost = server_info[2]
    #     hourly_server_cost = server_cost / (monthrange(today.year, today.month)[1] * 24)
    # else:
    hourly_server_cost = (vm.cpus * float(accounting["cpu_coef"])) + (vm.mem * float(accounting["mem_coef"])) + (vm.disk * float(accounting["disk_coef"]))
    return hourly_server_cost


def is_end_of_month(date):
    max_day = monthrange(date.year, date.month)[1]
    if date.day >= max_day:
        return True
    else:
        return False


def send_gmail(email_from, email_to, subject, text, email_username, email_password):
    """Sends an email through Gmail

    Used to notify the user which VMs he has in VMware

    Returns:
        n/a
    """
    msg = 'From: %s\nTo: %s\nSubject: %s\n\n%s' % (email_from, email_to, subject, text)
    logging.debug("Sending email to " + email_to)
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(email_username, email_password)
    server.sendmail(email_from, email_to, msg)
    server.quit()


# We read arguments
parser = argparse.ArgumentParser(
    description='Check VMs and Physical inventory',
    epilog="I'm no expert Python programmer. Take care when using this script..."
    )
parser.add_argument("config_file", type=argparse.FileType('r'), help="Configuration file")
parser.add_argument("-i", "--initialize_db", action="store_true", help="Initialize and populate new SQLite database")
# parser.add_argument("-u", "--update_hetzner", action="store_true", help="Update Hetzner server prices")
parser.add_argument("-p", "--update_providers", action="store_true", help="Update VM providers")
args = parser.parse_args()
config_file = args.config_file
initialize_db = args.initialize_db
# update_hetzner = args.update_hetzner
update_providers = args.update_providers

# We read configuration file
try:
    configs = read_config(config_file.name)
except Exception:
    print("Error reading config file\n")
    sys.exit(2)

# We configure logging
try:
    config_log_level = configs["logs"]["level"].upper()
except ValueError:
    config_log_level = default_log_level
try:
    log_file = configs["logs"]["file"]
except ValueError:
    log_file = default_log_file
log_level = getattr(logging, config_log_level)
handler = logging.handlers.RotatingFileHandler(
              log_file, mode='a', maxBytes=10485760, backupCount=5, encoding='utf-8')
logging.basicConfig(level=log_level,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    handlers=[handler])

logging.debug('Starting!')

# We open SQLite
if 'path' in configs["database"].keys():
    database_path = configs["database"]["path"]
else:
    database_path = default_database_path + '/' + default_database
try:
    logging.info('Connecting to SQLite database: ' + database_path)
    conn = sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES)
except Exception as e:
    logging.critical("Error opening database " + database_path + ": " + str(e))
    send_gmail(configs["email"]["from"], configs["email"]["admin"], "vNotifier error!",
               "Error opening SQlite database", configs["email"]["username"], configs["email"]["password"])
    sys.exit(2)

# If user just wants to update the Hetzner server price
# if update_hetzner:
#     try:
#         update_hetzner_prices_database(conn, configs["hetznerprices"])
#         sys.exit(0)
#     except Exception as e:
#         logging.critical("Error updating Hetzner database: " + str(e))
#         send_gmail(configs["email"]["from"], configs["email"]["admin"], "vNotifier error!",
#                    "Error updating Hetzner database: " + str(e), configs["email"]["username"],
#                    configs["email"]["password"])
#         sys.exit(2)


# We connect to Hetzner
# hetzner_request = requests.get(configs["hetznerconn"]["url"] + "/server",
#                                auth=(configs["hetznerconn"]["username"], configs["hetznerconn"]["password"]))
# try:
#     hetzner_request.raise_for_status()
# except Exception as e:
#     logging.critical("Error listing Hetzner servers:" + str(e))
#     send_gmail(configs["email"]["from"], configs["email"]["admin"], "vNotifier error!",
#                "Error listing Hetzner servers", configs["email"]["username"], configs["email"]["password"])
#     sys.exit(2)

# We iterate over the Hetzner servers
# for vm in hetzner_request.json():
#     # We create a new VM object...
#     hetznervm = VM(vm["server"]["server_name"])
#     hetznervm.update_from_hetzner(vm["server"]["product"], vm["server"]["dc"])
#     # ...and we append it to the global vm list
#     vms.append(hetznervm)

# We connect to Openstack
"""try:
    openstack_auth = keystoneauth1.identity.v3.Password(user_domain_name=configs["openstackconn"]["user_domain_name"],
                                                        user_domain_id=configs["openstackconn"]["user_domain_id"],
                                                        username=configs["openstackconn"]["username"],
                                                        password=configs["openstackconn"]["password"],
                                                        project_id=configs["openstackconn"]["root_project_id"],
                                                        auth_url=configs["openstackconn"]["auth_url"])
    openstack_session = keystoneauth1.session.Session(auth=openstack_auth)
    openstack_keystone = keystoneclient.v3.client.Client(session=openstack_session)

    # We list projects
    openstack_projects = openstack_keystone.projects.list()
except Exception as e:
    logging.critical("Error listing Openstack projects: " + str(e))
    send_gmail(configs["email"]["from"], configs["email"]["admin"], "vNotifier error!",
               "Error listing Openstack projects", configs["email"]["username"], configs["email"]["password"])
    sys.exit(2)

# We iterate through the projects
for project in openstack_projects:
    openvms = None
    # We list all the VMs in this project
    openstack_auth = keystoneauth1.identity.v3.Password(user_domain_name=configs["openstackconn"]["user_domain_name"],
                                                        user_domain_id=configs["openstackconn"]["user_domain_id"],
                                                        username=configs["openstackconn"]["username"],
                                                        password=configs["openstackconn"]["password"],
                                                        project_id=project.id,
                                                        auth_url=configs["openstackconn"]["auth_url"])
    openstack_session = keystoneauth1.session.Session(auth=openstack_auth)
    openstack_nova = novaclient.Client("2", session=openstack_session)
    openstack_cinder = cinderclient.Client("2", session=openstack_session)

    try:
        openvms = openstack_nova.servers.list()
    except Exception as e:
        logging.info("Error listing VMs from Openstack project " + project.id + ": " + str(e))
    if openvms:
        for vm in openvms:
            logging.debug("Reached Openstack VM " + vm.name + " from project " + project.name)
            # We create a new VM object...
            openvm = VM(project.name + "_" + vm.name)
            openvm.update_from_openstack(vm, openstack_nova, openstack_cinder)
            # ...and we append it to the global vm list
            vms.append(openvm)
"""
# We connect to vCenter
context = None
logging.info('Connecting to vSphere vCenter: ' + configs["vcenterconn"]["host"])
context = ssl._create_unverified_context()
service_instance = SmartConnect(host=configs["vcenterconn"]["host"],
                                user=configs["vcenterconn"]["username"],
                                pwd=configs["vcenterconn"]["password"],
                                port=configs["vcenterconn"]["port"],
                                sslContext=context)
if not service_instance:
        logging.info('Error connecting to vSphere vCenter')
        send_gmail(configs["email"]["from"], configs["email"]["admin"], "vNotifier error!",
                   "Error connecting to vSphere vCenter", configs["email"]["username"], configs["email"]["password"])
        sys.exit(2)

# We make sure we disconnect
atexit.register(Disconnect, service_instance)

# We retrieve info
content = service_instance.RetrieveContent()

# Get datacenter object
for child in content.rootFolder.childEntity:
    if hasattr(child, 'vmFolder'):
        datacenter = child
        folder_list = datacenter.vmFolder.childEntity
        break

# Create VM array
logging.debug("Iterating over the VMs")
max_depth = int(configs["other"]["maxdepth"])
vms += create_vmware_list(folder_list, max_depth)


# We connect to oVirt-Engine
ovirt_vms = []
logging.info('Connecting to oVirt Engine: ' + configs["ovirtconn"]["host"])
try:
    connection = sdk.Connection(url=configs["ovirtconn"]["host"], username=configs["ovirtconn"]["username"], password=configs["ovirtconn"]["password"], insecure=True)
    vms_service = connection.system_service().vms_service()
    ovirt_vms = vms_service.list()
except:
    print('Error connecting to oVirt')
    send_gmail(configs["email"]["from"], configs["email"]["admin"], "vNotifier error!",
                   "Error connecting to oVirt Engine", configs["email"]["username"], configs["email"]["password"])
    sys.exit(2)

logging.debug("Iterating over the VMs")
vms += create_ovirt_list(ovirt_vms)


# In case the user wants to initialize the SQLite database
if initialize_db:
    try:
        logging.info("Asked to initialize the database, so... INITIALIZING")
        destroy_vm_database(conn)
        destroy_account_database(conn)
        # destroy_hetzner_prices_database(conn)
        create_vm_database(conn)
        create_account_database(conn)
        # create_hetzner_prices_database(conn)
        populate_initial_vm_database(conn, vms)
        populate_initial_account_database(conn, vms)
        # update_hetzner_prices_database(conn, configs["hetznerprices"])
    except Exception as e:
        logging.critical("Error initializing database " + database_path + ": " + str(e))
        send_gmail(configs["email"]["from"], configs["email"]["admin"], "vNotifier error!",
                   "Error initializing SQlite database " + database_path + ": " + str(e), configs["email"]["username"],
                   configs["email"]["password"])
        sys.exit(2)

# In case the user wants to update the VM providers in the SQLite database
if update_providers:
    try:
        logging.info("Asked to update the providers, so... UPDATING")
        for vm in vms:
            logging.debug("Updating VM " + vm.name + " provider to " + vm.provider)
            update_vm_provider(conn, vm.name, vm.provider)
    except Exception as e:
        logging.critical("Error updating VM providers: " + str(e))
        send_gmail(configs["email"]["from"], configs["email"]["admin"], "vNotifier error!",
                   "Error updating VM providers: " + str(e), configs["email"]["username"],
                   configs["email"]["password"])
        sys.exit(2)

# try:
#     # We must delete orphaned VMs that have been already accounted for JUST FROM THE VM DATABASE
#     clean_orphaned_vms(conn, vms)
# except Exception as e:
#     logging.critical("Error cleaning SQLite database: " + str(e))
#     send_gmail(configs["email"]["from"], configs["email"]["admin"], "vNotifier error!",
#                "Error cleaning SQLite database: " + str(e), configs["email"]["username"], configs["email"]["password"])
#     sys.exit(2)

# Check if there are unknown VMs, if any VM has expired...
for vm in vms:
    # We gather related info from SQLite
    vm_data = query_vm(conn, vm.name)
    # If the VM is not in the inventory, save name to tell administrators later
    if not vm_data:
        logging.debug("Found unknown VM: {0}".format(vm.name))
        unknown_vms.append(vm)
    else:
        # We update VM data from database
        vm.update_metadata(vm_data[1], vm_data[2], vm_data[5], vm_data[3])
        # Check if VM is in its time frame
        if vm.expiration < datetime.datetime.today():
            logging.debug("Found expired VM: {0}".format(vm.name))
            # If it is not, we add the VM to the owners list
            if vm.owner not in expired:
                expired[vm.owner] = []
            expired[vm.owner].append(vm)

# We add unknown VMs to the SQLite database and send the administrators a list of VMs not in inventory
if unknown_vms:
    admin_email_subject = 'Unknown VMs and servers in Stratio'
    admin_email_text = '''The following VMs and servers appear to exist but are not in my local database.
I just added them :-( :\n\n'''
    for vm in unknown_vms:
        logging.info("Inserting unknown VM into database: {0}".format(vm.name))
        create_new_vm(conn, vm)
        admin_email_text += vm.provider + ": " + vm.name + "\n"
    try:
        send_gmail(configs["email"]["from"], configs["email"]["admin"], admin_email_subject, admin_email_text,
                   configs["email"]["username"], configs["email"]["password"])
    except Exception:
        logging.critical("Error sending email to administrator")

# We look for all the expired VMs and servers
if today.hour > 22:
    email_foot = "\n\n\nThis is an automated email and has the objective of keeping track of the environments. You " \
                 "will receive this email every day until the expiry date is extended. If we don't receive an answer " \
                 "in a week your servers will be blocked and eventually deleted."
    admin_email_subject = "Expired VMs in Stratio's environments"
    for user in expired:
        email_subject = "The VMs and servers in Stratio's environments for {0}".format(user)
        # We fetch the owner email from the first VM
        email_to = expired[user][0].email

        # We create the email text
        admin_email_text = "These VMs and servers look like they have expired. Perhaps they should be deleted:\n\n"
        email_text = "These VMs and servers which you seem responsible for look like they have expired. Please " \
                     "notify the Systems team if you are willing to keep them or they will be deleted:\n\n"
        logging.info("Preparing expiring email for {0}".format(user))
        for vm in expired[user]:
            email_text += vm.name + ": " + vm.description + "\n"
            admin_email_text += vm.name + " belonging to " + user + "\n"
        email_text += "\nThank you!" + email_foot
        try:
            send_gmail(configs["email"]["from"], email_to, email_subject, email_text,
                       configs["email"]["username"], configs["email"]["password"])
        except Exception:
            logging.critical("Error sending email to user " + user)
        admin_email_text += "\nThank you!"
        try:
            send_gmail(configs["email"]["from"], configs["email"]["admin"], admin_email_subject, admin_email_text,
                       configs["email"]["username"], configs["email"]["password"])
        except Exception:
            logging.critical("Error sending email to administrator")

# We start the accounting. We calculate every VM cost and insert it into the accounting database
for vm in vms:
    logging.debug("Accounting VM {0}".format(vm.name))
    if vm.state == True:
        vm_cost = calculate_vm_cost(conn, vm, configs[vm.provider])
        vm_cost = update_account_vm_cost(conn, vm.name, vm_cost)
        vm_account_info = [vm.name, vm_cost]
        if vm.owner not in owner_accounting:
            owner_accounting[vm.owner] = [vm.email, []]
        owner_accounting[vm.owner][1].append(vm_account_info)

# We check if we should send email
if is_end_of_month(today) and today.hour > 22:
    logging.info("It's end of month: " + str(today) + ". We send accounting email")
    admin_email_subject = "Summary of all the VMs in Stratio vSphere"
    admin_email_text = "This is a summary of all the VMs ran in the last month:\n\n"
    email_subject = "Accounting for VMs"
    # We send emails to every owner regarding their VMs and to the admin with a summary
    for i in owner_accounting:
        logging.info("Preparing accounting email for {0}".format(i))
        total_cost = 0
        email_to = owner_accounting[i][0]
        owners_vms = sorted(owner_accounting[i][1])
        admin_email_text += i + ":\n"
        for j in owners_vms:
            total_cost += j[1]
        email_text = "In the real world you would be charged for " +\
                     str(round(total_cost, 2)) + " euros\n\nThe cost is broken down the following way:\n\n"
        for j in owners_vms:
            email_text += j[0] + ": " + str(round(j[1], 2)) + " euros\n"
            admin_email_text += "    " + j[0] + ": " + str(round(j[1], 2)) + " euros\n"
        email_text += "\n\n Thank you!\n"
        send_gmail(configs["email"]["from"], email_to, email_subject, email_text, configs["email"]["username"],
                   configs["email"]["password"])
    send_gmail(configs["email"]["from"], configs["email"]["admin"], admin_email_subject, admin_email_text,
               configs["email"]["username"], configs["email"]["password"])

    # We already have sent the summary email so we clean the accounting database
    logging.info("We clean the accounting database")
    destroy_account_database(conn)
    create_account_database(conn)

# We clean a little
logging.info("Disconnecting from SQLite database")
conn.close()

logging.debug("Finished!")

sys.exit(0)
