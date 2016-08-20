import json
import ntpath
from netCDF4 import *

class Analyzer(object):
	
	"""Class to read and organize informations about a netcdf"""
	
	def __init__(self):
		
		self.rgrp = None
		self.path = None
		self.vars = []
		self.dims = []
		self.glob = []



	def ncOpen(self,path,mode='r'):

		try:
			self.rgrp = Dataset(path,mode)
			self.path = path
		except:
			print "couldn't open the file: ", path
			exit()

	

	def pathLeaf(self):
		head, tail = ntpath.split(self.path)
		return tail or ntpath.basename(head)	

	

	def getVarInfo(self):

		for variable in self.rgrp.variables.values():

			dimensions = []

			for dim in variable.dimensions:
				dimensions.append(dim)

			attributes = {}	
			for attr in variable.ncattrs():
				attributes.update({str(attr):str(variable.getncattr(attr))})

			shapes = []
			for shape in variable.shape:
				shapes.append(shape)

			types = []
			index = (0,)
			for t in variable.dimensions:
				types.append(str(type(self.rgrp.variables[variable.name][index])))
				index = index + (0,)

			self.vars.append({
								"name": str(variable.name),
								"dtype":str(variable.dtype),
								"shape": shapes,
								"dimensions": dimensions,
								"types": types,
								"attributes": attributes
							})



	def getDimInfo(self):

		for dimension in self.rgrp.dimensions.values():
			self.dims.append({
								"name": dimension.name,
								"size": dimension.size
							})



	def getGlobInfo(self):

		for attribute in self.rgrp.ncattrs():
			self.glob.append({
								"name": str(attribute),
								"value": str(self.rgrp.getncattr(attribute))
							})


	
	def asJson(self, show = False):

		jdoc = {}

		if self.path:
			jdoc.update({"File": self.pathLeaf()})

		if self.dims:
			jdoc.update({"dimensions": self.dims})

		if self.vars:
			jdoc.update({"variables": self.vars})

		if self.glob:
			jdoc.update({"globals": self.glob})

		if show:
			print json.dumps(jdoc, indent = 2)

		return jdoc


	
	def ncScan(self, dimensions = True, variables = True, glob = True):

		if dimensions:
			try:
				self.getDimInfo()
			except:
				print "couldn't scan for dimensions"
				pass

		if variables:
			try: 
				self.getVarInfo()
			except:
				print "couldn't scan for variables"
				raise

		if glob:
			try:
				self.getGlobInfo()
			except:
				print "couldn't scan for global attributes"



if __name__ == '__main__':
	
	an = Analyzer()
	an.ncOpen("../../files/regrid_files/test.nc")
	an.ncScan(False,True,False)
	an.asJson(show = True)

	