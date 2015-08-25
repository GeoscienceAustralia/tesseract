#!/usr/bin/env python

import argparse
import ConfigParser
import os
from os.path import join as pjoin

import numpy
import h5py

from gaip import acquisitions
from gaip import BAND_TYPE
from gaip import data
from gaip import gridded_geo_box
from gaip import stack_data
from eotools.tiling import generate_tiles


def l1t2hdf5(acqs, out_fname, chunksize=(64, 64), compression='lzf',
             chunk_multiples=1):
    """
    Given an `Acquisitions` list convert L1T geotiffs to a
    single HDF5 container.

    :param acqs:
        A list of `Aquisitions` objects.

    :param out_fname:
        A string containing the full file path name detailing
        the output filename.

    :param chunksize:
        A `tuple` of length 2 detailing the spatial block size
        that is to be used for storing the main datasets.
        Default is (64, 64).

    :param compression:
        A string detailing the output compression type.
        Default is `lzf`. See the h5py docs for available compreesion
        types.

    :param chunk_multiples:
        The chunksize multiples used for the I/O process. Default is 1.
        i.e the default chunksize and a chunk_multiples of 2 means
        that the process will perform all I/O operations in blocks
        of 128 by 128.

    :returm:
        None. File is written to disk.
    """
    # Get the band types and the reverse mapping
    btypes = BAND_TYPE.values()
    rev_btypes = {}
    for key, val in BAND_TYPE.items():
        rev_btypes[val] = key

    # Get a list of the band types contained within the acquisitions
    # see gaip/acquisitions.py for available band types
    acqs_stacks = {}
    for btype in btypes:
        acqs_stacks[btype] = [acq for acq in acqs if acq.band_type == btype]

    # Remove empty items
    remove = [key for key in acqs_stacks if len(acqs_stacks[key]) == 0]
    for key in remove: del acqs_stacks[key]

    # Get the spatial chunks we need to read/write
    chunk_x = chunksize[1] * chunk_multiples
    chunk_y = chunksize[0] * chunk_multiples

    # Define the output file and a container for the output datasets
    outf = h5py.File(out_fname, 'w')
    dsets = {}

    # Output a hdf5 container that contains datasets for each band type
    for btype, acq_stack in acqs_stacks.items():
        btype_name = rev_btypes[btype]

        # Get some basic image info
        samples = acq_stack[0].samples
        lines = acq_stack[0].lines
        bands = len(acq_stack)
        dtype = data(acq_stack[0], window=((0, 1), (0, 1))).dtype

        # We could have different resolution datasets and different origins
        geobox = gridded_geo_box(acq_stack[0])

        # Setup the dimensions and chunksize
        if bands > 1:
            dims = (bands, lines, samples)
            chunks = (bands, chunksize[0], chunksize[1])
        else:
            dims = (lines, samples)
            chunks = (chunksize[0], chunksize[1])

        # Create the output dataset eg /Reflective/data
        # This is to account for potential differences in resolution,
        # extents, therefore they'll have their own dimension attributes
        dset_name = pjoin(btype_name, 'data')
        dsets[dset_name] = outf.create_dataset(dset_name, dims, dtype=dtype,
                                               compression=compression,
                                               chunks=chunks)

        # Now we need to assign some attributes and dimensions to each of the
        # datasets, such as x_map/y_map units and arrays of map unit values,
        # a crs containing the transform and wkt or proj4 strings.
        # The dataset units could contain the spectral wavelength as the
        # identifier.
        x_name = pjoin(btype_name, 'x')
        y_name = pjoin(btype_name, 'y')
        x_dset = outf.create_dataset(x_name, (samples,), dtype='float64')
        y_dset = outf.create_dataset(y_name, (lines,), dtype='float64')
        xmap = numpy.array([geobox.convert_coordinates((i, 0), centre=True)[0]
                            for i in range(samples)])
        ymap = numpy.array([geobox.convert_coordinates((0, i), centre=True)[1]
                            for i in range(lines)])
        x_dset[:] = xmap
        y_dset[:] = ymap
        x_dset.attrs['name'] = 'x_coordinate'
        y_dset.attrs['name'] = 'y_coordinate'

        # The crs dataset will be interpreted as a scalar
        crs_dset_name = pjoin(btype_name, 'crs')
        crs_dset = outf.create_dataset(crs_dset_name, (), dtype='i')
        if geobox.crs.IsProjected():
            crs_name = geobox.crs.GetAttrValue('projcs')
        else:
            crs_name = geobox.crs.GetAttrValue('geogcs')
        crs_dset.attrs['name'] = crs_name
        crs_dset.attrs['crs_wkt'] = geobox.crs.ExportToWkt()
        crs_dset.attrs['crs_Proj4'] = geobox.crs.ExportToProj4()
        crs_dset.attrs['units'] = geobox.crs.GetAttrValue('unit', 0)
        crs_dset.attrs['transform'] = geobox.affine.to_gdal()


        # Now get the wavelengths
        try:
            acq_stack[0].wavelength
        except KeyError:
            # What to do for BQA???
            pass
        else:
            min_max_wl = [acq.wavelength for acq in acq_stack]
            centre_wlengths = [(w[1] + w[0]) / 2 for w in min_max_wl]
            cw_name = pjoin(btype_name, 'centre_wavelengths')
            cw_dset = outf.create_dataset(cw_name, data=centre_wlengths,
                                          dtype='f')
            cw_dset.attrs['name'] = 'centre_wavelengths'
            cw_dset.attrs['units'] = 'micrometres'

        # create some dimension scales
        if bands > 1:
            dsets[dset_name].dims.create_scale(cw_dset, 'centre_wavelengths')
            dsets[dset_name].dims.create_scale(y_dset, 'y_coordinate')
            dsets[dset_name].dims.create_scale(x_dset, 'x_coordinate')
            dsets[dset_name].dims[0].attach_scale(cw_dset)
            dsets[dset_name].dims[1].attach_scale(y_dset)
            dsets[dset_name].dims[2].attach_scale(x_dset)
            dsets[dset_name].dims[0].label = 'centre_wavelengths'
            dsets[dset_name].dims[1].label = 'y'
            dsets[dset_name].dims[2].label = 'x'
        else:
            dsets[dset_name].dims.create_scale(y_dset, 'y_coordinate')
            dsets[dset_name].dims.create_scale(x_dset, 'x_coordinate')
            dsets[dset_name].dims[0].attach_scale(y_dset)
            dsets[dset_name].dims[1].attach_scale(x_dset)
            dsets[dset_name].dims[0].label = 'y'
            dsets[dset_name].dims[1].label = 'x'

        # Flush the metadata to disk
        outf.flush()

        # Create a tile/window iterator to process in chunks
        tiles = generate_tiles(samples, lines, chunk_x, chunk_y, False)

        # Now read and write each tile
        for tile in tiles:
            ys, ye = tile[0]
            xs, xe = tile[1]

            # Get a stack of data
            # Note: stack_data always returns 3D so for single band use 3D idx
            stack, _ = stack_data(acq_stack, window=tile)

            # Output to disk
            if bands > 1:
                dsets[dset_name][:, ys:ye, xs:xe] = stack
            else:
                dsets[dset_name][ys:ye, xs:xe] = stack[0] # Note 3D index


if __name__ == '__main__':

    desc = 'Converts L1T scenes to HDF5'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--input_directory',
                        help=('The input directory containing a list of L1T '
                              'scenes.'))
    parser.add_argument('--cfg_file', help='The input configuration file.')

    parsed_args = parser.parse_args()

    indir = parsed_args.input_directory
    cfg_fname = parsed_args.cfg_file

    cfg = ConfigParser.SafeConfigParser()
    cfg.read(cfg_fname)

    l1t_scenes = os.listdir(indir)

    # Output options
    out_dir = cfg.get('output', 'output_directory')

    # File and processing options
    chunksize = cfg.get('file_options', 'chunksize')
    chunksize = tuple([int(i) for i in chunksize.split(',')])
    compression = cfg.get('file_options', 'compression')
    chunk_multiples = int(cfg.get('processing_options', 'chunk_multiples'))

    for l1t in l1t_scenes:
        acqs = acquisitions(pjoin(indir, l1t))
        out_fname = pjoin(out_dir, l1t + '.h5')
        l1t2hdf5(acqs, out_fname, chunksize, compression, chunk_multiples)
