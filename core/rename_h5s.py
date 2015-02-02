import h5py
import glob

search_path = '/g/data1/v10/HPCData/*.nc'

for nc_file in glob.glob(search_path):
    with h5py.File(nc_file, 'r+') as hfile:
        for key1 in hfile.keys:
            for key2 in hfile[key].keys:
                print key2
