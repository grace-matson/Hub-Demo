import os
import sys
import utilities
import yaml
import json
import logging
import subprocess as sp
import requests
import ast
from google.cloud import storage

#Setting logging level to INFO
logging.getLogger().setLevel(logging.INFO)
list = ['packages/database-plugin-db2-plugin/1.2.0/spec.json', 'packages/database-plugin-db2-plugin/1.3.0/spec.json', 'packages/plugin-google-drive/1.4.0/spec.json']
BUCKET_NAME = 'gs://hub-cdap-io/v2/'

##1. CREATING PACAKGES.JSON FILE
#Running steps to create packages.json
# os.chdir('./packager/')
# utilities.run_shell_command('mvn clean package')
# os.chdir('../')
# utilities.run_shell_command('java -cp "packager/target/lib/*:packager/target/*" io.cdap.hub.Tool build')

##2. FETCHING ADDED/MODIFIED PLUGINS
#Getting list of added plugins and modified plugins, and concatenating them
# added_list = ast.literal_eval(os.getenv('ADDED_LIST'))
# modified_list = ast.literal_eval(os.getenv('MODIFIED_LIST'))
# list = added_list + modified_list
# logging.info('List of added or modified files within pull request')
# logging.info(list)


specfiles = [] #storing the modified spec.json file names
modifiedPlugins = [] #storing the modified plugins as <plugin>/<version> format

#loop to check for modified spec.json files
for file in list:
  if(file.split('/')[-1]=="spec.json"):
    # example of file name:
    # packages/database-plugin-db2-plugin/1.2.0/spec.json
    specfiles.append(file)
    plugin = file.split('/')[1]
    version = file.split('/')[2]
    modifiedPlugins.append(plugin+'/'+version)

logging.info("Modified plugins are (where spec.json was modified/added) :")
logging.info(modifiedPlugins)
logging.info("Spec.json files are :")
logging.info(specfiles)

if(len(specfiles)==0):
  #exiting successfully if none of the modified/added files are spec.json
  sys.exit(0)

##3. CHECKING PACKAGES.JSON FILE
packagesList = json.loads(open("./packages.json", "r").read())
# converting to dictionary format to access easily later
mod_packagesDict = dict([(plugin['name'] + '/' + plugin['version'], plugin)  # Key: "<plugin_name>/<version>" Value: artifact object in packagesList
                         for plugin in packagesList
                         if plugin['name'] +'/' + plugin['version'] in modifiedPlugins]) # only appending those plugins which are modified/added
logging.info("Dictionary of modified packages: \n", mod_packagesDict)

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

  if(not(specFile['cdapVersion']==packagesDictObject['cdapVersion'])):
    sys.exit("Fields do not match in packages.json and the added plugins")

else :
  logging.info("Success, all modified/added plugin versions are added in packages.json")


##4. ITERATING THROUGH THE MODIFIED PLUGINS AND CHECKING IF ALL THE REQUIRED DEPENDENCIES ARE RETRIEVABLE

gcs_list = sp.getoutput(f'gsutil ls {BUCKET_NAME}packages/').split('\n')
# example of item in gcs_list = gs://hub-cdap-io/v2/packages/plugin-window-aggregation/
gcs_artifact_dir = [plugin.removeprefix(BUCKET_NAME)[:-1] #removing prefix and taking only -> packages/plugin-window-aggregation
                    for plugin in gcs_list]
logging.info(gcs_list)
logging.info(gcs_artifact_dir)

for specfile in specfiles:
  #example specfiles = "packages/database-plugin-db2-plugin/1.3.0/spec.json"
  pathList = specfile.split('/')
  artifactDir = os.path.join(pathList[0], pathList[1]) #ex: "packages/database-plugin-db2-plugin"
  artifactVersionDir = specfile[:-9] #ex: "packages/database-plugin-db2-plugin/1.3.0"

  logging.info(f'Inspecting spec.json of {artifactVersionDir} for necessary files') #necessary = jar or json files listed in actions field of spec.json file
  specData = json.loads(open(specfile, "r").read())
  necessaryFiles = []
  for object in specData['actions']:
    for property in object['arguments']:
      if(property['name'] == 'jar' or property['name'] == 'config'):
        necessaryFile = os.path.join(artifactVersionDir, property['value'])
        if(not (os.path.isfile(necessaryFile))):
          necessaryFiles.append(necessaryFile)
  if len(necessaryFiles) == 0 :
    continue
  gcs_artifact_version_dir = []
  if(artifactDir in gcs_artifact_dir):
    gcs_artifact_version_list = sp.getoutput(f'gsutil ls {BUCKET_NAME}'+artifactVersionDir).split('\n')
    gcs_artifact_version_dir = [version.removeprefix(BUCKET_NAME) for version in gcs_artifact_version_list]
    logging.info(gcs_artifact_version_dir)

  for necessaryFile in necessaryFiles :

    if(necessaryFile in gcs_artifact_version_dir):
      logging.info(necessaryFile+" found in GCS bucket")

    # elif(os.path.isfile(os.path.join(artifactDir, 'build.yaml'))):
    #   #getting required info from build.yaml file
    #   buildFile = open(os.path.join(artifactDir, 'build.yaml'))
    #   buildData = yaml.load(buildFile, Loader=yaml.FullLoader)
    #   groupId = buildData['maven-central']['groupId']
    #   artifactId = buildData['maven-central']['artifactId']
    #
    #   version = artifactVersionDir.split('/')[-1]
    #   packaging = necessaryFile.split('.')[-1]
    #
    #   #using Maven Central search api to get the required file
    #   response = requests.get(f'https://search.maven.org/solrsearch/select?q=g:{groupId}%20AND%20a:{artifactId}%20AND%20v:{version}%20AND%20p:{packaging}&rows=20&wt=json').json()
    #   logging.info(response['response']['docs'])
    #
    #   if(len(response['response']['docs'])>0):
    #     logging.info(necessaryFile+" found in Maven Central")
    #   else:
    #     logging.error(necessaryFile+" not found in Maven Central")
    #     sys.exit(necessaryFile+" is not available in GCS or Maven")
    else:
      logging.error('build.yaml file does not exist for ' + artifactDir)
      sys.exit(necessaryFile+" is not available in GCS or Maven")



