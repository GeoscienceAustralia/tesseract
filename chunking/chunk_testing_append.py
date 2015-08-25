#!/usr/bin/env python

from datetime import datetime as dt
import h5py
import matplotlib.pyplot as plt
import numpy

from eotools.tiling import generate_tiles


def test_append(dset, n):
    """
    Append `n` y by x arrays to the datasets `dset`.
    The append is performed sequentially to simulate
    `realtime` update as opposed to waiting for multiple
    `n` y by x arrays to become available before writing in
    one go.
    """
    time_list = []
    z, y, x = dset.shape
    st_zero = dt.now()
    dset.resize((z + n, y, x))
    for i in range(z, z + n, 1):
        st = dt.now()
        img = numpy.random.randint(0, 256, (y, x))
        dset[i] = img
        et = dt.now()
        time_list.append((et - st).total_seconds())
    et = dt.now()
    total_time = et - st_zero
    print "Time taken: {}".format(total_time)

    return (total_time, time_list)



out_fname = 'test_append_after_create.h5'

fid = h5py.File(out_fname, 'w')

dims = (90, 4000, 4000)
maxdims = (None, 4000, 4000)

n_append = 45

ds1 = fid.create_dataset('lzf_append', dims, maxshape=maxdims, dtype='uint8',
                         chunks=(32, 64, 64), compression='lzf')

ds2 = fid.create_dataset('gzip_append', dims, maxshape=maxdims,
                         chunks=(32, 64, 64), compression='gzip')

tiles = generate_tiles(dims[2], dims[1], 640, 640, generator=False)

lzf_times = []
gzip_times = []

print "Creating initial file"
for tile in tiles:
    ys, ye = tile[0]
    xs, xe = tile[1]
    ysize = ye - ys
    xsize = xe - xs

    data = numpy.random.randint(0, 256, (dims[0], ysize, xsize))

    st = dt.now()
    ds1[:, ys:ye, xs:xe] = data
    et = dt.now()
    lzf_times.append((et - st).total_seconds())

    st = dt.now()
    ds2[:, ys:ye, xs:xe] = data
    et = dt.now()
    gzip_times.append((et - st).total_seconds())

lzf_total_time = numpy.array(lzf_times).sum()
gzip_total_time = numpy.array(gzip_times).sum()
msg = "Time taken to create {} compressed dataset: {} seconds."
print msg.format("LZF", lzf_total_time)
print msg.format("GZip", gzip_total_time)

print "Testing lzf append"
lzf_app_ttime, lzf_append_times = test_append(ds1, n_append)

print "Testing gzip append"
gzip_app_ttime, gzip_append_times = test_append(ds2, n_append)


plot_fname = 'initial_creation_times.png'
fig = plt.figure()
axis = fig.add_subplot(111)
axis.plot(range(len(tiles)), lzf_times, 'r-o', label='lzf_compression')
axis.plot(range(len(tiles)), gzip_times, 'g-o', label='gzip_compression')
plt.title('Initital Dataset Creation Times per tile/window')
plt.xlabel('tile/window number')
plt.ylabel('Time elapsed (seconds)')
lgd = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 10})
textstr = 'Total initial creation times:\nLZF: {}s\nGZip: {}s'
textstr = textstr.format(lzf_total_time, gzip_total_time)
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
axis.text(1.02, 0.95, textstr, transform=axis.transAxes, fontsize=9,
          verticalalignment='top', bbox=props)
plt.savefig(plot_fname, bbox_extra_artists=(lgd,), bbox_inches='tight')


plot_fname = 'append_times.png'
fig = plt.figure()
axis = fig.add_subplot(111)
axis.plot(range(dims[0] + 1, dims[0] + 1 + n_append, 1), lzf_append_times,
          'r-o', label='lzf_compression')
axis.plot(range(dims[0] + 1, dims[0] +1 + n_append, 1), gzip_append_times,
          'g-o', label='gzip_compression')
plt.title('Time taken to append a new image')
plt.xlabel('Band index')
plt.ylabel('Time elapsed (seconds)')
lgd = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 10})
textstr = 'Total append times:\nLZF: {}\nGZip: {}'
textstr = textstr.format(lzf_app_ttime, gzip_app_ttime)
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
axis.text(1.02, 0.95, textstr, transform=axis.transAxes, fontsize=9,
          verticalalignment='top', bbox=props)
plt.savefig(plot_fname, bbox_extra_artists=(lgd,), bbox_inches='tight')
