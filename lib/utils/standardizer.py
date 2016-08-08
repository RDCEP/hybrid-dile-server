from unitinspector	import UnitInspector
from netcdfcopier 	import NetcdfCopier
from shutil			import copyfile
from netCDF4		import *

class Standardizer(object):
	
	def __init__(self, forcecopy = True):

		self.__forcecopy  = forcecopy
		self.dimblacklist = []
		self.varblacklist = []

		self.__oldlat    = None  # for rollback reasons
		self.__oldlon    = None  # for rollback reasons
		self.__oldtime   = None  # for rollback reasons
		self.__oldlev 	 = None  # for rollback reasons
		self.__latscaled = False # for rollback reasons
		self.__lonscaled = False # for rollback reasons



#	rollback the changes to the dimensions' names
	def __rollbackNames(self,nc):

		if self.__oldlat is not None:
			nc.renameDimension('lat',self.__oldlat)
			nc.renameVariable('lat',self.__oldlat)

		if self.__oldlon is not None:
			nc.renameDimension('lon',self.__oldlon)
			nc.renameVariable('lon',self.__oldlon)

		if self.__oldtime is not None:
			nc.renameDimension('time',self.__oldtime)
			nc.renameVariable('time',self.__oldtime)

		if self.__oldlev is not None:
			nc.renameDimension('level',self.__oldlevel)
			nc.renameVariable('level',self.__oldlevel)

#	rollback the possible shifting of the grid values (lat,lon)
	def __rollbackGrid(self,nc):

		if self.__latscaled:
			nc.variables["lat"][:] += 90

		if self.__lonscaled:
			nc.variables["lon"][:] += 180

		'''
		Convention Reliant
		if nc.variables["lon"][0] < nc.variables["lon"][-1]:
			nc.variables["lon"][:] = sorted(nc.variables["lon"],reverse=True)

		if nc.variables["lat"][0] < nc.variables["lat"][-1]:
			nc.variables["lat"][:] = sorted(nc.variables["lat"],reverse=True)
		'''

	
# 	try to set the range of lat/lon properly if the values are 
#	in the range lat->[0:90], lon->[0:180] the result is ambiguous
	def __checkRange(self,nc):
		
		if max(nc.variables["lon"]) > 180:
			nc.variables["lon"][:] -= -180
			self.__lonscaled = True

		if max(nc.variables["lat"]) > 90:
			
			nc.variables["lat"][:] -= 90
			self.__latscaled = True
		
		'''
		if nc.variables["lon"][0] > nc.variables["lon"][-1]:
			nc.variables["lon"][:] = sorted(nc.variables["lon"])

		if nc.variables["lat"][0] > nc.variables["lat"][-1]:
			nc.variables["lat"][:] = sorted(nc.variables["lat"])
		'''


#	set the convention for the dimentions involved
	def __checkUnits(self,nc):

		lat = False
		lon = False

		ui = UnitInspector()

		for dimension in  nc.dimensions.values():

			#if the dimension is present as variable as well (which it should)
			if ( dimension.name in [i.name for i in nc.variables.values()]):
				
				#try to load the correspondent variable
				try:
					var = nc.get_variables_by_attributes(name = dimension.name)[0]
				
				except IndexError:
					pass

				# otherwise change the name of the dimension and of the associated variable
				else:

					if ui.verifyLat(var):
						lat = True

						if var.name != 'lat':
							self.__oldlat = var.name
							nc.renameDimension(var.name,'lat')
							nc.renameVariable(var.name,'lat')			

					elif ui.verifyLon(var):
						lon = True

						if var.name != 'lon':
							self.__oldlon = var.name
							nc.renameDimension(var.name,'lon')
							nc.renameVariable(var.name,'lon')

					elif ui.verifyTime(var):

						if var.name != 'time':
							self.__oldtime = var.name
							nc.renameDimension(var.name,'time')
							nc.renameVariable(var.name,'time')

					elif ui.verifyLevel(var):

						if var.name != 'level':
							self.__oldlev = var.name
							nc.renameDimension(var.name,'level')
							nc.renameVariable(var.name,'level')

					else:
						self.dimblacklist.append(var.name)	# if the dimension is not among lat/lon/time/lev
			else:
				self.dimblacklist.append(dimension.name)	# if the dimension is has not a variable describing it
		
		return lat and lon

#	append a set of attributes to lat lon to describe them better
	def __checkLatLonAttr(self,nc):		

		latrange = [min(nc.variables["lat"][:]),max(nc.variables["lat"][:])]
		lonrange = [min(nc.variables["lon"][:]),max(nc.variables["lon"][:])]

		nc.setncattr("Conventions","COARDS/CF-1.0")
		
		#Latitude
		nc.variables["lat"].setncattr("units","degrees_north")
		nc.variables["lat"].setncattr("long_name","latitude")
		nc.variables["lat"].setncattr("standard_name","latitude")
		nc.variables["lat"].setncattr("axis","Y")
		nc.variables["lat"].setncattr("actual_range",latrange)

		#Longitude
		nc.variables["lon"].setncattr("units","degrees_east")
		nc.variables["lon"].setncattr("long_name","longitude")
		nc.variables["lon"].setncattr("standard_name","longitude")
		nc.variables["lon"].setncattr("axis","X")
		nc.variables["lon"].setncattr("actual_range",lonrange)


#	main function
	def createNetcdf(self,srcitem,dstitem,f="NETCDF4"):

		ncp  = NetcdfCopier()
		dst  = None
		src  = None

		if type(srcitem) is str:
			
			try:
				src = Dataset(srcitem,"a")
			except:
				print "couldn't open the source file"
				raise
		else:
			try:
				src = srcitem
				src.dimensions.values()
			except:
				print "src argument's type is not valid"

		if type(dstitem) is str:
			
			try:
				dst = Dataset(dstitem,"w",f)
			except:
				print "couldn't open the destination file"
				raise
		else:
			try:
				dst = dstitem
				dst.dimensions.values()
			except:
				print "dst argument's type is not valid"


		geo = self.__checkUnits(src)
		
		# if the file is geolocalized
		if geo:
				self.__checkRange(src)
				self.__checkLatLonAttr(src)

				# if any dimension or variable as been blacklisted, a copy is required
				if self.dimblacklist or self.varblacklist:
					ncp.copy(src,dst,dbl=self.dimblacklist,vbl=self.varblacklist)
					self.__rollbackGrid(src)
					self.__rollbackNames(src)
					src.close()

					return dst

				# otherwise a simple copy of the file will do
				else:
					if self.__forcecopy:
						try:
							copyfile(src.filepath(),dst.filepath())
						except:
							try:
								copyfile(srcitem, dstitem)
							except:
								try:
									copyfile(src.filepath(), dstitem)
								except:
									try:
										copyfile(srcitem, dst.filepath())
									except:
										pass
					return src
		else:
			return None


if __name__ == '__main__':
	
	std = Standardizer()
	std.varblacklist.append("tavg")
	std.createNetcdf("../../files/raw_files/AgMERRA_2010_tavg.nc", "../../files/std_files/AgMERRA_2010_tavg.nc")
	