#!/usr/bin/env python3

import subprocess

def contar_procesos_ansible():
    # Ejecutar el comando 'ps aux' para obtener una lista de todos los procesos
    resultado = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, universal_newlines=True)

    # Contar cuántas veces aparece 'ansible' en la salida del comando
    conteo_ansible = resultado.stdout.count('site-v')

    return conteo_ansible

# Llamar a la función y mostrar el resultado
numero_procesos_ansible = contar_procesos_ansible()
print(f"Número de procesos de Ansible en ejecución: {numero_procesos_ansible}")


def contar_playbooks_ansible():
    # Ejecutar el comando 'ps aux' para obtener una lista de todos los procesos
    resultado = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, universal_newlines=True)

    # Filtrar la salida para obtener solo las líneas que contienen 'ansible-playbook'
    lineas_playbook = [linea for linea in resultado.stdout.splitlines() if 'ansible-playbook' in linea]

    # Contar el número de playbooks
    conteo_playbooks = len(lineas_playbook)

    return conteo_playbooks

# Llamar a la función y mostrar el resultado
numero_playbooks_ansible = contar_playbooks_ansible()
print(f"Número de playbooks de Ansible en ejecución: {numero_playbooks_ansible}")

