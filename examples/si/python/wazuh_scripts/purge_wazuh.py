#!/usr/bin/env python3
import logging, os, configparser, requests, paramiko
from datetime import datetime, timedelta
import subprocess

config_file_path="./wazuh.config"

def load_config(config_file_path):
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config

def purge_wazuh():
    api_url = "https://wazuh-aws.int.stratio.com:55000/security/user/authenticate?raw=true"
    username = config['WAZUH']["USER"]
    password = config['WAZUH']["PASSWORD"]
    response = requests.get(api_url, auth=(username, password), verify=False)
    
    if response.status_code == 200:
        token = response.text
        url = "https://wazuh-aws.int.stratio.com:55000/agents?pretty=true&offset=1&select=status%2Cid%2Cname%2Cgroup%2ClastKeepAlive%2Cos.version%2Cos.name%2CdateAdd"
        response = requests.get(url, verify=False, headers={'Authorization': 'Bearer ' + token})
        data = response.json()
        print(data)
        with open('purge.log', 'a') as log_file:  # Abre el archivo purge.log para agregar contenido al final
            for item in data['data']['affected_items']:
                last_keep_alive_str = item.get('lastKeepAlive')
                
                if last_keep_alive_str:
                    last_keep_alive = datetime.strptime(last_keep_alive_str, '%Y-%m-%dT%H:%M:%S+00:00')
                    days_since_last_keep_alive = (datetime.now() - last_keep_alive).days
                    
                    if days_since_last_keep_alive > 14:
                        log_msg = f"El usuario {item['name']} con ID {item['id']} no se ha conectado en los últimos {days_since_last_keep_alive} días.\n"
                        log_file.write(log_msg)  # Escribe el mensaje en el archivo de log
                        remove_agent(item['id'], log_file)    # Llama a la función remove_agent con el ID del agente
                else:
                    log_msg = f"El usuario {item['name']} no tiene un registro de lastKeepAlive.\n"
                    log_file.write(log_msg)  # Escribe el mensaje en el archivo de log
                    remove_agent(item['id'], log_file)    # Llama a la función remove_agent con el ID del agente

    else:
        print("Request wazuh(" + api_url + ") fail HTTP response is: " + str(response.status_code))

def remove_agent(agent_id, log_file):
    try:
        command = f'/var/ossec/bin/manage_agents -r {agent_id}'
        
        # Ejecutar el comando localmente
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            # Éxito en la eliminación del agente
            log_msg = f"Agente eliminado: {agent_id}\n"
            log_file.write(log_msg)
        else:
            # Error al ejecutar el comando
            error_msg = f"Error al ejecutar el comando para eliminar el agente {agent_id}:\n"
            error_msg += result.stderr
            log_file.write(error_msg)
            print(error_msg)
    except Exception as e:
        # Error general
        error_msg = f"Error al ejecutar el comando para eliminar el agente {agent_id}: {str(e)}\n"
        log_file.write(error_msg)
        print(error_msg)


    
##################
###### MAIN
##################
def main():

    if os.path.isfile(config_file_path):
        # Read config file
        global config
        config=load_config(config_file_path)
        purge_wazuh()

if __name__ == "__main__":
    main()
