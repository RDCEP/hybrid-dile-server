from netCDF4 import *
from diles.dilefactory	import DileFactory
from diles.dile			import Dile
from numpy				import ndindex
from numpy.ma 			import MaskedArray

class Dataminer(object):
	
	"""docstring for Dataminer"""
	
	def __init__(self):

		self.indx  = {}
		self.indy  = {}
		self.path  = None
		self.rgrp  = None
		self.diles = None

	def ncOpen(self,path,mode='r'):

		try:
			self.rgrp = Dataset(path,mode)
			self.path = path
		except:
			print "couldn't open the file: ", path
			exit()

	def getBoundingBox(self):

		bb = {}
		bb['lat_min'] = min(self.rgrp.variables["lat"])
		bb['lat_max'] = max(self.rgrp.variables["lat"])
		bb['lon_min'] = min(self.rgrp.variables["lon"])
		bb['lon_max'] = max(self.rgrp.variables["lon"])

		return bb

	def createIndexTable(self, z):

		bb = self.getBoundingBox()
		df = DileFactory()
		
		self.diles = df.fromBoundingBox(bb['lon_min'], bb['lat_min'], bb['lon_max'], bb['lat_max'],zoom=z)

		mindile = Dile()
		maxdile = Dile()

		y_min,x_min = mindile.byZoomLonLat(z,bb['lon_min'], bb['lat_max'])
		y_max,x_max = maxdile.byZoomLonLat(z,bb['lon_max'], bb['lat_min'])

		# y-y_min shifts the range of the indices from [min,max] to [0,max-min]
		# list(set(l)) create a list of unique elements from l

		y = list(set([dile.y for dile in self.diles ]))
		
		# -(i+1) is to reverse the index axis 
		for i in range(y_min, y_max - y_min + 1):
			
			self.indy[i] = {
								"min": (y[-(i+1)]-y_min)*(mindile.YSIZE-1), 
								"max": (y[-(i+1)]-y_min+1)*(mindile.YSIZE-1) #every dile has the same X/Y SIZE
							}
		

		x = list(set([dile.x for dile in self.diles ]))

		for i in range(x_min, x_max - x_min + 1):
			
			self.indx[i] = {
								"min": (x[i]-x_min)*(mindile.XSIZE-1),
								"max": (x[i]-x_min+1)*(mindile.XSIZE-1)
							}
		

	def createDiles(self,root):

		dimensions = [d.name for d in self.rgrp.dimensions.values()]
		variables  = [v for v in self.rgrp.variables.values() if v.name not in dimensions]

		for var in variables:
			for ind in ndindex(var.shape[:-2]):
				for dile in self.diles:
					
					indstr = ""
					for i in ind:
						indstr += str(i)+"/"

					path = root+"/"+var.name+"/"+indstr


					a = self.indy[dile.y]["min"]
					b = self.indy[dile.y]["max"]
					c = self.indx[dile.x]["min"]
					d = self.indx[dile.x]["max"]

					if isinstance(var[ind], MaskedArray):
						matrix = var[ind].data
					else:
						matrix = var[ind]
					


					if '_FillValue' in var.ncattrs():
						dile.createNetCDF4(path,matrix[a:b+1,c:d+1],var.dtype,var.getncattr('_FillValue'))
					else:
						dile.createNetCDF4(path,matrix[a:b+1,c:d+1])
					exit()

				


if __name__ == '__main__':
	
	dm = Dataminer()
	#ETOPO1_Ice_g_gmt4.nc
	#AgMERRA_2010_tavg.nc
	dm.ncOpen("../files/regrid_files/ETOPO1_Ice_g_gmt4.nc")
	dm.createIndexTable(4)
	dm.createDiles("results/ETOPO1_Ice_g_gmt4")

	print dm.indy
	#print list(dm.rgrp.variables["z"][0:181,0:361].data)
