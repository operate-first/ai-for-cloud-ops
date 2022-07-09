#!/usr/bin/python3
import getpass
import sys
sys.path.insert(0, '../')
from cs_recorder import ds_watchdog, io

#import  io, ds_watchdog
from pathlib import Path
import os
import json
import yaml
import argparse
import subprocess

def get_free_filename(stub, directory, suffix=''):
    """ Get a file name that is unique in the given directory
    input: the "stub" (string you would like to be the beginning of the file
        name), the name of the directory, and the suffix (denoting the file type)
    output: file name using the stub and suffix that is currently unused
        in the given directory
    """
    counter = 0
    while True:
        file_candidate = '{}/{}-{}{}'.format(
            str(directory), stub, counter, suffix)
        if Path(file_candidate).exists():
            counter += 1
        else:  # No match found
            if suffix=='.p':
                print("will create pickle file")
            elif suffix:
                Path(file_candidate).touch()
            else:
                Path(file_candidate).mkdir()
            return file_candidate

def json_to_yaml(fname, yamlname, label=None):
    with open(fname) as json_file:
        data = json.load(json_file)

    changes = set()
    open_time = data['open_time']
    close_time = data['close_time']

    for f_create in data['creations']:
        # ADDED FILE SIZE!!
        if os.path.exists(f_create['filename']):
            fsize = os.path.getsize(f_create['filename'])
            addition = f_create['filename'] + " " + str(fsize)
            changes.add(addition)
        else:
            changes.add(f_create['filename'])

    for f_create in data['modifications']:
        # ADDED FILE SIZE!!
        if os.path.exists(f_create['filename']):
            fsize = os.path.getsize(f_create['filename'])
            addition = f_create['filename'] + " " + str(fsize)
            changes.add(addition)
        else:
            changes.add(f_create['filename'])

    #for f_create in data['deletions']:
    #    changes.add(f_create['filename'] + ' d')

    changes = list(changes)

    # create dictionary and save to yaml file
    yaml_in = {'open_time': open_time, 'close_time': close_time, 'label': label, 'changes': changes}
    with open(yamlname, 'w') as outfile:
        yaml.dump(yaml_in, outfile, default_flow_style=False)


if __name__ == '__main__':
    # Command line arguments!
    parser = argparse.ArgumentParser(description='Arguments for Praxi software discovery algorithm.')

    parser.add_argument('-t','--targetdir', help='Path to target directory.', required=True)
    parser.add_argument('-n', '--name', help='Application name', required=True)
    parser.add_argument('-v', '--version', help="Application version", required=True)
    parser.add_argument('-r', '--repetitions', help='Number of installations to perform', default=1)

    args = vars(parser.parse_args())

    num_reps = args['repetitions']
    targetdir = args['targetdir']
    name = args['name']
    version = args['version']
    label = name + '.' + version
    cmd_name = name  + '=' + version
    print(label)
    watch_paths = ['/var/', '/usr/', '/etc/', '/bin/', '/lib/', '/lib64/']

    cmd_install = ['sudo', 'apt-get', '--assume-yes', 'install', cmd_name]
    #cmd_uninstall = ['echo', '"y"', '|', 'sudo', 'apt-get', 'remove', name]
    cmd_uninstall = 'echo "y" | sudo apt-get remove --purge ' + name

    subprocess.call(cmd_install)
    os.system(cmd_uninstall)

    for i in range(int(num_reps)):
        yaml_name = get_free_filename(label, targetdir, suffix='.yaml')
        # use a different watchdog each time cuz im lazy
        dswd = ds_watchdog.DeltaSherlockWatchdog(watch_paths, "*", ".")
        # Recording begins immediately after instantiation.
        print("Recording started")
        subprocess.call(cmd_install)
        cs = dswd.mark()
        print("Recording stopped")
        print(cs)
        io.save_object_as_json(cs, 'cs.dscs')

        json_to_yaml('cs.dscs', yaml_name, label=label)
        os.remove("cs.dscs")

        os.system(cmd_uninstall)
        #subprocess.run(cmd_uninstall)

    print("done")
    del dswd
    sys.exit()
