from diles.dilegeometry		import DileGeometry
from gridfile				import GridFile
from netCDF4				import Dataset

class GridMaker(object):
	
	"""
	Class that regrids a netcdf file generic latlon grid into
	a uniform grid ready to be sliced in diles	
	"""
	
	def __init__(self, src, dst, z):
		
		self.src = src
		self.dst = dst
		self.z   = z


		def gridInit(self): 

		try:
			src = Dataset(self.src,"a")
		except:
			print "couldn't open ", self.src


		min_dile = DileGeometry()
		max_dile = DileGeometry()

		lon_min = min(src.variables["lon"])
		lon_max = max(src.variables["lon"])
		lat_min = min(src.variables["lat"])
		lat_max = max(src.variables["lat"])


		#converting bb into tiles delimiters
		y_max,x_min = min_dile.byZoomLonLat(self.z,lon_min,lat_min)
		y_min,x_max = max_dile.byZoomLonLat(self.z,lon_max,lat_max)		

		bb_min = min_dile.asBoundingBox()

		increment = 1/float(2**self.z)

		# xsize/ysize calculated as the indices distance
		# adding +1 to consider the lower bound
		xsize	= (x_max - x_min + 1)*min_dile.XSIZE #max_dile would be good as well
		ysize	= (y_max - y_min + 1)*min_dile.YSIZE
		xfirst	= bb_min["lon_min"]
		yfirst	= bb_min["lat_min"]
		xinc   	= increment
		yinc	= increment

		gf = GridFile("lonlat", xsize, ysize, xfirst, xinc, yfirst, yinc)
		gf.createGrid(self.dst)



if __name__ == '__main__':
	
	r = GridMaker("../testednc/AgMERRA_2010_tavg.nc", " ", 2)
	r.gridInit()