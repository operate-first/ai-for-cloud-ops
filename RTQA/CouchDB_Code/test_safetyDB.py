from struct import pack
from safety_db import INSECURE, INSECURE_FULL
import json
import distlib.database as database
import subprocess
from subprocess import PIPE, STDOUT
import time

def versions_from_pip(p_versions):
    p_versions_split = p_versions.split()
    begin = False
    res = list()
    for phrase in p_versions_split:

        if 'INSTALLED' in phrase:
            break

        if begin:
            ver = phrase.strip(',')
            res.append(ver)

        if 'versions:' in phrase:
            begin = True

    return res

def docker_gen_set(package, version):
    p_docker = subprocess.run(['docker', 'run', 'python', 'echo', 'hi'], shell=True, stdout=PIPE, stderr=PIPE)
    return

# p_versions = subprocess.run(['pip', 'index', 'versions', 'django'], shell=True, stdout=PIPE, stderr=PIPE)
# versions = versions_from_pip( p_versions.stdout.decode('utf-8'))
# print(versions)


i = 0
total_packages = 0
unlisted = 0
for key, value in INSECURE.items():
    i = i + 1
    if i == 1:  # First item doesn't count
        continue
    
    p_versions = subprocess.run(['pip', 'index', 'versions', key], shell=True, stdout=PIPE, stderr=PIPE)
    if (p_versions.returncode == 1): # Package doesn't exist
        unlisted = unlisted + 1
        continue

    versions = versions_from_pip( p_versions.stdout.decode('utf-8'))
    for version in versions:
        docker_gen_set(key, version)
        break

    # total_packages = total_packages + len(versions)


    if i > 10:
        break

print( str(i - unlisted) + "/" + str(i) + " Packages")
print(str(total_packages) + " versions")