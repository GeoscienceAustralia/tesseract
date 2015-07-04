#!/usr/bin/env python

import argparse
import h5py
import numpy
import pandas

from datacube.api.model import DatasetType, Satellite
from datacube.api.query import list_tiles_as_list
from datacube.api.utils import get_dataset_metadata
from datacube.api.utils import get_dataset_data
from datacube.config import Config
from eotools.tiling import generate_tiles


# Define a mapping from gdal datatypes to numpy datatypes
GDAL_2_NUMPY_DTYPES = {1: 'uint8',
                       2: 'uint16',
                       3: 'int16',
                       4: 'uint32',
                       5: 'int32',
                       6: 'float32',
                       7: 'float64',
                       8: 'complex64',
                       9: 'complex64',
                       10: 'complex64',
                       11: 'complex128'}


def convert_datasets_to_hdf5(tiles, outfname, chunks=(32, 128, 128),
                             compression='lzf')

    """
    Converts the list of `tiles` containing the datasets from a
    single cell returned from a query to the agdc.
    """

    # Get the acquisition times
    timestamps = []
    for ds in tiles:
        timestamps.append(ds.start_datetime)

    df = pandas.DataFrame({'Timestamp': timestamps}, index=timestamps)

    # Get the first dataset tile and retrieve basic info about the image
    ds_type = DatasetType.ARG25
    ds = tiles[0]
    dataset = ds.datasets[ds_type]
    md = get_dataset_metadata(dataset)
    samples, lines = md.shape

    # Define some basic info about our output collection
    dims = (len(tiles), lines, samples)
    max_dims = (None, lines, samples)

    # Create the output container for our collection
    outf = h5py.File(outfname)
    dsets = {}
    for dstype in ds.datasets:
        md = get_dataset_metadata(ds.datasets[dstype])
        for band in ds.datasets[dstype].bands:
            dtype = GDAL_2_NUMPY_DTYPES[md.bands[band].data_type]
            out_ds_name = '/data/{}'.format(band.name)
            dsets[band] = outf.create_dataset(out_ds_name, dims, dtype=dtype,
                                              compression=compression,
                                              chunks=chunks, maxshape=max_dims)
            dsets[band].attrs['axes'] = ['time', 'y', 'x']
            dsets[band].attrs['projection'] = md.projection
            dsets[band].attrs['geotransform'] = md.transform

    # TODO add a crs variable??? with x and y arrays containing coords???
    # Add a time axis
    ts_dims = (len(tiles),)
    ts_ds = outf.create_dataset('/metadata/timestamps', shape=ts_dims,
                                dtype=numpy.float, chunks=ts_dims)
    ts_ds.attrs['projection'] = md.projection
    ts_ds.attrs['geotransform'] = md.transform
    ts_ds.attrs['samples'] = samples
    ts_ds.attrs['lines'] = lines
    ts_ds.attrs['dimensions'] = dims

    # Output the time array in seconds
    ts_ds[:] = df['Timestamp'].values.astype('float')
    outf.flush()

    # Get the spatial and z-axis chunks we need to read/write
    chunks = generate_tiles(samples, lines, chunks[2], chunks[1],
                            generator=False)
    tchunks = generate_tiles(ts_dims, 100, chunks[0], 100, generator=False)
    tchunks = [x for y, x in tchunks]

    # Write out the data
    ds_init = tiles[0]
    for dstype in ds_init.datasets:
        md = get_dataset_metadata(ds_init.datasets[dstype])
        for band in ds.datasets[dstype].bands:
            dtype = GDAL_2_NUMPY_DTYPES[md.bands[band].data_type]
            for tchunk in tchunks:
                ts, te = tchunk
                tsize = te - ts
                ds_subs = tiles[ts:te]
                for chunk in chunks:
                    ys, ye = chunk[0]
                    xs, xe = chunk[0]
                    ysize = ye - ys
                    xsize = xe - xs
                    data = numpy.zeros((tsize, ysize, xsize), dtype=dtype)
                    for idx, ds in enumerate(ds_subs):
                        data[idx] = get_dataset_data(ds.datasets[dstype],
                                                     [band], x=xs, y=ys,
                                                     x_size=xsize,
                                                     y_size=ysize)[band]
                    dsets[band][ts:te, ys:ye, xs:xe] = data

    outf.flush()
    outf.close()
