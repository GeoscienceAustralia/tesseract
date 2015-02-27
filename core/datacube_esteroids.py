import math
import time
from datetime import datetime
import h5py
import os.path
import numpy as np
import pandas as pd
import argparse

abs_path = "/g/data1/v10/HPCData/test/"

class Datacube(object):
    # Consider integrating satellite information inside id_object
    def __init__(self, t_dim=None, x_dim=None, y_dim=None, b_dim=None, array=None):
        
        self.t_dim = t_dim
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.b_dim = b_dim
        self.array = array
     
        
def create_datacube(product=None, t1=None, t2=None, x1=None, x2=None, y1=None, y2=None, bands=None):
    # Consider integrating satellite information inside id_object
        
    file_names = _indexer(abs_path, product, t1, t2, x1, x2, y1, y2)

    cubes = []

    for file_name in file_names:
        
        if os.path.isfile(file_name):

            dc = Datacube()

            with h5py.File(file_name, 'r') as afile:

                    time_dim = afile[product].dims[0][0].value
                    x_dim = afile[product].dims[1][0].value
                    y_dim = afile[product].dims[2][0].value
                    if len(afile[product].shape) == 3:
                        band_dim = np.arange(1)
                    elif len(afile[product].shape) == 4:
                        band_dim = afile[product].dims[3][0].value

                    t1_i = get_index(time.mktime(t1.timetuple()), time_dim)
                    t2_i = get_index(time.mktime(t2.timetuple()), time_dim)
                    dc.t_dim = time_dim[t1_i:t2_i]

                    x1_i = get_index(x1, x_dim)
                    x2_i = get_index(x2, x_dim)
                    dc.x_dim = x_dim[x1_i:x2_i]

                    y1_i = get_index(y1, y_dim)
                    y2_i = get_index(y2, y_dim)
                    dc.y_dim = y_dim[y1_i:y2_i]

                    #Select bands from input parameters
                    dc.b_dim = band_dim

                    dc.array = afile[product][t1_i:t2_i, x1_i:x2_i, y1_i:y2_i]
                    #dc.array = afile[product][t1_i:t2_i, x1_i:x2_i, y1_i:y2_i, :]
            
            cubes.append(dc)

    # Here comes the function to merge the cubes  

    return cubes


def _indexer(root=None, product=None, t1=None, t2=None, x1=None, x2=None, y1=None, y2=None):
    files = []
    
    for year in range(t1.year, t2.year+1):
        for x in range(int(math.floor(x1)), int(math.floor(x2))+1):
            for y in range(int(math.floor(y1)), int(math.floor(y2))+1):
                files.append(root + "LS5_TM_{0}_{1}_{2:04d}_{3}.h5".format(product, x, y, year))
 
    return files


def get_index(value, dimension):
    return np.abs(dimension-value).argmin()


def pixel_drill(product=None, t1=None, t2=None, x=None, y=None):

    cubes = create_datacube(product=product, t1=t1, t2=t2, x1=x, x2=x+.00025, y1=y, y2=y+.00025)

    dfs = []
    for cube in cubes:
        index = map(datetime.fromtimestamp, cube.t_dim)
        dfs.append(pd.DataFrame(np.squeeze(cube.array), index=index,
                                columns=[product + '_' + str(i) for i in cube.b_dim]))

    df = pd.concat(dfs)
    df["index"] = df.index
    df = df.drop_duplicates(cols='index')
    df = df.drop("index", 1)

    return df


def test_pixel_drill(products=None, t1=None, t2=None, x=None, y=None):

    df = None
    for prod in products:
        df_prod = pixel_drill(product=prod, t1=t1, t2=t2, x=x, y=y)
        if df is None:
            df = df_prod
        else:
            df = df.join(df_prod)

    df.dropna(how='any', inplace=True)
    df["timestamp"] = df.index
    print df.head(10)
    return df.to_json(date_format='iso', orient='records')


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="""Pixel Drill argument parser""")
    parser.add_argument(dest="start_date", type=str, help="Pixel drill start date.")
    parser.add_argument(dest="end_date", type=str, help="Pixel drill end date.")
    parser.add_argument(dest="start_x", type=float, help="Pixel drill start x.")
    parser.add_argument(dest="start_y", type=float, help="Pixel drill start y.")
    parser.add_argument("-b", "--bands", dest="bands", type=int, default=1, help="Pixel drill bands span.")

    args = parser.parse_args()
        
    time1 = datetime.strptime(args.start_date, '%Y-%m-%dT%H:%M:%S.%fZ')
    time2 = datetime.strptime(args.end_date, '%Y-%m-%dT%H:%M:%S.%fZ')

    print test_pixel_drill(products=["FC", "WOFS"], t1=time1, t2=time2, x=args.start_x, y=args.start_y)

    #Test with
    # time python datacube_esteroids.py 1985-08-01T00:00:00.000Z 2000-09-01T00:00:00.000Z 147.542 -30.6234

