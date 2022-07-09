'''
This is a daemon script which performs several tasks for the Praxi Vowpal Wabbit machine learning pipeline.
The daemon first fetches changes from remote repositories containing vulnerable packages.
Then, pip install these packages within a container to generate changesets and tagsets for the VW model.
Finally, append these new changesets/tagsets into a local CouchDB database, and send them to our VW API for training

For demo purposes, this daemon will currently only write the generated changesets/tagsets into a text file
'''

# Fetch changes from remote sources

# URL to git repos
safetyDB_URL = "https://github.com/pyupio/safety-db.git"

# Checker function to detect changes in Safety_DB
def changed_safetyDB():
    return

# Function to obtain list of added packages from our sources. Each tailored to each source
# Each repo presumably has its own method of storing information
def get_package_safetyDB():
    return

# Function to start docker image, with bind mount. Runs a single pip install command with Praxi to generate changeset/tagset
def docker_gen_set():
    return

# Returns the changeset/tagset generated from the docker container
def retrieve_sets():
    return

# Sends the cumulated tagsets and changesets to our CouchDB database
def sets_to_db():
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

if changed_safetyDB():
    new_vuln_packages_safetyDB = get_package_safetyDB()

new_vuln_packages = new_vuln_packages_safetyDB
new_changesets = list()
new_tagsets = list()
# For each package, start a container, begin changeset recording, install package, and generate changeset
for package_info in new_vuln_packages:
    # Start docker container with bind mount to generate changeset/tagset
    docker_gen_set()
    # After gen finish, obtain changeset and tagset
    retrieved_sets = retrieve_sets()
    new_changesets.append(retrieve_sets.changeset)
    new_tagsets.append(retrieve_sets.tagsetset)


# Append to CouchDB
sets_to_db(new_changesets, new_tagsets)

# Write generated files to disk
with open("test_changesets.txt", "w") as f:
    f.write(str(new_changesets))

with open("test_tagsets.txt", "w") as f:
    f.write(str(new_tagsets))