#!/usr/bin/python3
###############
### IMPORTS ###
###############
import re, ipaddress, subprocess, os, paramiko, datetime, configparser, random , time
import mysql.connector

############
### VARS ###
############
WORK_DIR="/security/py-controller/"
GIT_REPOSITORY_NAME="sistemas-interna"
GIT_REPOSITORY="git@github.com:Stratio/sistemas-interna.git"

###############
### METHODS ###
###############
def is_valid_ip(ip_str):
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def get_users_connected(hostname, username, password, command):
    users=[]
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)

        stdin, stdout, stderr = client.exec_command(command)
        print(" ")
        output = stdout.read().decode("utf-8").splitlines()
        print(output)
        print(" ")
        for line in output:
            if "LDAP" in line:
                result=re.split('\t| ', str(line))
                filtered_list = list(filter(lambda item: item != "", result))
                if len(filtered_list) > 1:
                    username=filtered_list[1]
                    ip=filtered_list[-1]
                    if is_valid_ip(ip):
                        if username not in users:
                            users.append(username)
                            users.append(ip)
                else:
                    print("ERROR: Getting values from fortigate command")

        return users

    finally:
        client.close()

def generate_ansible_host(users):
    with open('ansible_hosts', 'w') as file:
        file.write("[linux-users]\n")
        l=0
        while l < len(users):
            file.write(users[l]+"				ansible_host="+users[l+1]+"\n")
            l=l+2


def launch_ansible(user,ansible_playbook):
    logging_file = "/security/py-controller/log.log"
    
    playbook_file="/security/vpn-access/sistemas-interna/ansible/playbook/"+ansible_playbook
    command = f"/usr/local/bin/ansible-playbook -u sistemas -e 'ansible_ssh_pipelining=True' -e '@/security/static/sistemas-vars.yml' -vv --key-file /home/sistemas/.ssh/id_rsa -l "+user+" "+playbook_file+"  2>&1 &"
    subprocess.Popen(command, shell=True)
    # Obtener hora actual
    hora_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Escribir en el archivo de registro
    with open(logging_file, 'a') as archivo:
        archivo.write(f"     » Lanzado el comcheck a {user} en:  {hora_actual}\n")

def update_repository():
    if not os.path.exists(WORK_DIR+GIT_REPOSITORY_NAME):
        # Clone the repository if the directory doesn't exist
        subprocess.run(['git', 'clone', GIT_REPOSITORY, WORK_DIR+GIT_REPOSITORY_NAME])
    else:
        # Change directory to the local repository
        os.chdir(WORK_DIR+GIT_REPOSITORY_NAME)
        
        # Fetch and reset to update the repository
        subprocess.run(['git', 'fetch', '--all'])
        subprocess.run(['git', 'reset', '--hard', 'origin/master'])  # Assuming master branch, adjust as needed

def get_users_linux(securitydb_host, securitydb_user, securitydb_password, securitydb_database):
    result=[]
    db_config = {
    'host': securitydb_host,
    'user': securitydb_user,
    'password': securitydb_password,
    'database': securitydb_database
    }
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query="select user,so from stratiosecuritycontroller where so like '%Ubuntu%' or so like '%UStratio%'"

        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            result.append(row[0])

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
        return result
def contar_playbooks_ansible():
    # Ejecutar el comando 'ps aux' para obtener una lista de todos los procesos
    resultado = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, universal_newlines=True)

    # Filtrar la salida para obtener solo las líneas que contienen 'ansible-playbook'
    lineas_playbook = [linea for linea in resultado.stdout.splitlines() if 'ansible-playbook' in linea]

    # Contar el número de playbooks
    conteo_playbooks = len(lineas_playbook)

    return conteo_playbooks


############
### MAIN ###
############
if __name__ == "__main__":
    logging_file = "/security/py-controller/log.log"
    hora_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(logging_file, 'a') as archivo:
        archivo.write(f"  \n")
        archivo.write(f" ««« Inicio de ejecucion {hora_actual} »»»  \n")
    #READ CONFIG FILE
    config = configparser.ConfigParser()
    config.read('vpn-access.config')

    firewall_hostname=config["FIREWALL"]["firewall_hostname"]
    firewall_user=config["FIREWALL"]["firewall_user"]
    firewall_password=config["FIREWALL"]["firewall_password"]

    securitydb_host=config["SECURITYDB"]["securitydb_host"]
    securitydb_user=config["SECURITYDB"]["securitydb_user"]
    securitydb_password=config["SECURITYDB"]["securitydb_password"]
    securitydb_database=config["SECURITYDB"]["securitydb_database"]

    ansible_playbook=config["PLAYBOOK"]["ansible_playbook"]


    #USERS CONNECTED TO VPN, GENERATE ANSIBLE HOSTS AND UPDATE REPOSITORY
    users_connected = get_users_connected(firewall_hostname, firewall_user, firewall_password, "a get vpn ssl monitor")
    generate_ansible_host(users_connected)
    update_repository()

    #USERS LINUX
    users_linux=get_users_linux(securitydb_host, securitydb_user, securitydb_password, securitydb_database)

    #CREATE user_proccess VAR WITH USERS CONNECTED AND LINUX SO
    users_proccess=[]
    for u in users_connected:
        if u in users_linux:
            users_proccess.append(u)

    #GET LAST TIME ANSIBLE WAS LAUNCHED AND EXECUTE IT OR NOT
    print("user to launch")
    print(users_proccess)
    for u in users_proccess:
        launch_ansible(u,ansible_playbook)

    hora_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(logging_file, 'a') as archivo:
        archivo.write(f" ««« Fin de ejecucion de com checks a las {hora_actual} »»»  \n")
        archivo.write(f"  \n")
        archivo.write(f"  \n")

