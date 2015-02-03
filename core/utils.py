import numpy as np

def get_geo_dim(start, extent, pixel_size):
    return np.linspace(start, start+extent, round(extent/pixel_size)+1)[:-1]

def get_index(value, dimension):
    return np.abs(dimension-value).argmin()

def filter_coord(value, dimension):
    return dimension[np.abs(dimension-value).argmin()]


if __name__ == "__main__":

    dim = get_geo_dim(0,1,.00025)
    print get_index(0.5334999999, dim)
    print filter_coord(0.5334999999, dim)