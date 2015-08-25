from datetime import datetime as dt
import h5py
import matplotlib.pyplot as plt
import numpy


def test_append_one_timeslice(dset):
    """
    Create a (32, 4000, 4000) array sequentially to the dataset `dset`.
    Simulates creating an (32, 4000, 4000) array as part of some higher
    workflow such as WOfS where every time slice is analysed independently
    (if multi-processed) or sequential (if single-processed).
    """
    st = dt.now()
    for i in range(32):
        dset[i] = numpy.random.randint(0, 256, (4000, 4000))
    et = dt.now()
    print "time taken: {}".format(et - st)
    return (et - st).total_seconds()


def test_append_full_time_chunk(dset, z_size):
    """
    Create a (32, 4000, 4000) array to the dataset `dset`.
    The `z_size` argument defines how large each z-axis block is to
    be, eg. 1, 2, 3, 4,..16, 17,..32.
    The idea is to define a dataset `dset` with predefined chunks such
    as 1, 2, or 4 and time how long it takes to create a 
    (32, 4000, 4000) array.
    """
    st = dt.now()
    for i in range(0, 32, z_size):
        data = numpy.random.randint(0, 256, (z_size, 4000, 4000))
        idx = i + z_size
        dset[i:idx] = data
    et = dt.now()
    print "time taken: {}".format(et - st)
    return (et - st).total_seconds()


f = h5py.File('test_create_append_single.h5')
dims = (32, 4000, 4000)

ds1 = f.create_dataset('data_1_chunked_lzf', dims, dtype='uint8', chunks=(1, 128, 128), compression='lzf')
ds2 = f.create_dataset('data_1_chunked_gzip', dims, dtype='uint8', chunks=(1, 128, 128), compression='gzip')

ds4 = f.create_dataset('data_2_chunked_lzf', dims, dtype='uint8', chunks=(2, 128, 128), compression='lzf')
ds5 = f.create_dataset('data_2_chunked_gzip', dims, dtype='uint8', chunks=(2, 128, 128), compression='gzip')

ds7 = f.create_dataset('data_4_chunked_lzf', dims, dtype='uint8', chunks=(4, 128, 128), compression='lzf')
ds8 = f.create_dataset('data_4_chunked_gzip', dims, dtype='uint8', chunks=(4, 128, 128), compression='gzip')

ds10 = f.create_dataset('data_8_chunked_lzf', dims, dtype='uint8', chunks=(8, 128, 128), compression='lzf')
ds11 = f.create_dataset('data_8_chunked_gzip', dims, dtype='uint8', chunks=(8, 128, 128), compression='gzip')

ds13 = f.create_dataset('data_16_chunked_lzf', dims, dtype='uint8', chunks=(16, 128, 128), compression='lzf')
ds14 = f.create_dataset('data_16_chunked_gzip', dims, dtype='uint8', chunks=(16, 128, 128), compression='gzip')

ds16 = f.create_dataset('data_32_chunked_lzf', dims, dtype='uint8', chunks=(32, 128, 128), compression='lzf')
ds17 = f.create_dataset('data_32_chunked_gzip', dims, dtype='uint8', chunks=(32, 128, 128), compression='gzip')

chunks = [1, 2, 4, 8, 16, 32]
hdf_lzf_times = []
hdf_gzip_times = []


print "Testing hdf 1 z-chunk lzf compression"
hdf_lzf_times.append(test_append_one_timeslice(ds1))

print "Testing hdf 1 z-chunk gzip compression."
hdf_gzip_times.append(test_append_one_timeslice(ds2))

print "Testing hdf 2 z-chunk lzf compression"
hdf_lzf_times.append(test_append_one_timeslice(ds4))

print "Testing hdf 2 z-chunk gzip compression."
hdf_gzip_times.append(test_append_one_timeslice(ds5))

print "Testing hdf 4 z-chunk lzf compression"
hdf_lzf_times.append(test_append_one_timeslice(ds7))

print "Testing hdf 4 z-chunk gzip compression."
hdf_gzip_times.append(test_append_one_timeslice(ds8))

print "Testing hdf 8 z-chunk lzf compression"
hdf_lzf_times.append(test_append_one_timeslice(ds10))

print "Testing hdf 8 z-chunk gzip compression."
hdf_gzip_times.append(test_append_one_timeslice(ds11))

print "Testing hdf 16 z-chunk lzf compression"
hdf_lzf_times.append(test_append_one_timeslice(ds13))

print "Testing hdf 16 z-chunk gzip compression."
hdf_gzip_times.append(test_append_one_timeslice(ds14))

print "Testing hdf 32 z-chunk lzf compression"
hdf_lzf_times.append(test_append_one_timeslice(ds16))

print "Testing hdf 32 z-chunk gzip compression."
hdf_gzip_times.append(test_append_one_timeslice(ds17))


ff = h5py.File('test_create_append_multi.h5')

chunks2 = [2, 4, 8, 16, 32]
hdf_lzf_times2 = []
hdf_gzip_times2 = []


ds19 = ff.create_dataset('data_2_chunked_lzf', dims, dtype='uint8', chunks=(2, 128, 128), compression='lzf')
ds20 = ff.create_dataset('data_2_chunked_gzip', dims, dtype='uint8', chunks=(2, 128, 128), compression='gzip')

ds22 = ff.create_dataset('data_4_chunked_lzf', dims, dtype='uint8', chunks=(4, 128, 128), compression='lzf')
ds23 = ff.create_dataset('data_4_chunked_gzip', dims, dtype='uint8', chunks=(4, 128, 128), compression='gzip')

ds25 = ff.create_dataset('data_8_chunked_lzf', dims, dtype='uint8', chunks=(8, 128, 128), compression='lzf')
ds26 = ff.create_dataset('data_8_chunked_gzip', dims, dtype='uint8', chunks=(8, 128, 128), compression='gzip')

ds28 = ff.create_dataset('data_16_chunked_lzf', dims, dtype='uint8', chunks=(16, 128, 128), compression='lzf')
ds29 = ff.create_dataset('data_16_chunked_gzip', dims, dtype='uint8', chunks=(16, 128, 128), compression='gzip')

ds31 = ff.create_dataset('data_32_chunked_lzf', dims, dtype='uint8', chunks=(32, 128, 128), compression='lzf')
ds32 = ff.create_dataset('data_32_chunked_gzip', dims, dtype='uint8', chunks=(32, 128, 128), compression='gzip')


print "Testing hdf write 2 chunk lzf compression"
hdf_lzf_times2.append(test_append_full_time_chunk(ds19, 2))

print "Testing hdf write 2 chunk gzip compression"
hdf_gzip_times2.append(test_append_full_time_chunk(ds20, 2))

print "Testing hdf write 4 chunk lzf compression"
hdf_lzf_times2.append(test_append_full_time_chunk(ds22, 4))

print "Testing hdf write 4 chunk gzip compression"
hdf_gzip_times2.append(test_append_full_time_chunk(ds23, 4))

print "Testing hdf write 8 chunk lzf compression"
hdf_lzf_times2.append(test_append_full_time_chunk(ds25, 8))

print "Testing hdf write 8 chunk gzip compression"
hdf_gzip_times2.append(test_append_full_time_chunk(ds26, 8))

print "Testing hdf write 16 chunk lzf compression"
hdf_lzf_times2.append(test_append_full_time_chunk(ds28, 16))

print "Testing hdf write 16 chunk gzip compression"
hdf_gzip_times2.append(test_append_full_time_chunk(ds29, 16))

print "Testing hdf write 32 chunk lzf compression"
hdf_lzf_times2.append(test_append_full_time_chunk(ds31, 32))

print "Testing hdf write 32 chunk gzip compression"
hdf_gzip_times2.append(test_append_full_time_chunk(ds32, 32))


out_fname = 'append_single_time_slice.png'
fig = plt.figure()
axis = fig.add_subplot(111)
axis.plot(chunks, hdf_lzf_times, 'r-o', label='lzf-compression')
axis.plot(chunks, hdf_gzip_times, 'g-o', label='gzip-compression')
plt.title('Appending 1 time slice sequentially')
plt.xlabel('Z-Chunk size')
plt.ylabel('Time elapsed (seconds)')
lgd = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 10})
plt.savefig(out_fname, bbox_extra_artists=(lgd,), bbox_inches='tight')

out_fname = 'append_multi_time_slice.png'
fig = plt.figure()
axis = fig.add_subplot(111)
axis.plot(chunks2, hdf_lzf_times2, 'r-o', label='lzf-compression')
axis.plot(chunks2, hdf_gzip_times2, 'g-o', label='gzip-compression')
plt.title('Appending multiple time slices at once.')
plt.xlabel('Z-Chunk size')
plt.ylabel('Time elapsed (seconds)')
lgd = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 10})
plt.savefig(out_fname, bbox_extra_artists=(lgd,), bbox_inches='tight')
