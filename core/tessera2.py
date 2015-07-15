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

        # Basic metadata info (timestamps for now)
        self.metadata = self.container['metadata']['timestamps']
        tmp_ = self.metadata[:].astype('datetime64[ns]')
        self.time_slices = tmp_.shape[0]
        self.timestamps = pandas.DataFrame({'idx': range(self.time_slices)},
                                           index=tmp_)

        # Setup the CRS/SRS/Projection (for now just keep GDAL like
        # 'projection' call. More recent libs use crs
        self.projection = self.metadata.attrs['projection']
        self.crs_wkt = self.metadata.attrs['projection']
        crs = osr.SpatialReference()
        crs.ImportFromWkt(self.metadata.attrs['projection'])
        self.crs = crs.ExportToProj4()
        
        # Setup the image tie point (just mimic the GDAL named 'geotransform'
        self.geotransform = tuple(self.metadata.attrs['geotransform'])

        # Array dimensions y (lines/height), x (samples/width)
        self.lines = self.metadata.attrs['lines']
        self.samples = self.metadata.attrs['samples']

        # Setup the datasets
        self.dsets = {}
        tmp_ = self.container['data']
        for key in self.container['data'].keys():
            self.dsets[key] = tmp_[key]
