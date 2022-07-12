import os
import sys
import utilities
import json
import logging

logging.getLogger().setLevel(logging.INFO)

list = os.getenv('LIST')
list = list.strip(']["').split(',')
logging.info(list)

specfiles = []
for file in list:
  if(file.split('/')[-1]=="spec.json"):
    specfiles.append(file)
logging.info(specfiles)
if(len(specfiles)==0):
  sys.exit(0)

os.chdir('./packager/')
utilities.run_shell_command('mvn clean package')
os.chdir('../')
utilities.run_shell_command('java -cp "packager/target/lib/*:packager/target/*" io.cdap.hub.Tool build')

f = open("./packages.json", "r")
l = json.loads(f.read())
print(l)
