import numpy as np
from collections import OrderedDict
from utils import get_geo_dim
from datetime import datetime
from pymongo import Connection
import h5py

# CONSTANTS
DATA_PATH = "/g/data1/v10/HPCData/"

# TODO: Consider utility of this function
def load_tile(prod, lat, lon, time):

    conn = Connection('128.199.74.80', 27017)
    db = conn["datacube"]

    item = db.index2.find_one({"product": prod, "lat_start": lat, "lon_start": lon, "time": time})
    
    return Tile(item[u'product'], item[u'lat_start'], item[u'lat_extent'], item[u'lon_start'], item[u'lon_extent'], item[u'pixel_size'],
         item[u'time'], bands= 6, array=None)

class Tile(object):

    def __init__(self, sat=None, prod=None, lat_id=None, lon_id=None, time=None, pixel_size=None, bands=None, 
                 lat_start=None, lon_start=None, lat_extent=None, lon_extent=None, array=None):
                 
        self._sat = sat 
        self._prod = prod 
        self._lat_id = lat_id
        self._lon_id = lon_id
        self._time = time
        self._pixel_size = pixel_size
        self._lat_start = lat_start
        self._lon_start = lon_start
        self._lat_extent = lat_extent
        self._lon_extent = lon_extent
        self._y_dim = get_geo_dim(lat_start, lat_extent, pixel_size)
        self._x_dim = get_geo_dim(lon_start, lon_extent, pixel_size)
        self._band_dim = np.arange(0,bands,1)+1
        self._array = array
         
        if array is None:
            with h5py.File(DATA_PATH + "", r) as dfile:
                print self._prod][self._time].value 
                self._array = dfile[self._prod][self._time].value 

    def __getitem__(self, index):
        # TODO: Properly implement band dimension
        if len(index) == 2:

            #print("Tile been called {}".format(index))
            #print self._y_dim
            #print index

            #Mostly sure about comparisons
            lat_bounds = self._y_dim[0] <= index[0].start <= self._y_dim[-1] or self._y_dim[0] < index[0].stop < self._y_dim[-1]
            lon_bounds = self._x_dim[0] <= index[1].start <= self._x_dim[-1] or self._x_dim[0] < index[1].stop < self._x_dim[-1]

            bounds = (lat_bounds, lon_bounds)
            if bounds.count(True) == len(bounds):

                start_lat_index = max(index[0].start, self._y_dim[0])
                array_lat_start_index = np.abs(self._y_dim - index[0].start).argmin()
                start_lon_index = max(index[1].start, self._x_dim[0])
                array_lon_start_index = np.abs(self._x_dim - index[1].start).argmin()

                if index[0].stop > np.max(self._y_dim):
                    end_lat_index = np.max(self._y_dim) + self._pixel_size
                    array_lat_end_index = None

                else:
                    end_lat_index = index[0].stop
                    array_lat_end_index = np.abs(self._y_dim - index[0].stop).argmin()

                if index[1].stop > np.max(self._x_dim):
                    end_lon_index = np.max(self._x_dim) + self._pixel_size
                    array_lon_end_index = None

                else:
                    end_lon_index = index[1].stop
                    array_lon_end_index = np.abs(self._x_dim - index[1].stop).argmin()


                if self._array is None:
                    return Tile(self._sat, self._prod, self._lat_id, self._lon_id, self._time, self._pixel_size, 
                                len(self._band_dim), start_lat_index, start_lon_index,
                                end_lat_index-start_lat_index, end_lon_index-start_lon_index, None)

                else:
                    return Tile(self._sat, self._prod, self._lat_id, self._lon_id, self._time, self._pixel_size, 
                                len(self._band_dim), start_lat_index, start_lon_index,
                                end_lat_index-start_lat_index, end_lon_index-start_lon_index, 
                                self._array[array_lon_start_index:array_lon_end_index,
                                array_lat_start_index:array_lat_end_index])

            else:
                return None
        else:
            # TODO: Properly manage index exceptions
            raise Exception

    @property
    def dims(self):
        """Mapping from dimension names to lengths.
        This dictionary cannot be modified directly, but is updated when adding
        new variables.
        """
        dim = OrderedDict()
        dim["latitude"] = self._y_dim
        dim["longitude"] = self._x_dim
        dim["band"] = self._band_dim
        return dim


    @property
    def shape(self):
        """Mapping from dimension names to lengths.
        This dictionary cannot be modified directly, but is updated when adding
        new variables.
        """
        dim = self.dims
        return "({}, {}, {})".format(dim["latitude"].shape[0], dim["longitude"].shape[0], dim["band"].shape[0])


    def get_time_adjacent(self, position=1):

        conn = Connection('128.199.74.80', 27017)
        db = conn["datacube"]


        if position >= 0:
	    cursor = db.index2.find({"product": self._prod, "lat_start": self._lat_id, "lon_start": self._lon_id, "time": {"$gte": self._time}}).sort("time", 1)
            item = cursor[position]
        else:
	    cursor = db.index2.find({"product": self._prod, "lat_start": self._lat_id, "lon_start": self._lon_id, "time": {"$lte": self._time}}).sort("time", -1)
            item = cursor[abs(position)]
	
        if item is not None:
            return Tile(item[u'product'], item[u'lat_start'], item[u'lat_extent'], item[u'lon_start'], item[u'lon_extent'], item[u'pixel_size'],
                        item[u'time'], bands= 6, array=None)

        else:
            return None 

if __name__ == "__main__":
    time = datetime.strptime("1994-04-22T23:58:40.830Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    tile = load_tile("NBAR", -32.0, 137.0, time)
    
    for i in range(10):
        print tile.get_consecutive(-i)._time
    """
    tile = tile[42.1:42.3, 111.3:111.4]
    print tile.shape
    tile = tile[42.1:42.3, 111.3:111.4]
    print tile.shape
    """
