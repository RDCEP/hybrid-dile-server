
import os
import pprint

from numpy 			import linspace
from numpy.ma 		import MaskedArray
from netCDF4 		import Dataset
from dilegeometry 	import DileGeometry

class Dile(DileGeometry):
	
	def __init__(self, z=0, y=0, x=0, variable=None, attributes=None):
	   
		self.variable 	= variable
		self.attributes = attributes

		super(Dile, self).__init__(z,y,x)


	def getFileName(self,base=''):

		return ( str(base)+
				 str(self.z)+'_'+
				 str(self.y)+'_'+
				 str(self.x)+'.nc' )


	# path must contain the extradimensional variables' indexes
	def getRelativePath(self,base=''):

		return ( str(base)+
				 str(self.z)+'/'+
				 str(self.y)+'/'+
				 str(self.x)+'/' )


	# create a netcdf4 matching the dile
	def createNetCDF4(self,path,matrix,dtype, fillvalue = None):

		#path example md5/varname/*time*/*level*/...

		dirname=self.getRelativePath(path)
		filename=dirname+self.getFileName()


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
		latitudes = rootgrp.createVariable("lat","f4",("lat",))
		longitudes = rootgrp.createVariable("lon","f4",("lon",))

		latitudes.units  = 'degrees_north'
		latitudes.axis   = 'Y'
		longitudes.units = 'degrees_east'
		longitudes.axis  = 'X'

		bb = self.asBoundingBox()
		
		lats =  linspace(bb['lat_min'],bb['lat_max'],self.YSIZE, endpoint=True)
		lons =  linspace(bb['lon_min'],bb['lon_max'],self.XSIZE, endpoint=True)

		latitudes[:] = lats
		longitudes[:] = lons
		
		if fillvalue:
			data = rootgrp.createVariable(self.variable,dtype,("lat","lon",),fill_value = fillvalue)
		else:
			data = rootgrp.createVariable("data",dtype,("lat","lon",))
		
		if isinstance(matrix, MaskedArray):
			data[:] = MaskedArray.copy(matrix)
		else:
			data[:] = matrix

		for attr in self.attributes:
			if attr != '_FillValue':
				data.setncattr(attr,self.attributes[attr])

		rootgrp.close()

		return filename



if __name__ == "__main__":

	dile=Dile()
	dile.byZoomLonLat(2, -99.713, 41.791)
	print dile.asBoundingBox()
	print dile.asDocument()
	print dile.z
	print dile.x
	print dile.y