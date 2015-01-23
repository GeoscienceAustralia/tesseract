import numpy as np
from collections import OrderedDict
from utils import get_geo_dim


class Tile(object):

    def __init__(self, lat_start=None, lat_extent=None, lon_start=None, lon_extent=None, pixel_size=None, bands= None, array=None):
        self._x_dim = get_geo_dim(lon_start, lon_extent, pixel_size)
        self._y_dim = get_geo_dim(lat_start, lat_extent, pixel_size)
        self._pixel_size = pixel_size
        self._band_dim = np.arange(0,bands,1)+1
        self._array = array

    def __getitem__(self, index):
        # TODO: Properly implement band dimension
        if len(index) == 2:

            print("Tile been called {}".format(index))
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
                    return Tile(start_lat_index, end_lat_index-start_lat_index, start_lon_index,
                                end_lon_index-start_lon_index, self._pixel_size, len(self._band_dim))

                else:
                    return Tile(start_lat_index, end_lat_index-start_lat_index, start_lon_index,
                                end_lon_index-start_lon_index, self._pixel_size, len(self._band_dim),
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



if __name__ == "__main__":

    tile = Tile(42.0,1.0,111.0,1.0,.0025, 6)
    print tile.shape
    tile = tile[42.1:42.3, 111.3:111.4]
    print tile.shape
    tile = tile[42.1:42.3, 111.3:111.4]
    print tile.shape