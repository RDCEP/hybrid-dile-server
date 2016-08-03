from netCDF4 import *

class netcdfcopier(object):
	"""create a copy of the netcdf, can exclude certain variables and/or dimensions"""

	# vbl : variables black list
	# dbl : dimensions black list
	# f   : format
	@staticmethod
	def copy(srcpath,dstpath,dbl=[],vbl=[],f="NETCDF4"):
		
		try:
			src = Dataset(srcpath,"r")
		except:
			print "couldn't open the source file for the copy"
			raise

		try:
			dst = Dataset(dstpath,"w",f)
		except:
			print "couldn't open the destination file for the copy"
			raise

		# dimensions that aren't in the blacklist
		for dimension in [d for d in src.dimensions.values() if d.name not in dbl]:
			dst.createDimension(dimension.name,dimension.size)
		
		# variables that don't run on the blacklisted dimensions 
		#(set.intersection intersect the vector of dimensions with the blacklist)
		# and are not blacklisted
		for variable in [v for v in src.variables.values() if not set(v.dimensions).intersection(dbl) and v.name not in vbl]:
			
			newvar = dst.createVariable(variable.name,variable.dtype,variable.dimensions)
			newvar[:] = variable[:]

			for attribute in variable.ncattrs():
				newvar.setncattr(str(attribute),str(variable.getncattr(attribute)))

		src.close()

		return dst	
