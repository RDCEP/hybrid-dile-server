from netCDF4 		import *
from dile 	 		import DileGeometry
from dilefactory 	import DileFactory
from numpy 			import absolute,floor,log2

class NetcdfGeometry(object):


	def getBoundingBox(self,lat,lon):
		
		bb = {}
		bb['lat_min'] = min(lat)
		bb['lat_max'] = max(lat)
		bb['lon_min'] = min(lon)
		bb['lon_max'] = max(lon)

		return bb

	def getMinDile(self, bb, z):
		
		mindile = DileGeometry()
		lon = bb['lon_min'] + 1e-12
		lat = bb['lat_max'] - 1e-12
		mindile.byZoomLonLat(z, lon, lat)
		return mindile

	def getMaxDile(self, bb, z):

		maxdile = DileGeometry()
		lon = bb['lon_max'] - 1e-12
		lat = bb['lat_min'] + 1e-12
		maxdile.byZoomLonLat(z,lon, lat)
		return maxdile


	def getDileIndexTable(self, bb, z):		

		mind = self.getMinDile(bb,z)
		maxd = self.getMaxDile(bb,z)
		indx = {}
		indy = {}

		x = range(mind.x,maxd.x+1)

		for i in x:
			indx[i] = 	{
							"min": (i - mind.x)*(mind.XSIZE-1),
							"max": (i - mind.x+1)*(mind.XSIZE-1)
						}

		y = range(mind.y,maxd.y+1)

		for i in y:
			indy[i] = 	{
							"min": (i - mind.y)*(mind.YSIZE-1),
							"max": (i - mind.y+1)*(mind.YSIZE-1)
						}

		return indx, indy

	
	def getZoomLevel(self,lat,lon):
		

		if len(lat) > 1  and len(lon) > 1:

				#compute the difference between the first/last two elements
				lat_diff1  = absolute(lat[0]-lat[1])
				lat_diff2  = absolute(lat[-1]-lat[-2])

				lon_diff1  = absolute(lon[0]-lon[1])
				lon_diff2  = absolute(lon[-1]-lon[-2])

				v1         = absolute(lat_diff1 - lat_diff2)
				v2         = absolute(lon_diff1 - lon_diff2)

				#if the diff is reasonably small the distance is considered uniform
				if v1 < 10e-6 and v2 < 10e-6:

						#the floor is needed to downscale the data (conservative)
						#in the future a delta could be used to adjust the zoom level
						#according to a certain level of precision

						return floor( ( -log2(lat_diff1) -log2(lon_diff1) )/2 )
				else:
						print "distance isn't uniform, can't determine z!"
		else:
				print "Not enough values for Latitude and/or Longitude"

	

if __name__ == '__main__':
	
	ncg = NetcdfGeometry()

	bb = {}
	bb['lat_min'] = -90
	bb['lat_max'] =  90
	bb['lon_min'] = -180
	bb['lon_max'] =  180

	z = 2

	x,y = ncg.getDileIndexTable(bb,z)

	print x
	print y

