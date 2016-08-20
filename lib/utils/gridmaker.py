from diles.dilegeometry		import DileGeometry
from gridfile				import GridFile
from netCDF4				import Dataset

class GridMaker(object):
	
	"""
	Class that regrids a netcdf file generic latlon grid into
	a uniform grid ready to be sliced in diles	
	"""
	
	def __init__(self):

		self.grid = None


	def gridInit(self,srcpath, dstpath, z): 

		try:
			src = Dataset(srcpath,"r")
		except:
			print "couldn't open ", srcpath
			exit()


		min_dile = DileGeometry()
		max_dile = DileGeometry()

		lon_min = min(src.variables["lon"])
		lon_max = max(src.variables["lon"])
		lat_min = min(src.variables["lat"])
		lat_max = max(src.variables["lat"])


		#converting bb into tiles delimiters
		y_max,x_min = min_dile.byZoomLonLat(z,lon_min,lat_min)
		y_min,x_max = max_dile.byZoomLonLat(z,lon_max,lat_max)		

		bb_min = min_dile.asBoundingBox()

		increment = 1/float(2**z)

		# xsize/ysize calculated as the indices distance
		# adding +1 to consider the lower bound

		'''
		explanation of the size formula:

		problem: 
			retrive how many diles cover a certain bounding box
			then create a grid that represent the diles merged
			in one grid

		data:
			x_max -> the highest x index of the diles covering the bb
			x_min -> the lowest  "" "" ""
			y_max -> the highest y index of the diles covering the bb
			y_min -> the lowest  "" "" ""

			XSIZE -> the size of the x axis of a single dile grid
			YSIZE -> ""  ""  ""  ""  y ""  ""  ""  ""

		analysis:

			the distance between indices both for x and y is
			(x_max - x_min + 1)
			(y_max - y_min + 1)
			where the +1 is needed to take in account the min value

			the multiplication for the size provides the number of
			elements for each axis, but there's a catch:

			the size of a dile grid is 181x361, which means that the 
			borders are both included in the grid, consequentially,
			if we consider 2 adjacent diles, they will share 1 border.
			Logically speaking this is not an hard constraint, but when
			calculating the grid size, it must be taken in consideration.

			ex:

									|	|
									v   v
								*---*---*---*
								| a | b | c |
							  ->*---*---*---*
								| d | e | f |
								*---*---*---*

			along the x axis a,b and b,c share a common vertical edge
			along the y axis a,d and b,e and c,f shere a common horizontal edge.
			to obtain the correct size along the axis we must consider this edges
			only once, therefore number of the internal edges has to be subtracted 
			from the total number of elements of the grid. This number is equal to
			the number of the diles along that axis minus once, in the previous 
			example infact that number is 2.
			There we have it:
			Number of total elements of the grid along x axis:
			n_x  = (x_max - x_min +1)*Dile_x_size
			Number of internal edges:
			i_e_x = n_x - 1
			Number of elements of along the x axis:
			n_x - i_e_x =
			(x_max - x_min + 1)*dile_x_size - (x_max - x_min + 1) - 1 =
			(x_max - x_min + 1)*dile_x_size - x_max + x_min

		'''
		
		xsize	= (x_max - x_min + 1)*min_dile.XSIZE - x_max + x_min  #max_dile would be good as well
		ysize	= (y_max - y_min + 1)*min_dile.YSIZE - y_max + y_min 
		xfirst	= bb_min["lon_min"]
		yfirst	= bb_min["lat_min"]
		xinc   	= increment
		yinc	= increment

		gf = GridFile("lonlat", xsize, ysize, xfirst, xinc, yfirst, yinc)
		
		return gf.createGrid(dstpath)



if __name__ == '__main__':
	
	r = GridMaker()
	r.gridInit("../files/std_files/ETOPO1_Ice_g_gmt4.nc", "../files/grid_files/ETOPO1_Ice_g_gmt4.grid", 4)