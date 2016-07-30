import numpy
import os
import pprint

from netCDF4 import Dataset
from dilegeometry import dilegeometry


class dile(dilegeometry):
	
	def __init__(self,z=0,x=0,y=0):
	   
		self.uri = None
		self.dimensions = None
		self.variable = None
		self.attributes = None
		super(dile, self).__init__(z,x,y)

	
	def asDocument(self):
	   
		document=super(Dile, self).asDocument()
	
		if self.uri is not None:
			
			document['uri']=self.uri
			return document
		
		else: return -1


	# create an empty netcdf4 matching the dile
	def createNetCDF4(self):

		dirname="/tmp/"+str(self.z)+"/"+str(self.x)+"/"+str(self.y)+"/"
	   
		try:
			os.makedirs(dirname)
	   
		except:
			pass
	   
		filename=dirname+str(self.z)+"_"+str(self.x)+"_"+str(self.y)+".nc"

		rootgrp = Dataset(filename, "w", format="NETCDF4")
		
		# add dimensions
		lat = rootgrp.createDimension("lat", DileGeometry.YSIZE)
		lon = rootgrp.createDimension("lon", DileGeometry.XSIZE)
		
		# add variables
		latitudes = rootgrp.createVariable("latitude","f4",("lat",))
		longitudes = rootgrp.createVariable("longitude","f4",("lon",))
		data = rootgrp.createVariable("data","f4",("lat","lon",))
		
		bb = self.asBoundingBox()
		
		lats =  numpy.linspace(bb['lat_min'],bb['lat_max'],181, endpoint=True)
		lons =  numpy.linspace(bb['lon_min'],bb['lon_max'],361, endpoint=True)
		
		latitudes[:] = lats
		longitudes[:] = lons
		
		# add attributes		
		'''
		add attributes here
		'''

		return filename




if __name__ == "__main__":

	dile=dile()
	dile.byZoomLonLat(8,14.28,40.85)
	print dile.z
	print dile.x
	print dile.y
	bb=dile.asBoundingBox()

	print bb