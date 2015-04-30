__author__ = 'roz016'

from index import Index
import math


class EraInterimIndex(Index):

    source = 'ERA_INTERIM'
    abs_path = "/g/data/v27/proto_datacube/ERA_INTERIM/"

    __class_description__ = """Class for indexing ERA INTERIM files"""
    __version__ = 0.1

    def __init__(self):

        super(EraInterimIndex, self).__init__()

    def get_files(self, prod, t1, t2, x1, x2, y1, y2):

        files = []

        files.append(self.abs_path + "TP_25-31_147-152_1985-2015.nc4")

        return files
