import h5py

with h5py.File("/g/data/rs0/tiles/EPSG4326_1deg_0.00025pixel_netcdf/HPCData/ERA_INTERIM/TP_25-31_147-152_1985-2015.h5", 'w') as hfile:
    y_dim = hfile["TP"].dims[1][0].value
    hfile["TP"].dims[1][0] = y_dim[::-1]
