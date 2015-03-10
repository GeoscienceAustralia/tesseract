__author__ = 'roz016'

from indexes import *
from indexes.index import Index

def IndexFactory(source):
    for cls in Index.__subclasses__():
        if cls.is_index_for(source):
            return cls()

    print("{} source not found".format(source))
    #raise ValueError

def IndexEnumerator():
    sources = {}
    for cls in Index.__subclasses__():
        if cls.source is not None:
            sources[cls.source] = cls
    return sources