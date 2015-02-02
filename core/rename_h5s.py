import h5py
import glob

search_path = '/g/data1/v10/HPCData/*.nc'

for nc_file in glob.glob(search_path):
    with h5py.File(nc_file, 'r+') as hfile:
        for key1 in hfile.keys():
            for key2 in hfile[key1].keys():
                if len(key2) != 23:
                    print "Hmmmm"
                else: 
                    hfile[key1][key2[:13]+":"+key2[14:16]+":"+key2[17:]] = hfile[key1][key2]
                    del hfile[key1][key2]
