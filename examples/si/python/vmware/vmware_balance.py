#!/usr/bin/python3
import pyVmomi
import argparse
import atexit
import itertools
from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
import humanize
import ssl

MBFACTOR = float(1 << 20)

########################################
##### GLOBAL VARS
########################################
printHost = True
VMWARE = []

########################################
##### CLASS
########################################
class VM:
	def __init__(self,name,cpus,mem):
		self.name = name
		self.cpus = cpus
		self.mem = mem

class Host:
	def __init__(self,name,cpus,mem,virtual_machines):
		self.name = name
		self.cpus = cpus
		self.mem = mem
		self.virtual_machines = virtual_machines		

	def addMV(self,mv):
		self.virtual_machines.append(mv)

class Cluster:
	def __init__(self,name,hosts):
		self.name = name
		self.hosts = hosts
	
	def addMVtoHost(self,hostName,mv):
		self.hosts[hostName].addMV(mv)

########################################
##### DEFS
########################################
def GetArgs():

	parser = argparse.ArgumentParser(
	    description='Process args for retrieving all the Virtual Machines')
	parser.add_argument('-s', '--host', required=True, action='store',
	                    help='Remote host to connect to')
	parser.add_argument('-o', '--port', type=int, default=443, action='store',
	                    help='Port to connect on')
	parser.add_argument('-u', '--user', required=True, action='store',
	                    help='User name to use when connecting to host')
	parser.add_argument('-p', '--password', required=False, action='store',
	                    help='Password to use when connecting to host')
	args = parser.parse_args()
	return args


def printHostInformation(host):
	try:
		summary = host.summary
		stats = summary.quickStats
		hardware = host.hardware
		cpuUsage = stats.overallCpuUsage
		memoryCapacity = hardware.memorySize
		memoryCapacityInMB = hardware.memorySize/MBFACTOR
		memoryUsage = stats.overallMemoryUsage
		freeMemoryPercentage = 100 - (
		    (float(memoryUsage) / memoryCapacityInMB) * 100
		)
		return Host(host.name,host.hardware.cpuInfo.numCpuThreads,humanize.naturalsize(memoryCapacity, binary=True),[])
	except Exception as error:
		print("Unable to access information for host: ", host.name)
		print(error)
		pass


def printComputeResourceInformation(computeResource):
    try:
        hostList = computeResource.host
        print("##################################################")
        print("Compute resource name: ", computeResource.name)
        print("##################################################")
        hostsInCluster=[]
        for host in hostList:
            hostsInCluster.append(printHostInformation(host))
        VMWARE.append(Cluster(computeResource.name,hostsInCluster))
    except Exception as error:
        print("Unable to access information for compute resource: ",
              computeResource.name)
        print(error)
        pass


def getVmInformation(virtual_machine, depth=1):
	maxdepth = 10
	if hasattr(virtual_machine, 'childEntity'):
		if depth > maxdepth:
		    return
		vmList = virtual_machine.childEntity
		for c in vmList:
		    getVmInformation(c, depth + 1)
		return
	try:
		print("##################################################")
		print("Name : ", virtual_machine.name)
		print("Memory : ", virtual_machine.summary.config.memorySizeMB)
		print("CPU : ", virtual_machine.summary.config.numCpu)
		print("HOST :", virtual_machine.runtime.host.name)
		print("##################################################")
		for c in VMWARE:
			if virtual_machine.runtime.host.name in c.hosts:
				c.addMVtoHost(VM(virtual_machine.name, virtual_machine.summary.config.numCpu, virtual_machine.summary.config.memorySizeMB))
		return VM(virtual_machine.name, virtual_machine.summary.config.numCpu, virtual_machine.summary.config.memorySizeMB)
	except Exception as error:
		print("Unable to access summary for VM: ", virtual_machine.name)
		print(error)
		pass
########################################
##### MAIN
########################################
def main():
	args = GetArgs()
	# try:
	context = ssl._create_unverified_context()
	si = SmartConnect(host=args.host, user=args.user,
	                  pwd=args.password, port=int(args.port),
	                  sslContext=context)
	atexit.register(Disconnect, si)
	content = si.RetrieveContent()


	for datacenter in content.rootFolder.childEntity:
		print("##################################################")
		print("### datacenter : " + datacenter.name)
		print("##################################################")

		VMs=[]
		if hasattr(datacenter.hostFolder, 'childEntity'):
			hostFolder = datacenter.hostFolder
			computeResourceList = hostFolder.childEntity
			for computeResource in computeResourceList:
				printComputeResourceInformation(computeResource)

#		for cluster in VMWARE:
#			print(str(cluster.name))
#			for host in cluster.hosts:
#				print(host.name)
#				print(host.cpus)
#				print(host.mem)
#				#for vm in host.virtual_machines: 
#				#	print(vm.name)
#
		if hasattr(datacenter.vmFolder, 'childEntity'):
			vmFolder = datacenter.vmFolder
			vmList = vmFolder.childEntity
			i=0
			for vm in vmList:
				VMs.append(getVmInformation(vm))
				i=i+1
				print(str(i)+"/"+str(len(vmList)))
				break

		for cluster in VMWARE:
			print(str(cluster.name))
			for host in cluster.hosts:
				print(host.name)
				print(host.cpus)
				print(host.mem)
				print(str(host.virtual_machines))
				for vm in host.virtual_machines: 
					print(vm.name)
		#for vm in VMs:
		#	print(str(vm.name))
			#print(str(vm.name))
			#print(str(vm.cpus))
			#print(str(vm.mem))




    # except Exception as error:
    #     print("Caught vmodl fault : " + error.msg)
    #     return -1
	return 0

if __name__ == "__main__":
    main()