import numpy
import os
import pprint

from netCDF4 import Dataset
from dilegeometry import DileGeometry

class Dile(DileGeometry):
	
	def __init__(self,z=0,x=0,y=0):
	   
		self.uri 		= None
		self.dimensions = None
		self.variable 	= None
		self.attributes = None

		super(Dile, self).__init__(z,x,y)

	
	def asDocument(self):
	   
		document=super(Dile, self).asDocument()
	
		if self.uri is not None:
			
			document['uri']=self.uri
			return document
		
		else: return -1


	# create a netcdf4 matching the dile
	def createNetCDF4(self,path,matrix,dtype, fillvalue = None):


		dirname=path+str(self.z)+"/"+str(self.x)+"/"+str(self.y)+"/"
		filename=dirname+"dile_"+str(self.z)+"_"+str(self.x)+"_"+str(self.y)+".nc"


		if not os.path.isfile(filename):
			if not os.path.exists(dirname):
				try:
					os.makedirs(dirname,0755)
				except:
					raise

		rootgrp = Dataset(filename, "w", format="NETCDF4")
		
		# add dimensions
		lat = rootgrp.createDimension("lat", DileGeometry.YSIZE)
		lon = rootgrp.createDimension("lon", DileGeometry.XSIZE)
		
		# add variables
		latitudes = rootgrp.createVariable("latitude","f4",("lat",))
		longitudes = rootgrp.createVariable("longitude","f4",("lon",))

		latitudes.units  = 'degrees_north'
		latitudes.axis   = 'Y'
		longitudes.units = 'degrees_east'
		longitudes.axis  = 'X'
		
		if fillvalue:
			data = rootgrp.createVariable("data",dtype,("lat","lon",),fill_value = fillvalue)
		else:
			data = rootgrp.createVariable("data",dtype,("lat","lon",))
		
		bb = self.asBoundingBox()
		
		lats =  numpy.linspace(bb['lat_min'],bb['lat_max'],181, endpoint=True)
		lons =  numpy.linspace(bb['lon_min'],bb['lon_max'],361, endpoint=True)
		
		latitudes[:] = lats
		longitudes[:] = lons
		data[:] = matrix
		
		# add attributes		
		'''
		add attributes here
		'''

		rootgrp.close()

		return filename



if __name__ == "__main__":

	dile=dile()
	dile.byZoomLonLat(8,14.28,40.85)
	print dile.z
	print dile.x
	print dile.y
	bb=dile.asBoundingBox()

	print bb