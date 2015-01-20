import numpy as np

class DataCube(object):
    
    def __init__(self):
        self.data = {}
        self.x_span = None
        self.y_span = None
        self.time_span = []
        
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
            
    
    def __getitem__(self, index):
        if isinstance(index, tuple):
            return self.data
        elif isinstance(index, slice):
            return self.data[index.start:index.stop]
        else:
            return self.data[index]


class Tile(object):
    
    def __init__(self, product, data_array, lat, lon, time, x_span, y_span):
        self.product = product
        self.data = data_array
        self.lat = lat
        self.lon = lon
        self.time = time
        self.x_span = x_span
        self.y_span = y_span
