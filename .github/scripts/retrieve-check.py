import os
import sys
import utilities
import yaml
import json
import logging
import requests
import ast
from google.cloud import storage
storage_client = storage.Client()
bucket_name = 'hub-cdap-io'
bucket_dir = 'v2/'
bucket = storage_client.bucket(bucket_name)
specfile = os.getenv('SPECFILE')
#example specfile = "packages/database-plugin-db2-plugin/1.3.0/spec.json"
pathList = specfile.split('/')
artifactDir = os.path.join(pathList[0], pathList[1]) #plugin directory ex: "packages/database-plugin-db2-plugin"
artifactVersionDir = specfile[:-9] #plugin version directory ex: "packages/database-plugin-db2-plugin/1.3.0"

logging.info(f'Inspecting spec.json of {artifactVersionDir} for required files') #required files = jar or json files listed in actions field of spec.json file
specData = json.loads(open(specfile, "r").read()) #loading json data in spec.json as dictionary
necessaryFiles = [] #list of files which need to be retrieved from GCS or Maven Central
for object in specData['actions']:
  for property in object['arguments']:
    if(property['name'] == 'jar' or property['name'] == 'config'): #json file names are under config property, and jar file names under jar property
      requiredFile = os.path.join(artifactVersionDir, property['value'])
      if(not (os.path.isfile(requiredFile))):
        necessaryFiles.append(requiredFile)

if len(necessaryFiles) == 0 :
  sys.exit(0)

for necessaryFile in necessaryFiles :

  # if(storage.Blob(bucket=bucket, name=bucket_dir+necessaryFile).exists(storage_client)):
  #   logging.info(necessaryFile+" found in GCS bucket")

  if(os.path.isfile(os.path.join(artifactDir, 'build.yaml'))):
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

    if(len(response['response']['docs'])>0 ):
      logging.info(necessaryFile+" found in Maven Central")
    elif(storage.Blob(bucket=bucket, name=bucket_dir+necessaryFile).exists(storage_client)):
      logging.info(necessaryFile+" found in GCS")
    else:
      logging.error(necessaryFile+" not found in Maven Central")
      sys.exit(necessaryFile+" is not available in GCS or Maven")
  elif(storage.Blob(bucket=bucket, name=bucket_dir+necessaryFile).exists(storage_client)):
    logging.info(necessaryFile+" found in GCS")
  else:
    logging.error('build.yaml file does not exist for ' + artifactDir)
    sys.exit(necessaryFile+" is not available in GCS or Maven")

