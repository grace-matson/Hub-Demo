import utilities
utilities.run_shell_command('pip3 install google-cloud-storage')

from google.cloud import storage
storage_client = storage.Client()
bucket_name = 'demo-automate-hub-release'
bucket = storage_client.bucket(bucket_name)
# print(storage.Blob(bucket=bucket, name='packages/database-plugin-db2-plugin/1.3.0/db2-plugin-1.3.0.jar').exists(storage_client))
blobs_all = list(bucket.list_blobs())
print(blobs_all)