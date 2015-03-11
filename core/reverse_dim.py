import h5py

with h5py.File("/g/data/v10/HPCData/test/test.h5", 'w') as hfile:
    y_dim = hfile["TP"].dims[1][0].value
    hfile["TP"].dims[1][0] = y_dim[::-1]
