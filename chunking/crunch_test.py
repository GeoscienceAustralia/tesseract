#!/usr/bin/env python

from datetime import datetime as dt
import os
from os.path import exists as pexists

import numpy
import rasterio
import h5py

from eotools.tiling import generate_tiles
from idl_functions import randomu


def create_files(dims):
    """
    We'll create float64 data, this should test speeds
    of read/write capabilities much better than uint8.
    """
    bands, lines, samples = dims

    # Setup the rasterio keyword arguments
    # if we want pixel interleave or bip/bil (if using envi format)
    # we probably would need a 3D array to write as opposed to sequentially
    # appending a 2D array.
    # The deflate compression seems to work better than lzw.
    kwargs = {'count': bands,
              'width': samples,
              'height': lines,
              'dtype': 'float64',
              'driver': 'GTiff',
              'compress': 'deflate',
              'bigtiff': 'yes',
              'interleave': 'band'}
              #'blockxsize': 64,
              #'blockysize': 64}

    # Initialise output files
    r_ds = rasterio.open('bsq.tif', 'w', **kwargs)
    fid = h5py.File('bsq_gzip_lzw.h5', 'w')

    lzf_ds = fid.create_dataset('lzf', dims, dtype='float64',
                                chunks=(16, 64, 64), compression='lzf')
    gzip_ds = fid.create_dataset('gzip', dims, dtype='float64',
                                 chunks=(16, 64, 64), compression='gzip')


    # Define a zero time delta
    tm_zero = dt.now()
    tm_zero = tm_zero - tm_zero
    rio_time = tm_zero
    lzf_time = tm_zero
    gzip_time = tm_zero

    # Yes this could be sped up if we write severl bands at once
    # but we are simulating an appending situation
    for i in range(bands):
        # randomu specifies [x, y, z, ...] as dims
        img, seed = randomu(None, [samples, lines], double=True, gamma=True)

        st = dt.now()
        r_ds.write_band(i + 1, img)
        et = dt.now()
        rio_time += (et - st)

        st = dt.now()
        lzf_ds[i, :, :] = img
        et = dt.now()
        lzf_time += (et - st)

        st = dt.now()
        gzip_ds[i, :, :] = img
        et = dt.now()
        gzip_time += (et - st)

    r_ds.close()
    fid.close()

    print 'rasterio creation time taken: {}'.format(rio_time)
    print 'h5 lzf creation time taken: {}'.format(lzf_time)
    print 'h5 gzip creation time taken: {}'.format(gzip_time)


def test_rasterio(fname):
    """
    This will operate in blocks of (1, 4000), slightly less
    than in the pure spatial sense for the h5 examples, and
    a lot less than when incorporating the z-axis that hdf5 is
    chunked over.

    The interleave is band therefore z-axis will be much slower.
    """
    st = dt.now()
    with rasterio.open(fname, 'r') as ds:
        nbands = ds.count
        lines = ds.height
        samples = ds.width
        xbar = numpy.zeros((nbands, 1, 1))

        for i in range(nbands):
            xbar[i] = (ds.read_band(i+1, masked=False)).mean()

        tiles = generate_tiles(samples, lines, samples, 1)

        bands = range(1, nbands + 1)

        for tile in tiles:
            data = ds.read(bands, window=tile)
            res = numpy.log(data) * numpy.sqrt(data) - xbar

    et = dt.now()

    time_taken = et - st

    return time_taken


def test_h5(fname, dsname):
    """
    This will operate in blocks of (64, 64) which is 4096
    elements, which is larger than what the tiff will operate in.
    Also this format is retrieving z-axis blocks as well, therefore
    more data in memory and should be faster.
    """
    st = dt.now()
    with h5py.File(fname, 'r') as fid:
        ds = fid[dsname]
        nbands, lines, samples = ds.shape
        xbar = numpy.zeros((nbands, 1, 1))

        for i in range(nbands):
            xbar[i] = ds[i].mean()

        tiles = generate_tiles(samples, lines, 64, 64)

        bands = range(nbands)

        for tile in tiles:
            ys, ye = tile[0]
            xs, xe = tile[1]
            data = ds[bands, ys:ye, xs:xe]
            res = numpy.log(data) * numpy.sqrt(data) - xbar

    et = dt.now()

    time_taken = et - st

    return time_taken


if __name__ == '__main__':

    # Remove if we have run before
    if pexists('bsq.tif'):
        os.remove('bsq.tif')
    if pexists('bsq_gzip_lzw.h5'):
        os.remove('bsq_gzip_lzw.h5')

    dims = (90, 4000, 4000)

    print "Creating files"
    create_files(dims)

    print "Running tests"
    time_taken = test_rasterio('bsq.tif')
    print "rasterio time taken: {}".format(time_taken)

    time_taken = test_h5('bsq_gzip_lzw.h5', 'lzf')
    print "h5-lzf time taken: {}".format(time_taken)

    time_taken = test_h5('bsq_gzip_lzw.h5', 'gzip')
    print "h5-gzip time taken: {}".format(time_taken)
