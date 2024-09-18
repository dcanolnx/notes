// Script Purgar componentes Nexus
import org.sonatype.nexus.repository.storage.StorageFacet;
import org.sonatype.nexus.common.app.GlobalComponentLookupHelper
import org.sonatype.nexus.repository.maintenance.MaintenanceService
import org.sonatype.nexus.repository.storage.ComponentMaintenance
import org.sonatype.nexus.repository.storage.Query;
import org.sonatype.nexus.script.plugin.RepositoryApi
import org.sonatype.nexus.script.plugin.internal.provisioning.RepositoryApiImpl
import com.google.common.collect.ImmutableList
import org.joda.time.DateTime;
import org.slf4j.Logger
import org.joda.time.DateTime
import org.joda.time.format.DateTimeFormat

def repositoryName = 'docker-releases';
MaintenanceService service = container.lookup("org.sonatype.nexus.repository.maintenance.MaintenanceService");
def repo = repository.repositoryManager.get(repositoryName);
def tx = repo.facet(StorageFacet.class).txSupplier().get();
def components = null;
def componentsDelete = []

try {
	tx.begin();
	components = tx.browseComponents(tx.findBucket(repo));
}catch(Exception e){
	log.info("Error: "+e);
}finally{
	if(tx!=null)
		tx.close();
}

if ( components != null ) {
	def listOfComponents = ImmutableList.copyOf(components)
//	log.info("STARTS SCRIPT")
	def nComponents=listOfComponents.size()
	def nCompPreserve=0
	log.info("${nComponents}")
	def i=1
	def dateThisYear = DateTime.parse("01-01-2020", DateTimeFormat.forPattern("dd-MM-yyyy"))

	listOfComponents.reverseEach { comp ->
		if ( comp.version().split('-').size() > 1 && comp.version().split('-').reverse()[0].matches("[A-Za-z0-9]+") && comp.version().split('-').reverse()[0].length() == 7 && comp.lastUpdated().isBefore(dateThisYear) ) {
//			log.info("NAME: ${comp.name()} ${comp.group()} ${comp.version()} ${comp.lastUpdated()}")
			def samename = listOfComponents.findAll { item ->
				item.name() == comp.name() && item.group() == comp.group() && item.version().split('-').init() == comp.version().split('-').init() && item.version().split('-').reverse()[0].length() == 7 }
			if ( samename.size() > 2 ) {
				def latestComp=samename.sort{ it.lastUpdated() }.reverse().first()
				def penultimateComp=samename.sort{ it.lastUpdated() }.reverse()[1]
					if ( latestComp.version() !=  comp.version() && penultimateComp.version() !=  comp.version() ) {
						componentsDelete.add(comp)
//						log.info("BORRAR;  ${comp.name()} ${comp.group()} - ${comp.version()} ${comp.lastUpdated()} por ${latestComp.version()} ${latestComp.lastUpdated()} Y ${penultimateComp.version()} ${penultimateComp.lastUpdated()}")
					}
					else {
						nCompPreserve++
					}
			}
//			log.info("${i}/${nComponents}")
		}
		i++
	}
//	log.info("ENDS SCRIPT")
	log.info("COMPONENTES A BORRAR; ${componentsDelete.size()}")
	log.info("COMPONENTES NO BORRAR; ${nCompPreserve}")
}


//////////////////////////////////////////////////////
def dockerRepository = repository.repositoryManager.get(repositoryName)
def dockerBlobStore = blobStore.blobStoreManager.get(dockerRepository.configuration.attributes.storage.blobStoreName)
def storageTx = dockerRepository.facet(StorageFacet.class).txSupplier().get()
log.info("Starting")
try {
	log.info("Medium")
    storageTx.begin()
    dockerRepository.stop()
    def bucket = storageTx.findBucket(dockerRepository)
    def borrados=1
    def images = storageTx.browseComponents(bucket).asCollection().asImmutable()
 	log.info("${componentsDelete}")
	images.forEach { component ->
		def sameNameAndVersion = componentsDelete.findAll { item ->
				item.name() == component.name() && item.version() == component.version() }
		if (sameNameAndVersion.size() == 1) {
			log.info("Delete ${component}")
			log.info("${borrados}/${componentsDelete.size()}")
			borrados++
			storageTx.deleteComponent(component)
		}
    }

    storageTx.commit()
    dockerBlobStore.compact()
} finally {
    dockerRepository.start()
    storageTx.close()
    log.info("Dangling cleanup done")
}
log.info("Finally")















































