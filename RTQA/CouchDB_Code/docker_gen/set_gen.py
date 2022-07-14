import os
import sys
import time
import math
import subprocess

# Non-default packages
from pip._internal import main as pipmain

# Obtain package name from command to install
package_name = sys.argv[1]
print("Recieved " + package_name)

# Start recording
dirname = os.path.dirname(__file__)
p = subprocess.Popen(['python', os.path.join(dirname, 'cs_rec.py'),'-t',os.path.join(dirname, 'changesets'),'-l',package_name], stdin=subprocess.PIPE, shell=True)

# Install package
p_pip = pipmain(['install', package_name])
if p_pip == 1:
    print("Module not found") 

# Stop recording
p.communicate(input=b'\n')

# Tagset gen
p2 = subprocess.Popen(['python', os.path.join(dirname, 'tagset_gen.py'),'-c',os.path.join(dirname, 'changesets'),'-t',os.path.join(dirname, 'tagsets')], stdin=subprocess.PIPE)