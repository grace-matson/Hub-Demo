import os
import utilities
import logging

#Setting logging level to INFO
logging.getLogger().setLevel(logging.DEBUG)

# Running steps to create packages.json
os.chdir('./packager/')
utilities.run_shell_command('mvn clean package')
os.chdir('../')
utilities.run_shell_command('java -cp "packager/target/lib/*:packager/target/*" io.cdap.hub.Tool build')
