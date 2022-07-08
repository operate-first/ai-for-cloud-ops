import sys
import os
import optparse
import pickle
import logging
import glob
import yaml
from datetime import datetime

from .trie import Trie
from .tags import filtertags

FILTER_PATH_TOKENS = ['usr', 'bin', 'proc', 'sys', 'etc', 'local', 'src',
                      'dev', 'home', 'root', 'lib', 'pkg', 'sbin', 'share',
                      'cache']

COLUMBUS_CACHE = {}


def refresh_columbus():
    global COLUMBUS_CACHE
    COLUMBUS_CACHE = {}


def columbus(changeset, freq_threshold=2, use_cache=False):
    """ Get labels from single changeset """
    if use_cache:
        key = str(sorted(changeset))
        if key in COLUMBUS_CACHE:
            return COLUMBUS_CACHE[key]
    tags = run_file_paths_discovery2(
        filtertags, changeset, freq_threshold=freq_threshold)
    if use_cache:
        COLUMBUS_CACHE[key] = tags
    return tags


def run_file_paths_discovery2(filtertags, changeset, freq_threshold=2):
    ftrie = Trie(frequency_limit=freq_threshold)
    for filepath in changeset:
        pathtokens = filepath.split('/')
        for token in pathtokens:
            if token not in FILTER_PATH_TOKENS:
                ftrie.insert(token)

    softtags = ftrie.get_all_tags()
    for tag in filtertags:
        softtags.pop(tag, None)
    return softtags
