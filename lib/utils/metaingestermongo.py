from netCDF4 				import *
from pymongo 				import MongoClient
from diles.dilefactory		import DileFactory
from diles.dile				import Dile
from diles.netcdfgeometry	import NetcdfGeometry
from utils.misc 			import ncOpen, pathLeaf,getMD5, printProgress
from numpy 					import ndindex
from datetime 				import datetime
from utils.chrono 			import Chrono

class MetaIngesterMongo(object):

	def __init__(self, nc):

		self.client = None
		self.entry  = None
		self.rgrp   = nc


	def onConnect(self, dbname, collection, host = 'localhost', port = 27017):

		self.client = MongoClient(host,port)
		db 			= self.client[dbname]
		self.entry	= db[collection]


	def onInsert(self, docs):
		if type(docs) == dict:
			self.entry.insert_one(docs)
		else:
			self.entry.insert_many(docs)

	def onIngest(self, srcpath, dstpath, bb, zoom):

		df = DileFactory()
		ng = NetcdfGeometry()

		basename = pathLeaf(srcpath)

		dimensions  = [d.name for d in self.rgrp.dimensions.values()]
		variables   = [v for v in self.rgrp.variables.values() if v.name not in dimensions]
		diles 		= df.fromBoundingBox(bb['lon_min'], bb['lat_min'], bb['lon_max'], bb['lat_max'],zoom)

		dates = None

		try:
			dates = num2date(rgrp['time'][:],rgrp['time'].units)
		except:
			pass

		# calculating the number of iterations required, for printing purposes
		iter_len 	= 0
		for var in variables:
			iter_len += reduce(lambda x, y: x*y, var.shape[:-2])*len(diles)

		x = 0
		for var in variables:
			
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

			y = 0
			for ind in ndindex(var.shape[:-2]):
				
				z = 0
				for dile in diles:
					
					docurl = dstpath
					item = dile.asDocument()

					indstr = []
					if timeind is not None:
						item['time'] = dates[ind[timeind]]
						indstr.append(str(ind[timeind]))

					if levelind is not None:
						item['level'] = ind[levelind]
						indstr.append(str(ind[levelind]))

					docurl += ''.join([i+'/' for i in indstr])
					docurl += dile.getRelativePath()
					fname  =  dile.getFileName('dile_'+''.join([i+'_' for i in indstr]))
					docurl += fname
												
					item['md5']   		= md5
					item['variable'] 	= var.name
					item['attributes'] 	= [{str(key): str(var.getncattr(key))} for key in var.ncattrs()]
					item['uri'] 		= docurl
					item['source'] 		= basename
					item['zoom'] 		= zoom
					item['cdate'] 		= datetime.now()

					
					self.onInsert(item)
					z += 1
					printProgress(x*(len(ind)*len(diles))+(y*len(diles)+z), iter_len, basename, fname)
				y += 1
			x += 1

			return iter_len

	
	def onClose(self):
		self.client.close()



if __name__ == '__main__':
	
	ng    = NetcdfGeometry()
	df    = DileFactory()
	timer = Chrono()

	path  = "results/sdiles/sdile_tasmax_2_0_0.nc"
	fname = pathLeaf(path,False)
	

	print "computing md5 for ", fname, "..."
	timer.start()
	md5   = getMD5(path)
	timer.stop()
	print "md5 computed in: ", timer.formatted()
	
	rgrp  = ncOpen(path, mode='r')
	bb 	  = ng.getBoundingBox(rgrp['lat'],rgrp['lon'])
	zoom  = ng.getZoomLevel(rgrp['lat'], rgrp['lon'])

	mim = MetaIngesterMongo(rgrp)

	url   = " http://s3.amazonaws.com/edu-uchicago-rdcep-diles/"
	url   += str(md5)+'/'+str(fname)+'/'

	mim.onConnect('test', 'diles')

	timer.reset()

	print "ingesting metadata..."
	timer.start()
	ndocs = mim.onIngest(path, url, bb, zoom)
	timer.stop()

	mim.onClose()
	rgrp.close()
	
	print chr(27) + "[2J" #escape sequence
	print ndocs, "documents ingested. task completed in: ", timer.formatted()
