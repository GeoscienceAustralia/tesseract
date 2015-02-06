import numpy as np
import h5py
import time
from random import randint


def get_xy_sum(x_lon, y_lat, ds):
    
    agg = ds[x_lon, y_lat, 0:ds.shape[2]]

    return np.sum(agg)

def random_pixel_drill(folder, product, x, y, year_range):

    time_series = []
    
    for year in year_range:
        with h5py.File(folder + "LS5_TM_124_-034_{}.nc".format(year), 'r') as fread:
            grp = fread[product]
            for date in grp.__iter__():
                ds = grp[date]
                time_series.append(get_xy_sum(x, y, ds))
    return time_series

years = range(1987, 2000) + range(2003,2012)

x = randint(0, 3999)
y = randint(0, 3999)

print "Doing"
random_pixel_drill("/g/data1/v10/HPCData/", "NBAR", x, y, years)
print "Done"
