import numpy as np
from collections import OrderedDict, namedtuple 
import datetime

class DataCube(object):

    
    def __init__(self):
        TileID = namedtuple('TileID', ['prod', 'lat_start', 'lat_end', 'lon_start', 'lon_end', 'pixel_size', 'time'])
        self._dims = None 
        self._arrays = {} 
        # Dimension: prod, lat, lon, time, band 
        # added for testing
        self._arrays[TileID("NBAR", 1, 50, 1, 35, 0.1, np.datetime64('2007-07-13T03:45:23.475923Z'))] = np.random.randint(255, size=(500, 350, 6))
        self._arrays[TileID("NBAR", 51, 100, 36, 65, 0.1, np.datetime64('2006-01-13T23:28:19.489248Z'))] = np.random.randint(255, size=(500, 300, 6))
        self._arrays[TileID("PQA", 1, 50, 1, 35, 0.1, np.datetime64('2010-08-13T04:56:37.452752Z'))] = np.random.randint(255, size=(500, 350, 6))
        
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
        if type(index) is tuple and len(index) == 4:
            try:
                self._translate_index(index[1], 1)
            except ValueError:
                pass

    def _translate_index(self, index, position):
        if position == 1:
            if type(index) is slice:
                start = np.abs(self._dims["latitude"]-index.start).argmin()               
                stop = np.abs(self._dims["latitude"]-index.stop).argmin()
                print start, stop 
                return slice(start, stop)
        
            elif isinstance(index, int) or isinstance(index, float):
                print np.abs(self._dims["latitude"]-index).argmin()               
                return np.abs(self._dims["latitude"]-index).argmin()               
        
        elif position == 2:
            if type(index) is slice:
                start = np.abs(self._dims["longitude"]-index.start).argmin()               
                stop = np.abs(self._dims["longitude"]-index.stop).argmin()               
                return slice(start, stop)
        
    @property
    def dims(self):
	"""Mapping from dimension names to lengths.
	This dictionary cannot be modified directly, but is updated when adding
	new variables.
	"""
        
        return self._dims

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
            
    
if __name__ == "__main__":

    dc = DataCube()
    print dc["", 2:3, 4, 4]
    print dc["", 2, 4, 4]
    print dc.dims["product"]
    print dc.dims["time"]
