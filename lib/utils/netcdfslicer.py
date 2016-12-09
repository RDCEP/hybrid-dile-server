from netCDF4 import *
from diles.dilefactory		import DileFactory
from diles.dile				import Dile
from diles.netcdfgeometry	import NetcdfGeometry
from misc 					import ncOpen, getMD5, pathLeaf, printProgress
from numpy					import ndindex
from numpy.ma 				import MaskedArray
from time 					import time, strftime
from chrono 				import Chrono
from lukepathwalker 		import LukePathWalker

class NetcdfSlicer(object):
	
	"""docstring for Dataminer"""	

	def __init__(self, nc):

		self.rgrp  = nc


	def createDiles(self, dstpath, bb, zoom):

		df 	  = DileFactory()
		ng 	  = NetcdfGeometry()

		basename = pathLeaf(dstpath)

		# delimiters for the diles contained in the matrix
		indx, indy = ng.getDileIndexTable(bb,zoom)

		# information extracted from the netcdf (dimensions, variables and diles' coverage)
		dimensions 	= [d.name for d in self.rgrp.dimensions.values()]
		variables  	= [v for v in self.rgrp.variables.values() if v.name not in dimensions]
		diles		= df.fromBoundingBox(bb['lon_min'], bb['lat_min'], bb['lon_max'], bb['lat_max'],zoom)

		# calculating the number of iterations required, for printing purposes
		iter_len 	= 0
		for var in variables:
			iter_len += reduce(lambda x, y: x*y, var.shape[:-2])*len(diles)

		# x,y,z indices for printing purposes
		x = 0
		for var in variables:
			
			y = 0
			timeind  = None
			levelind = None

			try:
				timeind = var.dimensions.index('time')
			except:
				pass

			try:
				levelind = var.dimensions.index('level')
			except:
				pass

			for ind in ndindex(var.shape[:-2]):
				z = 0
				for dile in diles:
					
					indstr = []
					if timeind is not None: indstr.append(str(ind[timeind]))
					if levelind is not None: indstr.append(str(ind[levelind]))

					fname = dile.getFileName('dile_'+''.join([i+'_' for i in indstr]))
					fpath = ''.join([i+'/' for i in indstr])+dile.getRelativePath()

					path = dstpath+'/'+var.name+'/'+fpath+fname

					a = indy[dile.y]["min"]
					b = indy[dile.y]["max"]
					c = indx[dile.x]["min"]
					d = indx[dile.x]["max"]


					if isinstance(var[ind], MaskedArray):
						matrix = var[ind].data
					else:
						matrix = var[ind]
					
					attributes = {}
					for attr in var.ncattrs():
						attributes.update({attr:var.getncattr(attr)})

					dile.variable   = var.name
					dile.attributes = attributes

					if '_FillValue' in var.ncattrs():
						dile.createNetCDF4(path,matrix[a:b+1,c:d+1],var.dtype,var.getncattr('_FillValue'))
					else:
						dile.createNetCDF4(path,matrix[a:b+1,c:d+1])

					z += 1
					printProgress(x*(len(ind)*len(diles))+(y*len(diles)+z), iter_len, basename, fname)
					
				y += 1
			x += 1

			return iter_len

			


if __name__ == '__main__':
	
	timer = Chrono()
	ncg   = NetcdfGeometry()
	lpw   = LukePathWalker()

	mydir = "/sdiles/ubuntu/sdiles"
	myext = ["nc"] 

	paths = []
	for file in lpw.getDirectoryContent(mydir):
		if lpw.checkExtention(myext, file):
			paths.append(file)


	for i in range(len(paths)):
		
		name = pathLeaf(paths[i])
		
		timer.start()
		md5 = getMD5(paths[i])
		timer.stop()

		print i, ") md5 for ",name, " computed in: ", timer.formatted()
		
		src = ncOpen(paths[i], mode='r')
		
		bb  = ncg.getBoundingBox(src['lat'],src['lon'])
		z 	= ncg.getZoomLevel(scr['lat'],src['lon'])

		ncs = NetcdfSlicer(src)

		timer.reset()

		timer.start()
		ndiles = ncs.createDiles("/sdiles/ubuntu/diles/"+md5+"/"+name,bb,int(z))
		timer.stop()

		exit()


	'''
	print "computing md5 for ", fname, "..."
	timer.start()
	md5   = getMD5(path)
	timer.stop()
	print "md5 computed in: ", timer.formatted()
	
	src  = ncOpen(path, mode='r')
	bb = ncg.getBoundingBox(src['lat'],src['lon'])
	z  = ncg.getZoomLevel(src['lat'],src['lon'])

	ncs  = NetcdfSlicer(src)

	timer.reset()

	print "extracting data tiles..."
	timer.start()
	ndiles = ncs.createDiles("/sdiles/ubuntu/diles/"+md5+"/"+fname,bb,int(z))
	timer.stop()
	print chr(27) + "[2J" #escape sequence
	print ndiles, "created. task completed in: ", timer.formatted()
	'''



