#!/usr/bin/env python

import numpy
import pandas
import h5py

from osgeo import gdal
from osgeo import osr

class TesseraDatasets(object):

    """
    A class object designed for reading data from a h5py file containing
    agdc structured data.
    """

    def __init__(self, filename):
        """
        Initialise the class structure.
        
        :param filename:
            A string containing the full filepath of a agdc structured
            hdf5 file.
        """
        self.fname = filename
        self.container = h5py.File(filename, 'r')

        self.metadata = self.container['metadata']['Timestamp']
        tmp_ = self.metadata[:].astype('datetime64[ps]')
        self.time_slices = tmp_.shape[0]
        self.timestamps = pandas.DataFrame({'idx': range(self.time_slices)},
                                           index=tmp_)
        self.projection = self.metadata.attrs['projection']
        self.geotransform = tuple(self.metadata.attrs['geotransform'])
        self.lines = self.metadata.attrs['lines']
        self.samples = self.metadata.attrs['samples']
        self.dsets = {}
        tmp_ = self.container['data']
        for key in self.container['data'].keys():
            self.dsets[key] = tmp_[key]

    # def get_dataset_data(self, dataset, index):
    #    if dataset not in self.dsets.keys():
    #         msg = "{} not in available datasets.".format(dataset)
    #         raise IndexError(msg)
