#!/usr/bin/python3

#IMPORTS
import requests, random, string, logging, re, json, argparse, wget
from time import sleep
import os, paramiko, shutil, subprocess
from multiprocessing import Pool
from requests.auth import HTTPBasicAuth
import sys

import io
try:
	to_unicode = unicode
except NameError:
	to_unicode = str

############################
#####    DEFAULTS      #####
############################
MAX_PAGES_ITERATIONS=100000
DOCKER_PORT=""
REPOSITORY_TYPE=""

############################
#####     VARS         #####
############################
nexusURL = "http://qa.int.stratio.com:8081/"
nexusDocker= "qa.int.stratio.com"
nexusURLDestiny= "http://qa.int.stratio.com:8081"
nexusDockerDestiny= "http://qa.int.stratio.com"

componentsEndpoint = "service/rest/v1/components"
repositories_raw_migrate = ["paas","thirdparty-binaries"]
txt_dockers_oldnexus="contenedores.txt"
json_maven_oldnexus="mavens.json"
json_raw_oldnexus="raw.json"
json_npm_oldnexus="npm.json"
temporal_dir_downloads="tmp/"

USER_NEXUS_DESTINY="admin"
PASSWORD_NEXUS_DESTINY="26c7e33117004051078a26e3d64944b2"

############################
#####      COMMON      #####
############################
def get_items(repository):
	last_page=False
	items=[]
	request_payload = { 'repository': repository }
	r = requests.get(nexusURL + componentsEndpoint, params=request_payload)
	json_result = r.json()
	num=0
	while ( num < MAX_PAGES_ITERATIONS ):
		#sleep(0.2)
		for i in json_result['items']:
			# START PROCESS
			if (repository.startswith("docker")):
				items.append(i['name']+":"+i['version'])
			if (REPOSITORY_TYPE == "maven2"):
				array_assets=[]
				for asset in i['assets']:
					array_assets.append(asset['downloadUrl'])
				dict_component = {'name': str(i['name']), 'group': str(i['group']), 'version': str(i['version']), 'id': str(i['id']), 'assets': array_assets }
				items.append(dict_component)
			if (REPOSITORY_TYPE == "raw"):
				array_assets=[]
				for asset in i['assets']:
					array_assets.append(asset['downloadUrl'])
				print(" -> "+str(i))
				dict_component = {'repository': repository,'name': str(i['name']), 'group': str(i['group']), 'version': str(i['version']), 'id': str(i['id']), 'assets': array_assets }
				items.append(dict_component)
			if (REPOSITORY_TYPE == "mvn"):
				array_assets=[]
				for asset in i['assets']:
					array_assets.append(asset['downloadUrl'])
				dict_component = {'name': str(i['name']), 'group': str(i['group']), 'version': str(i['version']), 'id': str(i['id']), 'assets': array_assets}
				items.append(dict_component)
			# END PROCESS
		if( json_result['continuationToken'] is None):
			print("END CORRECTLY")
			break
		sub_request_payload = {'repository': repository, 'continuationToken': json_result['continuationToken']}
		sub_request = requests.get(nexusURL + componentsEndpoint, params=sub_request_payload)
		if not str(sub_request.status_code).startswith("2"):
			#logging.debug("Received error. Aborting list, proceeding to deletion phase")
			break

		json_result = sub_request.json()
		num += 1
		print("Pag: "+str(num)+" / Repository: "+repository)
	return items

############################
##### DOCKER MIGRATION #####
############################
def exportDocker(repo):
	items=get_items(repo)
	with open(txt_dockers_oldnexus, 'w') as f:
		for item in items:
			f.write("%s\n" % item)

def loadDocker():
	with open(txt_dockers_oldnexus, 'r') as f:
		containers = [line.rstrip(u'\n') for line in f]
	print( containers )
	for c in containers:
		print(c)
		request_payload = {'docker.imageName': c.split(':')[0], 'docker.imageTag': c.split(':')[1] }
		r = requests.get(nexusURLDestiny + "/service/rest/v1/search", params=request_payload)
		json_result = r.json()
		#if len(json_result['items'])>0:
		#	print("Ya existe "+c)
		#	sleep(0.3)
		if False:
			print('HOLA')
		else:
			print("No existe "+c)
			os.system('docker pull '+nexusDocker+":10443"+"/"+c)
			print('docker pull '+nexusDocker+":10443"+"/"+c)
			os.system('docker tag '+nexusDocker+":10443"+"/"+c+" "+nexusDockerDestiny+":5006"+"/"+c)
			print('docker tag '+nexusDocker+":10443"+"/"+c+" "+nexusDockerDestiny+":5006"+"/"+c)
			print('docker push '+nexusDockerDestiny+":5006"+"/"+c)
			os.system('docker push '+nexusDockerDestiny+":5006"+"/"+c)
			#os.system('docker rmi '+nexusDockerDestiny+DOCKER_PORT+"/"+c)

############################
#####  MAVEN MIGRATION #####
############################
def exportMaven(repo):
	items=get_items(repo)
	with open(json_maven_oldnexus, 'w') as outfile:
		json.dump(items, outfile)

def loadMaven(repo):
	with open(json_maven_oldnexus) as f:
		data = json.load(f)
	i=1
	for component in data:
		print("-> "+str(component['name'])+" ("+str(i)+"/"+str(len(data))+")")
		i=i+1
		if( i > -1 ):
			if not os.path.exists(temporal_dir_downloads+component['name']):
				os.makedirs(temporal_dir_downloads+component['name'])
			print(temporal_dir_downloads+component['name'])
			for asset in component['assets']:
				wget.download(asset, temporal_dir_downloads+component['name'])
			files=os.listdir(temporal_dir_downloads+component['name'])
			
			prueba=requests.Session()
			prueba.auth=HTTPBasicAuth(USER_NEXUS_DESTINY, PASSWORD_NEXUS_DESTINY)
			params_content={'repository': repo}
			print("version: "+str(component['version']))
			data_content={ 'maven2.groupId': str(component['group']), 'maven2.version': component['version'],'maven2.artifactId': component['name'], 'maven2.generate-pom': False}
			file_content={}
			n_file=1
			for f in files:
				data_content.clear()
				file_content.clear()
				data_content={ 'maven2.groupId': str(component['group']), 'maven2.version': component['version'],'maven2.artifactId': component['name'], 'maven2.generate-pom': False}
				print(data_content)
				if(f.split('.')[-1]!="md5" and f.split('.')[-1]!="sha1"):
					#clasifier=re.findall("\.[0-9]-(.*)\.",f)
					#if(len(clasifier)==1):
					#	data_content['maven2.asset'+str(n_file)+'.classifier']=clasifier[0]
					data_content['maven2.asset'+str(n_file)+'.extension']=f.split('.')[-1]
					file_content['maven2.asset'+str(n_file)]=open(temporal_dir_downloads+component['name']+"/"+f,'rb')
					r = prueba.post(nexusURLDestiny + "/service/rest/v1/components",data=data_content, files=file_content, params=params_content)
					print("params: "+str(params_content)+" response "+str(r))
					sleep(0.3)
				n_file+=1
			if os.path.exists(temporal_dir_downloads+component['name']) and temporal_dir_downloads!="" and component['name']!="" and temporal_dir_downloads+component['name']!="/":
				os.system("rm -rf "+temporal_dir_downloads+component['name'])

############################
#####   RAW MIGRATION  #####
############################
def exportRaw(repo):
	items=get_items(repo)
	with open(json_raw_oldnexus, 'w') as outfile:
		json.dump(items, outfile)

def loadRaw(repo):
	with open(json_raw_oldnexus) as f:
		data = json.load(f)
	i=1
	for component in data:
		print("-> "+str(component['name'])+" "+repo+" ("+str(i)+"/"+str(len(data))+")")
		i=i+1
		if not os.path.exists(temporal_dir_downloads+component['name']):
			os.makedirs(temporal_dir_downloads+component['name'])
		for asset in component['assets']:
			wget.download(asset, temporal_dir_downloads+component['name'])
		files=os.listdir(temporal_dir_downloads+component['name'])

		prueba=requests.Session()
		prueba.auth=HTTPBasicAuth(USER_NEXUS_DESTINY, PASSWORD_NEXUS_DESTINY)
		params_content={ 'repository': repo }
		data_content={ 'maven2.groupId': '', 'maven2.version': component['version'],'maven2.artifactId': component['name'], 'maven2.generate-pom': False}
		file_content={}
		n_file=1
		for f in files:
			data_content.clear()
			file_content.clear()
			data_content={ 'raw.directory': '/','raw.asset'+str(n_file)+'.filename': component['name']}
#			#data_content['maven2.asset'+str(n_file)+'.extension']=f.split('.')[-1]
			file_content['raw.asset'+str(n_file)]=open(temporal_dir_downloads+component['name']+"/"+f,'rb')
			r = prueba.post(nexusURLDestiny + "/service/rest/v1/components",data=data_content, files=file_content, params=params_content)
			print(str(r.content)+" "+str(r))
			sleep(0.3)
			n_file+=1
		if os.path.exists(temporal_dir_downloads+component['name']) and temporal_dir_downloads!="" and component['name']!="" and temporal_dir_downloads+component['name']!="/":
			os.system("rm -rf "+temporal_dir_downloads+component['name'])

############################
#####   NPM MIGRATION  #####
############################
def exportNpm(repo):
	items=get_items(repo)
	with open(json_npm_oldnexus, 'w') as outfile:
		json.dump(items, outfile)

def loadNpm(repo):
	with open(json_npm_oldnexus) as f:
		data = json.load(f)
	i=1
	for component in data:
		print("-> "+str(component['name']))
		i=i+1
		if not os.path.exists(temporal_dir_downloads+component['name']):
			os.makedirs(temporal_dir_downloads+component['name'])
		for asset in component['assets']:
			print(asset)
			wget.download(asset, temporal_dir_downloads+component['name'])
		files=os.listdir(temporal_dir_downloads+component['name'])

		prueba=requests.Session()
		prueba.auth=HTTPBasicAuth(USER_NEXUS_DESTINY, PASSWORD_NEXUS_DESTINY)
		params_content={ 'repository': repo }
		data_content={ 'maven2.groupId': '', 'maven2.version': component['version'],'maven2.artifactId': component['name'], 'maven2.generate-pom': False }
		file_content={}
		n_file=1
		for f in files:
			data_content.clear()
			file_content.clear()
			file_content['npm.asset']=open(temporal_dir_downloads+component['name']+"/"+f,'rb')
			r = prueba.post(nexusURLDestiny + "/service/rest/v1/components",data=data_content, files=file_content, params=params_content)
			print(r)
			print(str(r.content))
			sleep(0.3)
			n_file+=1
		if os.path.exists(temporal_dir_downloads+component['name']) and temporal_dir_downloads!="" and component['name']!="" and temporal_dir_downloads+component['name']!="/":
			os.system("rm -rf "+temporal_dir_downloads+component['name'])

############################
#####      MAIN        #####
############################
def main():
	global REPOSITORY_TYPE
	parser = argparse.ArgumentParser()
	parser.add_argument("--export_docker ","-a", dest='export_docker')
	parser.add_argument("--docker ","-b", type=int, dest='docker')
	parser.add_argument("--export_maven ","-c", default=False, dest='export_maven')
	parser.add_argument("--maven ","-d",dest='maven', default=False)
	parser.add_argument("--export_raw ","-e",dest='export_raw', default=False)
	parser.add_argument("--raw ","-f", dest='raw', default=False)
	parser.add_argument("--export_npm ","-g", dest='export_npm', default=False)
	parser.add_argument("--npm ","-i", dest='npm', default=False)
	
	args=parser.parse_args()
	if (not args.export_docker and not args.docker and not args.export_maven and not args.maven and not args.export_raw and not args.raw and not args.export_npm and not args.npm):
		print(""""Usage:   migrate.py
		DOCKER:
		migrate -a{repository}		# Generate "+txt_dockers_oldnexus+" from Nexus Origin, contains all images
										# example:	migrate.py -adocker-releases
		migrate -b{port}		# Pull origin push destination
										# example:	migrate.py -b443
		MAVEN2:
		migrate -c{repository}		# Generate "+json_maven_oldnexus+" from Nexus Origin, contains all packages maven
										# example: migrate -creleases
		migrate -d{repository} 		# Download maven from Origin and upload to Destination
										# example: migrate -dreleases
		RAW:
		migrate -e{repository}		# Generate "+json_raw_oldnexus+" from Nexus Origin, contains all packages raw
										# example: migrate -epaas
		migrate -f{repository}		# Generate "+json_raw_oldnexus+" from Nexus Origin, contains all packages raw
										# example: migrate -fpaas
		NPM:
		migrate -g{repository}		# Generate "+json_npm_oldnexus+" from Nexus Origin, contains all packages npm
										# example: migrate -gstrationpmjs
		migrate -i{repository}		# 
										# example: migrate -istrationpmjs""")
	else:
		items=[]
		# EXPORT DOCKER
		if (args.export_docker):
			results = parser.parse_args()
			if ( results.export_docker is not None and  results.export_docker.startswith("docker")):
				exportDocker(results.export_docker)
			else:
				print("Error: It is necessary indicate a docker repository 'docker*'")
		# LOAD DOCKER
		if (args.docker):
			results = parser.parse_args()
			if ( results.docker is not None ):
				global DOCKER_PORT
				if(str(results.docker!="")):
					DOCKER_PORT=":"+str(results.docker)
				loadDocker()
			else:
				print("Error: It is necessary to indicate port")
		# EXPORT MAVEN
		if (args.export_maven):
			REPOSITORY_TYPE="maven2"
			results = parser.parse_args()
			if ( results.export_maven is not None ):
				exportMaven(results.export_maven)
			else:
				print("Error: It is necessary indicate a maven repository")
		# LOAD MAVEN
		if (args.maven):
			results = parser.parse_args()
			if ( results.maven is not None ):
				loadMaven(results.maven)
			else:
				print("Error: It is necessary to indicate a maven repository")
		# EXPORT RAW
		if (args.export_raw):
			REPOSITORY_TYPE="raw"
			results = parser.parse_args()
			if ( results.export_raw is not None):
				exportRaw(results.export_raw)
			else:
				print("Error: It is necessary indicate a raw repository")
		# LOAD RAW
		if (args.raw):
			results = parser.parse_args()
			if ( results.raw is not None ):
				loadRaw(results.raw)
			else:
				print("Error: It is necessary to indicate a maven repository")
		# EXPORT NPM
		if (args.export_npm):
			REPOSITORY_TYPE="mvn"
			results = parser.parse_args()
			if ( results.export_npm is not None):
				exportNpm(results.export_npm)
			else:
				print("Error: It is neccesary to indicate npm repository")
		# LOAD NPM
		if (args.npm):
			results = parser.parse_args()
			if ( results.npm is not None ):
				loadNpm(results.npm)
			else:
				print("Error: It is neccesary to indicate npm repository")

if __name__ == "__main__":
	main()
