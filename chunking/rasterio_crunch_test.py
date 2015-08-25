#!/usr/bin/env python

import argparse
from datetime import datetime as dt
import os
from os.path import exists as pexists

import numpy
import rasterio

from eotools.tiling import generate_tiles
from idl_functions import randomu


def create_sequential(dims):
    """
    Create 2 band sequential tif files, compressed using the
    deflate and lzw algorithms.
    The creation is performed sequentially to simulate many current
    processes such as WOfS where each y by x array is analysed and
    created independently.
    We'll create float64 data, this should test speeds
    of read/write capabilities much better than uint8.
    """
    bands, lines, samples = dims

    # Setup the rasterio keyword arguments
    # if we want pixel interleave or bip/bil (if using envi format)
    # we probably would need a 3D array to write as opposed to sequentially
    # appending a 2D array.
    gzip_kwargs = {'count': bands,
                   'width': samples,
                   'height': lines,
                   'dtype': 'float64',
                   'driver': 'GTiff',
                   'compress': 'deflate',
                   'bigtiff': 'yes',
                   'interleave': 'band'}
                   #'blockxsize': 64,
                   #'blockysize': 64}

    lzw_kwargs = {'count': bands,
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
    gzip_ds = rasterio.open('deflate.tif', 'w', **gzip_kwargs)
    lzw_ds = rasterio.open('lzw.tif', 'w', **lzw_kwargs)

    # Define a zero time delta
    tm_zero = dt.now()
    tm_zero = tm_zero - tm_zero
    gzip_time = tm_zero
    lzw_time = tm_zero

    # Yes this could be sped up if we write severl bands at once
    # but we are simulating an appending situation
    for i in range(bands):
        # randomu specifies [x, y, z, ...] as dims
        img, seed = randomu(None, [samples, lines], double=True, gamma=True)

        st = dt.now()
        gzip_ds.write_band(i + 1, img)
        et = dt.now()
        gzip_time += (et - st)

        st = dt.now()
        lzw_ds.write_band(i + 1, img)
        et = dt.now()
        lzw_time += (et - st)

    gzip_ds.close()
    lzw_ds.close()

    print 'rasterio deflate creation time taken: {}'.format(gzip_time)
    print 'rasterio lzw creation time taken: {}'.format(lzw_time)


def create_block(dims):
    """
    Create 2 band sequential tif files, compressed using the
    deflate and lzw algorithms.
    The creation is preformed with all z-axis data available for
    the given (z, y, x) array. This is to simulate a time-series
    workflow that can output a (z, y, x) array where most if not
    all the z-axis data is available.
    The datatype of the output array is float64 which should give
    the I/O mechanism a good workout.
    """
    bands, lines, samples = dims

    # Setup the rasterio keyword arguments
    # if we want pixel interleave or bip/bil (if using envi format)
    # we probably would need a 3D array to write as opposed to sequentially
    # appending a 2D array.
    gzip_kwargs = {'count': bands,
                   'width': samples,
                   'height': lines,
                   'dtype': 'float64',
                   'driver': 'GTiff',
                   'compress': 'deflate',
                   'bigtiff': 'yes',
                   'interleave': 'band'}

    lzw_kwargs = {'count': bands,
                  'width': samples,
                  'height': lines,
                  'dtype': 'float64',
                  'driver': 'GTiff',
                  'compress': 'lzw',
                  'bigtiff': 'yes',
                  'interleave': 'band'}

    # Initialise output files
    gzip_ds = rasterio.open('deflate.tif', 'w', **gzip_kwargs)
    lzw_ds = rasterio.open('lzw.tif', 'w', **lzw_kwargs)

    # Define a zero time delta
    tm_zero = dt.now()
    tm_zero = tm_zero - tm_zero
    gzip_time = tm_zero
    lzw_time = tm_zero

    tiles = generate_tiles(samples, lines, samples, 1)

    bnd_idx = range(1, bands + 1)

    for tile in tiles:
        ys, ye = tile[0]
        xs, xe = tile[1]
        ysize = ye - ys
        xsize = xe - xs

        # randomu specifies [x, y, z, ...] as dims
        img, seed = randomu(None, [xsize, ysize, bands], double=True,
                            gamma=True)

        st = dt.now()
        gzip_ds.write(img, indexes=bnd_idx, window=tile)
        et = dt.now()
        gzip_time += (et - st)

        st = dt.now()
        lzw_ds.write(img, indexes=bnd_idx, window=tile)
        et = dt.now()
        lzw_time += (et - st)

    gzip_ds.close()
    lzw_ds.close()

    print 'rasterio deflate creation time taken: {}'.format(gzip_time)
    print 'rasterio lzw creation time taken: {}'.format(lzw_time)


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

        kwrds = {'count': nbands,
                 'width': samples,
                 'height': lines,
                 'dtype': 'float64',
                 'driver': 'GTiff',
                 'compress': ds.kwds['compress'],
                 'bigtiff': 'yes',
                 'interleave': ds.kwds['interleave']}

        out_fname = fname.replace('.tif', '-result.tif')
        outds = rasterio.open(out_fname, 'w', **kwrds)

        xbar = numpy.zeros((nbands, 1, 1))

        for i in range(nbands):
            xbar[i] = (ds.read_band(i+1, masked=False)).mean()

        tiles = generate_tiles(samples, lines, samples, 1)

        bands = range(1, nbands + 1)

        for tile in tiles:
            data = ds.read(bands, window=tile)
            res = numpy.log(data) * numpy.sqrt(data) - xbar
            outds.write(res, indexes=bands, window=tile)
            

    et = dt.now()

    time_taken = et - st

    return time_taken


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequential",
                        help=("Selects more detail logging (default is INFO)"),
                        default=False, action='store_true')
    parser.add_argument('--dims', help='Array dimensions to create.')

    args = parser.parse_args()

    # Remove if we have run before
    if pexists('deflate.tif'):
        os.remove('deflate.tif')
    if pexists('lzw.tif'):
        os.remove('lzw.tif')

    dims = tuple([int(d) for d in args.dims.split(',')])

    print "Creating files"
    if args.sequential:
        create_sequential(dims)
    else:
        create_block(dims)

    print "Running tests"
    time_taken = test_rasterio('deflate.tif')
    print "rasterio deflate time taken: {}".format(time_taken)
    time_taken = test_rasterio('lzw.tif')
    print "rasterio lzw time taken: {}".format(time_taken)
