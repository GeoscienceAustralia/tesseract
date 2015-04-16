Basic Low Level API
===================

The AGDC Low Level API exposes data stored on disk at the lowest level. This implementation assumes data stored in HDF5 files containing 1 degree lat/lon spatial and 1 year temporal span.

Key files in this folder are:

  * index: This folder constains an abstraction of the database indexing system. 
  * tessera.py: This class abstracts the concept of a tile into an object containing dimensions and data. 
  * pixel_drill*.py: Different implementations of the pixel drill use case for different products. 


index
-----

Due to the regularity in the dimensions imposed by the multidimensional file format, the process of indexing can be hardcoded into functions that point to the data. This method provides an easy an efficient solution to indexing the files moving decisions on metadata storage and database model outside the API. 

HDF5 multidimensional files can contain arrays representing dimensional values of the contained data set. This feature is used to simplify the indexing system registering only dimensional ranges. For example, if each file contains a 1x1 degree spatial extent and 1 year of images, the indexing database will only know that if the requested data exists it must be in a series of files. A second step, will open files an retrieve the selected data.

Once an agreement is reached on the new database model, indexing can be done through it with a minimum impact to the Low Level API.


tessera.py
----------

Tessera represents the minimum unit of information of the Low Level API. This class represents the data, or portion of the data, contained in a single multidimensional file. 

A query that intercepts data contained in more than one file, will be represented as an array of Tessera objects.

The whole Low Level API idea builds upon this concept and implements fuctionalities to traverse through dimensions and process the data. 


pixel_drill*.py
---------------

This is an example of a function of the Low Level API that returns a JSON object containing the time series of a determined pixel for different products. This function is the one used in the "proof of concept" web application which wraps this function and exposes it following a RESTFul standards.

The procees followed to build the time series data is:

 1. Use the index to identify the files containing the requested data.
 2. Use the get_tesserae() function to create a collection of Tessera objects containing the requested pixel.
 3. Merge together all the Tessera objects into a Pandas Timeseries object.
 4. Serialise the Pandas Timeseries object into a JSON string and return it.

