'''
This is a daemon script which performs several tasks for the Praxi Vowpal Wabbit machine learning pipeline.
The daemon first fetches changes from remote repositories containing vulnerable packages.
Then, pip install these packages within a container to generate changesets and tagsets for the VW model.
Finally, append these new changesets/tagsets into a local CouchDB database, and send them to our VW API for training

For demo purposes, this daemon will currently only write the generated changesets/tagsets into a text file
'''

import requests
import json
import base64
import subprocess
from subprocess import PIPE
import concurrent
import os

# Checker function to detect changes in Safety_DB
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

# Couchdb helper functions
def couchdb_put(domain, path, uuid, dict):
    r = requests.put(domain + "/" + path + "/" + uuid, data=dict)

def couchdb_get(domain, path):
    r = requests.get(domain + "/" + path)
    return r.text

def changed_safetyDB():
    return

# Function to obtain list of added packages from our sources. Each tailored to each source
# Each repo presumably has its own method of storing information
def get_package_safetyDB(included_dict):
    res_dict = dict()

    headers = {"accept" : "application/vnd.github+json"}
    r = requests.get("https://api.github.com/repos/pyupio/safety-db/contents/data/insecure.json", headers=headers)
    data_dict = json.loads(r.content.decode('utf-8'))
    safety_dat_b64 = data_dict['content']
    safety_dat = base64.b64decode(safety_dat_b64).decode('utf-8')
    safety_dict = json.loads(safety_dat)
    print("Got safetydb")
    i = 0
    for key, item in safety_dict.items():
        i += 1
        if i > 20:
            break
        # Get all versions for the package
        p_versions = subprocess.run(['pip', 'index', 'versions', key], shell=True, stdout=PIPE, stderr=PIPE)
        print ("Done " + key)
        if (p_versions.returncode == 1): # Package has been unlisted from PYPI, skip
            continue

        # Obtain array of versions. versions = ['4.0.3', '4.0.2', ...]
        versions = versions_from_pip( p_versions.stdout.decode('utf-8'))
        # Get latest version
        latest_version = versions[0]

        # Check if key in included_dict
        if key not in included_dict.keys():
            res_dict[key] = versions
            continue

        print("found " + key )
        print("for " + included_dict[key])
        # Compare latest vers
        if latest_version != included_dict[key]:
            res_dict[key] = list()
            for version in versions:
                if version != included_dict[key]:
                    res_dict[key].append(version)
                else:
                    print("stopped at " + version)
                    break

    return res_dict

# docker_gen_set_raw installs a single package with no dependencies
# docker_gen_set_full installs a single package with full dependencies
def docker_gen_set_raw(package, version):
    p_docker = subprocess.run(['docker', 'run','-v', '/home/quanmp/Documents/docker_gen://praxi', 'shuttershy/python', 'python', 'set_gen_raw.py', package + "==" + version], stdout=PIPE, stderr=PIPE)
    # err = p_docker.stderr.decode('utf-8')
    # if not err.startswith('WARNING'):
    #   print(err)
    #   print("\n")
    return

# Function to start docker image, with bind mount. Runs a single pip install command with Praxi to generate changeset/tagset
def docker_gen_set(job_dict):
    # Generate the changesets, these will be located in the docker volumes
    for key, versions in job_dict.items():

        with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
            executor.map(docker_gen_set_raw, [key] * len(versions), versions)

        subprocess.run(['docker', 'system', 'prune', '--force'], stdout=PIPE, stderr=PIPE)
    
        print("Done " + key)
    return


# Sends the cumulated tagsets and changesets to our CouchDB database
def sets_to_db(changeset_path, tagset_path):

    changeset_list = os.listdir(changeset_path)
    tagset_list = os.listdir(tagset_path)

    # Iterate through list, get the filename, open the file, read the yaml into a list.
    # Then multithread the list, each yaml, convert to json, upload to couchdb

    changeset_yaml = list()
    for changeset_fn in changeset_list:
        with open(changeset_path + "/" + changeset_fn, 'r') as f:
            changeset_yaml.append(f.read())

    # Get UUID for each file
    r_uuid = requests.get("http://admin:admin@127.0.0.1:5984/_uuids?count=" + str(len(changeset_yaml)))
    uuids = json.loads(r_uuid.text)['uuids']

    # yaml to json
    changeset_json = list()
    for cs in changeset_yaml:
        cs_json = json.dumps(yaml.load(cs, Loader=yaml.Loader))
        changeset_json.append(cs_json)
    

    couchdb_domain = "http://admin:admin@127.0.0.1:5984"
    path = "power"

    # Send off to couchdb database
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
        executor.map(couchdb_put, [couchdb_domain] * len(changeset_json), [path] * len(changeset_json), uuids, changeset_json)

    return


# Sends tagsets to vw for training. This will be unused for now
def tagsets_to_vw():
    return

# Obtain list of new packages to install, in the following form:
# [
#   ("django", "2.4.2"),
#   ("tensorflor", "2.5.8"),
#   ...
# ]

# URL to couchdb 
couchdb = "http://admin:admin@127.0.0.1:5984"

test_dict = {
    "aegea" : "4.1.0",
    "aethos": "1.2.5"
}

print(get_package_safetyDB(test_dict))

included_dict = json.loads(couchdb_get(couchdb, "/included/included_packages"))
job_dict = get_package_safetyDB(included_dict)
docker_gen_set(job_dict)
changeset_path = "./docker_gen/changesets"
tagset_path = "./docker_gen/tagsets"
sets_to_db(changeset_path, tagset_path)

