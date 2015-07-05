#!/usr/bin/env python

import argparse
import ConfigParser
import cPickle as pickle
from datetime import date

import h5py
import numpy
import pandas

from datacube.api.model import DatasetType, Satellite
from datacube.api.query import list_tiles_as_list
from datacube.api.utils import get_dataset_metadata
from datacube.api.utils import get_dataset_data
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


# Define a DatasetType mapping
DS_TYPES_MAP = {'arg25': DatasetType.ARG25,
                'fc25': DatasetType.FC25,
                'pq25': DatasetType.PQ25}
#                'water': DatasetType.WATER}


def convert_datasets_to_hdf5(tiles, outfname, chunksize=(32, 128, 128),
                             chunk_multiples=1, compression='lzf',
                             dataset_types=None):
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
                                              chunks=chunksize,
                                              maxshape=max_dims)
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
    chunk_x = chunksize[2] * chunk_multiples
    chunk_y = chunksize[1] * chunk_multiples
    chunks = generate_tiles(samples, lines, chunk_x, chunk_y,
                            generator=False)
    tchunks = generate_tiles(ts_dims[0], 100, 256, 100,
                             generator=False)
    tchunks = [x for y, x in tchunks]

    # Write out the data
    ds_init = tiles[0]
    #for dstype in ds_init.datasets:
    for dstype in dataset_types:
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

if __name__ == '__main__':

    desc = 'Converts a sample datacube query into a hdf5 file.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--cfg_file', help='The input configuration file.')

    parsed_args = parser.parse_args()

    cfg_fname = parsed_args.cfg_file

    cfg = ConfigParser.SafeConfigParser()
    cfg.read(cfg_fname)


    # Retrieve the configuraiton option

    # Get the satellites we wish to query
    satellites = cfg.get('db_query', 'satellites')
    satellites = [Satellite(i) for i in satellites.split(',')]

    # Get the min/max date range to query
    min_date = cfg.get('db_query', 'min_date')
    min_date = [int(i) for i in min_date.split('_')]
    min_date = date(min_date[0], min_date[1], min_date[2])
    max_date = cfg.get('db_query', 'max_date')
    max_date = [int(i) for i in max_date.split('_')]
    max_date = date(max_date[0], max_date[1], max_date[2])

    # Get the cell
    cell_x = int(cfg.get('db_query', 'cell_x'))
    cell_y = int(cfg.get('db_query', 'cell_y'))

    # Get the DatasetTypes
    ds_types = cfg.get('db_query', 'dataset_types')
    ds_types = [i.lower() for i in ds_types.split(',')]
    ds_types = [DS_TYPES_MAP[i] for i in ds_types]

    # File and processing options
    chunksize = cfg.get('file_options', 'chunksize')
    chunksize = tuple([int(i) for i in chunksize.split(',')])
    compression = cfg.get('file_options', 'compression')
    chunk_multiples = int(cfg.get('processing_options', 'chunk_multiples'))

    # Output options
    out_fname = cfg.get('output', 'hdf5_filename')
    query_fname = cfg.get('output', 'query_filename')


    # Query the DB, save the result to disk
    tiles = list_tiles_as_list(x=[cell_x], y=[cell_y], acq_min=min_date,
                               acq_max=max_date, dataset_types=ds_types,
                               satellites=satellites)

    with open(query_fname, 'w') as outf:
        pickle.dump(tiles, outf)


    # Convert
    convert_datasets_to_hdf5(tiles, out_fname, chunksize=chunksize,
                             chunk_multiples=chunk_multiples,
                             compression=compression,
                             dataset_types=ds_types)
