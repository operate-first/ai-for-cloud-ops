'''
This python script performs the changeset generation for the packages contained in the safetyDB repo.
The script obtains the list of packages in safetyDB, gets the list of versions for each package,
and for each package-version, starts a docker container that installs the package while generating the changeset
for that particular package-version

Note that the docker containers created by this script uses a bind mount.
That mounted directory should contain the various scripts, directories, and additional files required
to properly install packages and generate the changesets

The mounted directory used for these experiments was named "docker_gen", and contained various python scripts which 
will be explaiend in thier own docstrings

Note the hardcoded paths in this script, which should be changed appropriately

Usage is:
python test_batch.py
'''
from base64 import decode
from struct import pack
from safety_db import INSECURE, INSECURE_FULL
import json
import distlib.database as database
import subprocess
from subprocess import PIPE, STDOUT
import concurrent.futures
import time
import os 

# Given the output from "pip index versions <package_name>", obtain a list of 
# version strings for that package
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

# Two functions which both starts a docker container with a command. 
# docker_gen_set_raw installs a single package with no dependencies
# docker_gen_set_full installs a single package with full dependencies
def docker_gen_set_raw(package, version):
    p_docker = subprocess.run(['docker', 'run','-v', '/c/Users/Quan Minh Pham/Documents/Projects/RTQA 2022/ai-for-cloud-fork/RTQA/CouchDB_Code/docker_gen://praxi', '--network', 'host', 'shuttershy/python', 'python', 'set_gen_raw.py', package + "==" + version], shell=True, stdout=PIPE, stderr=PIPE)
    return

def docker_gen_set_full(package, version):
    p_docker = subprocess.run(['docker', 'run','-v', '/c/Users/Quan Minh Pham/Documents/Projects/RTQA 2022/ai-for-cloud-fork/RTQA/CouchDB_Code/docker_gen://praxi', '--network', 'host', 'shuttershy/python', 'python', 'set_gen_full.py', package + "==" + version], shell=True, stdout=PIPE, stderr=PIPE)
    return


# Obtain list of packages whose changesets are already generated
already_got = set()
changeset_dir = os.listdir('./docker_gen/changesets')
for changeset in changeset_dir:
    module_name = changeset[0:changeset.find('=')]
    already_got.add(module_name)

i = 0
# insecure.json contains the list of vulnerable packages from safetyDB
INSECURE_file = open("data/insecure.json", "r")
INSECURE = json.load(INSECURE_file)
INSECURE_file.close()

for key, value in INSECURE.items():
    i = i + 1
    if i < 7:  # First key value is some metadata for SafetyDB. Skip it
        continue
    
    if key in already_got:
        continue

    # Get all versions for the package
    p_versions = subprocess.run(['pip', 'index', 'versions', key], shell=True, stdout=PIPE, stderr=PIPE)
    if (p_versions.returncode == 1): # Package has been unlisted from PYPI, skip
        continue

    # Obtain array of versions. versions = ['4.0.3', '4.0.2', ...]
    versions = versions_from_pip( p_versions.stdout.decode('utf-8'))

    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
        executor.map(docker_gen_set_raw, [key] * len(versions), versions)
    
    subprocess.run(['docker', 'system', 'prune', '--force'], shell=True, stdout=PIPE, stderr=PIPE)

    print("Done " + 'pip')

    if i > 11:
        break

# # Gen tagset
# dirname = os.path.dirname(__file__)
# p2 = subprocess.Popen(['python', os.path.join(dirname, 'docker_gen/tagset_gen.py'),'-c',os.path.join(dirname, 'docker_gen/changesets'),'-t',os.path.join(dirname, 'docker_gen/tagsets')], stdin=subprocess.PIPE)
