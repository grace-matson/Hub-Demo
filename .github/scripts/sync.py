import utilities

utilities.run_shell_command('gsutil -m rsync -d -c -r -n testdir/ gs://${CENTRAL_BUCKET}/packages')