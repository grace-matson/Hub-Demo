import os
import sys
import utilities
import yaml
import json
import logging
import requests
import ast
from google.cloud import storage

#Setting logging level to INFO
logging.getLogger().setLevel(logging.INFO)

#Connecting to the GCS bucket
storage_client = storage.Client()
bucket_name = 'hub-cdap-io'
bucket_dir = 'v2/'
bucket = storage_client.bucket(bucket_name)
only_warning_types =['create_driver_artifact']
##1. CREATING PACAKGES.JSON FILE
# Running steps to create packages.json
os.chdir('./packager/')
utilities.run_shell_command('mvn clean package')
os.chdir('../')
utilities.run_shell_command('java -cp "packager/target/lib/*:packager/target/*" io.cdap.hub.Tool build')

##2. FETCHING ADDED/MODIFIED PLUGINS
#Getting list of added plugins and modified plugins, and concatenating them
added_list = ast.literal_eval(os.getenv('ADDED_LIST'))
modified_list = ast.literal_eval(os.getenv('MODIFIED_LIST'))
am_list = added_list + modified_list
logging.info('List of added or modified files within pull request')
logging.info(am_list)


specfiles = [] #storing the modified spec.json file names
modifiedPlugins = [] #storing the modified plugins as <plugin>/<version> format

#loop to check for modified spec.json files
for file in am_list:
  if(file.split('/')[-1]=="spec.json"):
    # example of file name:
    # packages/database-plugin-db2-plugin/1.2.0/spec.json
    specfiles.append(file)
    plugin = file.split('/')[1]
    version = file.split('/')[2]
    modifiedPlugins.append(plugin+'/'+version)

#logging the final list of plugin version which were added/modified
logging.info("Modified plugins are (where spec.json was modified/added) :")
logging.info(modifiedPlugins)
logging.info("Spec.json files are :")
logging.info(specfiles)

if(len(specfiles)==0):
  #exiting successfully if none of the modified/added files are spec.json
  sys.exit(0)

##3. CHECKING PACKAGES.JSON FILE
packagesList = json.loads(open("./packages.json", "r").read())
# converting list to dictionary format to access easily later
mod_packagesDict = dict([(plugin['name'] + '/' + plugin['version'], plugin)  # Key: "<plugin_name>/<version>" Value: artifact object in packagesList
                         for plugin in packagesList
                         if plugin['name'] +'/' + plugin['version'] in modifiedPlugins]) # only appending those plugins which are modified/added
logging.info("Dictionary of modified artifacts: \n", mod_packagesDict)

if(len(mod_packagesDict)!=len(modifiedPlugins)):
  #Exit failure if the no.of modified plugins in the packages.json file is not the same as the no.of modified plugins
  sys.exit("no.of modified plugins in the packages.json file is not the same as the no.of modified plugins")

for index, plugin in enumerate(modifiedPlugins):
  specFile = json.loads(open(specfiles[index], "r").read())
  logging.info("\n\n Printing specFile for "+ plugin)
  logging.info(json.dumps(specFile, indent=2))

  packagesDictObject = mod_packagesDict[plugin]
  logging.info("\n\n Printing packages.json info for "+ plugin)
  logging.info(json.dumps(packagesDictObject, indent=2))

  #Validating packages.json
  if('cdapVersion' in specFile and not(specFile['cdapVersion']==packagesDictObject['cdapVersion'])):
    sys.exit("Fields do not match in packages.json and the added plugins")

else :
  logging.info("Success, all modified/added plugin versions are added in packages.json")


##4. ITERATING THROUGH THE MODIFIED PLUGINS AND CHECKING IF ALL THE REQUIRED DEPENDENCIES ARE RETRIEVABLE

#iterating through each plugin
for specfile in specfiles:
  #example specfile = "packages/database-plugin-db2-plugin/1.3.0/spec.json"
  pathList = specfile.split('/')
  artifactDir = os.path.join(pathList[0], pathList[1]) #plugin directory ex: "packages/database-plugin-db2-plugin"
  artifactVersionDir = specfile[:-10] #plugin version directory ex: "packages/database-plugin-db2-plugin/1.3.0"

  logging.info(f'Inspecting spec.json of {artifactVersionDir} for required files') #required files = jar or json files listed in actions field of spec.json file
  specData = json.loads(open(specfile, "r").read()) #loading json data in spec.json as dictionary
  necessaryFiles = [] #list of files which need to be retrieved from GCS or Maven Central
  only_warn= []
  for object in specData['actions']:
    warn = False
    if object['type'] in only_warning_types:
      warn = True
    for property in object['arguments']:
      if(property['name'] == 'jar' or property['name'] == 'config'): #json file names are under config property, and jar file names under jar property
        requiredFile = os.path.join(artifactVersionDir, property['value'])
        if(not (os.path.isfile(requiredFile))):
          necessaryFiles.append(requiredFile)
          only_warn.append(warn)

  if len(necessaryFiles) == 0 :
    continue

  for index, necessaryFile in enumerate(necessaryFiles) :

    if(storage.Blob(bucket=bucket, name=bucket_dir+necessaryFile).exists(storage_client)):
      logging.info(necessaryFile+" found in GCS bucket")

    elif(os.path.isfile(os.path.join(artifactDir, 'build.yaml'))):
      #getting required info from build.yaml file
      buildFile = open(os.path.join(artifactDir, 'build.yaml'))
      buildData = yaml.load(buildFile, Loader=yaml.FullLoader)
      groupId = buildData['maven-central']['groupId']
      artifactId = buildData['maven-central']['artifactId']

      version = artifactVersionDir.split('/')[-1]
      packaging = necessaryFile.split('.')[-1]

      #using Maven Central search api to get the required file
      response = requests.get(f'https://search.maven.org/solrsearch/select?q=g:{groupId}%20AND%20a:{artifactId}%20AND%20v:{version}%20AND%20p:{packaging}&rows=20&wt=json').json()
      logging.info(response['response']['docs'])

      if(len(response['response']['docs'])>0):
        logging.info(necessaryFile+" found in Maven Central")
      else:
        logging.warning(necessaryFile+" not found in GCS or Maven Central")
        if(not(only_warn[index])):
          sys.exit(necessaryFile+" is not available in GCS or Maven")
    else:
      logging.warning('build.yaml file does not exist for ' + artifactDir)
      if(not(only_warn[index])):
        sys.exit(necessaryFile+" is not available in GCS or Maven")


