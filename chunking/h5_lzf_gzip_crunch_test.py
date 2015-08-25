#!/usr/bin/env python

import argparse
from datetime import datetime as dt
import os
from os.path import exists as pexists

import numpy
import h5py

from eotools.tiling import generate_tiles
from idl_functions import randomu


def create_files_sequential(fname, dims, chunks):
    """
    Create 2 hdf5 files, one compressed with lzf the other
    compressed with gzip, given dimensions `dims` and chunksizes
    `chunks`.
    The creation is performed sequentially to simulate many current
    processed such as WOfS where each y by x array is analysed and
    created independently. Also doubles as a test for appending data.
    We'll create float64 data, this should test speeds
    of read/write capabilities much better than uint8.
    """
    bands, lines, samples = dims
    maxdims = (None, lines, samples)


    with h5py.File(fname, 'w') as fid:

        lzf_ds = fid.create_dataset('data-lzf', dims, dtype='float64',
                                    chunks=chunks, maxshape=maxdims,
                                    compression='lzf')
        gzip_ds = fid.create_dataset('data-gzip', dims, dtype='float64',
                                     chunks=chunks, maxshape=maxdims,
                                     compression='gzip')


        tm_zero = dt.now()
        tm_zero = tm_zero - tm_zero
        lzf_time = tm_zero
        gzip_time = tm_zero

        for i in range(bands):
            # randomu specifies [x, y, z, ...] as dims
            img, seed = randomu(None, [samples, lines], double=True,
                                gamma=True)

            st = dt.now()
            lzf_ds[i, :, :] = img
            et = dt.now()
            lzf_time += (et - st)

            st = dt.now()
            gzip_ds[i, :, :] = img
            et = dt.now()
            gzip_time += (et - st)


    print 'h5 lzf creation time taken: {}'.format(lzf_time)
    print 'h5 gzip creation time taken: {}'.format(gzip_time)


def create_files_block(fname, dims, chunks):
    """
    Create 2 hdf5 files, one compressed with lzf the other
    compressed with gzip, given dimensions `dims` and chunksizes
    `chunks`.
    The creation is preformed with all z-axis data available for
    the given (z, y, x) array. This is to simulate a time-series
    workflow that can output a (z, y, x) array where most if not
    all the z-axis data is available.
    The datatype of the output array is float64 which should give
    the I/O mechanism a good workout.
    """
    bands, lines, samples = dims
    maxdims = (None, lines, samples)

    tiles = generate_tiles(samples, lines, chunks[2], chunks[1])

    with h5py.File(fname, 'w') as fid:

        lzf_ds = fid.create_dataset('data-lzf', dims, dtype='float64',
                                    chunks=chunks, maxshape=maxdims,
                                    compression='lzf')
        gzip_ds = fid.create_dataset('data-gzip', dims, dtype='float64',
                                     chunks=chunks, maxshape=maxdims,
                                     compression='gzip')

        # Initialise time-zero
        tm_zero = dt.now()
        tm_zero = tm_zero - tm_zero
        lzf_time = tm_zero
        gzip_time = tm_zero

        # Loop over each spatial (y, x) block/tile
        for tile in tiles:
            ys, ye = tile[0]
            xs, xe = tile[1]
            ysize = ye - ys
            xsize = xe - xs

            # randomu specifies [x, y, z, ...] as dims
            img, seed = randomu(None, [xsize, ysize, bands], double=True,
                                gamma=True)

            st = dt.now()
            lzf_ds[:, ys:ye, xs:xe] = img
            et = dt.now()
            lzf_time += (et - st)

            st = dt.now()
            gzip_ds[:, ys:ye, xs:xe] = img
            et = dt.now()
            gzip_time += (et - st)


    print 'h5 lzf creation time taken: {}'.format(lzf_time)
    print 'h5 gzip creation time taken: {}'.format(gzip_time)


def test_h5(fname, dsname):
    """
    Perform a basic algorithm against the available data
    and output the result to disk based on the input data's
    dimensions and chunksize.
    The synthetic algorithm needs to evaluate the mean (xbar) at
    each time point for the entire (y, x) grid before evaluating
    log(data) * sqrt(data) - xbar
    where `data` is a (z, y-subset, x-subset) 3D NumPy array.
    """
    st = dt.now()

    # Open the file in read/write mode
    with h5py.File(fname, 'a') as fid:

        # Get the dataset and dimension info
        ds = fid[dsname]
        dims = ds.shape
        chunks = ds.chunks
        nbands, lines, samples = dims

        # Setup the output dataset
        out_dsname = dsname + '-result'
        outds = fid.create_dataset(out_dsname, dims, dtype=ds.dtype,
                                   chunks=chunks, maxshape=ds.maxshape,
                                   compression=ds.compression)

        xbar = numpy.zeros((nbands, 1, 1))

        for i in range(nbands):
            xbar[i] = ds[i].mean()

        tiles = generate_tiles(samples, lines, chunks[2], chunks[1])

        # Loop over each (ysize, xsize) tile and read all bands
        for tile in tiles:
            ys, ye = tile[0]
            xs, xe = tile[1]
            data = ds[:, ys:ye, xs:xe]
            res = numpy.log(data) * numpy.sqrt(data) - xbar
            outds[:, ys:ye, xs:xe] = res

    et = dt.now()

    time_taken = et - st

    return time_taken


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_fname", required=True, help="Output filename.")
    parser.add_argument("--sequential",
                        help=("Selects more detail logging (default is INFO)"),
                        default=False, action='store_true')
    parser.add_argument('--dims', help='Array dimensions to create.')
    parser.add_argument('--chunks', help='Storage chunksize to use.')

    args = parser.parse_args()

    # Remove if we have run before
    fname = args.out_fname
    if pexists(fname):
        os.remove(fname)

    dims = tuple([int(d) for d in args.dims.split(',')])
    chunks = tuple([int(c) for c in args.chunks.split(',')])

    print "dimensions: {}".format(dims)
    print "chunks: {}".format(chunks)

    print "Creating file: {}".format(fname)
    if args.sequential:
        create_files_sequential(fname, dims, chunks)
    else:
        create_files_block(fname, dims, chunks)

    print "Running tests"

    time_taken = test_h5(fname, 'data-lzf')
    print "h5-lzf time taken: {}".format(time_taken)

    time_taken = test_h5(fname, 'data-gzip')
    print "h5-gzip time taken: {}".format(time_taken)
