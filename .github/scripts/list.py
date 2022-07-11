import os

list = os.getenv('LIST')
list = list.strip('][').split(', ')
for file in list:
  print(file)