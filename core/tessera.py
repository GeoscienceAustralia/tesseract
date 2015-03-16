__author__ = 'pablo'

import h5py
import os.path
import time
import numpy as np
from datetime import datetime

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

    for source in sources:

        index = IndexFactory(source)

        for product in products:

            file_names = index.get_files(product, t1, t2, x1, x2, y1, y2)
            
            for file_name in file_names:

                if os.path.isfile(file_name):
                    tessera = Tessera(source=source, product=product)

                    with h5py.File(file_name, 'r') as hfile:

                        time_dim = hfile[product].dims[0][0].value
                        x_dim = hfile[product].dims[1][0].value
                        y_dim = hfile[product].dims[2][0].value

                        if len(hfile[product].shape) == 3:
                            band_dim = np.arange(1)
                        elif len(hfile[product].shape) == 4:
                            band_dim = hfile[product].dims[3][0].value
                        
                        t1_i = get_index(time.mktime(t1.timetuple()), time_dim)
                        t2_i = get_index(time.mktime(t2.timetuple()), time_dim)
                        tessera.t_dim = time_dim[t1_i:t2_i]

                        x1_i = get_index(x1, x_dim)
                        x2_i = get_index(x2, x_dim)
                        tessera.x_dim = x_dim[x1_i:x2_i]

                        #File names are top-left -> bottom-left
                        y1_i = 3999 - get_index(y1, y_dim)
                        y2_i = 3999 - get_index(y2, y_dim)
                        tessera.y_dim = y_dim[y1_i:y2_i]

                        #Select bands from input parameters
                        tessera.b_dim = band_dim

                        tessera.array = hfile[product][t1_i:t2_i, y1_i:y2_i, x1_i:x2_i]

                    tesserae.append(tessera)

    return tesserae


if __name__ == "__main__":

    t1 = "1985-08-01T00:00:00.000Z"
    t2 = "2000-09-01T00:00:00.000Z"

    time1 = datetime.strptime(t1, '%Y-%m-%dT%H:%M:%S.%fZ')
    time2 = datetime.strptime(t2, '%Y-%m-%dT%H:%M:%S.%fZ')

    get_tesserae(sources=["LS5", "LS7"], products=["NBAR"], t1=time1, t2=time2, x1=147.542, x2=147.542+.00025,
                 y1=-30.6234, y2=-30.6234+.00025)

