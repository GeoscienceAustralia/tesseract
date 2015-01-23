import numpy as np
from collections import OrderedDict, namedtuple
from tile import Tile
from utils import get_geo_dim
# import only for test plotting
#from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt
#from matplotlib import cm
from mpl_toolkits.mplot3d.axes3d import Axes3D

TileID = namedtuple('TileID', ['prod', 'lat_start', 'lat_extent', 'lon_start', 'lon_extent', 'pixel_size', 'time'])

def load_data(prod, min_lat, max_lat, min_lon, max_lon):

    import pymongo
    from pymongo import Connection

    conn = Connection('128.199.74.80', 27017)
    db = conn["datacube"]

    cursor = db.index2.find({"product": prod, "lat_start": {"$gte": min_lat, "$lte": max_lat}, "lon_start": {"$gte": min_lon, "$lte": max_lon}})
    arrays = {}
    for item in cursor:
        arrays[TileID(item[u'product'], item[u'lat_start'], item[u'lat_extent'], item[u'lon_start'],
                      item[u'lon_extent'], item[u'pixel_size'], np.datetime64(item[u'time']))] = \
            Tile(item[u'lat_start'], item[u'lat_extent'], item[u'lon_start'], item[u'lon_extent'], item[u'pixel_size'],
                 bands= 6, array=None)

    return DataCube(arrays)

 
class DataCube(object):
    
    def __init__(self, arrays={}):
        self._dims = None 
        self._arrays = arrays
        self._attrs = None
        self._dims_init()

    def _dims_init(self):
        dims = OrderedDict()
        tile_ids = self._arrays.keys()

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
            new_arrays = {}
            for key, value in self._arrays.iteritems():
                tile = value[index[1].start:index[1].stop, index[2].start:index[2].stop]
                if tile is not None:
                    tile_lat_start = tile._y_dim[0]
                    tile_lat_extent = tile._y_dim[-1] - tile._y_dim[0] + key.pixel_size
                    tile_lon_start = tile._x_dim[0]
                    tile_lon_extent = tile._x_dim[-1] - tile._x_dim[0] + key.pixel_size
                    new_arrays[TileID(key.prod, tile_lat_start ,tile_lat_extent, tile_lon_start, tile_lon_extent,
                                      key.pixel_size, key.time)] = tile

            if len(new_arrays) > 0:
                return DataCube(new_arrays)

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
        for key, value in self._arrays.iteritems():
            times_conv[key.time] = np.float32(key.time)
            if np.float32(key.time) < min_time:
                min_time = np.float32(key.time)
            if np.float32(key.time) > max_time:
                max_time = np.float32(key.time)

        for key, value in self._arrays.iteritems():
            times_conv[key.time] = times_conv[key.time] - min_time

        min_z = np.inf
        max_z = -np.inf
        for key, value in self._arrays.iteritems():
            lons = get_geo_dim(key.lon_start, key.lon_extent, key.pixel_size)
            lats = get_geo_dim(key.lat_start, key.lat_extent, key.pixel_size)
            x, y = np.meshgrid(lons, lats)
            z = times_conv[key.time]
            surf = ax.plot_wireframe(x, y, z, rstride=1, cstride=1)

            if z < min_z:
                min_z = z
            if z > max_z:
                max_z = z

        ax.set_zlim(min_z-1.0, max_z+1.0)

        #ax.zaxis.set_major_locator(LinearLocator(10))
        #ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

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
    arrays[TileID("NBAR", 43.0, 1.0, 112.0, 1.0, 0.0025, np.datetime64('2007-07-13T03:45:23.475923Z'))] = Tile(43.0, 1.0, 112.0, 1.0, 0.0025, 6, np.random.randint(255, size=(4000, 4000, 6)))
    arrays[TileID("NBAR", 44.0, 1.0, 112.0, 1.0, 0.0025, np.datetime64('2006-01-13T23:28:19.489248Z'))] = Tile(44.0, 1.0, 112.0, 1.0, 0.0025, 6, np.random.randint(255, size=(4000, 4000, 6)))
    arrays[TileID("PQA", 43.0, 1.0, 112.0, 1.0, 0.0025, np.datetime64('2010-08-13T04:56:37.452752Z'))] = Tile(43.0, 1.0, 112.0, 1.0, 0.0025, 6, np.random.randint(255, size=(4000, 4000, 6)))
        
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
    """

    dc = load_data("NBAR", -45, -33, 111, 127)
    print dc.shape
    dc = dc["", -34.5:-33.5, 125.5:126.5, 4]
    print dc.shape
