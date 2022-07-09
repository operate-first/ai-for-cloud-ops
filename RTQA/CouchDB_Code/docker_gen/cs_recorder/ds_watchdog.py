# DeltaSherlock. See README.md for usage. See LICENSE for MIT/X11 license info.
"""
DeltaSherlock client watchdog module. Contains methods for analyzing the
filesystem and creating changesets.
"""
# pylint: disable=C0326, R0913
import time
from os import path
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from os import listdir
from os.path import dirname, basename, isfile, getsize
from itertools import chain
#from deltasherlock.common.changesets import Changeset


class ChangesetRecord(object):
    """
    Container for a filesystem change record
    :attribute filename: the full path to the file recorded
    :attribute mtime: the unix timestamp at which this event occurred
    :attribute neighbors: the "neighbors" of this file (ie. files that also
    exist in the same directory as this one)
    :attribute filesize: the size of the file in bytes
    """

    def __init__(self, filename: str, mtime: int, neighbors: list = None, filesize: int = None):
        self.filename = filename
        self.mtime = mtime
        self.neighbors = neighbors if neighbors is not None else []
        self.filesize = filesize
        return

    def filetree_sentence(self) -> list:
        """
        Return the sentence this record represents in the form of a list of
        words (filetree)
        """
        return list(filter(None, self.filename.split("/")))

    def neighbor_sentence(self) -> list:
        """
        Return the sentence this record represents in the form of a list of
        words (neighbor)
        """
        return [basename(self.filename)] + self.neighbors

    def find_neighbors(self):
        """
        Get all of the "neighbors" of this file (eg. files that also exist in
        the same directory) and save the results in the list
        """
        try:
            excluded_entries = [basename(self.filename), ".", ".."]
            parent = dirname(self.filename)
            files = [f for f in listdir(parent) if isfile(parent + '/' + f)]
            self.neighbors = list(set(files) - set(excluded_entries))
        except:
            raise IOError("Neighors could not be obtained")
        return

    def basename(self) -> str:
        """
        Returns the basename of the record's filename
        """
        return basename(self.filename)

    def __lt__(self, other):
        """
        Allows comparison by mtime
        """
        return self.mtime < other.mtime

    def __gt__(self, other):
        """
        Allows comparison by mtime
        """
        return self.mtime > other.mtime

    def __eq__(self, other):
        """
        Allows checking for total equality
        """
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return ("<" + self.filename + " at " + str(self.mtime) + ">")


class Changeset(object):
    """
    Represents all filesystem changes during a certain interval (between its
    open_time and close_time). It is helpful to think of a changeset as an
    audio CD-R: it is made to be "loaded" into a "recorder" (DeltaSherlockWatchdog),
    where it is "opened" for recording events, then "closed" (permanently)
    when recording has finished, and then is ususally immediately replaced by a
    fresh "blank" Changeset
    :attribute open_time: the unix timestamp when this changeset began recording
    events
    :attribute open: true if the changeset is currently being "written to",
    false otherwise. Note that you almost always have to close a changeset
    before you can doing anything useful with it. Always use .close() instead of
    changing this attribute directly
    :attribute close_time: the unix timestamp when this changeset stopped
    recording events
    :attribute creations: a list of ChangesetRecords representing files created
    during the recording interval
    :attribute modifications: a list of ChangesetRecords representing files
    modified during the recording interval
    :attribute deleted: a list of ChangesetRecords representing files deleted
    during the recording interval
    :attribute predicted_quantity: the quantity of events (ie an application
    installation) that probably occurred during the recording interval.
    Determined using histogram analysis upon .close()
    :attribute db_id: an optional identifier populated when a changeset is
    "unwrapped" from the database
    """

    def __init__(self, open_time: int):
        # Define the interval that the changeset covers
        # (or at least the start of it)
        self.open_time = open_time
        self.open = True
        self.close_time = -1

        self.creations = []
        self.modifications = []
        self.deletions = []

        self.labels = []

        self.predicted_quantity = -1
        self.db_id = None
        return

    def add_creation_record(self, filename: str, mtime: int):
        if not self.open:
            raise ValueError("Cannot modify closed Changeset")

        filesize = None
        try:
            filesize = getsize(filename)
        except:
            # file was probably deleted too quickly
            pass

        self.creations.append(ChangesetRecord(filename, mtime, filesize=filesize))
        return

    def add_modification_record(self, filename: str, mtime: int):
        if not self.open:
            raise ValueError("Cannot modify closed Changeset")

        filesize = None
        try:
            filesize = getsize(filename)
        except:
            # file was probably deleted too quickly
            pass

        self.modifications.append(ChangesetRecord(filename, mtime, filesize=filesize))
        return

    def add_deletion_record(self, filename: str, mtime: int):
        if not self.open:
            raise ValueError("Cannot modify closed Changeset")

        self.deletions.append(ChangesetRecord(filename, mtime))
        return

    def close(self, close_time: int):
        """
        Close changeset, indicating that no further changes should be recorded.
        Then balance the records lists so that temporary files that were created
        and deleted during the interval are not considered "created"
        :param close_time: the unix timestamp of when this changeset was closed
        """
        # First, balance and sort our records
        self.__balance()
        self.__sort()

        # Now that everything is balanced, find the neighbors of each changeset
        # record
        for record in chain(self.creations, self.modifications, self.deletions):
            try:
                record.find_neighbors()
            except IOError:
                # File or containing directory no longer exists
                # TODO Log this? Probably can't do much else about this
                pass

        # And finally, set the close markers
        self.close_time = close_time
        self.open = False

        # Run the quantity analysis
        self.predicted_quantity = self.__predict_quantity()
        return

    def get_filetree_sentences(self) -> list:
        """
        Produces a list of filetree sentences (which are just lists of words)
        corresponding to all changes within the set. Can only be called after
        changeset is closed
        :return: the list of filetree sentences
        """
        # Only usable once record is closed
        if self.open:
            raise ValueError("Cannot obtain sentences from an open changeset")

        sentences = []

        for record in self.creations:
            sentences.append(record.filetree_sentence())
        for record in self.modifications:
            sentences.append(record.filetree_sentence())
        for record in self.deletions:
            sentences.append(record.filetree_sentence())

        return sentences

    def get_neighbor_sentences(self) -> list:
        """
        Produces a list of neighbor sentences (which are just lists of words)
        corresponding to all changes within the set. Can only be called after
        changeset is closed
        :return: the list of neighbor sentences
        """
        # Only usable once record is closed
        if self.open:
            raise ValueError("Cannot obtain sentences from an open changeset")

        sentences = []

        for record in self.creations:
            sentences.append(record.neighbor_sentence())
        for record in self.modifications:
            sentences.append(record.neighbor_sentence())
        for record in self.deletions:
            sentences.append(record.neighbor_sentence())

        return sentences

    def get_basenames(self) -> list:
        """
        Returns a list of basenames of all files changed within the interval,
        duplicates removed. Can only be called after changeset is closed
        :return: the list of basenames
        """
        # Only usable once record is closed
        if self.open:
            raise ValueError("Cannot obtain basenames from an open changeset")

        basenames = []

        for record in self.creations:
            basenames.append(record.basename())
        for record in self.modifications:
            basenames.append(record.basename())
        for record in self.deletions:
            basenames.append(record.basename())

        return list(set(basenames))

    def add_label(self, label: str):
        """
        Labels will most likely be used to store tags for which apps
        :param label: the "name" of the event label (likely an application name)
        """
        self.labels.append(label)
        return

    def filter_to_unique(self, rules: dict, label_names: list=None):
        """
        Filter this changeset to only its unique files (according to rule-
        based method output). If label_names is provided, use that to determine
        which labels to include, otherwise just use the internal labels field.
        """

        # Allow user to specify alternate label names, just in case our internal
        # label field has been set to database IDs instead of real names
        if label_names is None:
            label_names = self.labels

        # Determine unique files for all labels
        unique_files = []
        for label in label_names:
            for rule_sublist in rules[label]:
                unique_files.append(rule_sublist[0][0][4:])

        # Do the actual filtering
        new_creations, new_modifications, new_deletions = [], [], []
        for record in self.creations:
            if record.filename in unique_files:
                new_creations.append(record)
        for record in self.modifications:
            if record.filename in unique_files:
                new_modifications.append(record)
        for record in self.deletions:
            if record.filename in unique_files:
                new_deletions.append(record)

        # Replace old lists
        self.creations = new_creations
        self.modifications = new_modifications
        self.deletions = new_deletions


    def __predict_quantity(self) -> int:
        """
        Uses histogram analysis to make an educated guess as to how many
        installations occured within this changeset. Only looks at file creations.
        Should only be called by close(). Value can be found in .predicted_quantity
        :returns: the predicted quantity of apps
        """
        if self.open:
            raise ValueError("Cannot predict quatity on an open changeset")

        if len(self.creations) == 0:
            # No creations, no prediction
            return 0

        # First, figure out the bounds of our histogram
        self.__sort()
        minimum = float(self.creations[0].mtime)
        maximum = float(self.creations[-1].mtime)
        interval = int(maximum - minimum) + 1

        # Then, try to create the empty histogram
        try:
            fileHistogram = [[] for i in range(0, interval, 1)]
        except OverflowError:
            print("Overly big histogram. Skipping...")
            return 1

        # Organize creations into the histogram
        for entry in self.creations:
            fileHistogram[int(entry.mtime - minimum)].append(entry)

        # Prep for analysis
        empty_count = 0
        clusters = 0
        flag = False
        lastFlag = False
        cluster_list = []
        timeHistogram = []

        # Analyze
        for index, histBin in enumerate(fileHistogram):
            numChanges = len(histBin)
            if numChanges > 2:
                flag = True
                empty_count = 0

            else:
                empty_count += 1
                if empty_count == 3:
                    flag = False

            if flag and not lastFlag:
                clusters += 1
                cluster_begin = index
            if lastFlag and not flag:
                cluster_end = index
                cluster_list.append((cluster_begin, cluster_end))

            lastFlag = flag
            timeHistogram.append(numChanges)

        # All done!
        #import ipdb; ipdb.set_trace()
        # return len(cluster_list)
        return clusters

    def __sort(self):
        """
        Sorts all internal records by mtime
        """
        self.creations = sorted(self.creations)
        self.modifications = sorted(self.modifications)
        self.deletions = sorted(self.deletions)
        return

    def __balance(self):
        """
        Create a proper "delta" by pruning all records lists of entries that
        were both created and deleted within the same changeset. Ususally only
        called by close()
        """
        self.creations = self.__filter_duplicates(self.creations)
        self.modifications = self.__filter_duplicates(self.modifications)
        self.deletions = self.__filter_duplicates(self.deletions)

    @classmethod
    def __filter_duplicates(cls, records: list) -> list:
        """
        Filters a list of changeset records for duplicates, only leaving the
        latest changes behind
        :param records: a list of ChangesetRecords to be filtered
        :return: the resulting filtered list
        """
        new_records = []

        for record in records:
            # First, scan the new list to ensure this does not already exist
            handled = False
            for new_record in new_records:
                if new_record.filename == record.filename and record > new_record:
                    new_records[new_records.index(new_record)] = record
                    handled = True
            if not handled:
                new_records.append(record)

        return new_records

    def __add__(self, other):
        """
        Enables "adding" (read: combining) of two closed changesets
        """
        if self.open or other.open:
            raise ArithmeticError("Cannot add open changesets")

        lowest_open_time = self.open_time if self.open_time < other.open_time else other.open_time
        highest_close_time = self.close_time if self.close_time > other.close_time else other.close_time

        sum_changeset = Changeset(lowest_open_time)
        sum_changeset.creations = sorted(self.creations + other.creations)
        sum_changeset.modifications = sorted(
            self.modifications + other.modifications)
        sum_changeset.deletions = sorted(self.deletions + other.deletions)
        sum_changeset.close(highest_close_time)

        return sum_changeset

    def __eq__(self, other):
        """
        Determine equality (ie all IMPORTANT fields are exactly the same)
        """
        return (self.open_time == other.open_time
                and self.open == other.open
                and self.close_time == other.close_time
                and self.creations == other.creations
                and self.modifications == other.modifications
                and self.deletions == other.deletions
                and self.labels == other.labels
                and self.predicted_quantity == other.predicted_quantity)

    def __repr__(self):
        return ("<" + ("Open" if self.open else "Closed") + " changeset from " +
                str(self.open_time) + " to " + str(self.close_time) + " with " +
                str(len(self.creations)) + " creations, " +
                str(len(self.modifications)) + " modifications, and " +
                str(len(self.deletions)) + " deletions.>")
##########################################################################


class DeltaSherlockEventHandler(PatternMatchingEventHandler):
    """
    Default handler for filesystem events. Called on each file creation,
    modification, deletion, and move.
    """

    def __init__(self, changeset, patterns=None, ignore_patterns=None,
                 ignore_directories=True, case_sensitive=False):
        super(DeltaSherlockEventHandler, self).__init__(
            ["*"], None, True, False)
        self.current_changeset = changeset

    def on_created(self, event):
        self.current_changeset.add_creation_record(event.src_path, time.time())

    def on_modified(self, event):
        self.current_changeset.add_modification_record(
            event.src_path, time.time())

    def on_deleted(self, event):
        self.current_changeset.add_deletion_record(event.src_path, time.time())

    def on_moved(self, event):
        # Treated as a deletion of the source and a creation of the destination
        self.current_changeset.add_deletion_record(event.src_path, time.time())
        self.current_changeset.add_creation_record(event.dest_path, time.time())

    def replace_changeset(self, new_changeset):
        """
        Swap out the current changeset being recorded to with a new changeset.
        :param new_changeset: the changeset to be "swapped in" to the watchdog
        :return: the old, closed changeset that you just replaced
        """
        if not new_changeset.open:
            raise ValueError("Cannot give a closed changeset to event handler")

        old_changeset = self.current_changeset
        self.current_changeset = new_changeset
        old_changeset.close(time.time())
        return old_changeset


class DeltaSherlockWatchdog(object):
    """
    Manages the watchdog that monitors the filesystem for changes
    """

    def __init__(self, paths: list, patterns: str = "*", ignore_patterns: str = None):
        """
        See http://pythonhosted.org/watchdog/api.html#watchdog.events.PatternMatchingEventHandler
        for explanation on the "patterns" parameters
        """
        # Create changeset infrastructure
        self.__changesets = []

        self.__observer = Observer()
        self.__handler = DeltaSherlockEventHandler(Changeset(time.time()),
                                                   patterns=patterns,
                                                   ignore_patterns=ignore_patterns,
                                                   ignore_directories=True,
                                                   case_sensitive=False)
        for p in paths:
            if path.isfile(p) or path.isdir(p):
                self.__observer.schedule(self.__handler, p, recursive=True)
            else:
                # Path does not exist.
                # TODO: throw warning?
                pass
        self.__observer.start()
        return

    def __del__(self):
        self.__observer.stop()
        # Block until thread has stopped
        self.__observer.join()
        return

    def mark(self) -> Changeset:
        """
        Close the current changeset being recorded to, open a new one, and
        return the former
        :return: the old, closed changeset that was just "ejected"
        """
        latest_changeset = self.__handler.replace_changeset(
            Changeset(time.time()))
        self.__changesets.append(latest_changeset)
        return latest_changeset

    def get_changeset(self, first_index: int, last_index: int = None) -> Changeset:
        """
        Returns the sum of all changesets between two indexes (inclusive of
        first, exclusive of last), or just the single changeset specified
        :param first_index: the index of the first changeset you'd like to
        include
        :param last_index: the index of the changeset AFTER the last changeset
        you'd like to include, or None if you only want the changeset specified
        by first_index
        :return: the sum of all changesets across the specified range
        """
        sum_changeset = self.__changesets[first_index]

        if last_index is not None:
            for changeset in self.__changesets[first_index + 1:last_index]:
                sum_changeset += changeset

        return sum_changeset
