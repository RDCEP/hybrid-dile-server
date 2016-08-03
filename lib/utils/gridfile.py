class gridfile(object):
	"""file rapresenting the interpolation grid for CDO"""
	
	def __init__(self, gridtype, xsize, ysize, xfirst, xinc, yfirst, yinc):

		self.gridtype 	= gridtype
		self.xsize		= xsize
		self.ysize		= ysize
		self.xfirst		= xfirst
		self.xinc		= xinc		
		self.yfirst		= yfirst
		self.yinc		= yinc

	def createGrid(self,path):

		try:
			file = open(path+"info.grid","w")
		except:
			print "couldn't create info.grid!"
		
		file.write("gridtype = "+str(self.gridtype)+"\n")
		file.write("xsize = "+str(self.xsize)+"\n")
		file.write("ysize = "+str(self.ysize)+"\n")
		file.write("xfirst = "+str(self.xfirst)+"\n")
		file.write("xinc = "+str(self.xinc)+"\n")
		file.write("yfirst = "+str(self.yfirst)+"\n")
		file.write("yinc = "+str(self.yinc)+"\n")

		file.close()

		return path+"info.grid"