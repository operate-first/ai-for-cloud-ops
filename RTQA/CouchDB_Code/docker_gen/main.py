#!/usr/bin/env python3
""" Script function:
    - two modes:
        1) Cross Validation: takes a single directory of tagsets and runs the
                Praxi application discovery algorithm, dividing the
                data into folds and repeatedly running the experiment
                with each fold being the test set
        2) "Real World" Experiment: takes two directories of tagsets, one for
                training, one for testing, and runs Praxi once, first training
                the model and then evaluating its accuracy using the test
                directory
    - inputs/arguments:
        * -t [directory name]: path to training tagset directory (REQUIRED)
        * -s [directory name]: path to testing tagset directory (only required
                               for experiment 2)
        * -o [directory name]: path to desired result directory
        * -m: run a multilabel experiment
        * -w [args]: customize arguments for VW learning algorithm
        * -n [# of folds]: number of folds to use if running an experiment with
                           cross validation
        * -f: output the full results instead of a summary
        * -v: increase verbosity of log messages
    - output: outputs a text file containing statistics about the performance
              of the algorithm; choice between summary or full result file
"""

# Imports
from multiprocessing import Lock

import logging
import logging.config

import os
from os import listdir
from os.path import isfile, join

from pathlib import Path
import random
#import tempfile
import time
import yaml
import pickle
import copy
import argparse

from sklearn.base import BaseEstimator
from tqdm import tqdm

import numpy as np
from numpy import savetxt
from sklearn import metrics
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

from hybrid_tags import Hybrid

print("In main")

LOCK = Lock()

#######################################
#   FUNCTIONS for accessing tagsets   #
#######################################
def parse_ts(tagset_names, ts_dir):
    # Arguments: - tagset_names: a list of names of tagsets
    #            - ts_dir: the directory in which they are located
    # Returns: - tags: list of lists-- tags for each tagset name
    #          - labels: application name corresponding to each tagset
    tags = []
    labels = []
    for ts_name in tqdm(tagset_names):
            ts_path = ts_dir + '/' + ts_name
            tagset = get_tagset(ts_path)
            if 'labels' in tagset:
                # Multilabel changeset
                labels.append(tagset['labels'])
            else:
                labels.append(tagset['label'])
            tags.append(tagset['tags'])
    return tags, labels

def get_tagset(ts_path): # combine with parse_ts
    # Argument: - complete path to a tagset .yaml file
    # Returns:  - tagset dictionary contained in file (tags, labels)
    with open(ts_path, 'r') as stream:
        data_loaded = yaml.full_load(stream)
    return data_loaded

#######################################
#     MISCELLANEOUS                   #
#######################################

def get_free_filename(stub, directory, suffix=''):
    counter = 0
    while True:
        file_candidate = '{}/{}-{}{}'.format(
            str(directory), stub, counter, suffix)
        if Path(file_candidate).exists():
            print("file exists")
            counter += 1
        else:  # No match found
            # print("no file")
            if suffix=='.p':
                """"""# print("will create pickle file")
            elif suffix:
                Path(file_candidate).touch()
            else:
                Path(file_candidate).mkdir()
            return file_candidate

def fold_partitioning(ts_names, n=3):
    # partition tagsets into folds for cross validation
    folds = [[] for _ in range(n)]

    just_progs = []
    for name in ts_names:
        ts_name_comps = name.split('.')
        just_progs.append(ts_name_comps[0])

    prog_set = set(just_progs)
    unique_progs = (list(prog_set))

    #print(unique_progs)
    #input("Press enter to continue...")

    prog_partition = [[] for _ in range(len(unique_progs))]

    for name in ts_names:
        name_comps = name.split('.')
        just_pname = name_comps[0]
        for i, prog in enumerate(unique_progs):
            if just_pname == prog:
                prog_partition[i].append(name)

    for ts_names in prog_partition:
        for idx, name in enumerate(ts_names):
            folds[idx % n].append(name)

    #print(folds)
    #input("Press enter to continue...")
    return folds

################################
##### ITERATIVE TRAINING #######
################################
def iterative_experiment(train_path, test_path, resfile_name,
                        outdir, vwargs, result_type,
                        initial_model=None, print_misses=False, new_model_name=None,
                        just_train=False, just_test=False):
    """ This function is for running iterative experiments. The model data for
        iterative experiments will be saved to the working directory, and the
        function has the option of building on an existing model.
    input: paths to test directory, train directory, and result directory,
        desired result file name, vw arguments, type of result desired, and
        optionally the name of a pickle file containing a previously trained
        model (an instance of the hybrid class)
    output: trained model .p and .vw files (written to working directory),
        pickle file with label predictions and text file with experiment
        performance statistics (written to result directory)
    """
    if initial_model is None:
        suffix = 'iterative'
        iterative = True
        modfile = new_model_name
        clf = Hybrid(freq_threshold=2, pass_freq_to_vw=True, probability=False,
                     vw_args= vwargs, suffix=suffix, iterative=iterative,
                     use_temp_files=True, vw_modelfile=modfile)
    else:
        clf = pickle.load(open(initial_model, "rb"))

    if not just_test:
        train_names = [f for f in listdir(train_path) if (isfile(join(train_path, f))and f[-3:]=='tag')]
        if(len(train_names) == 0):
            logging.error("No tagsets found in provided training directory")
            raise ValueError("No tagsets in training directory!")
        train_tags, train_labels = parse_ts(train_names, train_path)
    if not just_train:
        test_names = [f for f in listdir(test_path) if (isfile(join(test_path, f)) and f[-3:]=='tag')]
        if(len(test_names) == 0):
            logging.error("No tagsets found in provided testing directory")
            raise ValueError("No tagsets in testing directory!")
        test_tags, test_labels = parse_ts(test_names, test_path)

    resfile = open(resfile_name, 'wb')
    results = []

    # Now train iteratively! (just fit and predict)
    if not (just_test or just_train):
        labels, preds = get_scores(clf, train_tags, train_labels, test_tags, test_labels)
        results.append((labels, preds))

        if print_misses:
            print("Predicting labels:")
            for label, pred in zip(labels, preds):
                if label != pred:
                    print('label:',label,'prediction:',pred)

        # save and print results
        pickle.dump(results, resfile)
        resfile.close()
        logging.info("Printing results:")
        print_results(resfile_name, outdir, result_type, iterative=True)

        # save model
        save_name = clf.vw_modelfile[:-2] + 'p'
        pickle.dump(clf, open(save_name, "wb" ))
    elif just_test:
        preds = clf.predict(test_tags)
        # so results are in test_labels, preds
        results.append((test_labels, preds))
        pickle.dump(results, resfile)
        resfile.close()
        logging.info("Printing results:")
        print_results(resfile_name, outdir, result_type, iterative=True)
    else:
        #just train
        clf.fit(train_tags, train_labels)
        save_name = clf.vw_modelfile[:-2] + 'p'
        pickle.dump(clf, open(save_name, "wb"))

#################################
#### SINGLE LABEL EXPERIMENT ####
#################################
def single_label_experiment(nfolds, tr_path, resfile_name, outdir, vwargs, result_type, ts_path=None, print_misses=False):
    # instantiate hybrid object
    suffix = 'single'
    clf = Hybrid(freq_threshold=2, pass_freq_to_vw=True, probability=False,
                 vw_args=vwargs, suffix=suffix, iterative=False,
                 use_temp_files=True)
    resfile = open(resfile_name, 'wb')
    results = []
    if(ts_path==None): # folds!
        tr_names = [f for f in listdir(tr_path) if (isfile(join(tr_path, f))and f[-3:]=='tag')]
        random.shuffle(tr_names)
        logging.info("Partitioning into %d folds", nfolds)
        folds = fold_partitioning(tr_names, n=nfolds)
        logging.info("Starting cross validation folds: ")
        #
        tags = []
        labels = []
        for fold in folds:
            curtags, curlabels = parse_ts(fold, tr_path)
            tags.append(curtags)
            labels.append(curlabels)

        for idx in range(len(folds)):
            # take current fold to be the "test", use the rest as training
            logging.info("Test fold is: %d", idx)
            #test_tagset_names = fold
            test_tags = tags[idx]
            test_labels = labels[idx]
            train_idx_list = list(range(len(folds)))
            train_idx_list.remove(idx)
            logging.info("Training folds: %s", str(train_idx_list))
            train_tags = []
            train_labels = []
            for i in train_idx_list:
                train_tags += tags[i]
                train_labels += labels[i]

            true_labels, preds = get_scores(clf, train_tags, train_labels, test_tags, test_labels)
            results.append((true_labels, preds))
            if print_misses:
                print("Misclassified labels for fold:", idx)
                for label, pred in zip(true_labels, preds):
                    if label != pred:
                        print('label:',label,'prediction:',pred)

    else: # no folds/crossvalidation
        # get traintags, trainlabels, etc from ts_path, tr_path
        ts_train_names = [f for f in listdir(tr_path) if (isfile(join(tr_path, f))and f[-3:]=='tag')]
        ts_test_names = [f for f in listdir(ts_path) if (isfile(join(ts_path, f)) and f[-3:]=='tag')]

        train_tags, train_labels = parse_ts(ts_train_names, ts_train_path)
        test_tags, test_labels = parse_ts(ts_test_names, ts_test_path)

        logging.info("Getting single label scores:")
        labels, preds = get_scores(clf, train_tags, train_labels, test_tags, test_labels)
        results.append((labels, preds))

        if print_misses:
            print("Misclassified labels:")
            for label, pred in zip(labels, preds):
                if label != pred:
                    print('label:',label,'prediction:',pred)

    pickle.dump(results, resfile)
    # results is a list of tuples!!
    resfile.close()
    logging.info("Printing results:")
    print_results(resfile_name, outdir, result_type)

def get_scores(clf, train_tags, train_labels, test_tags, test_labels,
               binarize=False, store_true=False):
    """ Gets two lists of changeset ids, does training+testing """
    if binarize:
        binarizer = MultiLabelBinarizer()
        clf.fit(train_tags, binarizer.fit_transform(train_labels))
        preds = binarizer.inverse_transform(clf.predict(test_labels))
    else:
        logging.info("Fitting model:")
        clf.fit(train_tags, train_labels) # train model
        logging.info("Generating predictions:")
        preds = clf.predict(test_tags) # predict labels for test set
    return copy.deepcopy(test_labels), preds

def print_results(resfile, outdir, result_type='summary', n_strats=1, args=None, iterative=False):
    """ Calculate result statistics and print them to result file
    input: name of result pickle file, path to result directory, type of result
           desired
    output: text file with experiment result statistics
    """
    logging.info("Writing scores to %s", str(outdir))
    with open(resfile, 'rb') as f:
        results = pickle.load(f)
    # # Now do the evaluation!
    # #results = [
    # #    0 => ([x, y, z], <-- true
    # #          [x, y, k]) <-- pred
    # #]
    numfolds = len(results)
    y_true = []
    y_pred = []
    for result in results:
        y_true += result[0]
        y_pred += result[1]

    labels = sorted(set(y_true))
    # these will be all length 1
    classifications = []
    f1_weighted = []
    f1_micro = []
    f1_macro = []
    p_weighted = []
    p_micro = []
    p_macro = []
    r_weighted = []
    r_micro = []
    r_macro = []
    confusions = []
    label_counts = []
    x = y_true
    y = y_pred

    classifications.append(metrics.classification_report(x, y, labels=labels))
    f1_weighted.append(metrics.f1_score(x, y, labels=labels, average='weighted'))
    f1_micro.append(metrics.f1_score(x, y, labels=labels, average='micro'))
    f1_macro.append(metrics.f1_score(x, y, labels=labels, average='macro'))
    p_weighted.append(metrics.precision_score(x, y, labels=labels, average='weighted'))
    p_micro.append(metrics.precision_score(x, y, labels=labels, average='micro'))
    p_macro.append(metrics.precision_score(x, y, labels=labels, average='macro'))
    r_weighted.append(metrics.recall_score(x, y, labels=labels, average='weighted'))
    r_micro.append(metrics.recall_score(x, y, labels=labels, average='micro'))
    r_macro.append(metrics.recall_score(x, y, labels=labels, average='macro'))
    confusions.append(metrics.confusion_matrix(x, y, labels=labels))
    label_counts.append(len(set(x)))

    # this for loop will only run once
    for strat, report, f1w, f1i, f1a, pw, pi, pa, rw, ri, ra, confuse, lc in zip(
            range(n_strats), classifications, f1_weighted, f1_micro, f1_macro,
            p_weighted, p_micro, p_macro, r_weighted, r_micro, r_macro,
            confusions, label_counts):
        if not iterative:
            if numfolds == 1: # no cross validation
                file_header = (
                    "SINGLE LABEL EXPERIMENTAL REPORT:\n" +
                    time.strftime("Generated %c\n\n") +
                    ('\n Args: {}\n\n'.format(args) if args else '') +
                    "EXPERIMENT WITH {} TEST CHANGESETS\n".format(len(y_true)))
                fstub = 'single_exp'
            else:
                file_header = (
                    "SINGLE LABEL EXPERIMENTAL REPORT:\n" +
                    time.strftime("Generated %c\n\n") +
                    ('\n Args: {}\n\n'.format(args) if args else '') +
                    "{} FOLD CROSS VALIDATION WITH {} CHANGESETS\n".format(numfolds, len(y_true)))
                fstub = 'single_exp_cv'
        else:
            file_header = (
                "ITERATIVE EXPERIMENTAL REPORT:\n" +
                time.strftime("Generated %c\n\n") +
                ('\nArgs: {}\n\n'.format(args) if args else '') +
                "LABEL COUNT : {}\n\n".format(lc) +
                "EXPERIMENT WITH {} TEST CHANGESETS\n".format(len(y_true)))
            fstub = 'iter_exp'

        os.makedirs(str(outdir), exist_ok=True) # makes directory if it doesn't exist
        if result_type == 'summary':
            fstub += '_summary'
            file_header += (
                "F1 SCORE : {:.3f} weighted\n".format(f1w) +
                "PRECISION: {:.3f} weighted\n".format(pw) +
                "RECALL   : {:.3f} weighted\n\n".format(rw))
            if numfolds == 1:
                hits = misses = predictions = 0
                for pred, label in zip(y_true, y_pred):
                    if pred == label:
                        hits += 1
                    else:
                        misses += 1
                    predictions += 1
                str_add = "Preds: " + str(predictions) + "\nHits: " + str(hits) + "\nMisses: " + str(misses)
                file_header += str_add
            fname = get_free_filename(fstub, outdir, '.txt')
            f = open(fname, "w")
            f.write(file_header) # just need header b/c no confusion matrix
            f.close()
        else:
            # FULL RESULTS (original result format)
            file_header += (
                "F1 SCORE : {:.3f} weighted, {:.3f} micro-avg'd, {:.3f} macro-avg'd\n".format(f1w, f1i, f1a) +
                "PRECISION: {:.3f} weighted, {:.3f} micro-avg'd, {:.3f} macro-avg'd\n".format(pw, pi, pa) +
                "RECALL   : {:.3f} weighted, {:.3f} micro-avg'd, {:.3f} macro-avg'd\n#\n".format(rw, ri, ra))
            file_header += ("# {:-^55}\n#".format("CLASSIFICATION REPORT") + report.replace('\n', "\n#") +
                           " {:-^55}\n".format("CONFUSION MATRIX"))
            fname = get_free_filename(fstub, outdir, '.txt')
            savetxt("{}".format(fname),
                    confuse, fmt='%d', header=file_header, delimiter=',',comments='')

##############################################################################
###                MULTILABEL EXPERIMENTS                                  ###
##############################################################################

def multi_label_experiment(nfolds, tr_path, resfile_name, outdir, vwargs, result_type, ts_path=None):
    suffix = 'multi'
    # VW ARGS SHOULD BE PASSED IN
    clf = Hybrid(freq_threshold=2, pass_freq_to_vw=True, probability=True,
                 vw_args=vwargs, suffix=suffix, use_temp_files=True)

    resfile = open(resfile_name, 'wb')
    results = []
    if (ts_path==None): # CROSS VALIDATION EXPERIMENT!
        tagset_names = [f for f in listdir(tr_path) if (isfile(join(tr_path, f))and f[-3:]=='tag')]
        random.shuffle(tagset_names)
        # Partition into folds (random)
        folds = [[] for _ in range(nfolds)]
        # randomly shuffle tagset names, split into 4
        for i, name in enumerate(tagset_names):
            folds[i%nfolds].append(name)
        tags = []
        labels = []
        for fold in folds:
            curtags, curlabels = parse_ts(fold, tr_path)
            tags.append(curtags)
            labels.append(curlabels)
        for idx in range(len(folds)):
            # take current fold to be the "test", use the rest as training
            logging.info("Test fold is: %d", idx)
            test_tags = tags[idx]
            test_labels = labels[idx]
            train_idx_list = list(range(len(folds)))
            train_idx_list.remove(idx)
            logging.info("Training folds: %s", str(train_idx_list))
            train_tags = []
            train_labels = []
            for i in train_idx_list:
                train_tags += tags[i]
                train_labels += labels[i]
            results.append(get_multilabel_scores(clf, train_tags, train_labels, test_tags, test_labels))
    else:
        ts_train_names = [f for f in listdir(tr_path) if (isfile(join(tr_path, f))and f[-3:]=='tag')]
        ts_test_names = [f for f in listdir(ts_path) if (isfile(join(ts_path, f)) and f[-3:]=='tag')]

        train_tags, train_labels = parse_ts(ts_train_names, ts_train_path)
        test_tags, test_labels = parse_ts(ts_test_names, ts_test_path)

        results.append(get_multilabel_scores(clf, train_tags, train_labels, test_tags, test_labels))

    pickle.dump(results, resfile)
    resfile.close()
    print_multilabel_results(resfile_name, outdir, result_type, args=clf.get_args(), n_strats=1)


def get_multilabel_scores(clf, train_tags, train_labels, test_tags, test_labels):
    """Gets scores while providing the ntags to clf"""
    clf.fit(train_tags, train_labels)
    # rulefile = get_free_filename('rules', '.', suffix='.yml')
    # logging.info("Dumping rules to %s", rulefile)
    # with open(rulefile, 'w') as f:
    #     yaml.dump(clf.rules, f)
    ntags = [len(y) if isinstance(y, list) else 1 for y in test_labels]
    preds = clf.top_k_tags(test_tags, ntags)
    return test_labels, preds

def print_multilabel_results(resfile, outdir, result_type, args=None, n_strats=1, summary=False):
    """ Calculate result statistics and print them to result file
    input: name of result pickle file, path to result directory, type of result
           desired
    output: text file with experiment result statistics
    """
    #logging.info('Writing scores to %s', str(outdir))
    with open(resfile, 'rb') as f:
        results = pickle.load(f)
    numfolds = len(results)
    y_true = []
    y_pred = []
    for result in results:
        y_true += result[0]
        y_pred += result[1]

    bnz = MultiLabelBinarizer()
    bnz.fit(y_true)
    all_tags = copy.deepcopy(y_true)
    for preds in y_pred:
        for label in preds:
            if label not in bnz.classes_:
                all_tags.append([label])
                bnz.fit(all_tags)
    y_true = bnz.transform(y_true)
    y_pred = bnz.transform(y_pred)

    labels = bnz.classes_
    report = metrics.classification_report(y_true, y_pred, target_names=labels)
    f1w = metrics.f1_score(y_true, y_pred, average='weighted')
    f1i = metrics.f1_score(y_true, y_pred, average='micro')
    f1a = metrics.f1_score(y_true, y_pred, average='macro')
    pw = metrics.precision_score(y_true, y_pred, average='weighted')
    pi = metrics.precision_score(y_true, y_pred, average='micro')
    pa = metrics.precision_score(y_true, y_pred, average='macro')
    rw = metrics.recall_score(y_true, y_pred, average='weighted')
    ri = metrics.recall_score(y_true, y_pred, average='micro')
    ra = metrics.recall_score(y_true, y_pred, average='macro')

    os.makedirs(str(outdir), exist_ok=True)

    if numfolds == 1:
        file_header = ("MULTILABEL EXPERIMENT REPORT\n" +
            time.strftime("Generated %c\n") +
            ('\nArgs: {}\n\n'.format(args) if args else '') +
            "EXPERIMENT WITH {} TEST CHANGESETS\n".format(len(y_true)))
        fstub = 'multi_exp'
    else:
        file_header = ("MULTILABEL EXPERIMENT REPORT\n" +
            time.strftime("Generated %c\n") +
            ('\nArgs: {}\n'.format(args) if args else '') +
            "\n{} FOLD CROSS VALIDATION WITH {} CHANGESETS\n".format(numfolds, len(y_true)))
        fstub = 'multi_exp_cv'

    if result_type == 'summary':
        file_header += ("F1 SCORE : {:.3f} weighted\n".format(f1w) +
            "PRECISION: {:.3f} weighted\n".format(pw) +
            "RECALL   : {:.3f} weighted\n".format(rw))
        fstub += '_summary'
    else:
        file_header += ("F1 SCORE : {:.3f} weighted, {:.3f} micro-avg'd, {:.3f} macro-avg'd\n".format(f1w, f1i, f1a) +
            "PRECISION: {:.3f} weighted, {:.3f} micro-avg'd, {:.3f} macro-avg'd\n".format(pw, pi, pa) +
            "RECALL   : {:.3f} weighted, {:.3f} micro-avg'd, {:.3f} macro-avg'd\n\n".format(rw, ri, ra))
        file_header += (" {:-^55}\n".format("CLASSIFICATION REPORT") + report.replace('\n', "\n"))
    fname = get_free_filename(fstub, outdir, '.txt')


    savetxt("{}".format(fname),
            np.array([]), fmt='%d', header=file_header, delimiter=',',
            comments='')


if __name__ == '__main__':
    prog_start = time.time()

    parser = argparse.ArgumentParser(description='Arguments for Praxi software discovery algorithm.')
    parser.add_argument('-t','--traindir', help='Path to training tagset directory.', default=None)
    parser.add_argument('-s', '--testdir', help='Path to testing tagset directoy.', default=None)
    parser.add_argument('-o', '--outdir', help='Path to desired result directory', default='.')
    # run a single label experiment by default, if --multi flag is added, run a multilabel experiment!
    parser.add_argument('-m','--multi', dest='experiment', action='store_const', const='multi',
                        default='single', help="Type of experiment to run (single-label default).")
    parser.add_argument('-w','--vwargs', dest='vw_args', default='-b 26 --learning_rate 1.5 --passes 10',
                        help="custom arguments for VW.")
    parser.add_argument('-n', '--nfolds', help='number of folds to use in cross validation', default=1) # make default 1?
    parser.add_argument('-f', '--fullres', help='generate full result file.', dest='result',
                        action='store_const', const='full', default='summary')
    parser.add_argument('-v', '--verbosity', dest='loglevel', action='store_const', const='DEBUG',
                        default='WARNING',help='specify level of detail for log file')
    # IMPLEMENT THIS!
    parser.add_argument('-l' '--labels', dest='print_labels', action='store_const', const=True, default=False,
                        help='Print missed labels')
    # DEFAULT: NO FOLDS
    #   - will expect TWO directories as arguments
    # iterative options
    parser.add_argument('-i', '--iterative', default=None, help='Run iterative experiment (provide name)')
    parser.add_argument('-p', '--previous', default=None, help='Optional: previous model name')
    # THE FOLLOWING OPTIONS CAN ONLY BE USED WITH ITERATIVE TRAINING
    parser.add_argument('-r', '--jtrain', dest='justtrain', action='store_const', const=True, default=False, help='Just train and save the model')
    parser.add_argument('-e', '--jtest', dest='justtest', action='store_const', const=True, default=False, help='Just test against previously trained model')

    args = vars(parser.parse_args())

    outdir = os.path.abspath(args['outdir'])
    nfolds = int(args['nfolds'])
    ts_train_path = args['traindir']
    ts_test_path = args['testdir']

    # SET UP LOGGING
    loglevel = args['loglevel']
    stub = 'praxi_exp'
    logfile_name = get_free_filename(stub, outdir, '.log')

    numeric_level = getattr(logging, loglevel, None)
    logging.basicConfig(filename=logfile_name,level=numeric_level)

    # Log command line args
    result_type = args['result'] # full or summary
    logging.info("Result type: %s", result_type)

    exp_type = args['experiment'] # single or multi
    logging.info("Experiment type: %s", exp_type)

    print_misses = args['print_labels']

    vwargs = args['vw_args']
    logging.info("Arguments for Vowpal Wabbit: %s", vwargs)

    ####################
    iterative = args['iterative']
    initial_model = args['previous']
    j_tr = args['justtrain']
    j_ts = args['justtest']

    if(iterative is None and initial_model is not None):
        iterative = initial_model

    if(nfolds!= 1 and ts_test_path!=None):
        # ERROR: SHOULDNT HAVE A TEST DIRECTORY IF CROSS VALIDATION IS OCCURRING
        logging.error("Too many input directories. If performing cross validation, expect just one.")
        raise ValueError("Too many input directories! Only need one for cross validation.")
    else:
        if iterative is not None:
            # run iterative exp (all single label for now, no cross validation)
            logging.info("Starting iterative experiment")
            logging.info("Model files will be saved to working directory")
            if initial_model is not None:
                logging.info("Will iteratively train the model: %s", initial_model)
                new_model_name = None
            else:
                new_model_name = iterative
                logging.info("Will save new model to %s", new_model_name)
            # Might not need training/testing directory! (later add "just testing" and "just training" option)
            logging.info("Training directory: %s", ts_train_path)
            logging.info("Testing directory: %s", ts_test_path)
            resfile_name = get_free_filename('iterative_test', outdir, '.p') # add arg to set stub?
            iterative_experiment(ts_train_path, ts_test_path, resfile_name, outdir, vwargs, result_type,
                                 initial_model=initial_model, print_misses=print_misses, new_model_name=new_model_name,
                                 just_train=j_tr, just_test=j_ts)
        else:
            if exp_type == 'single':
                if(nfolds == 1):
                    logging.info("Starting single label experiment")
                    logging.info("Training directory: %s", ts_train_path)
                    logging.info("Testing directory: %s", ts_test_path)
                else:
                    # CROSS VALIDATION
                    logging.info("Starting cross validation single label experiment with %s folds", str(nfolds))
                    logging.info("Tagset directory: %s", ts_train_path)
                resfile_name = get_free_filename('single_test', outdir, '.p') # add arg to set stub?
                single_label_experiment(nfolds, ts_train_path, resfile_name, outdir, vwargs, result_type,
                                        ts_path=ts_test_path, print_misses=print_misses) # no train directory
            else: # multi
                if(nfolds == 1):
                    logging.info("Starting multi label experiment")
                    logging.info("Training directory: %s", ts_train_path)
                    logging.info("Testing directory: %s", ts_test_path)
                else:
                    # CROSS VALIDATION
                    logging.info("Starting cross validation multi label experiment with %s folds", str(nfolds))
                    logging.info("Tagset directory: %s", ts_train_path)
                resfile_name = get_free_filename('multi_test', outdir, '.p')
                multi_label_experiment(nfolds, ts_train_path, resfile_name, outdir, vwargs,
                                       result_type, ts_path=ts_test_path) #, print_misses=print_misses)

    logging.info("Program runtime: %s", str(time.time()-prog_start))
