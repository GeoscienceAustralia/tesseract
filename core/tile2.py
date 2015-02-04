import numpy as np
from collections import OrderedDict
from utils import get_geo_dim, filter_coord, get_index
from datetime import datetime
from pymongo import Connection
import h5py

# CONSTANTS
DATA_PATH = "/g/data1/v10/HPCData/"

def load_full_tile(item, lazy=True):
    # TODO Hardcoded bands
    return Tile2(origin_id=item, bands=6, lat_start=item[u'lat_start'], lat_end=item[u'lat_start']+item[u'lat_extent'],
                lon_start=item[u'lon_start'], lon_end=item[u'lon_start']+item[u'lon_extent'], lazy=lazy)


def load_partial_tile(item, lat_start, lat_end, lon_start, lon_end, lazy=True):
    # TODO Hardcoded bands
    return Tile2(origin_id=item, bands=6, lat_start=lat_start, lat_end=lat_end,
                 lon_start=lon_start, lon_end=lon_end, lazy=lazy)
                 


class Tile2(object):

    # Consider integrating satellite information inside id_object
    def __init__(self, origin_id=None, bands=None, lat_start=None, lat_end=None,
                 lon_start=None, lon_end=None, array =None, lazy=True):

        self.origin_id = origin_id
        # TODO Hardcoded satellite (Should come with origin_id)
        self.origin_id["satellite"] = "LS5_TM"

        orig_y_dim = get_geo_dim(origin_id["lat_start"], origin_id["lat_extent"], origin_id["pixel_size"])
        orig_x_dim = get_geo_dim(origin_id["lon_start"], origin_id["lon_extent"], origin_id["pixel_size"])

        corr_lat_start = filter_coord(lat_start, orig_y_dim)
        corr_lon_start = filter_coord(lon_start, orig_x_dim)

        corr_lat_end = filter_coord(lat_end, orig_y_dim)
        corr_lon_end = filter_coord(lon_end, orig_x_dim)

        lat1 = get_index(corr_lat_start, orig_y_dim)
        lat2 = get_index(corr_lat_end, orig_y_dim) + 1
        lon1 = get_index(corr_lon_start, orig_x_dim) 
        lon2 = get_index(corr_lon_end, orig_x_dim) + 1

        self.y_dim = get_geo_dim(corr_lat_start, corr_lat_end-corr_lat_start+self.origin_id["pixel_size"], self.origin_id["pixel_size"])
        self.x_dim = get_geo_dim(corr_lon_start, corr_lon_end-corr_lon_start+self.origin_id["pixel_size"], self.origin_id["pixel_size"])
        self.band_dim = np.arange(0,bands,1)+1
        self.array = None

        if not lazy:
            with h5py.File(DATA_PATH + "{0}_{1:03d}_{2:04d}_{3}.nc".format(self.origin_id["satellite"],
                                                               int(self.origin_id[u'lon_start']),
                                                               int(self.origin_id[u'lat_start']),
                                                               self.origin_id[u'time'].year), 'r') as dfile:
                
                self.array = dfile[self.origin_id["product"]][self.timestamp].value[lat1:lat2, lon1:lon2]

    def __getitem__(self, index):
        # TODO: Properly implement band dimension
        if len(index) == 2:

            corr_lat_start = filter_coord(index[0].start, self.y_dim)
            corr_lat_end = filter_coord(index[0].end, self.y_dim)
            corr_lon_start = filter_coord(index[1].start, self.x_dim)
            corr_lon_end = filter_coord(index[1].end, self.x_dim)

            lat1 = get_index(corr_lat_start, self.y_dim)
            lat2 = get_index(corr_lat_end, self.y_dim) + 1
            lon1 = get_index(corr_lon_start, self.x_dim)
            lon2 = get_index(corr_lon_end, self.x_dim) + 1


            if self.array is None:
                return Tile2(origin_id=self.origin_id, bands=None, lat_start=corr_lat_start, lat_end=corr_lat_end,
                 lon_start=corr_lon_start, lon_end=corr_lon_end, array=None, lazy=True)

            else:
                return Tile2(origin_id=self.origin_id, bands=None, lat_start=corr_lat_start, lat_end=corr_lat_end,
                 lon_start=corr_lon_start, lon_end=corr_lon_end, array=self.array[lon1:lon2, lat1:lat2], lazy=True)

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
        dim["latitude"] = self.y_dim
        dim["longitude"] = self.x_dim
        dim["band"] = self.band_dim
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
        return self.origin_id[u'time'].strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]


    def traverse_time(self, position=1):

        conn = Connection('128.199.74.80', 27017)
        db = conn["datacube"]


        if position >= 0:
	        cursor = db.index.find(dict(product=self.origin_id["product"], lat_start=self.origin_id["lat_start"],
                                         lon_start=self.origin_id["lon_start"], time={"$gte": self.origin_id["time"]})).sort("time", 1)

        else:
	        cursor = db.index.find(dict(product=self.origin_id["product"], lat_start=self.origin_id["lat_start"],
                                         lon_start=self.origin_id["lon_start"], time={"$lte": self.origin_id["time"]})).sort("time", -1)
        item = cursor[abs(position)]
	
        if item is not None:
            return Tile2(origin_id=item, bands=6, lat_start=self.y_dim[0], lat_end=self.y_dim[-1],
                 lon_start=self.x_dim[0], lon_end=self.x_dim[-1], lazy=True)

        else:
            return None 

if __name__ == "__main__":

    conn = Connection('128.199.74.80', 27017)
    db = conn["datacube"]

    time1 = datetime.strptime("2006-01-01T00:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    time2 = datetime.strptime("2007-01-01T00:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    
    item = db.index.find_one({"product": "NBAR", "lat_start": -34, "lon_start": 121, "time": {"$gte": time1, "$lt": time2}})

    tile = load_partial_tile(item, -33.83333333, -33.333333, 80, 130, lazy=True)
    print tile.dims
    print tile.timestamp
    print tile.shape

    next_tile= tile.traverse_time(1)
    print next_tile.dims
    print next_tile.timestamp
    print next_tile.shape
    
    next_tile= next_tile.traverse_time(1)
    print next_tile.dims
    print next_tile.timestamp
    print next_tile.shape
    
    next_tile= next_tile.traverse_time(1)
    print next_tile.dims
    print next_tile.timestamp
    print next_tile.shape
