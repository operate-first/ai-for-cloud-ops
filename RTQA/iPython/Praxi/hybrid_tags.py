"""Contains class and functions for Praxi algorithm
"""
# Imports
from collections import Counter
import logging
import logging.config
from multiprocessing import Lock
import os
from pathlib import Path
import random
import tempfile
import time
import yaml

#add this
from columbus import columbus

import envoy
from sklearn.base import BaseEstimator
from tqdm import tqdm

LOCK = Lock()

class Hybrid(BaseEstimator):
    """ scikit style class for hybrid method """
    def __init__(self, freq_threshold=1, vw_binary="pathtovw",
                 pass_freq_to_vw=False, pass_files_to_vw=False,
                 vw_args='-b 26 --passes=20 -l 50',
                 probability=False, tqdm=True,
                 suffix='', iterative=False,
                 loss_function='hinge',
                 use_temp_files=False,
                 vw_modelfile='model.vw'): # if this is set true it will delete everything after end of runtime?
        """ Initializer for Hybrid method. Do not use multiple instances
        simultaneously.
        """
        # getting path to vw
        fout=os.popen("which vw")
        fout = fout.read().strip()
        vw_binary = fout
        

        self.freq_threshold = freq_threshold
        self.vw_args = vw_args
        self.pass_freq_to_vw = pass_freq_to_vw
        self.probability = probability
        self.loss_function = loss_function
        self.vw_binary = vw_binary
        self.tqdm = tqdm #loop progrss
        self.pass_files_to_vw = pass_files_to_vw # bool
        self.suffix = suffix
        self.iterative = iterative
        self.use_temp_files = use_temp_files # (not self.iterative) and
        self.vw_modelfile = vw_modelfile
        self.trained = False # model is always instantiated untrained

    def get_args(self):
        """ Returns vw args """
        try:
            retval = self.vw_args_
        except AttributeError:
            retval = self.vw_args
        return retval

    def refresh(self):
        """Remove all cached files, reset iterative training."""
        if self.trained:
            safe_unlink(self.vw_modelfile)
            self.indexed_labels = {}
            self.reverse_labels = {}
            self.all_labels = set()
            self.label_counter = 1
        self.trained = False
        columbus.refresh_columbus()

    def fit(self, X, y): # X = TAGsets, y = labels
        """ Trains classifier
        input: list of tags [list] and labels [list] for ALL training tagsets
        output: trained model
        """
        start = time.time()
        if not self.probability: # probability has to do with whether or not it is multilabel
            X, y = self._filter_multilabels(X, y)
        if self.use_temp_files and not self.iterative:
            modelfileobj = tempfile.NamedTemporaryFile('w', delete=False)
            self.vw_modelfile = modelfileobj.name
            modelfileobj.close()
        else:
            #self.vw_modelfile = 'trained_model-%s.vw' % self.suffix
            if not (self.iterative and self.trained):
                safe_unlink(self.vw_modelfile)
            else:
                logging.info("Using old vw_modelfile: %s", self.vw_modelfile)
        logging.info('Started hybrid model, vw_modelfile: %s',
                     self.vw_modelfile)
        self.vw_args_ = self.vw_args
        if not (self.iterative and self.trained):
            self.indexed_labels = {}
            self.reverse_labels = {}
            self.all_labels = set()
            self.label_counter = 1
        else:
            # already have a trained model
            self.vw_args_ += ' -i {}'.format(self.vw_modelfile)
        # add labels in y to all_labels
        for labels in y:
            if isinstance(labels, list):
                for l in labels:
                    self.all_labels.add(l)
            else:
                self.all_labels.add(labels)
        for label in sorted(list(self.all_labels)):
            if label not in self.indexed_labels:
                self.indexed_labels[label] = self.label_counter
                self.reverse_labels[self.label_counter] = label
                self.label_counter += 1
        ################################################
        ## Create VW arg string ########################
        if self.probability:
            self.vw_args_ += ' --csoaa {}'.format(len(self.all_labels))
        else:
            self.vw_args_ += ' --probabilities'
            self.loss_function = 'logistic'
            self.vw_args_ += ' --loss_function={}'.format(self.loss_function)
            if self.iterative:
                self.vw_args_ += ' --oaa 80'
            else:
                self.vw_args_ += ' --oaa {}'.format(len(self.all_labels))
        if self.iterative:
            self.vw_args_ += ' --save_resume'
        self.vw_args_ += ' --kill_cache --cache_file a.cache'
        ####################################################
        train_set = list(zip(X, y))
        random.shuffle(train_set)
        if self.use_temp_files:
            f = tempfile.NamedTemporaryFile('w', delete=False)
        else:
            with open('./label_table-%s.yaml' % self.suffix, 'w') as f:
                yaml.dump(self.reverse_labels, f)
            f = open('./fit_input-%s.txt' % self.suffix, 'w')
        for tag, labels in train_set:
            if isinstance(labels, str):
                labels = [labels]
            input_string = ''
            if self.probability:
                for label, number in self.indexed_labels.items():
                    if label in labels:
                        input_string += '{}:0.0 '.format(number)
                    else:
                        input_string += '{}:1.0 '.format(number)
            else:
                input_string += '{} '.format(self.indexed_labels[labels[0]])
            f.write('{}| {}\n'.format(input_string, ' '.join(tag)))
        f.close()
        # write all tag/label combos into a file f ^^^
        ######## Call VW ML alg ##################################
        # print("Calling " + '{vw_binary} {vw_input} {vw_args} -f {vw_modelfile}'.format(
        #     vw_binary=self.vw_binary, vw_input=repr(f.name),
        #     vw_args=self.vw_args_, vw_modelfile=repr(self.vw_modelfile)))

        # time.sleep(20)

        command = '{vw_binary} {vw_input} {vw_args} -f {vw_modelfile}'.format(
            vw_binary=self.vw_binary, vw_input=repr(f.name),
            vw_args=self.vw_args_, vw_modelfile=repr(self.vw_modelfile))
        #logging.info('vw input written to %s, starting training', f.name)
        #logging.info('vw command: %s', command)
        vw_start = time.time()
        c = envoy.run(command)
        ##########################################################
        ### Print info about VW run ##############################
        #logging.info("vw took %f secs." % (time.time() - vw_start))
        print("vw took this many seconds: ", (time.time() - vw_start))
        if c.status_code:
            logging.error(
                'something happened to vw, code: %d, out: %s, err: %s',
                c.status_code, c.std_out, c.std_err)
            raise IOError('something happened to vw, code: %d, out: %s, err: %s',
                c.status_code, "\n", c.std_out, "\n", c.std_err)
        else:
            logging.info(
                'vw ran sucessfully. out: %s, err: %s',
                c.std_out, c.std_err)
        if self.use_temp_files: # WILL USUALLY BE FALSE
            safe_unlink(f.name)
        self.trained = True # once the fit function has been run, model has been trained!
        logging.info("Training took %f secs." % (time.time() - start))

    def predict_proba(self, X): # X = tagsets
        """Calculates probability of any of the labels that the model has been
            trained on belonging to each tagset in X
        input: list of tagsets
        output: probabilities for each label and each tagset
        """
        start = time.time()
        if not self.trained:
            raise ValueError("Need to train the classifier first")
        #tags = self._get_tags(X) (X = tags)
        if self.use_temp_files:
            f = tempfile.NamedTemporaryFile('w', delete=False)
            outfobj = tempfile.NamedTemporaryFile('w', delete=False)
            outf = outfobj.name
            outfobj.close()
        else:
            f = open('./pred_input-%s.txt' % self.suffix, 'w')
            outf = './pred_output-%s.txt' % self.suffix
        if self.probability:
            for tag in X:
                f.write('{} | {}\n'.format(
                    ' '.join([str(x) for x in self.reverse_labels.keys()]),
                    ' '.join(tag)))
        else:
            for tag in X:
                f.write('| {}\n'.format(' '.join(tag)))
        f.close()
        logging.info('vw input written to %s, starting testing', f.name)
        args = f.name
        args += ' -r %s' % outf
        command = '{vw_binary} {args} -t -i {vw_modelfile}'.format(
            vw_binary=self.vw_binary, args=args,
            vw_modelfile=self.vw_modelfile)
        logging.info('vw command: %s', command)
        vw_start = time.time()
        c = envoy.run(command)
        logging.info("vw took %f secs." % (time.time() - vw_start))
        if c.status_code:
            logging.error(
                'something happened to vw, code: %d, out: %s, err: %s',
                c.status_code, c.std_out, c.std_err)
            raise IOError('Something happened to vw')
        else:
            logging.info(
                'vw ran sucessfully. out: %s, err: %s',
                c.std_out, c.std_err)
        all_probas = []
        with open(outf, 'r') as f:
            for line in f:
                probas = {}
                for word in line.split(' '):
                    tag, p = word.split(':')
                    probas[tag] = float(p)
                all_probas.append(probas)
        if self.use_temp_files:
            safe_unlink(f.name)
            safe_unlink(outf)
            if not self.iterative:
                safe_unlink(self.vw_modelfile)
        logging.info("Testing took %f secs." % (time.time() - start))
        return all_probas

    def top_k_tags(self, X, ntags):
        """ Given a list of multilabel tagsets and the number of predicted labels
            for each, returns predicted labels for each tagset
        input: list of multilabel tagsets, corresponding list containing the
               number of labels expected for each
        output: list of lists containing the predicted labels for each tagset
        """
        probas = self.predict_proba(X)
        result = []
        for ntag, proba in zip(ntags, probas):
            cur_top_k = []
            for i in range(ntag):
                if self.probability:
                    tag = min(proba.keys(), key=lambda key: proba[key])
                else:
                    tag = max(proba.keys(), key=lambda key: proba[key])
                proba.pop(tag)
                cur_top_k.append(self.reverse_labels[int(tag)])
            result.append(cur_top_k)
        return result

    def predict(self, X):
        """ Make label predictions for a list of tagsets
        input: list of tagsets
        output: list of predicted labels
        """
        start = time.time()
        if not self.trained:
            raise ValueError("Need to train the classifier first")
        if self.use_temp_files:
            f = tempfile.NamedTemporaryFile('w', delete=False)
            outfobj = tempfile.NamedTemporaryFile('w', delete=False)
            outf = outfobj.name
            outfobj.close()
        else:
            f = open('./pred_input-%s.txt' % self.suffix, 'w')
            outf = './pred_output-%s.txt' % self.suffix
        for tag in X:
            f.write('| {}\n'.format(' '.join(tag)))
        f.close()
        #logging.info('vw input written to %s, starting testing', f.name)
        command = '{vw_binary} {vw_input} -t -p {outf} -i {vw_modelfile}'.format(
            vw_binary=self.vw_binary, vw_input=repr(f.name), outf=repr(outf),
            vw_modelfile=repr(self.vw_modelfile))
        #logging.info('vw command: %s', command)
        vw_start = time.time()
        c = envoy.run(command)
        logging.info("vw took %f secs." % (time.time() - vw_start))
        if c.status_code:
            logging.error(
                'something happened to vw, code: %d, out: %s, err: %s',
                c.status_code, c.std_out, c.std_err)
            raise IOError('Something happened to vw', '-------', c.status_code, '-------', c.std_out, '--------',c.std_err)
        else:
            logging.info(
                'vw ran sucessfully. out: %s, err: %s',
                c.std_out, c.std_err)
        all_preds = []
        with open(outf, 'r') as f:
            for line in f:
                try:
                    all_preds.append(self.reverse_labels[int(line)])
                except KeyError:
                    logging.critical("Got label %s predicted!?", int(line))
                    all_preds.append('??')
        if self.use_temp_files:
            safe_unlink(f.name)
            if not self.iterative:
                safe_unlink(self.vw_modelfile)
        logging.info("Testing took %f secs." % (time.time() - start))
        return all_preds

    def _filter_multilabels(self, X, y):
        """Remove all multilabel tagsets from the X, y list"""
        new_X = []
        new_y = []
        for data, labels in zip(X, y):
            if isinstance(labels, list) and len(labels) == 1:
                new_X.append(data)
                new_y.append(labels[0])
            elif isinstance(labels, str):
                new_X.append(data)
                new_y.append(labels)
        return new_X, new_y

    def score(self, X, y):
        """ Returns the number of hits and misses for a given list of tagsets
        after first predicting the labels"""
        predictions = self.predict(X)
        logging.info('Getting scores')
        hits = misses = preds = 0
        for pred, label in zip(predictions, y):
            if int(self.indexed_labels[label]) == int(pred):
                hits += 1
            else:
                misses += 1
            preds += 1
        return {'preds': preds, 'hits': hits, 'misses': misses}

def safe_unlink(filename):
    """ Delete file path """
    try:
        os.unlink(filename)
    except (FileNotFoundError, OSError): # OSError raised if directory instead of file
                                         # exception is also raised if you attempt to remove a file that is in use
        pass
