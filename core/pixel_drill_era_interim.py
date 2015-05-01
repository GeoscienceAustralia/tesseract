__author__ = 'pablo'

from tessera import get_tesserae
from datetime import datetime
import argparse
import pandas as pd
import numpy as np


def pixel_drill_era_tp(sources=None, products=None, t1=None, t2=None, x=None, y=None):

    v_epoch2datetime = np.vectorize(lambda x: datetime.fromtimestamp(x))

    cubes = get_tesserae(sources=sources, products=products, t1=t1, t2=t2, x1=x, x2=x+.125, y1=y, y2=y+.125)
 
    index = v_epoch2datetime(cubes[0].t_dim)

    df = pd.DataFrame(np.squeeze(cubes[0].array), index=index, columns=["TP"])

    df.sort_index(inplace=True)

    #remove negative offset
    df.TP += (0-df.TP.min())

    #aggregate and return
    df = df.resample("7D", how="sum")
    df["timestamp"] = df.index
    return df

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="""Pixel Drill argument parser""")
    parser.add_argument(dest="start_date", type=str, help="Pixel drill start date.")
    parser.add_argument(dest="end_date", type=str, help="Pixel drill end date.")
    parser.add_argument(dest="start_x", type=float, help="Pixel drill start x.")
    parser.add_argument(dest="start_y", type=float, help="Pixel drill start y.")

    args = parser.parse_args()

    time1 = datetime.strptime(args.start_date, '%Y-%m-%dT%H:%M:%S.%fZ')
    time2 = datetime.strptime(args.end_date, '%Y-%m-%dT%H:%M:%S.%fZ')

    df = pixel_drill_era_tp(sources=["ERA_INTERIM"], products=["TP"], t1=time1, t2=time2, x=args.start_x, y=args.start_y)
    print df.to_json(date_format='iso', orient='records')
