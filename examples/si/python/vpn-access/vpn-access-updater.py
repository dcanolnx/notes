#!/usr/bin/python3
###############
### IMPORTS ###
###############
import re, ipaddress, subprocess, os, paramiko, datetime, configparser, random , time
import mysql.connector

############
### VARS ###
############
WORK_DIR="/security/vpn-access/"
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
    logging_file = "/security/vpn-access/hardenner_log.log"
    
    playbook_file="/security/vpn-access/sistemas-interna/ansible/playbook/"+ansible_playbook
    command = f"/usr/local/bin/ansible-playbook -u sistemas -e 'ansible_ssh_pipelining=True' -e '@/security/static/sistemas-vars.yml' -vv --key-file /home/sistemas/.ssh/id_rsa -l "+user+" "+playbook_file+"  2>&1 &"
    subprocess.Popen(command, shell=True)
    # Obtener hora actual
    hora_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Escribir en el archivo de registro
    with open(logging_file, 'a') as archivo:
        archivo.write(f"Lanzado el hardening a {user} en {hora_actual}\n")

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

def get_ara_lastExecutions(aradb_host, aradb_user, aradb_password, aradb_database, users,ansible):
    result=[]
    db_config = {
    'host': aradb_host,
    'user': aradb_user,
    'password': aradb_password,
    'database': aradb_database
    }
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        for u in users:
            query="""SELECT max(ara.hosts.updated) as date
            from ara.hosts, ara.playbooks 
            WHERE ara.hosts.name='""" + u + """' 
            AND (
                (ara.playbooks.status!= "failed" AND ara.playbooks.status!= "running") 
                OR 
                (ara.playbooks.status= "running" AND TIMESTAMPDIFF(HOUR, ara.hosts.updated, NOW()) < 1)
                OR
                (ara.playbooks.status = "failed" AND TIMESTAMPDIFF(HOUR, ara.hosts.updated, NOW()) >= 4)
            )
            AND ara.hosts.playbook_id=ara.playbooks.id 
            AND ara.playbooks.path LIKE '%""" + ansible + """'
            LIMIT 1"""
            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                result.append([u,row[0]])

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
        return result

############
### MAIN ###
############
if __name__ == "__main__":

    #READ CONFIG FILE
    config = configparser.ConfigParser()
    config.read('vpn-access.config')

    firewall_hostname=config["FIREWALL"]["firewall_hostname"]
    firewall_user=config["FIREWALL"]["firewall_user"]
    firewall_password=config["FIREWALL"]["firewall_password"]
    
    aradb_host=config["ARADB"]["aradb_host"]
    aradb_user=config["ARADB"]["aradb_user"]
    aradb_password=config["ARADB"]["aradb_password"]
    aradb_database=config["ARADB"]["aradb_database"]

    securitydb_host=config["SECURITYDB"]["securitydb_host"]
    securitydb_user=config["SECURITYDB"]["securitydb_user"]
    securitydb_password=config["SECURITYDB"]["securitydb_password"]
    securitydb_database=config["SECURITYDB"]["securitydb_database"]

    ansible_playbook=config["PLAYBOOK"]["ansible_playbook"]

    #USERS DEFINED MANUALLY TO PROCSESS
    #USERS=['alopez','mafernandez','acascajero','stamayo','mraposo','aluengo','ajimenezvisus','jmtroconis','agorines','abravo','mruizmartinez','aalfonso','rherrero','jcgarcia','dandres','cnavalon','dalonso','rcastro','jmboyero','jorgejimenez','pgo-nextret','dpalomo','cmunoz','lrios','ibasarte','vherrerias','pgdiaz','jperez','mdelgado','ababe','usarasola','asoriano','samuelgonzalez','jesusramos','rlopezroldan','alejandromateos','adoblas','imorales','jmolina','dpaul','ccaballero','rodrigocastro','dsantibanez','jmontesinos','arey','ocamps','egonzalez','hcortes','sanchezsanz','cluaces','jalonso','carlosagudo','agala','alejandrosanz','jamartinez','danielrodriguez','jvela','hdominguez','lhermida','acamacho','pmarin','mmartinez','ernestolazaro','alvarojimenez','malgarra','soniacalvo','adrianhernandez','scalvo','jcarretero','dgutierrez','lcarballo','darroyo','agarciaprieto','pbedia','rotero','fjgavilan','rbelda','jelboutaibi','cristinalopez','armando.perez','miguelocon','vmorales','martalopez','jbernal','diegomartinez','bglowacz','smartin','jmruiz','afsantamaria','atejero','gram','abailon','dmendes','jmunoz','lgutierrez','cfuertes','msierra','vbrouard','sdabbour','amateos','javiergarcia','oyurkiv','jmoralo','jortega','agolubinskiy','erodriguez','jgduarte','jiniguez','mjara','jfmodrono','rsalazar','cagomez','igurucelain','ldiaz','odelafuente','spineda','evega','abenitez','majimenez','emgaitan','antoniogomez','iolivares','rprivado','osanchez','jesusgarciag','dalvarez','xgan','jsevillano','acampesino','epons','mrivera','jgracia','aahamad','bpariente','abarbara','monicamoreno','descudero','acontreras','albertogomez','jmonedero','dcano','pgonzalez','fmedrano','jmrojas','emoyano','jarranz','antoniomiranda','eortiz','ignaciomartinez','fjcorrales','fjrodriguez','jmbriceno','tperez','aalvarez','vdelacalle','ddelasheras','vjacynycz','jguerrero','tvalido','ssantos','acarrasco','jgterradillos','hjacynycz','avelasco','msantana','jlsanchez','jpascual','alfonsofernandez','esierra','tmorales','mmoreno','skhalifa','gmachin','rmolina','cgil','jbarrocal','imoreno','mmoro','lrecio','shernandez','jdiez','pholnick','uarrien','sergisanchez','josemanueldiaz','forselli','msequedo','apaniagua','dfernandez','dmatilla','juria','eborque','shamoud','albavargas','pablo.langa','martabe','mberrojalbiz','rvelasco','oscargomez','dvelasco','bgago','mleida','aberro','pdiaz','gperianez','adelgado','grios','mlorenzo','jhernandez','orodriguez','jneira','alvarolopez','fgavilan','horozco','santiagosanchez','amontes','iiglesias','mgilperez','bsuarez','csantisteban','enriquegarcia','relouarghani','javendano','mavazquez']
    #random.shuffle(USERS)

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
    execution_count = 0
    execution_limit = 0
#    launch_ansible('mleohernandez',ansible_playbook) 
#    launch_ansible('drobayo',ansible_playbook)
#    launch_ansible('pedroruiz',ansible_playbook) 
#    launch_ansible('diamprea',ansible_playbook) 
#    launch_ansible('grueda',ansible_playbook) 
#    launch_ansible('cclopez',ansible_playbook)
#    launch_ansible('agonzalez',ansible_playbook) 
#    launch_ansible('jpalmero',ansible_playbook) 
#    launch_ansible('ajgonzalez',ansible_playbook) 
#    launch_ansible('jorgejimenez',ansible_playbook)



    #GET LAST TIME ANSIBLE WAS LAUNCHED AND EXECUTE IT OR NOT
    users_lastexecution=get_ara_lastExecutions(aradb_host, aradb_user, aradb_password, aradb_database, users_proccess,ansible_playbook)
    for u in users_lastexecution:
        if execution_count >= execution_limit:
            # Si se alcanza el límite de ejecuciones, salir del bucle
            print("INFO: Se ha alcanzado el límite de ejecuciones.")
            break
        if(u[1] is None):
            print("INFO: Has never been executed on user: "+u[0])
            launch_ansible(u[0],ansible_playbook)
            execution_count += 1
        else:
            time_difference = datetime.datetime.now() - u[1]
            if time_difference > datetime.timedelta(days=30):
                print("INFO: Last executed on user "+u[0]+" is more than 30 days("+str(u[1])+")")
                launch_ansible(u[0],ansible_playbook)
            else:
                print("OK: Last executed on user "+u[0]+" is within the last 30 days ("+str(u[1])+")")

#######
#NOTES:
#######
## Comprobar si el usuario lleva con el PC sin reiniciar mas de 7 dias
## Recopilar quienes han cambiado los parametros



