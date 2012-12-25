__author__ = 'gtarcea'

import os.path
import os
import codecs
from whoosh import index
from whoosh.fields import Schema, ID, TEXT

def clean_index(path):
    # Always create the index from scratch
    ix = index.create_in(path + "/index", schema=get_schema())
    writer = ix.writer()

    # Assume we have a function that gathers the filenames of the
    # documents to be indexed
    fileList = os.listdir(path)
    for filename in fileList:
        fname, fextension = os.path.splitext(filename)
        if fextension == ".txt":
            print("Indexing: " + filename + "\n")
            add_doc(writer, path + "/" + filename)

    writer.commit()

def get_schema():
    return Schema(path=ID(unique=True, stored=True), content=TEXT)


def add_doc(writer, path):
    fileobj = codecs.open(path, "rb", "UTF-8")
    content=fileobj.read()
    fileobj.close()
    writer.add_document(path=unicode(path), content=content)

if __name__ == "__main__":
    clean_index("/Users/gtarcea/NotesTest")

