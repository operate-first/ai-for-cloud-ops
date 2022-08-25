'''
A python script used to install a python package with full dependancies, and generate the changeset for that package
The script also tries to detect whether there was an error in the package installation/changeset generation,
and if yes, writes out to an error text file

INPUT:
    - python package name, can specify version (i.e django==1.1.0)
'''

import os
import sys
import time
import math
import subprocess
import yaml

# Non-default packages
from pip._internal import main as pipmain

# Obtain package name from command to install
package_name = sys.argv[1]
print("Recieved " + package_name)

# Start recording
dirname = os.path.dirname(__file__)
p = subprocess.Popen(['python', os.path.join(dirname, 'cs_rec.py'),'-t',os.path.join(dirname, 'changesets_full'),'-l',package_name], stdin=subprocess.PIPE)
print("Started recording")
# Install package without dependancies
install_error = False
try:
    p_pip = subprocess.run(['pip', 'install', package_name], timeout=3600) # Maximum install time of 1 hour
except subprocess.TimeoutExpired as e:
    install_error = True

# Stop recording
p.communicate(input=b'\n')

changeset_path = "./changesets_full/" + package_name + "-0.yaml"
# Check changeset problems
if os.path.getsize(changeset_path) == 0:
    install_error = True
else:
    f_changeset = open(changeset_path, "r")
    changeset_dict = yaml.load(f_changeset.read(), Loader=yaml.Loader)
    if (len(changeset_dict['changes']) < 2):
        install_error = True


if install_error:
    f = open("./errors.txt", "a")
    f.write(package_name)
    f.write("\n")
    f.close()
    os.remove(changeset_path)

# Tagset gen
# p2 = subprocess.Popen(['python', os.path.join(dirname, 'tagset_gen.py'),'-c',os.path.join(dirname, 'changesets'),'-t',os.path.join(dirname, 'tagsets')], stdin=subprocess.PIPE)
# p2.communicate()