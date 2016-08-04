from unitinspector	import UnitInspector
from netcdfcopier 	import NetcdfCopier
from netCDF4 import *

class standardizer(object):
	
	def __init__(self, srcpath, dstpath, file, mode='a'):

		self.__srcpath = srcpath
		self.__dstpath = dstpath
		self.__file = file
		self.__mode = mode
		self.__rgrp = None

		self.__blacklist = []

		self.__oldlat   = None # for rollback reasons
		self.__oldlon   = None # for rollback reasons
		self.__oldtime  = None # for rollback reasons
		self.__oldlev   = None # for rollback reasons




#	open the netcdf file
	def __netcdfOpen(self,path,file,mode):

		try:
			self.__rgrp = Dataset(path+file,mode)
		except:
			print "File couldn't be opened"

# rollback the changes to the dimensions' names
	def __rollback(self):

		if self.__oldlat is not None:
			self.__rgrp.renameDimension('lat',self.__oldlat)
			self.__rgrp.renameVariable('lat',self.__oldlat)

		if self.__oldlon is not None:
			self.__rgrp.renameDimension('lon',self.__oldlon)
			self.__rgrp.renameVariable('lon',self.__oldlon)

		if self.__oldtime is not None:
			self.__rgrp.renameDimension('time',self.__oldtime)
			self.__rgrp.renameVariable('time',self.__oldtime)

		if self.__oldlev is not None:
			self.__rgrp.renameDimension('level',self.__oldlevel)
			self.__rgrp.renameVariable('level',self.__oldlevel)

#	main function
	def createNetcdf(self):

		ncp  = NetcdfCopier()

		self.__netcdfOpen(self.__srcpath,self.__file,self.__mode)
		
		geo = self.__checkUnits()
		if geo:		
			# if there is any variable left
			if [v for v in self.__rgrp.variables.values() if not set(v.dimensions).intersection(self.__blacklist)]:
				srcpath = self.__srcpath+self.__file
				dstpath = self.__dstpath+self.__file
				dst = ncp.copy(srcpath,dstpath,dbl=self.__blacklist)
				
		
		self.__rollback()

		return dst

#	set the convention for the dimentions involved
	def __checkUnits(self):

		lat = False
		lon = False

		ui = unitinspector()

		for dimension in  self.__rgrp.dimensions.values():
			
			#if the dimension is present as variable as well (which it should)
			if ( dimension.name in [i.name for i in self.__rgrp.variables.values()]):
				
				#try to load the correspondent variable
				try:
					var = self.__rgrp.get_variables_by_attributes(name = dimension.name)[0]
				
				except IndexError:
					pass

				# otherwise change the name of the dimension and of the associated variable
				else:

					if ui.verifyLat(var):

						lat = True

						if var.name != 'lat':
							self.__oldlat = var.name
							self.__rgrp.renameDimension(var.name,'lat')
							self.__rgrp.renameVariable(var.name,'lat')			

					elif ui.verifyLon(var):

						lon = True

						if var.name != 'lon':
							self.__oldlon = var.name
							self.rgrp.renameDimension(var.name,'lon')
							self.rgrp.renameVariable(var.name,'lon')

					elif ui.verifyTime(var):

						if var.name != 'time':
							self.__oldtime = var.name
							self.rgrp.renameDimension(var.name,'time')
							self.rgrp.renameVariable(var.name,'time')

					elif ui.verifyLevel(var):

						if var.name != 'level':
							self.__oldlev = var.name
							self.rgrp.renameDimension(var.name,'level')
							self.rgrp.renameVariable(var.name,'level')

					else:
						self.__blacklist.append(var.name)	# if the dimension is not among lat/lon/time/lev
			else:
				self.__blacklist.append(dimension.name)		# if the dimension is has not a variable describing it
		
		return lat and lon


if __name__ == '__main__':
	
	std = standardizer("../../rawnc/", "../../testednc/", "AgMERRA_2010_tavg.nc")
	std.createNetcdf()