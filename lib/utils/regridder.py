from fabric.api				import run,local
from ..diles.dilegeometry	import dilegeometry
from gridfile				import gridfile
from netCDF4				import Dataset

class regridder(object):
	
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
			src = Dataset(self.src,"w")
		except:
			print "couldn't open ", self.src


		
		min_dile = dilegeometry()
		max_dile = dilegeometry()

		#assuming the vectors are ordered
		lon_min = src.variables["lon"][0]
		lon_max = src.variables["lon"][-1]
		lat_min = src.variables["lat"][0]
		lat_max = src.variables["lat"][-1]

		#converting bb into tiles delimiters
		y_max,x_min = min_dile.byZoomLonLat(self.z,lon_min,lat_min)
		y_min,x_max = max_dile.byZoomLonLat(self.z,lon_max,lat_max)		

		bb_min = min_dile.asBoundingBox()

		increment = 1/float(2**z)

		xsize	= (x_max - x_min)*361
		ysize	= (y_max - y_min)*181
		xfirst	= bb_min["lon_min"]
		yfirst	= bb_min["lat_min"]
		xinc   	= increment
		xync	= increment

		gf = gridfile("lonlat", xsize, ysize, xfirst, xinc, yfirst, yinc)
		gf.createGrid("")


if __name__ == '__main__':
	
	r = regridder("../../rawnc/", " ", 2)
	r.gridInit()