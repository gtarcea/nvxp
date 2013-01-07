
import time
import re
import logging
import json


class Note:

    def __init__(self, title, content=u'', deleted=False, tags=[], savedate=0, createdate=-1, modifydate=-1, key=u''):
        self.title = title
        self.content = content
        self.deleted = deleted
        self.tags = tags
        self.savedate = savedate
        if createdate == -1:
            self.createdate = time.time()
        else:
            self.createdate = createdate
        if modifydate == -1:
            self.modifydate = time.time()
        else:
            self.modifydate = modifydate
        self.key = key

    def match_gstyle(self, search_string=None):
        if self.deleted:
            return False
        elif not search_string:
            return True
        else:
            # group0: ag - not used
            # group1: t(ag)?:([^\s]+)
            # group2: multiple words in quotes
            # group3: single words
            # example result for 't:tag1 t:tag2 word1 "word2 word3" tag:tag3' ==
            # [('', 'tag1', '', ''), ('', 'tag2', '', ''), ('', '', '', 'word1'), ('', '', 'word2 word3', ''), ('ag', 'tag3', '', '')]

            groups = re.findall(
                't(ag)?:([^\s]+)|"([^"]+)"|([^\s]+)', search_string)
            tms_pats = [[] for _ in range(3)]

            # we end up with [[tag_pats],[multi_word_pats],[single_word_pats]]
            for gi in groups:
                for mi in range(1, 4):
                    if gi[mi]:
                        tms_pats[mi - 1].append(gi[mi])

            logging.debug(
                "===== starting new search %s =====", (search_string))
            content = self.title + ' ' + self.content

            # case insensitive mode: WARNING - SLOW!
            if not self.config.case_sensitive and content:
                content = content.lower()

            #tagmatch = self._helper_gstyle_tagmatch(tms_pats[0], note)
            tagmatch = False

            # case insensitive mode: WARNING - SLOW!
            msword_pats = tms_pats[1] + tms_pats[2] if self.config.case_sensitive else [p.lower() for p in tms_pats[1] + tms_pats[2]]
            if tagmatch and self._helper_gstyle_mswordmatch(msword_pats, content):
                return True

        return False

    def match_regexp(self, search_string=None):
        """Return list of notes filtered with search_string,
        a regular expression, each a tuple with (local_key, note).
        """

        return False

        # if search_string:
        #     try:
        #         if self.config.case_sensitive == 0:
        #             sspat = re.compile(search_string, re.I)
        #         else:
        #             sspat = re.compile(search_string)
        #     except re.error:
        #         sspat = None

        # else:
        #     sspat = None

        # filtered_notes = []
        # # total number of notes, excluding deleted ones
        # active_notes = 0
        # for k in self.notes:
        #     notes = self.notes[k]
        #     # we don't do anything with deleted notes (yet)
        #     if notes.get('deleted'):
        #         continue

        #     active_notes += 1

        #     content = notes.get('content') + ' ' + notes.get('title')
        #     if self.config.search_tags == 1:
        #         tags = notes.get('tags')
        #         if sspat:
        #             # this used to use a filter(), but that would by definition
        #             # test all elements, whereas we can stop when the first
        #             # matching element is found
        #             # now I'm using this awesome trick by Alex Martelli on
        #             # http://stackoverflow.com/a/2748753/532513
        #             # first parameter of next is a generator
        #             # next() executes one step, but due to the if, this will
        #             # either be first matching element or None (second param)
        #             if tags and next((ti for ti in tags if sspat.search(ti)), None) is not None:
        #                 # we have to store our local key also
        # filtered_notes.append(utils.KeyValueObject(key=k, note=notes,
        # tagfound=1))

        #             elif sspat.search(content):
        #                 # we have to store our local key also
        # filtered_notes.append(utils.KeyValueObject(key=k, note=notes,
        # tagfound=0))

        #         else:
        #             # we have to store our local key also
        #             filtered_notes.append(utils.KeyValueObject(key=k, note=notes, tagfound=0))
        #     else:
        #         if (not sspat or sspat.search(content)):
        #             # we have to store our local key also
        # filtered_notes.append(utils.KeyValueObject(key=k, note=notes,
        # tagfound=0))

        # match_regexp = search_string if sspat else ''

        # return filtered_notes, match_regexp, active_notes

    def match_find(self, search_string):
        """
        filters out notes using str.find
        @param search_string:
        @return:
        """

        if self.deleted:
            return False
        elif not search_string:
            return True

        content_to_search = self.title + ' ' + self.content

        if content_to_search.find(search_string) != -1:
            return True
        else:
            return False


def _serialize_note_2_json(note):
    d = {
        '__class__': note.__class__.__name__,
        '__module__': note.__module__
    }
    note_dictionary_no_content_field = {key: value for (key, value) in note.__dict__.items() if key != 'content'}
    d.update(note_dictionary_no_content_field)
    return d


def note_2_json(note):
    return json.dumps(note, default=_serialize_note_2_json)


def note_2_jsonfile(note, filename):
    with open(filename, 'wb') as fp:
        return json.dump(note, fp, default=_serialize_note_2_json)


def _dict_to_note_object(d):
    if '__class__' in d:
        d.pop('__class__')
        d.pop('__module__')
        #module = __import__(module_name)
        #class_ = getattr(module, class_name)
        kwargs = dict((key.encode('ascii'), value) for key, value in d.items())
        inst = Note(**kwargs)
    else:
        inst = d
    return inst


def json_2_note(json_):
    return json.loads(json_, object_hook=_dict_to_note_object)


def jsonfile_2_note(filename):
    with open(filename, 'rb') as fp:
        return json.load(fp, object_hook=_dict_to_note_object)
