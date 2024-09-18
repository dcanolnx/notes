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
//  log.info("STARTS SCRIPT")
    def nComponents=listOfComponents.size()
    log.info("${nComponents}")
    def nDockers=0
    def ntesting=0
    def dateThisYear = DateTime.parse("01-06-2019", DateTimeFormat.forPattern("dd-MM-yyyy"))

    listOfComponents.reverseEach { comp ->
        if ( comp.version().toLowerCase().contains("snapshot") && comp.name().toLowerCase().startsWith("stratio/") &&  comp.lastUpdated().isBefore(dateThisYear) ) {
            ntesting++
            componentsDelete.add(comp)
            //log.info("DOCKERS "+comp.name()+" "+comp.version())
        }
        nDockers++
    }
    log.info(ntesting+"/"+nDockers)
}
