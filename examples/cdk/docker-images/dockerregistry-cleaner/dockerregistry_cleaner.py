#!/usr/bin/python3
import requests, json, datetime, sys, timedelta,socket, subprocess
from datetime import datetime, timedelta

DOCKERREGISTRY="http://docker-registry:5000/v2/"

def recentDateOfImageTag(image,tag):
	print("image "+image+" tag "+tag)
	r = requests.get(DOCKERREGISTRY+image+'/manifests/'+tag,headers={'Accept':'application/vnd.oci.image.index.v1+json'})
	tagInfo=r.json()
	recentDate=""
	if 'manifests' in tagInfo and tagInfo['manifests']!=None:
		for manifest in tagInfo['manifests']:
			if len(manifest) == 4:
				date=manifest['annotations']['buildkit/createdat']
				if recentDate == "":
					recentDate = datetime.strptime(date.split('.')[0],'%Y-%m-%dT%H:%M:%S')
				else:
					if recentDate < datetime.strptime(date.split('.')[0],'%Y-%m-%dT%H:%M:%S'):
						recentDate = datetime.strptime(date.split('.')[0],'%Y-%m-%dT%H:%M:%S')
	else:
		print("WARNING: "+str(tagInfo))
		recentDate=datetime.now()
	return recentDate

def deleteImageTag(image,tag):
	print("Delete: "+image+" "+tag)
	r = requests.get(DOCKERREGISTRY+image+'/manifests/'+tag,headers={'Accept':'application/vnd.oci.image.index.v1+json'})
	if 'Docker-Content-Digest' in r.headers:
		r = requests.delete(DOCKERREGISTRY+image+'/manifests/'+r.headers['Docker-Content-Digest'])
		if r.status_code != 202:
			print("WARNING: "+image+" "+tag+" can not be deleted, response not 2XX")
		else:
			return True
	else:
		print("WARNING: "+image+" "+tag+" can not be deleted, does not exists")

def main():
	if (len(sys.argv) != 2 or not sys.argv[1].isdigit()):
		print("./docker-registry.py $NUMBEROFDAYS #Delete images older than $NUMBEROFDAYS")
	else:
		today = datetime.now()
		before = today - timedelta(days = int(sys.argv[1]))
		r = requests.get(DOCKERREGISTRY+'_catalog')
		repositories=r.json()
		for repo in repositories['repositories']:
			r = requests.get(DOCKERREGISTRY+str(repo)+'/tags/list')
			tags=r.json()
			if ('tags' in tags and tags['tags']!=None ):
				for tag in tags['tags']:
					recent=recentDateOfImageTag(repo,tag)
					print(str(recent))
					if (str(recent) != "" and recent < before):
						deleteImageTag(repo,tag)
					print("")
		print("Call API garbage-collect function")
		command="curl -s localhost:1234/garbage-collect"
		subprocess.check_output(command, shell=True)

if __name__ == "__main__":
	main()
