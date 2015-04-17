import time
from datetime import datetime
import h5py
import os.path
import numpy as np
import pandas as pd
import argparse

abs_path = "/g/data/rs0/tiles/EPSG4326_1deg_0.00025pixel_netcdf/HPCData/"



        
def create_datacube(source=None, product=None, t1=None, t2=None, x1=None, x2=None, y1=None, y2=None, bands=None):

    tesserae = []

    for src in source:

        for prod in product:

            file_names = _indexer(abs_path, src, prod, t1, t2, x1, x2, y1, y2)

            for file_name in file_names:

                if os.path.isfile(file_name):

                    tessera = Tessera(source=src, product=prod)

                    with h5py.File(file_name, 'r') as afile:
                       
                        time_dim = afile[prod].dims[0][0].value
                        x_dim = afile[prod].dims[1][0].value
                        y_dim = afile[prod].dims[2][0].value
                        if len(afile[prod].shape) == 3:
                            band_dim = np.arange(1)
                        elif len(afile[prod].shape) == 4:
                            band_dim = afile[prod].dims[3][0].value

                        t1_i = get_index(time.mktime(t1.timetuple()), time_dim)
                        t2_i = get_index(time.mktime(t2.timetuple()), time_dim)
                        tessera.t_dim = time_dim[t1_i:t2_i]

                        x1_i = get_index(x1, x_dim)
                        x2_i = get_index(x2, x_dim)
                        tessera.x_dim = x_dim[x1_i:x2_i]

                        y1_i = get_index(y1, y_dim)
                        y2_i = get_index(y2, y_dim)
                        tessera.y_dim = y_dim[y1_i:y2_i]

                        #Select bands from input parameters
                        tessera.b_dim = band_dim

                        tessera.array = afile[prod][t1_i:t2_i, x1_i:x2_i, y1_i:y2_i]
                        #tessera.array = afile[prod][t1_i:t2_i, x1_i:x2_i, y1_i:y2_i, :]

                    tesserae.append(tessera)

    # Here comes the function to merge the cubes

    return tesserae


#This function will be replaced by an external db indexing the system



def pixel_drill(product=None, t1=None, t2=None, x=None, y=None):

    v_epoch2datetime = np.vectorize(lambda x: datetime.fromtimestamp(x))

    cubes = create_datacube(product=product, t1=t1, t2=t2, x1=x, x2=x+.00025, y1=y, y2=y+.00025)

    dfs = []
    for cube in cubes:
        index = v_epoch2datetime(cube.t_dim)
        dfs.append(pd.DataFrame(np.squeeze(cube.array), index=index,
                                columns=[product + '_' + str(i) for i in cube.b_dim]))

    df = pd.concat(dfs)
    df["index"] = df.index
    df = df.drop_duplicates(cols='index')
    df = df.drop("index", 1)

    return df


def pixel_drill_ecmwf(t1=None, t2=None, x=None, y=None):

    era_interim = abs_path + "TP_25-31_147-152_1985-2015.h5"

    with h5py.File(era_interim, 'r') as hfile:

        t_dim = hfile["time"].value
        index = v_epoch2datetime(t_dim)

        y_dim = hfile["Y"].value
        x_dim = hfile["X"].value
        x_i = get_index(x, x_dim)
        y_i = get_index(y, y_dim)

        #Note y and x dims are swaped as satellite
        df = pd.DataFrame(hfile["TP"][:, y_i, x_i], index=index, columns=["TP"])
        #remove negative offset
        df.TP += (0-df.TP.min())

        #aggregate and return
        return df.resample("7D", how="sum")


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
    
    df = df[df.FC_0 != -999]
    df = df[df.FC_1 != -999]
    df = df[df.FC_2 != -999]

    df = df[['FC_0', 'FC_2', 'FC_1', 'FC_3', 'WOFS_0', 'timestamp']]
    df.drop('FC_3', axis=1, inplace=True)
    df['Total'] = 10000.0 / (df['FC_0'] + df['FC_2'] + df['FC_1'])
    df['FC_0'] = df['FC_0'] * df['Total']
    df['FC_1'] = df['FC_1'] * df['Total']
    df['FC_2'] = df['FC_2'] * df['Total']
    df.drop('Total', axis=1, inplace=True)

    df_rain = pixel_drill_ecmwf(t1=t1, t2=t2, x=x, y=y)

    df_rain = df_rain.reindex(df.index, method='ffill')
    df["TP"] = df_rain["TP"]
    
    return df.to_json(date_format='iso', orient='records')


def test_pixel_drill2(sources=None, products=None, t1=None, t2=None, x=None, y=None):

    cube = create_datacube(source=sources, product=products, t1=t1, t2=t2, x1=x, x2=x+.00025, y1=y, y2=y+.00025)

    for tessera in cube:
        print tessera.product



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

    test_pixel_drill2(sources=["LS5", "LS7"], products=["FC"], t1=time1, t2=time2, x=args.start_x, y=args.start_y)

    #print test_pixel_drill(products=["FC"], t1=time1, t2=time2, x=args.start_x, y=args.start_y)



    #Test with
    # time python datacube_steroids.py 1985-08-01T00:00:00.000Z 2000-09-01T00:00:00.000Z 147.542 -30.6234

