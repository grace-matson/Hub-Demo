import utilities
import subprocess as sp
# output = sp.getoutput('gsutil ls gs://demo-automate-hub-release/packages/').split('\n')
import requests
# print (output.split('\n'))
# utilities.run_shell_command('pip3 install google-cloud-storage')
# output = utilities.run_shell_command('gsutil ls gs://demo-automate-hub-release/packages/')
# print("coutput :", output)

from google.cloud import storage
# storage_client = storage.Client()
# bucket_name = 'hub-cdap-io'
# bucket = storage_client.bucket(bucket_name)
# print(storage.Blob(bucket=bucket, name='packages/database-plugin-db2-plugin/1.3.0/db2-plugin-1.3.0.jar').exists(storage_client))
# blobs_all = list(bucket.list_blobs())
# print(blobs_all)
groupId ='io.cdap.plugin'
artifactId = 'google-cloud'
version = '0.14.0'
p = 'jar'
response = requests.get(f'https://search.maven.org/solrsearch/select?q=g:{groupId}%20AND%20a:{artifactId}%20AND%20v:{version}%20AND%20p:{p}&rows=20&wt=json')
print(response)
response = response.json()
print(response['response']['docs'])
import ast
#
# str = '["packages/plugin-google-drive/1.4.0/ico.png","packages/plugin-google-drive/1.4.0/spec.json"]'
# print(str)
# print(ast.literal_eval(str))
# print(str.strip('[]"').split(','))
# print(type(ast.literal_eval(str)))
#
# list = ['packages/database-plugin-db2-plugin/1.2.0/spec.json', 'packages/database-plugin-db2-plugin/1.3.0/spec.json']
#
# plugin = "gs://hub-cdap-io/v2/packages/plugin-window-aggregation/"
# print("/".join(plugin.split("/")[:-1][4:]))
# print(plugin.split('gs://hub-cdap-io/v2/')[1])

l = ["hello", "i am ", "ho ho"]
print(str(l))