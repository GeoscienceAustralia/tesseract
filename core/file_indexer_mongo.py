import os
import glob
import pymongo
from pymongo import Connection
import datetime


path = '/g/data1/rs0/tiles/EPSG4326_1deg_0.00025pixel/LS5_TM'

conn = Connection('128.199.74.80', 27017)
db = conn["datacube"]
coll = db["index2"]

for tile in [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]:
    for year in [name for name in os.listdir(path + '/{}'.format(tile)) if os.path.isdir(os.path.join('{}/{}'.format(path, tile), name))]:
        for file in glob.glob('{}/{}/{}/*.tif'.format(path, tile, year)):
            #ds = gdal.Open(file)
            info = file[:-4].split('/')[-1].split('_')
            try:
                date = datetime.datetime.strptime(info[5], '%Y-%m-%dT%H-%M-%S.%f')
            except:
                date = datetime.datetime.strptime(info[5], '%Y-%m-%dT%H-%M-%S')
            
            dict = { 'lat_start': float(info[4]), 'lat_extent': 1.0, 'lon_start': float(info[3]), 'lon_extent':1.0, 'pixel_size': 1.0/4000, 'product': info[2], 'time': date}
            coll.insert(dict)               

coll.ensure_index({'lat_start': 1, 'lon_start':1, 'time':1})
