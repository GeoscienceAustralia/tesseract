from datetime import datetime
import numpy as np
from collections import OrderedDict, namedtuple
from tile import Tile, load_partial_tile
from math import floor
from utils import get_geo_dim
# import only for test plotting
#from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt
#from matplotlib import cm
from mpl_toolkits.mplot3d.axes3d import Axes3D
from pymongo import Connection

TileID = namedtuple('TileID', ['prod', 'lat_start', 'lat_extent', 'lon_start', 'lon_extent', 'pixel_size', 'time'])

def load_data(prod, min_lat, max_lat, min_lon, max_lon, time_start, time_end, lazy=True):

    conn = Connection('128.199.74.80', 27017)
    db = conn["datacube"]

    cursor = db.index.find({"product": prod, "lat_start": {"$gte": int(floor(min_lat)), "$lte": int(floor(max_lat))},
                             "lon_start": {"$gte": int(floor(min_lon)), "$lte": int(floor(max_lon))},
                             "time": {"$gte": time_start, "$lt": time_end}})
    tiles = {}
    for item in cursor:
        lat_start = max(item[u'lat_start'], min_lat)
        lon_start = max(item[u'lon_start'], min_lon)
        lat_extent = min(abs(item[u'lat_start']+item[u'lat_extent']-lat_start), abs(max_lat-lat_start))
        lon_extent = min(abs(item[u'lon_start']+item[u'lon_extent']-lon_start), abs(max_lon-lon_start))

        if lat_extent > 0 and lon_extent > 0:
            tiles[TileID(item[u'product'], lat_start, lat_extent, lon_start, lon_extent, item[u'pixel_size'], np.datetime64(item[u'time']))] = \
                load_partial_tile(item, lat_start, lon_start, lat_extent, lon_extent, lazy=lazy)
            """
            Tile(sat="LS5_TM", prod=item[u'product'], lat_id=item[u'lat_start'], lon_id=item[u'lon_start'], time=item[u'time'], pixel_size=item[u'pixel_size'], bands=6,
            lat_start=lat_start, lon_start=lon_start, lat_extent=lat_extent, lon_extent=lon_extent, array=None, lazy=lazy)
            """
    return DataCube(tiles)

def get_snapshot(prod, min_lat, max_lat, min_lon, max_lon, time):

    dc = _load_data_time(prod, min_lat, max_lat, min_lon, max_lon, time, lazy=False)
    
    for key, value in dc._tiles.iteritems():
        print value._array.shape
        break



def _load_data_time(prod, min_lat, max_lat, min_lon, max_lon, time, lazy=True):
    lats = np.arange(floor(min_lat), floor(max_lat)+1)  
    lons = np.arange(floor(min_lon), floor(max_lon)+1)  

    conn = Connection('128.199.74.80', 27017)
    db = conn["datacube"]

    tiles = {}
    for lat in lats:
        for lon in lons:

            cursor = db.index.find({"product": prod, "lat_start": lat, "lon_start": lon}).sort("time", -1).limit(1)
            
            if cursor.count(with_limit_and_skip = True) == 1:
                item = cursor[0] 
                lat_start = max(item[u'lat_start'], min_lat)
                lon_start = max(item[u'lon_start'], min_lon)
                lat_extent = min(abs(item[u'lat_start']+item[u'lat_extent']-lat_start), abs(max_lat-lat_start))
                lon_extent = min(abs(item[u'lon_start']+item[u'lon_extent']-lon_start), abs(max_lon-lon_start))

                if lat_extent > 0 and lon_extent > 0:
                    tiles[TileID(item[u'product'], lat_start, lat_extent, lon_start, lon_extent, item[u'pixel_size'], np.datetime64(item[u'time']))] = \
                      load_partial_tile(item, lat_start, lon_start, lat_extent, lon_extent, lazy=lazy)
                    print lat, lon, item[u'time']
    
    return DataCube(tiles)


class DataCube(object):
    
    def __init__(self, tiles={}):
        self._dims = None 
        self._tiles = tiles
        self._attrs = None
        self._dims_init()

    def _dims_init(self):
        dims = OrderedDict()
        tile_ids = self._tiles.keys()

        products = np.unique(np.sort(np.array([tile_id.prod for tile_id in tile_ids])))
        dims["product"] = products

        max_pixel = max([tile_id.pixel_size for tile_id in tile_ids])
        
        min_lat = min([tile_id.lat_start for tile_id in tile_ids])
        max_lat = max([tile_id.lat_start+tile_id.lat_extent for tile_id in tile_ids])
        latitudes = get_geo_dim(min_lat, max_lat-min_lat, max_pixel)
        dims["latitude"] = latitudes
        
        min_lon = min([tile_id.lon_start for tile_id in tile_ids])
        max_lon = max([tile_id.lon_start+tile_id.lon_extent for tile_id in tile_ids])
        longitudes = get_geo_dim(min_lon, max_lon-min_lon, max_pixel)
        dims["longitude"] = longitudes
       
        times = np.unique(np.sort(np.array([tile_id.time for tile_id in tile_ids])))
        dims["time"] = times
        self._dims = dims        

    def __getitem__(self, index):
        #TODO: Implement rest of dimensions
        if len(index) == 4:
            new_tiles = {}
            for key, tile in self._tiles.iteritems():
                tile = tile[index[1].start:index[1].stop, index[2].start:index[2].stop]
                if tile is not None:
                    tile_lat_start = tile._y_dim[0]
                    tile_lat_extent = tile._y_dim[-1] - tile._y_dim[0] + key.pixel_size
                    tile_lon_start = tile._x_dim[0]
                    tile_lon_extent = tile._x_dim[-1] - tile._x_dim[0] + key.pixel_size
                    new_tiles[TileID(key.prod, tile_lat_start ,tile_lat_extent, tile_lon_start, tile_lon_extent,
                                      key.pixel_size, key.time)] = tile
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


    """
    def add_tile(self, tile):
        
        self.data[(tile.prod, tile.lat, tile.lon, tile.time)] = tile
        
        if self.x_span is None:
            self.x_span = np.arange(tile.lon, tile.lon+1, 1/tile.x_span)
        else:
            self.x_span = np.arange(min(self.x_span, tile.lon), max(self.x_span, tile.lon+1), 1/tile.x_span)
        
        if self.y_span is None:
            self.y_span = np.arange(tile.lat, tile.lat+1, 1/tile.y_span)
        else:
            self.y_span = np.arange(min(self.y_span, tile.lat), max(self.y_span, tile.lat+1), 1/tile.y_span)
            
        self.time_span.append(tile.time).sort()
    """
            
    
if __name__ == "__main__":
    
    """
    arrays = {}
    for i in range(10000):
        print i
        arrays[TileID("NBAR", float(i), 1.0, 112.0, 1.0, 0.00025, np.datetime64('2007-07-13T03:45:23.475923Z'))] = Tile(43.0, 1.0, 112.0, 1.0, 0.0025, 6, np.zeros((4000, 4000, 6, ), dtype=np.uint16))
        
    dc = DataCube(arrays)
    print dc.shape
    dc = dc["", 43.0:44.0, 112.0:113.0, 4]
    print dc.shape
    dc.plot_datacube()
    dc = dc["", 43.5:44.0, 112.6:112.8, 4]
    print dc.shape
    #
    #print dc["", 2, 4, 4]
    #print dc.dims["product"]
    #print dc.dims["time"]
    time1 = datetime.strptime("2007-08-01T00:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    time2 = datetime.strptime("2007-09-01T00:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    dc = load_data("NBAR", -35.0, -33.0, 124.0, 127.0, time1, time2, lazy=False)
    print dc.shape
    dc = dc["", -34.5:-33.5, 125.5:126.5, 4]
    print len(dc._tiles)
    print dc.shape

    dc1 = dc["", -34.5:-34.1, 125.5:126.5, 4]
    print len(dc1._tiles)
    print dc1.shape

    dc2 = dc["", -33.90:-33.5, 125.5:126.5, 4]
    print len(dc2._tiles)
    print dc2.shape

    print dc.shape

    """
    time1 = datetime.strptime("2007-08-01T00:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    dc = load_data_time("NBAR", -35.0, -33.0, 124.0, 127.0, time1, lazy=False)

    #dc2.plot_datacube()
