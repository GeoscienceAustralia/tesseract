from datetime import datetime
import numpy as np
import pandas as pd
from collections import OrderedDict, namedtuple
from tile2 import Tile2, load_partial_tile, drill_tiles
from math import floor
from utils import get_geo_dim
# import only for test plotting
#from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt
#from matplotlib import cm
from mpl_toolkits.mplot3d.axes3d import Axes3D
from pymongo import Connection

def load_data(prod, min_lat, max_lat, min_lon, max_lon, time_start, time_end, lazy=True):

    conn = Connection('128.199.74.80', 27017)
    db = conn["datacube"]

    cursor = db.index.find({"product": prod, "lat_start": {"$gte": int(floor(min_lat)), "$lte": int(floor(max_lat))},
                             "lon_start": {"$gte": int(floor(min_lon)), "$lte": int(floor(max_lon))},
                             "time": {"$gte": time_start, "$lt": time_end}})
    tiles = []
    for item in cursor:
        tiles.append(load_partial_tile(item, min_lat, max_lat, min_lon, max_lon, lazy=lazy))

    return DataCube(tiles)


def get_snapshot(prod, min_lat, max_lat, min_lon, max_lon, time, lazy=True):

    lats = np.arange(floor(min_lat), floor(max_lat)+1)  
    lons = np.arange(floor(min_lon), floor(max_lon)+1)  

    conn = Connection('128.199.74.80', 27017)
    db = conn["datacube"]

    tiles = []
    for lat in lats:
        for lon in lons:
            cursor = db.index.find({"product": prod, "lat_start": lat, "lon_start": lon}).sort("time", -1).limit(1)
            
            if cursor.count(with_limit_and_skip = True) == 1:
                item = cursor[0]
                tiles.append(load_partial_tile(item, min_lat, max_lat, min_lon, max_lon, lazy=lazy))
                print lat, lon, item[u'time']
    
    return DataCube(tiles)


def get_timeseries(product, lat, lon, time_start, time_end, band, nan_value=-999):

    tiles = _pixel_drill(product, lat, lon, time_start, time_end, band)
    
    ts_data = [] 
    for tile in tiles:
        filt_array = [None if x==nan_value else x for x in tile.array[0][0]]
        if all(filt_array):
            filt_array = [tile.origin_id[u'time']] + filt_array
            ts_data.append(tuple(filt_array))
   
    return pd.DataFrame(ts_data)
    


def _pixel_drill(product, lat, lon, time_start, time_end, band):

    conn = Connection('128.199.74.80', 27017)
    db = conn["datacube"]

    print "index sent"
    cursor = db.index.find({"product": product, "lat_start": int(floor(lat)), "lon_start": int(floor(lon)),
                             "time": {"$gte": time_start, "$lt": time_end}}).sort("time", 1)
    print "index returned"

    tiles = drill_tiles(cursor, lat, lon, product, band)

    #return DataCube(tiles)
    return tiles


class DataCube(object):
    
    def __init__(self, tiles=[]):
        self._dims = None 
        self._tiles = tiles
        self._attrs = None
        self._dims_init()

    def _dims_init(self):
        dims = OrderedDict()

        products = np.unique(np.sort(np.array([tile.origin_id[u'product'] for tile in self._tiles])))
        dims["product"] = products

        max_pixel = max([tile.origin_id[u'pixel_size'] for tile in self._tiles])
        
        min_lat = min([min(tile.y_dim) for tile in self._tiles])
        max_lat = max([max(tile.y_dim) for tile in self._tiles])
        latitudes = get_geo_dim(min_lat, max_lat-min_lat, max_pixel)
        dims["latitude"] = latitudes
        
        min_lon = min([min(tile.x_dim) for tile in self._tiles])
        max_lon = max([max(tile.x_dim) for tile in self._tiles])
        longitudes = get_geo_dim(min_lon, max_lon-min_lon, max_pixel)
        dims["longitude"] = longitudes
       
        times = np.unique(np.sort(np.array([tile.origin_id[u'time'] for tile in self._tiles])))
        dims["time"] = times
        self._dims = dims        

    def __getitem__(self, index):
        #TODO: Implement rest of dimensions
        if len(index) == 4:
            new_tiles = []
            for tile in self._tiles:
                tile = tile[index[1].start:index[1].stop, index[2].start:index[2].stop]
                if tile is not None:
                    new_tiles.append(tile)
            if len(new_tiles) > 0:
                return DataCube(new_tiles)

            else:
                return None

    
    @property
    def shape(self):
        """Mapping from dimension names to lengths.
        This dictionary cannot be modified directly, but is updated when adding
        new variables.
        """
        return "({}, {}, {}, {})".format(self._dims["product"].shape[0], self._dims["latitude"].shape[0],
                                         self._dims["longitude"].shape[0], self._dims["time"].shape[0])

    @property
    def dims(self):
        """Mapping from dimension names to lengths.
        This dictionary cannot be modified directly, but is updated when adding
        new variables.
        """
        return self._dims


    def plot_datacube(self):
        fig = plt.figure()
        ax = fig.gca(projection='3d')

        times_conv = {}
        min_time = np.inf
        max_time = -np.inf
        for key, value in self._tiles.iteritems():
            times_conv[key.time] = np.float32(key.time)
            if np.float32(key.time) < min_time:
                min_time = np.float32(key.time)
            if np.float32(key.time) > max_time:
                max_time = np.float32(key.time)

        for key, value in self._tiles.iteritems():
            times_conv[key.time] = times_conv[key.time] - min_time

        min_z = np.inf
        max_z = -np.inf
        print len(self._tiles)
        for key, value in self._tiles.iteritems():
            lons = get_geo_dim(key.lon_start, key.lon_extent, key.pixel_size)
            lats = get_geo_dim(key.lat_start, key.lat_extent, key.pixel_size)
            x, y = np.meshgrid(lons, lats)
            z = times_conv[key.time]
            print 1
            ax.plot_wireframe(x, y, z, rstride=1, cstride=1)
            print 2

            if z < min_z:
                min_z = z
            if z > max_z:
                max_z = z

        ax.set_zlim(min_z-1.0, max_z+1.0)

        #ax.zaxis.set_major_locator(LinearLocator(10))
        #ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
        print 3
        plt.show()
        #return plt


    def add_tile(self, tile):

        self._tiles.append(tile) 
        self._dims_init()

    
if __name__ == "__main__":
    
    time1 = datetime.strptime("1982-08-01T00:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    time2 = datetime.strptime("2011-08-01T00:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    
    ts = get_timeseries("NBAR", -32.495, 126.532, time1, time2, 6)
    print ts
    print ts.head
