import numpy as np

def get_geo_dim(start, extent, pixel_size):
    return np.linspace(start, start+extent, round(extent/pixel_size)+1)[:-1]