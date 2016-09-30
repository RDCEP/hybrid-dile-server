from os import path, makedirs


class GridFile(object):
	
	"""file rapresenting the interpolation grid for CDO"""
	
	def __init__(self, gridtype, xsize, ysize, xfirst, xinc, yfirst, yinc):

		self.gridtype 	= gridtype
		self.xsize		= xsize
		self.ysize		= ysize
		self.xfirst		= xfirst
		self.xinc		= xinc		
		self.yfirst		= yfirst
		self.yinc		= yinc


	def createGrid(self,fname):

		if not path.exists(path.dirname(fname)):
			try:
				makedirs(path.dirname(fname))
			except OSError as exc: # Guard against race condition
				if exc.errno != errno.EEXIST:
					raise
		with open(fname, "w") as f:
		
			f.write("gridtype = "+str(self.gridtype)+"\n")
			f.write("xsize = "+str(self.xsize)+"\n")
			f.write("ysize = "+str(self.ysize)+"\n")
			f.write("xfirst = "+str(self.xfirst)+"\n")
			f.write("xinc = "+str(self.xinc)+"\n")
			f.write("yfirst = "+str(self.yfirst)+"\n")
			f.write("yinc = "+str(self.yinc)+"\n")



		return fname