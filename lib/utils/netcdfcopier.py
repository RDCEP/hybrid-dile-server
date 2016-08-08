from netCDF4 import *
from numpy	 import ndarray
from sys 	 import getsizeof

class NetcdfCopier(object):
	"""create a copy of the netcdf, can exclude certain variables and/or dimensions"""

	# vbl : variables black list
	# dbl : dimensions black list
	# f   : format
	@staticmethod
	def copy(srcitem,dstitem,dbl=[],vbl=[],f="NETCDF4"):
		
		if type(srcitem) is str:
			
			try:
				src = Dataset(srcitem,"r")
			except:
				print "couldn't open the source file for the copy"
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
				print "couldn't open the destination file for the copy"
				raise
		else:
			try:
				dst = dstitem
				dst.dimensions.values()
			except:
				print "dst argument's type is not valid"

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

		if type(dstitem) is str:
			return dst