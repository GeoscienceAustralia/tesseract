import numpy as np
from collections import OrderedDict, namedtuple
# import only for test plotting
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d.axes3d import Axes3D

TileID = namedtuple('TileID', ['prod', 'lat_start', 'lat_end', 'lon_start', 'lon_end', 'pixel_size', 'time'])

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
        
        min_lat = min([tile_id.lat_start for tile_id in tile_ids])
        max_lat = max([tile_id.lat_end for tile_id in tile_ids])
        pixel = set([tile_id.pixel_size for tile_id in tile_ids])
        latitudes = np.arange(min_lat, max_lat, next(iter(pixel)))
        dims["latitude"] = latitudes
        
        min_lon = min([tile_id.lon_start for tile_id in tile_ids])
        max_lon = max([tile_id.lon_end for tile_id in tile_ids])
        pixel = set([tile_id.pixel_size for tile_id in tile_ids])
        longitudes = np.arange(min_lon, max_lon, next(iter(pixel)))
        dims["longitude"] = longitudes
       
        times = np.unique(np.sort(np.array([tile_id.time for tile_id in tile_ids])))
        dims["time"] = times
        
        self._dims = dims        

    def __getitem__(self, index):
        if len(index) == 4:
            new_arrays = {}
            for key, value in self._arrays.iteritems():
                # First check if within bounds
                #prod_bounds = key.prod in index[0]
                prod_bounds = True
                lat_bounds = key.lat_start <= index[1].start <= key.lat_end or key.lat_start <= index[1].stop <= key.lat_end
                lon_bounds = key.lon_start <= index[2].start <= key.lon_end or key.lon_start <= index[2].stop <= key.lon_end                
                #time_bounds = index[3].start <= key.time <= key.lon_end
                time_bounds = True
                
                bounds = (prod_bounds, lat_bounds, lon_bounds, time_bounds)
                if bounds.count(True) == len(bounds):
                    tile_lat_dim = np.arange(key.lat_start, key.lat_end, key.pixel_size)
                    lat_i1 = np.abs(tile_lat_dim - index[1].start).argmin()
                    lat_i2 = np.abs(tile_lat_dim - index[1].stop).argmin()
                    
                    tile_lon_dim = np.arange(key.lon_start, key.lon_end, key.pixel_size)
                    lon_i1 = np.abs(tile_lon_dim - index[2].start).argmin()
                    lon_i2 = np.abs(tile_lon_dim - index[2].stop).argmin()
                        
                    new_arrays[TileID(key.prod, tile_lat_dim[lat_i1], tile_lat_dim[lat_i2], tile_lon_dim[lon_i1], tile_lon_dim[lon_i2], key.pixel_size, key.time)] = value[lat_i1:lat_i2, lon_i1:lon_i2]
            
            return DataCube(new_arrays)
                
                    
    """    
    if type(index) is tuple and len(index) == 4:
        new_index = (index[0], _translate_index(index, 2), _translate_index(index, 3), index[4])
    """   
            
    """
    def _translate_index(self, index, pos):
        if pos == 1:
            if type(index[pos]) is slice:
                start = np.abs(self._dims["latitude"]-index.start).argmin()               
                stop = np.abs(self._dims["latitude"]-index.stop).argmin()
                print start, stop 
                return slice(start, stop)
        
            elif isinstance(index[pos], int) or isinstance(index[pos], float):
                print np.abs(self._dims["latitude"]-index).argmin()               
                return np.abs(self._dims["latitude"]-index).argmin()               
        
        elif pos == 2:
            if type(index) is slice:
                start = np.abs(self._dims["longitude"]-index.start).argmin()               
                stop = np.abs(self._dims["longitude"]-index.stop).argmin()               
                return slice(start, stop)
            
        elif isinstance(index[pos], int) or isinstance(index[pos], float):
                print np.abs(self._dims["longitude"]-index).argmin()               
                return np.abs(self._dims["longitude"]-index).argmin()               
    """
    
    @property
    def shape(self):
	"""Mapping from dimension names to lengths.
	This dictionary cannot be modified directly, but is updated when adding
	new variables.
	"""
        return "({}, {}, {}, {})".format(self._dims["product"].shape[0], self._dims["latitude"].shape[0], self._dims["longitude"].shape[0], self._dims["time"].shape[0])

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
            lons = np.arange(key.lon_start, key.lon_end, key.pixel_size)
            lats = np.arange(key.lat_start, key.lat_end, key.pixel_size)
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


	return plt
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
    arrays = {}
    arrays[TileID("NBAR", 1, 50, 1, 35, 0.1, np.datetime64('2007-07-13T03:45:23.475923Z'))] = np.random.randint(255, size=(500, 350, 6))
    arrays[TileID("NBAR", 51, 100, 36, 65, 0.1, np.datetime64('2006-01-13T23:28:19.489248Z'))] = np.random.randint(255, size=(500, 300, 6))
    arrays[TileID("PQA", 1, 50, 1, 35, 0.1, np.datetime64('2010-08-13T04:56:37.452752Z'))] = np.random.randint(255, size=(500, 350, 6))
        
    dc = DataCube(arrays)
    print dc["", 2:3, 14:56, 4]
    dc.plot_datacube()
    #print dc["", 2, 4, 4]
    #print dc.dims["product"]
    #print dc.dims["time"]
