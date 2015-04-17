__author__ = 'pablo'

import numpy as np
import h5py
from osgeo import gdal
import glob
import os.path
from datetime import datetime
import time

years = range(1987, 2012)
lats = range(-31, -25)
lons = range(147, 153)
path = "/g/data1/v10/HPCData/test/"

for lon in lons:
    for lat in lats:
        for year in years:
            if not os.path.isfile(
                            path + 'LS5_TM_WOFS_{lon:03d}_{lat:04d}_{year}.h5'.format(lon=lon, lat=lat, year=year)):
                if os.path.isdir(
                        "/g/data1/rs0/tiles/EPSG4326_1deg_0.00025pixel/LS5_TM/{lon:03d}_{lat:04d}/{year}/".format(
                                lon=lon, lat=lat, year=year)):

                    wofs_tiffs = glob.glob(
                        "/g/data1/u46/wofs/water_f7q/extents/{lon:03d}_{lat:04d}/*{year}*.tif".format(lon=lon, lat=lat,
                                                                                                      year=year))

                    if len(wofs_tiffs) > 0:

                        wofs_tiffs = sorted(wofs_tiffs)

                        with h5py.File(path + 'LS5_TM_WOFS_{lon:03d}_{lat:04d}_{year}.h5'.format(lon=lon, lat=lat,
                                                                                                 year=year),
                                       'w') as h5f:
                            h5f.create_dataset("X", data=np.arange(4000, dtype=np.float64) * 0.00025 + lon)
                            h5f.create_dataset("Y", data=np.arange(4000, dtype=np.float64) * 0.00025 + lat)

                            cube = None

                            time_dim = np.zeros(shape=len(wofs_tiffs), dtype=np.float64)

                            for i, tiff in enumerate(wofs_tiffs):

                                img_params = tiff[:-4].split('/')[-1].split('_')
                                d = datetime.strptime(img_params[5], '%Y-%m-%dT%H-%M-%S.%f')
                                posix = time.mktime(d.timetuple()) + (np.float64(d.microsecond) / 1000000)
                                time_dim[i] = posix

                                image = gdal.Open(tiff)

                                if cube is None:
                                    cube = np.array(image.GetRasterBand(1).ReadAsArray())[np.newaxis, :]
                                else:
                                    cube = np.concatenate(
                                        (cube, np.array(image.GetRasterBand(1).ReadAsArray())[np.newaxis, :]), axis=0)

                            h5f.create_dataset("time", data=time_dim)
                            ds = h5f.create_dataset("WOFS", data=cube, compression='lzf',
                                                    chunks=(len(wofs_tiffs), 100, 100))

                            ds.dims[0].attach_scale(h5f["time"])
                            ds.dims[0].label = "time"
                            ds.dims[1].attach_scale(h5f["X"])
                            ds.dims[1].label = "x"
                            ds.dims[2].attach_scale(h5f["Y"])
                            ds.dims[2].label = "y"
