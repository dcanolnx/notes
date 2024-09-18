import org.sonatype.nexus.repository.Repository
import org.sonatype.nexus.repository.storage.Asset
import org.sonatype.nexus.repository.storage.Component
import org.sonatype.nexus.repository.storage.StorageFacet
import org.joda.time.DateTime
import org.joda.time.format.DateTimeFormat
import groovy.json.JsonOutput

/**********
 // ARGS //
 *********/
def beforeDate = "1-1-2020"    // Formato en valor numerico -> dia-mes-anyo
def repositories = ["releases"]
def path = "/tmp/"


/*****************
 // START SCRIPT //
 *****************/
repository.repositoryManager.browse().each { Repository repo ->

    if (repo.name in repositories){
        // Define y obtiene el Supplier
        def tx_bucket = repo.facet(StorageFacet).txSupplier().get()
        def tx_component = repo.facet(StorageFacet).txSupplier().get()

        // Se define el directorio donde se guardará toda la información del repo
        def file = new File("${path}${repo.name}.txt")

        // Se define el directorio para el borrado y la fecha en formado DateTime
        def fileAfter = new File("${path}${repo.name}_${beforeDate}.json")
        def afterDateTime = DateTime.parse(beforeDate, DateTimeFormat.forPattern("dd-MM-yyyy"))

        try {
            // Inicializa el tx bucket
            tx_bucket.begin()
            // Obtiene el bucket correspondiente al repo
            buckets = tx_bucket.findBucket(repo)
            tx_bucket.commit()

            // Y ahora para los componentes
            tx_component.begin()
            // Obtiene los componentes correspondiente al bucket
            components = tx_component.browseComponents(buckets)
            tx_component.commit()

            // Creamos la lista para los ficheros a borrar en formato Json
            List<componentJson> comps = []

            // Recorrer Lista Componentes
            components.each { Component comp ->
                if ( (comp.version().toString() =~ ($/.*SNAPSHOTPR.*/$)) ){

                    // Define y obtiene el Supplier
                    def tx_assets = repo.facet(StorageFacet).txSupplier().get()

                    // Inicializa la fecha minima del paquete
                    def lastDate = DateTime.parse("01-01-2014", DateTimeFormat.forPattern("dd-MM-yyyy"))

                    // Lista con las URLs de los Assets
                    List<String> urlAssets = []

                    try {
                        // Inicializa el tx assets
                        tx_assets.begin()
                        // Obtiene los assets correspondientes al repo
                        assets = tx_assets.browseAssets(comp)
                        tx_assets.commit()

                        // Recorremos la lista de assets para coger la fecha mas moderna
                        assets.each { Asset asset ->

                            // Almacenamos la URL del asset
                            urlAssets.add(asset.name())

                            // Obtenemos la fecha de ultima descarga del asset
                            assetLastDownloaded = asset.lastDownloaded()

                            // Compara con la anterior fecha registrada
                            if ( assetLastDownloaded.isAfter(lastDate.toInstant()) ){
                                // Si la fecha actual es posterior a la registrada se actualiza
                                lastDate = assetLastDownloaded
                            }
                        }

                        // Guardamos a fichero con el formato de fecha que nos interesa en función del grupo
                        if ( comp.group() != null ) {
                            file << ("${comp.group()}.${comp.name()}:${comp.version()}+${lastDate.toString("yyyy-MM-dd")}\n")
                            // Se tiene en cuenta si se quiere borrar o no
                            if ((beforeDate != null || beforeDate != "") && lastDate.isBefore(afterDateTime.toInstant())) {
                                comps.add(new componentJson(comp.group(), comp.name(), comp.version(),
                                        lastDate.toString("yyyy-MM-dd"), comp.format(), urlAssets ))
                            }
                        }
                        else {
                            file << ("${comp.name()}:${comp.version()}+${lastDate.toString("yyyy-MM-dd")}\n")
                            // Se tiene en cuenta si se quiere borrar o no
                            if ( (beforeDate != null || beforeDate != "") && lastDate.isBefore(afterDateTime.toInstant()) ) {
                                comps.add(new componentJson(comp.name(), comp.version(),
                                        lastDate.toString("yyyy-MM-dd"), comp.format(), urlAssets ))
                            }
                        }

                    } catch (Exception e) { // Si falla coge la excepcion
                        log.warn("Transaction failed - Asset -- {}", e.toString())
                        tx_assets.rollback()

                    } finally { // Al terminar cierra el tx
                        tx_assets.close()
                    }
                }
            }

            // Escribir en formato Json
            fileAfter << JsonOutput.toJson(comps)

        } catch (Exception e) { // Si falla coge la excepcion
            log.warn("Transaction failed -- {}", e.toString())
            tx_bucket.rollback()
            tx_component.rollback()

        } finally { // Al terminar cierra el tx y el file
            tx_bucket.close()
            tx_component.close()
        }
    }
}

static String monthToNumber(String month){
    switch (month) {
        case "Jan": return "01"; break
        case "Feb": return "02"; break
        case "Mar": return "03"; break
        case "Apr": return "04"; break
        case "May": return "05"; break
        case "Jun": return "06"; break
        case "Jul": return "07"; break
        case "Aug": return "08"; break
        case "Sep": return "09"; break
        case "Oct": return "10"; break
        case "Nov": return "11"; break
        case "Dec": return "12"; break
        default: return "00"
    }
}

class componentJson {
    String group, name, version, lastDownloaded, format
    List<String> assetsURL

    componentJson(group, name, version, lastDownloaded, format, assetsURL){
        this.group = group
        this.name = name
        this.version = version
        this.lastDownloaded = lastDownloaded
        this.format = format
        this.assetsURL = assetsURL
    }

    componentJson(name, version, lastDownloaded, format, assetsURL){
        this.group = null
        this.name = name
        this.version = version
        this.lastDownloaded = lastDownloaded
        this.format = format
        this.assetsURL = assetsURL
    }
}