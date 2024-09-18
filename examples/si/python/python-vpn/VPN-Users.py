#!/usr/bin/python3

##################
###### IMPORTS
##################
import requests, logging, paramiko, configparser, base64, urllib3, re, subprocess, argparse, sys, logging
from datetime import datetime,timedelta
import mysql.connector

##################
###### VARS
##################
class Employee:
    def __init__(self,hostname,SN,lastERAUpdate,esetInstalled,SN_GLPI):
        self.hostname = hostname
        self.SN = SN
        self.lastERAUpdate = lastERAUpdate
        self.esetInstalled = esetInstalled
        self.SN_GLPI= SN_GLPI

##################
###### FUNCTIONS
##################
def get_ldap_users(ldap_url,ldap_user,ldap_password,ldap_basedn):
    users=[]
    output = subprocess.check_output('ldapsearch -H '+ldap_url+' -D "'+ldap_user+'" -w'+ldap_password+' -b "ou=Others,ou=Spain,ou=Internal,ou=Users,dc=stratio,dc=com" dn | grep "ou=Others,ou=Spain,ou=Internal,ou=Users,dc=stratio" | grep -v "#"', shell=True)
    for u in str(output).split():
        user=re.findall('cn=(.*?),ou=Others', u)
        if len(user) == 1:
            users.append(user[0])
    users.sort()
    return users

def get_ldap_vpn_users(ldap_url,ldap_user,ldap_password,ldap_basedn):
    users=[]
    output = subprocess.check_output('ldapsearch -H '+ldap_url+' -D "'+ldap_user+'" -w'+ldap_password+' -b "cn=VPN,ou=Internal,ou=Groups,dc=stratio,dc=com" member | grep "ou=Others" | grep -v "#"', shell=True)
    for u in str(output).split():
        user=re.findall('cn=(.*?),ou=Others', u)
        if len(user) == 1:
            users.append(user[0])
    users.sort()
    return users

def remove_ldap_vpn_user(ldap_url,ldap_user,ldap_password,ldap_basedn,user):
    output = subprocess.check_output('ldapmodify -H '+ldap_url+' -D "'+ldap_user+'" -w'+ldap_password+""" <<EOF
dn: cn=VPN,ou=Internal,ou=Groups,dc=stratio,dc=com
changetype: modify
delete: member
member: cn="""+user+""",ou=Others,ou=Spain,ou=Internal,ou=Users,dc=stratio,dc=com
EOF""", shell=True)

def add_ldap_vpn_user(ldap_url,ldap_user,ldap_password,ldap_basedn,user):
    output = subprocess.check_output('ldapmodify -H '+ldap_url+' -D "'+ldap_user+'" -w'+ldap_password+""" <<EOF
dn: cn=VPN,ou=Internal,ou=Groups,dc=stratio,dc=com
changetype: modify
add: member
member: cn="""+user+""",ou=Others,ou=Spain,ou=Internal,ou=Users,dc=stratio,dc=com
EOF""", shell=True)

# Function to get all users connected on VPN
def get_vpn_users(fortigate_url, api_token):
    logging.info("Getting VPN Users")

    forti_vpn = "https://" + fortigate_url + ":443"
    forti_api_path = "/api/v2/monitor/vpn/ssl"
    forti_api_token = "?access_token=" + api_token
    logging.info("Url to access: " + forti_vpn+forti_api_path+forti_api_token)

    forti_api_headers = {'accept': 'application/json'}
    logging.info("Using Headers: " + str(forti_api_headers))

    logging.info("Launching Requests")
    forti_vpn_users = []
    resp = requests.get(forti_vpn+forti_api_path+forti_api_token, headers=forti_api_headers, verify=False)
    if resp.status_code != 200:
        logging.error("Request status: " + str(resp.status_code))
        logging.error(request_status_code(resp.status_code))
        return forti_vpn_users

    logging.info("Created users array")
    for user in resp.json()["results"]:
        logging.info("Get user: " + user['user_name'])
        forti_vpn_users.append(user['user_name'])

    logging.info("Return users array")
    return forti_vpn_users

# Function to down a user VPN
def remove_vpn_user(fortigate_url, api_token, user_name):
    logging.info("Closing VPN session for user " + str(user_name))
    forti_vpn = "https://" + fortigate_url + ":443"

    logging.info("Getting all user sessions IDs")
    forti_api_path = "/api/v2/monitor/vpn/ssl"
    forti_api_token = "?access_token=" + api_token
    logging.info("Url to access: " + forti_vpn + forti_api_path + forti_api_token)

    forti_api_headers = {'accept': 'application/json'}
    logging.info("Using Headers: " + str(forti_api_headers))

    logging.info("Launching Requests")
    resp = requests.get(forti_vpn + forti_api_path + forti_api_token, headers=forti_api_headers, verify=False)
    if resp.status_code != 200:
        logging.error("Request status: " + str(resp.status_code))
        logging.error(request_status_code(resp.status_code))
        exit(-1)

    forti_vpn_user_id = []
    logging.info("Created user array")
    for user in resp.json()["results"]:
        if user['user_name'] == str(user_name):
            forti_vpn_user_id.append(user['subsessions'][0]['index'])

    logging.info("Close all sessions for user " + str(user_name))
    logging.info("Sessions for user " + str(user_name) + ": " + str(forti_vpn_user_id))
    forti_api_path = "/api/v2/monitor/vpn/ssl/delete"
    forti_api_token = "?access_token=" + api_token
    logging.info("Url to access: " + forti_vpn+forti_api_path+forti_api_token)

    forti_api_headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    logging.info("Using Headers: " + str(forti_api_headers))

    for user_id in forti_vpn_user_id:
        forti_api_data = {
            "type": "subsessions",
            "index": user_id,
        }
        logging.info("Using Body: " + str(forti_api_data))

        logging.info("Launching requests for user index " + str(user_id))
        resp = requests.post(forti_vpn+forti_api_path+forti_api_token, headers=forti_api_headers, json=forti_api_data,
                             verify=False)
        if resp.status_code != 200:
            logging.error("Request status: " + str(resp.status_code))
            logging.error(request_status_code(resp.status_code))
            exit(-1)

    logging.info("User " + str(user_name) + " dropped")

# Function to tranform Fortigate Status Codes
def request_status_code(status_code: int):
    status_codes = {
        400: "Bad Request: Request cannot be processed by the API",
        401: "Not Authorized: Request without successful login session",
        403: "Forbidden: Request is missing CSRF token or administrator is missing access profile permissions.",
        404: "Resource Not Found: Unable to find the specified resource.",
        405: "Method Not Allowed: Specified HTTP method is not allowed for this resource.",
        413: "Request Entity Too Large: Request cannot be processed due to large entity",
        424: "Failed Dependency: Fail dependency can be duplicate resource, missing required parameter, " +
             "missing required attribute, invalid attribute value",
        429: "Access temporarily blocked: Maximum failed authentications reached. The offended source is " +
             "temporarily blocked for certain amount of time.",
        500: "Internal Server Error: Internal error when processing the request",
    }
    return status_codes.get(status_code, "Wrong Status Code")

# Function to get SN and last connected from ERA SERVER
def get_eraserver_information(users,era_server,era_ssh_username,era_ssh_password,era_db_name,era_db_user,era_db_password):
    # We will exec 2 SQLs on ERA to create arr_out which contains [username1, sn1, last_conected1, username2, ..... ]
    employees=[]
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect( hostname = era_server, username = era_ssh_username, password = era_ssh_password )
    arr_out=[]

    # SQL 1 
    sql="select tbl_computers.computer_name, tbld_identifiers_list_status_value.Value SerialNumber,tbl_computers_aggr.computer_connected from tbl_computers,tblf_identifiers_list_status,tbld_identifiers_list_status_value,tbl_computers_aggr where tbl_computers.computer_name IN ("
    for user in users:
        sql+="'"+user+"',"
    sql=sql[:-1]+") and tblf_identifiers_list_status.SourceUuid=tbl_computers.computer_uuid and tbld_identifiers_list_status_value.skey=tblf_identifiers_list_status.Value_skey and tbld_identifiers_list_status_value.Value not like '"+user+"' and tbl_computers_aggr.computer_id=tbl_computers.computer_id  GROUP BY tbl_computers.computer_name"


    cnx = mysql.connector.connect(user=era_db_user, password=era_db_password, database=era_db_name, host=era_server)
    cursor = cnx.cursor()
    query = (sql)
    cursor.execute(query)
    records=cursor.fetchall()

    for row in records:
        if(row[0] != ""):
            arr_out.append(row[0])
            sn=row[1].replace('\r', '').replace('\n', '').replace(' ','')
            arr_out.append(sn)
            if (row[2]!=None):
                last_connect_user = row[2] + timedelta(hours=2)
            arr_out.append(str(last_connect_user))
    
    cursor.close()
    cnx.close()

    # SQL 2 - to know if user has agent and eset installed
    users_eset_installed=[]
    sql="select computer_name from tblf_apps_installed_status,tbl_computers where tbl_computers.computer_name IN ("
    for user in users:
        sql+="'"+user+"',"
    sql=sql[:-1]+") and tbl_computers.computer_uuid=tblf_apps_installed_status.SourceUuid and (tblf_apps_installed_status.Name_skey=82 or tblf_apps_installed_status.Name_skey=292 ) group by computer_name;"
    cnx = mysql.connector.connect(user=era_db_user, password=era_db_password, database=era_db_name, host=era_server)
    cursor = cnx.cursor()
    query = (sql)
    cursor.execute(query)
    secondSqlResult=cursor.fetchall()
    for i in secondSqlResult:
        users_eset_installed.append(str(i)[2:-3])


    # Iterate over users to know if they appears on array arr_out
    for user in users:
        if user in arr_out:
            ser=str(arr_out[arr_out.index(str(user))+1])
            last=str(arr_out[arr_out.index(str(user))+2])
            if user in users_eset_installed:
                employees.append(Employee(user,ser,last,True,""))
            else:
                employees.append(Employee(user,ser,last,False,""))
        else:
            employees.append(Employee(user,"","",False,""))
    c.close()
    return employees

# Function to get SN from GLPI
def get_glpi_information(users, glpi_server, glpi_db_name, glpi_db_user, glpi_db_password):
    employees=[]
    arr_out=[]

    cnx = mysql.connector.connect(user=glpi_db_user, password=glpi_db_password, database=glpi_db_name, host=glpi_server)
    cursor = cnx.cursor()
    sql="select name,serial from glpi_computers where name IN ("
    for user in users:
        sql+="'"+user.hostname+"',"
    sql=sql[:-1]+") and is_deleted=0;"
    query = (sql)
    
    cursor.execute(query)
    records=cursor.fetchall()

    for row in records:
        arr_out.append(row[0])
        arr_out.append(row[1])
    
    cursor.close()
    cnx.close()

    # Iterate over users
    for user in users:
        if user.hostname in arr_out:
            # User exists on GLPI only one time
            if arr_out.count(str(user.hostname))==1:
                serial=str(arr_out[arr_out.index(str(user.hostname))+1])
                employees.append(Employee(user.hostname,user.SN,user.lastERAUpdate,user.esetInstalled,[serial]))
            # User exists on GLPI more than one time
            else:
                employees.append(Employee(user.hostname,user.SN,user.lastERAUpdate,user.esetInstalled,["",""]))
        # User does not exists on GLPI
        else:
            employees.append(Employee(user.hostname,user.SN,user.lastERAUpdate,user.esetInstalled,""))  
#    c.close()
    return employees  

def filter_list(full_list, excludes):
    s = set(excludes)
    return (x for x in full_list if x not in s)

def replase_users_differenthostname(users):
    with open('vpn-differenthostname.whitelist') as my_file:
        for line in my_file:
            if(len(line.rstrip().split(';'))==2):
                hostname_expected=str(line.rstrip().split(';')[0])
                hostname_real=str(line.rstrip().split(';')[1])
                if (hostname_expected in users):
                    users.remove(hostname_expected)
                    users.append(hostname_real)
            else:
                logging.error("ERROR READING vpn-differenthostname.whitelist FILE")
    return users


##################
###### MAIN
##################
def main():
    logging.basicConfig(filename="log/vpn-users.log",level=logging.INFO)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--allusers ","-a", action="store_true",dest="allusers")
    parser.add_argument("--vpnusers ","-b", action="store_true",dest="vpnusers")
    args = parser.parse_args()

    # Read config file
    config = configparser.ConfigParser()
    config.read('vpn-users.config')
    fortigate_url=config["FORTIGATE"]["fortigate_url"]
    api_token=config["FORTIGATE"]["api_token"]

    era_server=config["ERA"]["era_server"]
    era_ssh_username=config["ERA"]["era_ssh_username"]
    era_ssh_password=str(base64.b64decode(config["ERA"]["era_ssh_password"]))[2:-3]
    era_db_name=config["ERA"]["era_db_name"]
    era_db_user=config["ERA"]["era_db_user"]
    era_db_password=config["ERA"]["era_db_password"]
    
    glpi_server=config["GLPI"]["glpi_server"]
    glpi_db_name=config["GLPI"]["glpi_db_name"]
    glpi_db_user=config["GLPI"]["glpi_db_user"]
    glpi_db_password=config["GLPI"]["glpi_db_password"]

    ldap_url=config["LDAP"]["ldap_url"]
    ldap_user=config["LDAP"]["ldap_user"]
    ldap_password=config["LDAP"]["ldap_password"]
    ldap_basedn=config["LDAP"]["ldap_basedn"]
    ldap_user_read=config["LDAP"]["ldap_user_read"]
    ldap_password_read=config["LDAP"]["ldap_password_read"]

    # Define vars
    employeestemp=[]
    employees=[]
    temporal_users=[]
    users=[]
    logging.info("info: GET LDAP INFORMATION")
    if args.allusers:
        temporal_users=get_ldap_users(ldap_url,ldap_user_read,ldap_password_read,ldap_basedn)
    if args.vpnusers:
        temporal_users=get_vpn_users(fortigate_url,api_token)

    #temporal_users=['yvillamil']
    #temporal_users=temporal_users[:5]
    # Remove users who appears in vpn-users.whitelist
    users_ldap_vpn=get_ldap_vpn_users(ldap_url,ldap_user,ldap_password,ldap_basedn)
    #print(str(users_ldap_vpn))
    whitelist_users = []
    with open('vpn-users.whitelist') as my_file:
        for line in my_file:
            if (not str(line.strip()).startswith("#") and str(line.strip())!=""):
                whitelist_users.append(line.rstrip())
    users = list(filter_list(temporal_users, whitelist_users))
    # Replace users hostname which appears in vpn-differenthostname.whitelist
    users=replase_users_differenthostname(users)
    logging.info("info: GET ERA INFORMATION"+str(datetime.now()))
    # Get ERA information
    employeestemp=get_eraserver_information(users,era_server,era_ssh_username,era_ssh_password,era_db_name,era_db_user,era_db_password)
    # Get GPLI information
    logging.info("info: GET GLPI INFORMATION"+str(datetime.now()))
    employees=get_glpi_information(employeestemp, glpi_server, glpi_db_name, glpi_db_user, glpi_db_password)
    logging.info("info: SHOW INFORMATION "+str(datetime.now()))
    # Message output for each user connected
    employeesOK=0
    employeesERROR=0
    for e in employees:
        message=""
        correcto=True
        if e.SN != "":
            if e.esetInstalled==True:
                message+=" Antivirus SN: "+str(e.SN)+";LastUpdate: "+e.lastERAUpdate
                last_connect_user = datetime.strptime(e.lastERAUpdate, '%Y-%m-%d %H:%M:%S')
                yesterday = datetime.now() - timedelta(days=5)
                if(last_connect_user<yesterday):
                    message+=";El antivirus se actualizo por ultima vez el "+e.lastERAUpdate
                    correcto=False
                elif len(e.SN_GLPI)==0:
                    message+=";Usuario no aparece en GLPI (SN de Antivirus "+e.SN+")"
                    #correcto=False
                    correcto=True
                elif len(e.SN_GLPI)>1:
                    message+=";Usuario dispone de varios dispositivos asignados en GLPI (SN de Antivirus "+e.SN+")"
                    correcto=True
                    #correcto=False
                else:
                    if str(e.SN_GLPI[0]) == e.SN:
                        message+=";SN de GPLI igual que SN de antivirus"
                    else:
                        message+=";El SN de GLPI (" +str(e.SN_GLPI[0])+") y el SN de Antivirus ("+e.SN+") no coinciden"
                        #correcto=False
                        correcto=True
            else:
                message+=";Agente de antivirus no instalado"
                correcto=False
        else:
            message+=";Agente de antivirus no instalado"
            correcto=False

        if correcto:
            logging.info("OK;"+e.hostname+";"+message)
            if e.hostname not in users_ldap_vpn:
                logging.info(e.hostname+" add user from ldap vpn group")
                add_ldap_vpn_user(ldap_url,ldap_user,ldap_password,ldap_basedn,e.hostname)
            employeesOK=employeesOK+1
        else:
            logging.info(" ERROR;"+e.hostname+";"+message)
            if e.hostname in users_ldap_vpn:
                logging.info(e.hostname+" del user from ldap vpn group")
                remove_ldap_vpn_user(ldap_url,ldap_user,ldap_password,ldap_basedn,e.hostname)
            employeesERROR=employeesERROR+1  
    logging.info("OK: "+str(employeesOK)+" / ERROR: "+str(employeesERROR))

if __name__ == "__main__":
    main()

