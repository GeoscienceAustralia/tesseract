import numpy as np
from collections import OrderedDict
from utils import get_geo_dim
from datetime import datetime
from pymongo import Connection
import h5py

# CONSTANTS
DATA_PATH = "/g/data1/v10/HPCData/"

class Tile(object):

    def __init__(self, sat=None, prod=None, lat_id=None, lon_id=None, time=None, pixel_size=None, bands=None, 
                 lat_start=None, lon_start=None, lat_extent=None, lon_extent=None, array=None, lazy=True):
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

        if not lazy:
            print DATA_PATH + "{}_{}_{}_{}.nc".format(self._sat, self._lon_id, self._lat_id, self._time.year)
            with h5py.File(DATA_PATH + "{}_{}_{}_{}.nc".format(self._sat, self._lon_id, self._lat_id, self._time.year), 'r') as dfile:
                print self.timestamp
                print dfile[self._prod].keys()[5]

    def __getitem__(self, index):
        # TODO: Properly implement band dimension
        if len(index) == 2:

            #print("Tile been called {}".format(index))
            #print self._y_dim
            #print index

            #Mostly sure about comparisons
            #lat_bounds = self._y_dim[0] <= index[0].start <= self._y_dim[-1] or self._y_dim[0] < index[0].stop < self._y_dim[-1]
            #lon_bounds = self._x_dim[0] <= index[1].start <= self._x_dim[-1] or self._x_dim[0] < index[1].stop < self._x_dim[-1]
            lat_bounds = index[0].start <= self._y_dim[-1] and index[0].stop > self._y_dim[0]
            lon_bounds = index[1].start <= self._x_dim[-1] and index[1].stop > self._x_dim[0]

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


    @property
    def timestamp(self):
        """Mapping from dimension names to lengths.
        This dictionary cannot be modified directly, but is updated when adding
        new variables.
        """
        return self._time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]


    def traverse_time(self, position=1):

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
    
    conn = Connection('128.199.74.80', 27017)
    db = conn["datacube"]

    time1 = datetime.strptime("2006-01-01T00:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    time2 = datetime.strptime("2007-01-01T00:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    
    item = db.index2.find_one({"product": "NBAR", "lat_start": -34, "lon_start": 121, "time": {"$gte": time1, "$lt": time2}})
    print item 
    tile = Tile(sat="LS5_TM", prod=item[u'product'], lat_id="{0:04d}".format(int(item[u'lat_start'])), lon_id="{0:03d}".format(int(item[u'lon_start'])), time=item[u'time'], pixel_size=item['pixel_size'], bands=6, lat_start=-33.8, lon_start=121.4, lat_extent=0.45, lon_extent=0.3 , array=None, lazy=True)
    print tile.shape 
    #print tile.dims
    tile = tile[-33.8:-33.4, 121.45:121.65]    
    print tile.shape
    #print tile.dims
    tile = tile[-33.9:-33.4, 121.45:121.6]
    print tile.shape 
    #print tile.dims
    """
    return Tile(item[u'product'], item[u'lat_start'], item[u'lat_extent'], item[u'lon_start'], item[u'lon_extent'], item[u'pixel_size'],
         item[u'time'], bands= 6, array=None)
    
    tile = Tile(sat="LS5_TM", prod="NBAR", lat_id=-34, lon_id=121, time=None, pixel_size=0.00025, bands=None, 
                 lat_start=45.0, lon_start=0.0, lat_extent=1.0, lon_extent=1.0 , array=None)

    time = datetime.strptime("1994-04-22T23:58:40.830Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    #tile = load_tile("NBAR", -32.0, 137.0, time)
    
    for i in range(10):
        print tile.get_consecutive(-i)._time
    tile = tile[42.1:42.3, 111.3:111.4]
    print tile.shape
    tile = tile[42.1:42.3, 111.3:111.4]
    print tile.shape
    """
