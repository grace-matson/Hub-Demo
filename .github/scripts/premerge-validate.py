import os
import sys
import yaml
import json
import logging
import requests
import ast
import subprocess as sp

#Setting logging level to DEBUG
logging.getLogger().setLevel(logging.DEBUG)

bucket_name = 'hub-cdap-io'
bucket_dir = 'v2/'
only_warning_types =['create_driver_artifact']

##1. FETCHING ADDED/MODIFIED ARTIFACTS
#Getting list of added artifacts and modified artifacts, and concatenating them
added_list = ast.literal_eval(os.getenv('ADDED_LIST'))
modified_list = ast.literal_eval(os.getenv('MODIFIED_LIST'))
renamed_list = ast.literal_eval(os.getenv('RENAMED_LIST'))
am_list = added_list + modified_list + renamed_list
logging.debug('List of added or modified files within pull request')
logging.debug(am_list)


specFiles = [] #storing the modified spec.json file names
modifiedArtifacts = [] #storing the modified artifacts as <artifact>/<version> format

#loop to check for modified spec.json files
for file in am_list:
  if(file.split('/')[-1]=="spec.json"):
    # example of file name:
    # packages/database-plugin-db2-plugin/1.2.0/spec.json
    specFiles.append(file)
    artifact = file.split('/')[1]
    version = file.split('/')[2]
    modifiedArtifacts.append(artifact + '/' + version)

#logging the final list of artifact versions which were added/modified
logging.debug("Modified artifacts are (where spec.json was modified/added) :")
logging.debug(modifiedArtifacts)
logging.debug("Spec.json files are :")
logging.debug(specFiles)

if(len(specFiles)==0):
  #exiting successfully if none of the modified/added files are spec.json
  sys.exit(0)

##2. CHECKING PACKAGES.JSON FILE
packagesList = json.loads(open("./packages.json", "r").read())
# converting list to dictionary format to access easily later
mod_packagesDict = dict([(artifact['name'] + '/' + artifact['version'], artifact)  # Key: "<artifact_name>/<version>" Value: artifact object in packagesList
                         for artifact in packagesList
                         if artifact['name'] + '/' + artifact['version'] in modifiedArtifacts]) # only appending those artifacts which are modified/added
logging.debug("Dictionary of modified artifacts: \n")
logging.debug(mod_packagesDict)

if(len(mod_packagesDict)!=len(modifiedArtifacts)):
  #Exit failure if the no.of modified artifacts in the packages.json file is not the same as the no.of modified artifacts
  sys.exit("no.of modified artifacts in the packages.json file is not the same as the no.of modified artifacts")

for index, artifact in enumerate(modifiedArtifacts):
  specFile = json.loads(open(specFiles[index], "r").read())
  logging.debug("\n\n Printing specFile for " + artifact)
  logging.debug(json.dumps(specFile, indent=2))

  packagesDictObject = mod_packagesDict[artifact]
  logging.debug("\n\n Printing packages.json info for " + artifact)
  logging.debug(json.dumps(packagesDictObject, indent=2))

  #Validating packages.json
  if('cdapVersion' in specFile and not(specFile['cdapVersion']==packagesDictObject['cdapVersion'])):
    sys.exit("Fields do not match in packages.json and the added artifacts")

else :
  logging.debug("Success, all modified/added artifact versions are added in packages.json")


##3. ITERATING THROUGH THE MODIFIED ARTIFACTS AND CHECKING IF ALL THE REQUIRED DEPENDENCIES ARE RETRIEVABLE

#iterating through each artifact
for specFile in specFiles:
  #example specFile = "packages/database-plugin-db2-plugin/1.3.0/spec.json"
  pathList = specFile.split('/')
  artifactDir = os.path.join(pathList[0], pathList[1]) #artifact directory ex: "packages/database-plugin-db2-plugin"
  artifactVersionDir = os.path.join(artifactDir, pathList[2]) #artifact version directory ex: "packages/database-plugin-db2-plugin/1.3.0"

  logging.debug(f'Inspecting spec.json of {artifactVersionDir} for required files') #required files = jar or json files listed in actions field of spec.json file
  specData = json.loads(open(specFile, "r").read()) #loading json data in spec.json as dictionary
  necessaryFiles = [] #list of files which need to be retrieved from GCS or Maven Central
  only_warn= []
  for object in specData['actions']:
    for property in object['arguments']:
      if(property['name'] == 'jar' or property['name'] == 'config'): #json file names are under config property, and jar file names under jar property
        warn = False
        if (object['type'] in only_warning_types and property['name'] == 'config'):
          warn = True
        requiredFile = os.path.join(artifactVersionDir, property['value'])
        #ex: packages/database-plugin-db2-plugin/1.3.0/db2-plugin-1.3.0.json
        if(not(os.path.isfile(requiredFile))):
          necessaryFiles.append(requiredFile)
          only_warn.append(warn)

  if len(necessaryFiles) == 0 :
    logging.debug("All required artifacts retrievable from version directory")
    continue

  for index, necessaryFile in enumerate(necessaryFiles) :

    if(sp.getoutput(f'gsutil -q stat gs://{bucket_name}/{bucket_dir}{necessaryFile}; echo $?')=='0'):
      logging.debug(necessaryFile+" found in GCS bucket")

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
      logging.debug(response['response']['docs'])

      if(len(response['response']['docs'])>0):
        logging.debug(necessaryFile+" found in Maven Central")
      else:
        logging.warning(necessaryFile+" not found in GCS or Maven Central")
        if(not(only_warn[index])):
          sys.exit(necessaryFile+" is not available in GCS or Maven")
    else:
      logging.warning('build.yaml file does not exist for ' + artifactDir)
      if(not(only_warn[index])):
        sys.exit(necessaryFile+" is not available in GCS or Maven")


