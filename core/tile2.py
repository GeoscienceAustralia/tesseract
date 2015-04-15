import numpy as np
from collections import OrderedDict
from utils import get_geo_dim, filter_coord, get_index
from datetime import datetime
from pymongo import Connection
import h5py

# CONSTANTS
DATA_PATH = "/g/data1/rs0/tiles/EPSG4326_1deg_0.00025pixel_netcdf/HPCData/"

mongo_ip = 'localhost'

def load_full_tile(item, lazy=True):
    # TODO Hardcoded bands
    return Tile2(origin_id=item, bands=6, lat_start=item[u'lat_start'], lat_end=item[u'lat_start']+item[u'lat_extent'],
                lon_start=item[u'lon_start'], lon_end=item[u'lon_start']+item[u'lon_extent'], lazy=lazy)


def load_partial_tile(item, lat_start, lat_end, lon_start, lon_end, bands, lazy=True):
    # TODO Hardcoded bands
    return Tile2(origin_id=item, bands=bands, lat_start=lat_start, lat_end=lat_end,
                 lon_start=lon_start, lon_end=lon_end, lazy=lazy)

                 
def drill_tile_complete(item, lat_start, lat_end, lon_start, lon_end, bands, nan_value=-999):

    tile = load_partial_tile(item, lat_start, lat_end, lon_start, lon_end, bands, lazy=False)
    covered_area = np.ma.masked_equal(tile.array, nan_value)

    print tile.array.shape
    print np.count_nonzero(covered_area) - covered_area.count()

    while (np.count_nonzero(covered_area) - covered_area.count()) > 0:
        tile = tile.traverse_time(-1)
        print tile.array.shape
        print np.count_nonzero(covered_area) - covered_area.count()
        next_covered_area = np.ma.masked_equal(tile.array, nan_value)
        next_covered_area.mask = np.logical_not(np.logical_and(covered_area.mask, np.logical_not(next_covered_area.mask))) 
        covered_area = np.ma.array(np.dstack((covered_area, next_covered_area)), mask=np.dstack((covered_area.mask, next_covered_area.mask)))
        covered_area = np.prod(covered_area, axis=2)

    return covered_area.data


def drill_pixel_tile2(cursor, lat, lon, product, band):
    # TODO Hardcoded bands
    tiles = []
    year_file = None
    dfile = None
    for item in cursor:
        item_year = item[u'time'].year
        if item_year != year_file:
            if dfile is not None:
                dfile.close()
            dfile = h5py.File(DATA_PATH + "{0}_{1:03d}_{2:04d}_{3}.h5".format("LS5_TM",
                                                               int(item[u'lon_start']),
                                                               int(item[u'lat_start']),
                                                               item[u'time'].year), 'r')

            year_file = item_year
        tiles.append(Tile2(origin_id=item, bands=[0,1,3,4,5], lat_start=lat, lat_end=lat,
                    lon_start=lon, lon_end=lon, array=None, lazy=True, f_pointer=dfile))
    
    return tiles


def drill_pixel_tile(cursor, lat, lon, product, band):
    # TODO Hardcoded bands
    # TODO Year aggregation optimization

    tiles = []

    for item in cursor:
        tiles.append(Tile2(origin_id=item, bands=band, lat_start=lat, lat_end=lat,
                     lon_start=lon, lon_end=lon, array=None, lazy=False))

    return tiles


def drill_pixel_tile_parallel(queue, cursor, lat, lon, product, band):
    # TODO Hardcoded bands
    # TODO Year aggregation optimization

    tiles = []

    for item in cursor:
        tiles.append(Tile2(origin_id=item, bands=band, lat_start=lat, lat_end=lat,
                     lon_start=lon, lon_end=lon, array=None, lazy=False))

    queue.put(tiles)


class Tile2(object):

    # Consider integrating satellite information inside id_object
    def __init__(self, origin_id=None, bands=None, lat_start=None, lat_end=None,
                 lon_start=None, lon_end=None, array =None, lazy=True, f_pointer=None):

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

        self.bands = bands
        if type(bands) is int: 
            self.band_dim = np.arange(0,1,1)+1
        elif type(bands) is list: 
            self.band_dim = np.arange(0,len(bands),1)+1
        else:
            #TODO throw exception
            pass 

        self.array = None

        if not lazy:
            with h5py.File(DATA_PATH + "{0}_{1:03d}_{2:04d}_{3}.h5".format(self.origin_id["satellite"],
                                                               int(self.origin_id[u'lon_start']),
                                                               int(self.origin_id[u'lat_start']),
                                                               self.origin_id[u'time'].year), 'r') as dfile:
                if len(dfile[self.origin_id["product"]][self.timestamp].shape) == 3:
                    self.array = dfile[self.origin_id["product"]][self.timestamp][lat1:lat2, lon1:lon2, bands]
                else: 
                    self.array = dfile[self.origin_id["product"]][self.timestamp][lat1:lat2, lon1:lon2]
                #print lat1,lat2,lon1,lon2,bands
        
        if f_pointer is not None:
                self.array = f_pointer[self.origin_id["product"]][self.timestamp][lat1:lat2, lon1:lon2, bands]


    def __getitem__(self, index):
        # TODO: Properly implement band dimension
        if len(index) == 2:

            corr_lat_start = filter_coord(index[0].start, self.y_dim)
            corr_lat_end = filter_coord(index[0].stop, self.y_dim)
            corr_lon_start = filter_coord(index[1].start, self.x_dim)
            corr_lon_end = filter_coord(index[1].stop, self.x_dim)

            lat1 = get_index(corr_lat_start, self.y_dim)
            lat2 = get_index(corr_lat_end, self.y_dim) + 1
            lon1 = get_index(corr_lon_start, self.x_dim)
            lon2 = get_index(corr_lon_end, self.x_dim) + 1


            if self.array is None:
                return Tile2(origin_id=self.origin_id, bands=6, lat_start=corr_lat_start, lat_end=corr_lat_end,
                 lon_start=corr_lon_start, lon_end=corr_lon_end, array=None, lazy=True)

            else:
                return Tile2(origin_id=self.origin_id, bands=6, lat_start=corr_lat_start, lat_end=corr_lat_end,
                 lon_start=corr_lon_start, lon_end=corr_lon_end, array=self.array[lon1:lon2, lat1:lat2], lazy=False)

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

        conn = Connection(mongo_ip, 27017)

        db = conn["datacube"]


        if position >= 0:
	        cursor = db.index.find(dict(product=self.origin_id["product"], lat_start=self.origin_id["lat_start"],
                                         lon_start=self.origin_id["lon_start"], time={"$gte": self.origin_id["time"]})).sort("time", 1)

        else:
	        cursor = db.index.find(dict(product=self.origin_id["product"], lat_start=self.origin_id["lat_start"],
                                         lon_start=self.origin_id["lon_start"], time={"$lte": self.origin_id["time"]})).sort("time", -1)
        item = cursor[abs(position)]
	
        if item is not None:
            return load_partial_tile(item, self.y_dim[0], self.y_dim[-1], self.x_dim[0], self.x_dim[-1], self.bands, lazy=False)
            #return load_partial_tile(origin_id=item, bands=self.bands, lat_start=self.y_dim[0], lat_end=self.y_dim[-1],
            #     lon_start=self.x_dim[0], lon_end=self.x_dim[-1], lazy=False)

        else:
            print "ohhh"
            return None 

if __name__ == "__main__":
    
    conn = Connection(mongo_ip, 27017)
    db = conn["datacube"]

    time1 = datetime.strptime("2006-01-01T00:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    time2 = datetime.strptime("2007-01-01T00:00:00.000Z", '%Y-%m-%dT%H:%M:%S.%fZ')
    
    item = db.index.find_one({"product": "NBAR", "lat_start": -30, "lon_start": 121, "time": {"$gte": time1, "$lt": time2}})

    tile =  drill_tile_complete(item, -30.8, -30.5, 121.2, 121.7, 1, -999)
    print tile 
    print np.count_nonzero(np.ma.masked_equal(tile, -999))
