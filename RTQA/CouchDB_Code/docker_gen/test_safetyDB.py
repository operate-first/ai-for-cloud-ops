from struct import pack
from safety_db import INSECURE, INSECURE_FULL
import json
from pip._internal import main as pipmain
import time

output_file = open("existing_packages.txt", "w")
i = 0
for package in INSECURE.keys():
    i = i + 1
    if (i == 1):
        continue

    res = pipmain(['install', package, '--no-dependencies', '-q', '-q'])
    print(package + " ", res)
    if (res == 0):
        output_file.write(package)
        output_file.write("\n")


output_file.close()