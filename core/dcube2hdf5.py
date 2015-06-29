#!/usr/bin/env python

import argparse
from datetime import date
import h5py
import pandas
import numpy
from datacube.api.model import DatasetType, Satellite
from datacube.api.query import list_tiles_as_list
from datacube.api.utils import get_dataset_metadata
from datacube.api.utils import get_dataset_data
from datacube.config import Config
from eotools.tiling import generate_tiles


def write_datasets_to_hdf5(tiles, outfname, bsq=True, compression='gzip'):
    """
    Outputs the list of tiles returned from a datacube query, to a hdf5
    file container. It is assumed that the tiles are from a single cell.
    Default is to simulate a bsq interleaved file.
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

    # Define a mapping from gdal datatypes to numpy datatypes
    gdal_2_numpy_dtypes = {1: 'uint8',
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

    # Define some basic info about our output collection
    dims = (len(tiles), lines, samples)
    max_dims = (None, lines, samples)
    if bsq:
        chunks = (1, 100, samples)
    else:
        chunks = (dims[0], 1, samples)

    # Create the output container for our collection
    outf = h5py.File(outfname)
    dsets = {}
    for dstype in ds.datasets:
        md = get_dataset_metadata(ds.datasets[dstype])
        for band in ds.datasets[dstype].bands:
            samples, lines = md.shape
            dtype = gdal_2_numpy_dtypes[md.bands[band].data_type]
            out_ds_name = '/data/{}'.format(band.name)
            dsets[band] = outf.create_dataset(out_ds_name, dims, dtype=dtype,
                                              compression=compression,
                                              chunks=chunks, maxshape=max_dims)
            dsets[band].attrs['axes'] = ['time', 'y', 'x']
            dsets[band].attrs['projection'] = md.projection
            dsets[band].attrs['geotransform'] = md.transform

    # Add a time axis
    ts_dims = (len(tiles),)
    ts_ds = outf.create_dataset('/metadata/timestamps', shape=ts_dims,
                                dtype=numpy.float, chunks=ts_dims)
    ts_ds.attrs['projection'] = md.projection
    ts_ds.attrs['geotransform'] = md.transform
    ts_ds.attrs['samples'] = samples
    ts_ds.attrs['lines'] = lines

    # Output the time array in seconds
    ts_ds[:] = df['Timestamp'].values.astype('float')
    outf.flush()

    # Write all the data
    if bsq:
        # Now loop over each dataset tile, each dataset type and each band
        for idx, ds in enumerate(tiles):
            for dstype in ds.datasets:
                for band in ds.datasets[dstype].bands:
                    data = get_dataset_data(ds.datasets[dstype], [band])
                    dsets[band][idx] = data[band]
    else:
        chunks = generate_tiles(samples, lines, samples, 100, generator=False)
        ds_init = tiles[0]
        for dstype in ds_init.datasets:
            md = get_dataset_metadata(ds_init.datasets[dstype])
            for band in ds.datasets[dstype].bands:
                dtype = gdal_2_numpy_dtypes[md.bands[band].data_type]
                for chunk in chunks:
                    ychunk = chunk[0]
                    ysize = ychunk[1] - ychunk[0]
                    data = numpy.zeros((len(tiles), ysize, samples),
                                       dtype=dtype)
                    for idx, ds in enumerate(tiles):
                        data[idx, :, :] = get_dataset_data(ds.datasets[dstype],
                                                           [band], y=ychunk[0],
                                                           y_size=ysize)[band]
                    dsets[band][:, ychunk[0]:ychunk[1], :] = data

    outf.flush()
    outf.close()


if __name__ == '__main__':

    desc = 'Converts a sample datacube query into a hdf5 file.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--outfname', required=True,
                        help='The output filename.')
    parser.add_argument('--bil', action="store_false",
                        help='Simulate a bil interleaved file.')
    parser.add_argument('--compression', default='gzip',
                        help='The compression format to use. Default is gzip.')

    parsed_args = parser.parse_args()

    outfname = parsed_args.outfname
    bsq = parsed_args.bil
    compression = parsed_args.compression

    config = Config()
    satellites = [Satellite(i) for i in ['LS5', 'LS7']]
    min_date = date(1987, 01, 01)
    max_date = date(2015, 12, 31)
    ds_type = DatasetType.ARG25

    x_cell = [146]
    y_cell = [-34]

    tiles = list_tiles_as_list(x=x_cell, y=y_cell, acq_min=min_date,
                               acq_max=max_date,
                               satellites=satellites,
                               datasets=ds_type,
                               database=config.get_db_database(),
                               user=config.get_db_username(),
                               password=config.get_db_password(),
                               host=config.get_db_host(),
                               port=config.get_db_port())

    write_datasets_to_hdf5(tiles, outfname, bsq, compression)
