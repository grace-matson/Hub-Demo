import os
import subprocess
import json
import re
import logging

logging.getLogger().setLevel(logging.INFO)    # Enable logging in GitHub Workflow and enable printing of info level logs

class LazyDecoder(json.JSONDecoder):
  def decode(self, s, **kwargs):
    regex_replacements = [
        (re.compile(r'([^\\])\\([^\\])'), r'\1\\\\\2'),
        (re.compile(r',(\s*])'), r'\1'),
    ]
    for regex, replacement in regex_replacements:
      s = regex.sub(replacement, s)
    return super().decode(s, **kwargs)

def run_shell_command(cmd):
  process = subprocess.run(cmd, stderr=subprocess.PIPE, shell=True)
  if(process.returncode != 0):
    print('Process completed with error: ', process.stderr)
  assert process.returncode == 0
