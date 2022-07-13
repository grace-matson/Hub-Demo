import os
import sys
import utilities
import json
import logging

logging.getLogger().setLevel(logging.INFO)

os.chdir('./packager/')
utilities.run_shell_command('mvn clean package')
os.chdir('../')
utilities.run_shell_command('java -cp "packager/target/lib/*:packager/target/*" io.cdap.hub.Tool build')

added_list = os.getenv('ADDED_LIST').strip(']["').split(',')
modified_list = os.getenv('MODIFIED_LIST').strip(']["').split(',')
list = added_list + modified_list
logging.info(list)

specfiles = []
for file in list:
  if(file.split('/')[-1]=="spec.json"):
    specfiles.append(file)
logging.info(specfiles)
if(len(specfiles)==0):
  sys.exit(0)

f = open("./packages.json", "r")
l = json.loads(f.read())
print(l)


#"packages/database-plugin-db2-plugin/1.2.0/spec.json"

