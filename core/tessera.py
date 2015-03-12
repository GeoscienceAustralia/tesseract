__author__ = 'pablo'

import h5py
import os.path
import time
import numpy as np
from datetime import datetime
import pandas as pd

from utils import get_index
from index.index_factory import IndexFactory

class Tessera(object):

    # Consider integrating satellite information inside id_object
    def __init__(self, source=None, product=None, t_dim=None, x_dim=None, y_dim=None, b_dim=None, array=None):

        self.source = source
        self.product = product
        self.t_dim = t_dim
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.b_dim = b_dim
        self.array = array


def get_tesserae(sources=None, products=None, t1=None, t2=None, x1=None, x2=None, y1=None, y2=None, bands=None):

    tesserae = []

    print(sources)
    print(t1)
    print(t2)
    print(x1)
    print(x2)
    print(y1)
    print(y2)

    for source in sources:

        index = IndexFactory(source)

        for product in products:

            file_names = index.get_files(product, t1, t2, x1, x2, y1, y2)

            for file_name in file_names:

                if os.path.isfile(file_name):
                    print file_name
                    tessera = Tessera(source=source, product=product)

                    with h5py.File(file_name, 'r') as hfile:

                        time_dim = hfile[product].dims[0][0].value
                        x_dim = hfile[product].dims[1][0].value
                        y_dim = hfile[product].dims[2][0].value

                        if len(hfile[product].shape) == 3:
                            band_dim = np.arange(1)
                        elif len(hfile[product].shape) == 4:
                            band_dim = hfile[product].dims[3][0].value
                        
                        print time_dim
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

                        print(product)
                        print(t1_i)
                        print(t2_i)
                        print(x1_i)
                        print(x2_i)
                        print(y1_i)
                        print(y2_i)


                        tessera.array = hfile[product][t1_i:t2_i, x1_i:x2_i, y1_i:y2_i]
                        #tessera.array = hfile[prod][t1_i:t2_i, x1_i:x2_i, y1_i:y2_i, :]

                    tesserae.append(tessera)

    return tesserae


"""


if __name__ == "__main__":

    t1 = "1985-08-01T00:00:00.000Z"
    t2 = "2000-09-01T00:00:00.000Z"

    time1 = datetime.strptime(t1, '%Y-%m-%dT%H:%M:%S.%fZ')
    time2 = datetime.strptime(t2, '%Y-%m-%dT%H:%M:%S.%fZ')

    df_fc = pixel_drill_fc(sources=["LS5", "LS7"], products=["FC"], t1=time1, t2=time2, x=147.542, y=-30.6234)
    df_wofs = pixel_drill_fc(sources=["LS5", "LS7"], products=["WOFS"], t1=time1, t2=time2, x=147.542, y=-30.6234)
    df_tp = pixel_drill_era_tp(sources=["ERA_INTERIM"], products=["TP"], t1=time1, t2=time2, x=147.542, y=-30.6234)

    df = df_fc.combine_first(df_tp)
    df.TP.interpolate(inplace=True)
    df = df[np.isfinite(df['FC_0'])] 
    print df.head(10)
"""
