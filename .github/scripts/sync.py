import utilities

utilities.run_shell_command('gsutil -m rsync -r ./testdir gs://${CENTRAL_BUCKETd}/')