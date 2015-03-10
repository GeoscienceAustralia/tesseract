__author__ = 'roz016'

from index import Index
import math


class LS7Index(Index):

    source = 'LS7'
    abs_path = "/g/data/rs0/tiles/EPSG4326_1deg_0.00025pixel_netcdf/HPCData/LS7/"
    
    __class_description__ = """Class for extracting crop biomass of a plot"""
    __version__ = 0.1
    
    def __init__(self):
    
        super(LS7Index, self).__init__()
    
    def get_files(self, prod, t1, t2, x1, x2, y1, y2):
    
        files = []
    
        for year in range(t1.year, t2.year+1):
            for x in range(int(math.floor(x1)), int(math.floor(x2))+1):
                for y in range(int(math.floor(y1)), int(math.floor(y2))+1):
                    files.append(self.abs_path + "LS7_ETM_{0}_{1}_{2:04d}_{3}.h5".format(prod, x, y, year))
    
        return files