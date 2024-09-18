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
    def nCompPreserve=0
    log.info("${nComponents}")
    def nreleases=0
    def ntesting=0
    def nsnapshots=0
    def nthirdparties=0
    def totalpackages=0
    def restantes=0
    def dateThisYear = DateTime.parse("01-01-2020", DateTimeFormat.forPattern("dd-MM-yyyy"))

    listOfComponents.reverseEach { comp ->
        if ( comp.version().split('-').size() > 1 && comp.version().split('-').reverse()[0].matches("[A-Za-z0-9]+") && comp.version().split('-').reverse()[0].length() == 7 ) {
            ntesting++
            log.info("TESTING "+comp.name()+" "+comp.version())
        } else if (comp.version().split('-').size() > 1 && comp.version().split('-').reverse()[0].matches("M[0-9]+") ) {
            ntesting++
            log.info("TESTING "+comp.name()+" "+comp.version())
        } else if ( comp.version().toLowerCase().contains("snapshot") ) {
            nsnapshots++
            log.info("SNAPSHOT "+comp.name()+" "+comp.version())
        } else if ( !comp.name().toLowerCase().startsWith("stratio/") ) {
            nthirdparties++
            log.info("THIRDPARTIES "+comp.name()+" "+comp.version())
        } else {
            log.info("RELEASES "+comp.name()+" "+comp.version())
            restantes++
        }
        //log.info(comp.name()+" "+comp.version())
        totalpackages++
    }
    log.info("COMPONENTES docker_snapshot; ${nsnapshots}")
    log.info("COMPONENTES docker_testing; ${ntesting}")
    log.info("COMPONENTES docker_thirdparties; ${nthirdparties}")
    log.info("COMPONENTES restantes; ${restantes}")
    log.info("COMPONENTES total dockers; ${totalpackages}")

}