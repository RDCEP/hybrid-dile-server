from netCDF4 import *
from numpy	 import ndarray
from sys 	 import getsizeof

class NetcdfCopier(object):
	
	"""create a copy of the netcdf, can exclude certain variables and/or dimensions"""

	# vbl : variables black list
	# dbl : dimensions black list
	# f   : format

	def copy(self,src,dst,dbl=[],vbl=[],f="NETCDF4"):
		
		# dimensions that aren't in the blacklist
		for dim in [d for d in src.dimensions.values() if d.name not in dbl]:
					
			if dim.isunlimited():
				dst.createDimension(dim.name,None)
			else:
				dst.createDimension(dim.name,dim.size)
		
		# variables that don't run on the blacklisted dimensions 
		#(set.intersection intersect the vector of dimensions with the blacklist)
		# and are not blacklisted

		for var in [v for v in src.variables.values() if not set(v.dimensions).intersection(dbl) and v.name not in vbl]:
			
			if '_FillValue' in var.ncattrs():				
				newvar = dst.createVariable(var.name,var.dtype,var.dimensions, fill_value =  var.getncattr('_FillValue'))
			else:
				newvar = dst.createVariable(var.name,var.dtype,var.dimensions)

			
			newvar[:] = var[:]

			for attr in var.ncattrs():
				
				if attr != '_FillValue':
					newvar.setncattr(attr,var.getncattr(attr))

		return dst