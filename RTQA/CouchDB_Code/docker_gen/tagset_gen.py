#!/usr/bin/python3
""" Script function:
     - given a directory of changesets, create a directory containing the
       corresponding tagsets
COMMAND LINE INPUTS:
     - one input: changeset directory
     - two inputs: changset directory, tagset directory (IN THAT ORDER)
         * changeset directory must exist, if tagset directory does not exist it
           will be created
OUTPUTS:
     - a directory containing tagsets (.yaml files w/ .tag extension) for each
       of the changesets in the given changeset directory
"""

# Imports
#from collections import Counter
from multiprocessing import Lock

import logging
import logging.config

import argparse
import os
from os import listdir
from os.path import isfile, join, isabs
import sys
sys.path.insert(0, '../')

from pathlib import Path
import time
import yaml

import envoy
from tqdm import tqdm

from columbus.columbus import columbus

LOCK = Lock()

def parse_cs(changeset_names, cs_dir, multilabel=False): # SHOULD PROBABLY GET RID OF ITERATIVE OPTION
    """ Function for parsing a list of changesets.
    input: list of changeset names (strings), name of the directory in which
            they are located
    output: a list of labels and a corresponding list of features for each
            changeset in the directory
            (list of filepaths of changed/added files)
    """
    features = []
    labels = []
    for cs_name in tqdm(changeset_names):
            changeset = get_changeset(cs_name, cs_dir)
            if multilabel:
                """ running a trial in which there may be more than one label for
                    a given changeset """
                if 'labels' in changeset:
                    labels.append(changeset['labels'])
                else:
                    labels.append(changeset['label'])
            else: # each changeset will have just one label
                labels.append(changeset['label'])
            features.append(changeset['changes'])
    return features, labels

def get_changeset(cs_fname, cs_dir):
    """ Function that takes a changeset and returns the dictionary stored in it
    input: file name of a *single* changeset
    output: dictionary containing changed/added filepaths and label(s)
    """
    cs_dir_obj = Path(cs_dir).expanduser()
    changeset = None
    for csfile in cs_dir_obj.glob(cs_fname):
        if changeset is not None:
            raise IOError("Too many changesets match the file name")
        with csfile.open('r') as f:
            changeset = yaml.full_load(f)
    if changeset is None:
        logging.error("No changesets match the name %s", str(csfile))
        raise IOError("No changesets match the name")
    if 'changes' not in changeset or ('label' not in changeset and 'labels' not in changeset):
        logging.error("Couldn't read changeset")
        raise IOError("Couldn't read changeset")
    return changeset

def get_columbus_tags(X, disable_tqdm=False, return_freq=True,
                       freq_threshold=2):
    """ Function that gets the columbus tags for a given list of filesystem
        changes
    input: a list of filesystem changes
    output: a list of tags and their frequency (as strings separated by a colon)
    """
    tags = []
    for changeset in tqdm(X, disable=disable_tqdm):
        tag_dict = columbus(changeset, freq_threshold=freq_threshold)
        if return_freq:
            tags.append(['{}:{}'.format(tag, freq) for tag, freq
                         in tag_dict.items()])
        else:
            tags.append([tag for tag, freq in tag_dict.items()])
    return tags

def create_tagset_names(changeset_names):
    """ Create names for the new tagset files
        (same as changeset names but with a .tag extension)
    input: list of changeset names
    output: list of names for tagsets created for these changesets
    """
    tagset_names = []
    for name in changeset_names:
        new_tagname = name[:-4] + "tag"
        tagset_names.append(new_tagname)
    return tagset_names

def get_changeset_names(cs_dir):
    """ Get the names of all the changesets in a given directory
    # input: a directory name
    # output: names of all changeset files within the directory
    """
    all_files = [f for f in listdir(cs_dir) if isfile(join(cs_dir, f))]
    changeset_names = [f for f in all_files if ".yaml" in f and ".tag" not in f]
    return changeset_names

def get_ids(changeset_names):
    """ Get the unique ID's of each changeset in a list
    input: list of changeset names
    output: list of ids of all changesets in the list (between first and second '.')
    """
    c_ids = []
    c = '.'
    for cs_name in changeset_names:
        idxs = [pos for pos, char in enumerate(cs_name) if char == c]
        print(idxs)
        print("this was idxs")
        curr_id = cs_name[idxs[0]+1:idxs[1]]
        c_ids.append(curr_id)
    return c_ids

def create_files(tagset_names, ts_dir, labels, ids, tags):
    """ Creates the tagset files and puts them in the specified directory
    input: names of tagsets, name of target directory, labels, ids, and tags
    output: returns nothing, creates tagset files (.yaml format) in given directory
    """
    for i, tagset_name in enumerate(tagset_names):
        if(isinstance(labels[i], list)):
            cur_dict = {'labels': labels[i], 'id': ids, 'tags': tags[i]}
        else:
            cur_dict = {'label': labels[i], 'id': ids, 'tags': tags[i]}
        cur_fname = ts_dir + '/' + tagset_name
        with open(cur_fname, 'w') as outfile:
            yaml.dump(cur_dict, outfile, default_flow_style=False)


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
            if suffix:
                Path(file_candidate).touch()
            else:
                Path(file_candidate).mkdir()
            return file_candidate

def create_res_dir(work_dir, path_str=""):
    """ Either creates a result directory in the working directory or
        creates a directory with the specified path name
    input: path of working directory, OPTIONAL additional path string
    output: full file path
    """
    if (path_str!=""): # path specified
        if not os.path.isabs(path_str):
            # IF PATH IS NOT ABSOLUTE, ASSUMED TO BE RELATIVE
            path_str = work_dir + '/' + path_str
        # check if directory exists, if it doesn't, create one!
        if not os.path.isdir(path_str):
            os.mkdir(path_str)
    else: # no path specified
        # create a directory in the working directory for tagsets
        path_str = get_free_filename('tagsets', work_dir)
    return path_str

def get_cs_dir(path_str, work_dir):
    # if not absolute, assume relative
    if not os.path.isabs(path_str):
        path_str = work_dir + '/' + path_str
    # Check if directory exists
    if not os.path.isdir(path_str):
        raise ValueError('Error: directory does not exsist!')
        path_str = ""
    return path_str

def get_directories(c_path, t_path):
    """ Get the names of the changeset and tagset directories from the command
        line inputs
    input: command line arguments passed in at runtime
    output: name of changeset directory, name of tagset directory
    """
    cs_dir = ""
    ts_dir = ""
    valid = True
    if t_path is None:
        # Must create a result directory
        ts_dir = create_res_dir(work_dir)
        # Check if cs_dir exists
        cs_dir = c_path
        if not os.path.isdir(cs_dir):
            raise ValueError("Error: Changeset directory does not exist")
        else:
            cs_dir = get_cs_dir(c_path, work_dir)
    else:
        # use result dir given
        ts_dir = create_res_dir(work_dir, t_path)
        cs_dir = c_path
        if not os.path.isdir(cs_dir):
            raise ValueError("Error: Changeset directory does not exist")
        else:
            cs_dir = get_cs_dir(c_path, work_dir)

    return cs_dir, ts_dir


if __name__ == '__main__':
    prog_start = time.time()
    work_dir = os.path.abspath('.')


    parser = argparse.ArgumentParser(description='Arguments for tagset generation.')
    parser.add_argument('-c','--changedir', help='Path to changeset directory.', required=True)
    parser.add_argument('-t', '--tagdir', help='Optional path to desired tagset directoy.', default=None)

    args = vars(parser.parse_args())

    c_path = args['changedir']
    t_path = args['tagdir']

    cs_dir, ts_dir = get_directories(c_path, t_path)

    if cs_dir == '':
        raise ValueError("Invalid changeset directory")
    if ts_dir == '':
        raise ValueError("Invalid tagset directory")

    # No log messages before logging is set up
    # loglevel = 'DEBUG' # add level options to this?
    # stub = 'tagset_gen'
    # logfile_name = get_free_filename(stub, ts_dir, '.log')

    # numeric_level = getattr(logging, loglevel, None)
    # logging.basicConfig(filename=logfile_name,level=numeric_level)

    changeset_names = get_changeset_names(cs_dir)
    if len(changeset_names)==0:
        logging.error("No changesets in selected directory. Make sure to chose an input directory containing changesets")
        raise ValueError("No changesets in selected directory")

    # logging.info("Creating names for new tagset files:")
    tagset_names = create_tagset_names(changeset_names)
    # ids = get_ids(changeset_names)
    ids = []

    changesets = []
    labels = []
    changesets, labels = parse_cs(changeset_names, cs_dir, multilabel = True)

    # logging.info("Generating tagsets:")
    tags = get_columbus_tags(changesets)

    # logging.info("Writing tagset files to %s", ts_dir)
    create_files(tagset_names, ts_dir, labels, ids, tags)

    # logging.info("Tagset generation time: %s", str(time.time() - prog_start))

