import os
import sys
import utilities
import json
import logging

logging.getLogger().setLevel(logging.INFO)
# list = ['packages/database-plugin-db2-plugin/1.2.0/spec.json', 'packages/database-plugin-db2-plugin/1.3.0/spec.json']
os.chdir('./packager/')
utilities.run_shell_command('mvn clean package')
os.chdir('../')
utilities.run_shell_command('java -cp "packager/target/lib/*:packager/target/*" io.cdap.hub.Tool build')

added_list = os.getenv('ADDED_LIST').strip(']["').split(',')
modified_list = os.getenv('MODIFIED_LIST').strip(']["').split(',')
list = added_list + modified_list
logging.info(list)

specfiles = []
modifiedPlugins = []
for file in list:
  if(file.split('/')[-1]=="spec.json"):
    specfiles.append(file)
    modifiedPlugins.append(file.split('/')[1]+'/'+file.split('/')[2])
logging.info(modifiedPlugins)
logging.info(specfiles)

if(len(specfiles)==0):
  sys.exit(0)

packagesList = json.loads(open("./packages.json", "r").read())
#converting to dictionary format to access easily later    Key: "<plugin_name>/<version>" Value: artifact object in packagesList
#only appending those plugins which are modified/added
packagesDict = dict([(plugin['name']+'/'+plugin['version'], plugin)
                     for plugin in packagesList
                     if plugin['name']+'/'+plugin['version'] in modifiedPlugins])
print("Dictionary of modified packages: \n", packagesDict)

if(len(packagesDict)!=len(modifiedPlugins)):
  sys.exit(1)

for index, plugin in enumerate(modifiedPlugins):
  specFile = json.loads(open(specfiles[index], "r").read())
  packagesDictObject = packagesDict[plugin]

  logging.info("\n\n Printing specFile for "+ plugin)
  logging.info(json.dumps(specFile, indent=2))

  logging.info("\n\n Printing packages.json info for "+ plugin)
  logging.info(json.dumps(packagesDictObject, indent=2))

  if(not(specFile['cdapVersion']==packagesDictObject['cdapVersion'])):
    sys.exit("Fields do not match in packages.json and the added plugins")

else :
  logging.info("Success, all modified/added plugin versions are added in packages.json")



#"packages/database-plugin-db2-plugin/1.2.0/spec.json"

