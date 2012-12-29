# nvPY: cross-platform note-taking app with simplenote syncing
# copyright 2012 by Charl P. Botha <cpbotha@vxlabs.com>
# new BSD license

import codecs
import copy
import glob
import os
import json
import logging
from Queue import Queue, Empty
import re

from threading import Thread
import time
import utils

ACTION_SAVE = 0

class SyncError(RuntimeError):
    pass

class ReadError(RuntimeError):
    pass

class WriteError(RuntimeError):
    pass



class NotesDB(utils.SubjectMixin):
    """NotesDB will take care of the local notes database and syncing with SN.
    """

    def __init__(self, config):
        utils.SubjectMixin.__init__(self)
        
        self.config = config
        
        # create db dir if it does not exist
        if not os.path.exists(config.db_path):
            os.mkdir(config.db_path)
            
        self.db_path = config.db_path

        # create txt Notes dir if it does not exist
        if not os.path.exists(config.txt_path):
            os.mkdir(config.txt_path)

        self.initialize_on_disk_notes()# save and sync queue
        self.q_save = Queue()
        self.q_save_res = Queue()

        thread_save = Thread(target=self.worker_save)
        thread_save.setDaemon(True)
        thread_save.start()

        
    def create_note(self, title):
        # need to get a key unique to this database. not really important
        # what it is, as long as it's unique.
        new_key = utils.generate_random_key()
        while new_key in self.notes:
            new_key = utils.generate_random_key()
            
        timestamp = time.time()
            
        # note has no internal key yet.
        new_note = {
                    'content' : "",
                    'title': title,
                    'modifydate' : timestamp,
                    'createdate' : timestamp,
                    'savedate' : 0, # never been written to disc
                    'syncdate' : 0, # never been synced with server
                    'tags' : []
                    }
        
        self.notes[new_key] = new_note
        
        return new_key

    def initialize_on_disk_notes(self):
        now = time.time()
        # now read all .json files from disk
        fnlist = glob.glob(self.helper_key_to_fname('*'))
        txtlist = glob.glob(unicode(self.config.txt_path + '/*' + self.config.note_extension, 'utf-8'))
        txtlist += glob.glob(unicode(self.config.txt_path + '/*.mkdn', 'utf-8'))
        # removing json files and force full full sync if using text files
        # and none exists and json files are there
        if not txtlist and fnlist:
            logging.debug('Forcing resync: using text notes, first usage')
            for fn in fnlist:
                os.unlink(fn)
            fnlist = []
        self.notes = {}
        self.titlelist = {}

        for fn in fnlist:
            try:
                n = json.load(open(fn, 'rb'))
                nt = utils.get_note_title_file(n, self.config.note_extension)
                tfn = os.path.join(self.config.txt_path, nt)
                if os.path.isfile(tfn):
                    self.titlelist[n.get('key')] = nt
                    txtlist.remove(tfn)
                    if os.path.getmtime(tfn) > os.path.getmtime(fn):
                        logging.debug('Text note was changed: %s' % (fn,))
                        with codecs.open(tfn, mode='rb', encoding='utf-8') as f:
                            c = f.read()

                        n['content'] = c
                        n['modifydate'] = os.path.getmtime(tfn)
                else:
                    logging.debug('Deleting note : %s' % (fn,))
                    os.unlink(fn)
                    continue

            except IOError, e:
                logging.error('NotesDB_init: Error opening %s: %s' % (fn, str(e)))
                raise ReadError('Error opening note file')

            except ValueError, e:
                logging.error('NotesDB_init: Error reading %s: %s' % (fn, str(e)))
                raise ReadError('Error reading note file')

            else:
                # we always have a localkey, also when we don't have a note['key'] yet (no sync)
                localkey = os.path.splitext(os.path.basename(fn))[0]
                self.notes[localkey] = n
                # we maintain in memory a timestamp of the last save
                # these notes have just been read, so at this moment
                # they're in sync with the disc.
                n['savedate'] = now

        for fn in txtlist:
            logging.debug('New text note found : %s' % (fn), )
            tfn = os.path.join(self.config.txt_path, fn)
            try:
                with codecs.open(tfn, mode='rb', encoding='utf-8') as f:
                    c = f.read()

            except IOError, e:
                logging.error('NotesDB_init: Error opening %s: %s' % (fn, str(e)))
                raise ReadError('Error opening note file')

            except ValueError, e:
                logging.error('NotesDB_init: Error reading %s: %s' % (fn, str(e)))
                raise ReadError('Error reading note file')

            else:
                nn = os.path.splitext(os.path.basename(fn))[0]
                nk = self.create_note(nn)
                self.notes[nk]['content'] = c
                #if nn != utils.get_note_title(self.notes[nk]):
                #    logging.debug('nn: %s, title: %s' % (nn, utils.get_note_title(self.notes[nk])))
                #    logging.debug('tfn: %s' % (tfn))
                #    #self.notes[nk]['content'] = nn + "\n\n" + c
                #    self.notes[nk]['content'] = c

                # os.unlink(tfn)


    def delete_note(self, key):
        n = self.notes[key]
        n['deleted'] = 1
        n['modifydate'] = time.time()


    def filter_notes(self, search_string=None):
        """Return list of notes filtered with search string.

        Based on the search mode that has been selected in self.config,
        this method will call the appropriate helper method to do the
        actual work of filtering the notes.

        @param search_string: String that will be used for searching.
         Different meaning depending on the search mode.
        @return: notes filtered with selected search mode and sorted according
        to configuration. Two more elements in tuple: a regular expression
        that can be used for highlighting strings in the text widget; the
        total number of notes in memory.
        """

        if self.config.search_mode == 'regexp':
            filtered_notes, match_regexp, active_notes = self.filter_notes_regexp(search_string)
        elif self.config.search_mode == 'gstyle':
            filtered_notes, match_regexp, active_notes = self.filter_notes_gstyle(search_string)
        else:
            filtered_notes, match_regexp, active_notes = self.filter_notes_find(search_string)

        if self.config.sort_mode == 0:
            if self.config.pinned_ontop == 0:
                # sort alphabetically on title
                filtered_notes.sort(key=lambda o: utils.get_note_title(o.note))
            else:
                filtered_notes.sort(utils.sort_by_title_pinned)

        else:
            if self.config.pinned_ontop == 0:
                # last modified on top
                filtered_notes.sort(key=lambda o: -float(o.note.get('modifydate', 0)))
            else:
                filtered_notes.sort(utils.sort_by_modify_date_pinned, reverse=True)

        return filtered_notes, match_regexp, active_notes


    def _helper_gstyle_tagmatch(self, tag_pats, note):
        if tag_pats:
            tags = note.get('tags')

            # tag: patterns specified, but note has no tags, so no match
            if not tags:
                return 0

            # for each tag_pat, we have to find a matching tag
            for tp in tag_pats:
                # at the first match between tp and a tag:
                if next((tag for tag in tags if tag.startswith(tp)), None) is not None:
                    # we found a tag that matches current tagpat, so we move to the next tagpat
                    continue

                else:
                    # we found no tag that matches current tagpat, so we break out of for loop
                    break

            else:
                # for loop never broke out due to no match for tagpat, so:
                # all tag_pats could be matched, so note is a go.
                return 1


            # break out of for loop will have us end up here
            # for one of the tag_pats we found no matching tag
            return 0


        else:
            # match because no tag: patterns were specified
            return 2


    def _helper_gstyle_mswordmatch(self, msword_pats, content):
        """If all words / multi-words in msword_pats are found in the content,
        the note goes through, otherwise not.

        @param msword_pats:
        @param content:
        @return:
        """

        # no search patterns, so note goes through
        if not msword_pats:
            return True

        # search for the first p that does NOT occur in content
        if next((p for p in msword_pats if p not in content), None) is None:
            # we only found pats that DO occur in content so note goes through
            return True

        else:
            # we found the first p that does not occur in content
            return False



    def filter_notes_gstyle(self, search_string=None):

        filtered_notes = []
        # total number of notes, excluding deleted
        active_notes = 0

        if not search_string:
            for k in self.notes:
                n = self.notes[k]
                if not n.get('deleted'):
                    active_notes += 1
                    filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=0))

            return filtered_notes, [], active_notes

        # group0: ag - not used
        # group1: t(ag)?:([^\s]+)
        # group2: multiple words in quotes
        # group3: single words
        # example result for 't:tag1 t:tag2 word1 "word2 word3" tag:tag3' ==
        # [('', 'tag1', '', ''), ('', 'tag2', '', ''), ('', '', '', 'word1'), ('', '', 'word2 word3', ''), ('ag', 'tag3', '', '')]

        groups = re.findall('t(ag)?:([^\s]+)|"([^"]+)"|([^\s]+)', search_string)
        tms_pats = [[] for _ in range(3)]

        # we end up with [[tag_pats],[multi_word_pats],[single_word_pats]]
        for gi in groups:
            for mi in range(1,4):
                if gi[mi]:
                    tms_pats[mi-1].append(gi[mi])

        logging.debug("===== starting new search %s =====", (search_string))

        for k in self.notes:
            n = self.notes[k]
            logging.debug("searching note %s", (n.get('title')))

            if not n.get('deleted'):
                active_notes += 1
                c = n.get('content') + ' ' + n.get('title')

                # case insensitive mode: WARNING - SLOW!
                if not self.config.case_sensitive and c:
                    c = c.lower()

                tagmatch = self._helper_gstyle_tagmatch(tms_pats[0], n)
                # case insensitive mode: WARNING - SLOW!
                msword_pats = tms_pats[1] + tms_pats[2] if self.config.case_sensitive else [p.lower() for p in tms_pats[1] + tms_pats[2]]
                if tagmatch and self._helper_gstyle_mswordmatch(msword_pats, c):
                    # we have a note that can go through!

                    # tagmatch == 1 if a tag was specced and found
                    # tagmatch == 2 if no tag was specced (so all notes go through)
                    tagfound = 1 if tagmatch == 1 else 0
                    # we have to store our local key also
                    filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=tagfound))

        return filtered_notes, '|'.join(tms_pats[1] + tms_pats[2]), active_notes


    def filter_notes_regexp(self, search_string=None):
        """Return list of notes filtered with search_string, 
        a regular expression, each a tuple with (local_key, note). 
        """

        if search_string:
            try:
                if self.config.case_sensitive == 0:
                    sspat = re.compile(search_string, re.I)
                else:
                    sspat = re.compile(search_string)
            except re.error:
                sspat = None
            
        else:
            sspat = None

        filtered_notes = []
        # total number of notes, excluding deleted ones
        active_notes = 0
        for k in self.notes:
            n = self.notes[k]
            # we don't do anything with deleted notes (yet)
            if n.get('deleted'):
                continue

            active_notes += 1

            c = n.get('content') + ' ' + n.get('title')
            if self.config.search_tags == 1:
                t = n.get('tags')
                if sspat:
                    # this used to use a filter(), but that would by definition
                    # test all elements, whereas we can stop when the first
                    # matching element is found
                    # now I'm using this awesome trick by Alex Martelli on
                    # http://stackoverflow.com/a/2748753/532513
                    # first parameter of next is a generator
                    # next() executes one step, but due to the if, this will
                    # either be first matching element or None (second param)
                    if t and next((ti for ti in t if sspat.search(ti)), None) is not None:
                        # we have to store our local key also
                        filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=1))

                    elif sspat.search(c):
                        # we have to store our local key also
                        filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=0))

                else:
                    # we have to store our local key also
                    filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=0))
            else:
                if (not sspat or sspat.search(c)):
                    # we have to store our local key also
                    filtered_notes.append(utils.KeyValueObject(key=k, note=n, tagfound=0))

        match_regexp = search_string if sspat else ''

        return filtered_notes, match_regexp, active_notes

    def filter_notes_find(self, search_string):
        """
        filters out notes using str.find
        @param search_string:
        @return:
        """
        filtered_notes = []
        active_notes = 0
        print("searching: %d" % (len(self.notes.values())))
        for note_key in self.notes:
            note = self.notes[note_key]
            if note.get('deleted'):
                continue

            active_notes += 1

            #
            # Skip searching tags for now
            #
            content_to_search = note.get('content') + ' ' + note.get('title')
            if not search_string:
                filtered_notes.append(utils.KeyValueObject(key = note_key, note = note, tagfound = 0))
            elif content_to_search.find(search_string) != -1:
                filtered_notes.append(utils.KeyValueObject(key = note_key, note = note, tagfound = 0))

        return filtered_notes, '', active_notes


    def get_note(self, key):
        return self.notes[key]


    def get_note_content(self, key):
        return self.notes[key].get('content')

    
    def get_note_status(self, key):
        n = self.notes[key]
        o = utils.KeyValueObject(saved=False, synced=False, modified=False)
        modifydate = float(n['modifydate'])
        savedate = float(n['savedate'])
        
        if savedate > modifydate:
            o.saved = True
        else:
            o.modified = True
            
        if float(n['syncdate']) > modifydate:
            o.synced = True
            
        return o


    def get_save_queue_len(self):
        return self.q_save.qsize()

        
    def helper_key_to_fname(self, k):
            return os.path.join(self.db_path, k) + '.json'

    
    def helper_save_note(self, k, note):
        """Save a single note to disc.
        
        """

        t = utils.get_note_title_file(note, self.config.note_extension)
        if t and not note.get('deleted'):
            if k in self.titlelist:
                logging.debug('Writing note : %s %s' % (t,self.titlelist[k] ))
                if self.titlelist[k] != t:
                    dfn = os.path.join(self.config.txt_path, self.titlelist[k])
                    if os.path.isfile(dfn):
                        logging.debug('Delete file %s ' % (dfn, ))
                        os.unlink(dfn)
                    else:
                        logging.debug('File not exits %s ' % (dfn, ))
            else:
                logging.debug('Key not in list %s ' % (k, ))

            self.titlelist[k] = t
            fn = os.path.join(self.config.txt_path, t)
            try:
                with codecs.open(fn, mode='wb', encoding='utf-8') as f:
                    c = note.get('content')
                    if isinstance(c, str):
                        c = unicode(c, 'utf-8')
                    else:
                        c = unicode(c)

                    f.write(c)
            except IOError, e:
                logging.error('NotesDB_save: Error opening %s: %s' % (fn, str(e)))
                raise WriteError ('Error opening note file')

            except ValueError, e:
                logging.error('NotesDB_save: Error writing %s: %s' % (fn, str(e)))
                raise WriteError ('Error writing note file')

        elif t and note.get('deleted') and k in self.titlelist:
            dfn = os.path.join(self.config.txt_path, self.titlelist[k])
            if os.path.isfile(dfn):
                logging.debug('Delete file %s ' % (dfn, ))
                os.unlink(dfn)
        
        fn = self.helper_key_to_fname(k)
        if note.get('deleted'):
            if os.path.isfile(fn):
                os.unlink(fn)
        else:
            json.dump(note, open(fn, 'wb'), indent=2)

        # record that we saved this to disc.
        note['savedate'] = time.time()

        
    def sync_note_unthreaded(self, k):
        """Sync a single note with the on disk view.

        The note on disk may have changed (for example edited outside of nvxp). Here we
        sync up its on disk state with our in memory one.
        """

        note = self.notes[k]

        tfn = self.get_note_filepath(k)
        with codecs.open(tfn, mode='rb', encoding='utf-8') as f:
            content = f.read()
            n = note
            n['content'] = content
            n['modifydate'] = os.path.getmtime(tfn)
        note.update(n)
        return (k, True)

        
    def save_threaded(self):
        for k,n in self.notes.items():
            savedate = float(n.get('savedate'))
            if float(n.get('modifydate')) > savedate or \
               float(n.get('syncdate')) > savedate:
                cn = copy.deepcopy(n)
                # put it on my queue as a save
                o = utils.KeyValueObject(action=ACTION_SAVE, key=k, note=cn)
                self.q_save.put(o)
                
        # in this same call, we process stuff that might have been put on the result queue
        nsaved = 0
        something_in_queue = True
        while something_in_queue:
            try:
                o = self.q_save_res.get_nowait()
                
            except Empty:
                something_in_queue = False
                
            else:
                # o (.action, .key, .note) is something that was written to disk
                # we only record the savedate.
                self.notes[o.key]['savedate'] = o.note['savedate']
                self.notify_observers('change:note-status', utils.KeyValueObject(what='savedate',key=o.key))
                nsaved += 1
                
        return nsaved


    def sync_local_changes(self):
        logging.debug("in sync_local_changes")
        self.initialize_on_disk_notes()

    
    def sync_full(self):
        """
            Check file system and resync our in memory view
        """
        self.sync_local_changes()


    def get_note_filepath(self, note_key):
        filename = os.path.join(self.config.txt_path, utils.get_note_title_file(self.notes[note_key], self.config.note_extension))
        return filename

        
    def set_note_content(self, key, content):
        n = self.notes[key]
        old_content = n.get('content')
        if content != old_content:
            n['content'] = content
            n['modifydate'] = time.time()
            self.notify_observers('change:note-status', utils.KeyValueObject(what='modifydate', key=key))


    def set_note_tags(self, key, tags):
        n = self.notes[key]
        old_tags = n.get('tags')
        tags = utils.sanitise_tags(tags)
        if tags != old_tags:
            n['tags'] = tags
            n['modifydate'] = time.time()
            self.notify_observers('change:note-status', utils.KeyValueObject(what='modifydate', key=key))


    def set_note_pinned(self, key, pinned):
        n = self.notes[key]
        old_pinned = utils.note_pinned(n)
        if pinned != old_pinned:
            if 'systemtags' not in n:
                n['systemtags'] = []

            systemtags = n['systemtags']

            if pinned:
                # which by definition means that it was NOT pinned
                systemtags.append('pinned')

            else:
                systemtags.remove('pinned')

            n['modifydate'] = time.time()
            self.notify_observers('change:note-status', utils.KeyValueObject(what='modifydate', key=key))


    def worker_save(self):
        while True:
            o = self.q_save.get()

            if o.action == ACTION_SAVE:
                # this will write the savedate into o.note
                # with filename o.key.json
                try:
                    self.helper_save_note(o.key, o.note)

                except WriteError, e:
                    logging.error('FATAL ERROR in access to file system')
                    print "FATAL ERROR: Check the nvpy.log"
                    os._exit(1) 

                else:
                    # put the whole thing back into the result q
                    # now we don't have to copy, because this thread
                    # is never going to use o again.
                    # somebody has to read out the queue...
                    self.q_save_res.put(o)
