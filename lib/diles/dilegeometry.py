
from numpy import floor
from geojson import Polygon, Feature, Point, FeatureCollection

class dilegeometry(object):
	
	MAX_Z=10
	XSIZE=361
	YSIZE=181

	def __init__(self,z=0,x=0,y=0):
		
		self.z = z
		self.x = x
		self.y = y
		self.xSize = Dile.XSIZE
		self.ySize = Dile.YSIZE


	def asBoundingBox(self):
		
		bb=None
		sigma = 2**self.z

		#check x/y are in bound within the desired zoom  level
		if  self.x>=0 and self.x <= sigma-1  and self.y>=0 and self.y <= sigma-1 :

			#calculating the amount of lat/lon degrees in a tile
			delta_lat = 180/float(sigma)
			delta_lon = 360/float(sigma)

			#shifting (0,0) from upper left corner to center
			lat_max   = 90 -  delta_lat*self.y
			lon_min   = delta_lon*self.x - 180

			bb = {
				'lon_min':float(lon_min),
				'lon_max':float(delta_lon+lon_min),
				'lat_min':float(lat_max-delta_lat),
				'lat_max':float(lat_max)
			}

		return bb

	
	def asPolygon(self):
		
		bb=self.asBoundingBox()
		
		return Polygon([[
						(bb['lon_min'], bb['lat_min']), 
						(bb['lon_min'], bb['lat_max']), 
						(bb['lon_max'], bb['lat_max']), 
						(bb['lon_max'], bb['lat_min']),
						(bb['lon_min'], bb['lat_min'])
						]])

	
	def byZoomLonLat(self,zoom,lon,lat):
		
		x=0
		y=0
		
		try:

			# 1/sigma is the distance between each lat/lon datum at a certain lvl
			sigma   = 2**zoom

			# amount of degrees per tile
			dlat    = 180/float(sigma)
			dlon    = 360/float(sigma)

			# the floor rapresent an hard constraint
			# in the future a % of admittance could work better
			x = floor( (lon + 180)/float(dlon)  )
			y = floor( (lat - 90 )/float(-dlat) )


		except TypeError:
		
			print "wrong format provided for either x and/or y"
		
		else:

			self.z=zoom
			self.x=int(x)
			self.y=int(y)

	
	def asDocument(self):
		
		document= {
			"loc":Feature(geometry=self.asPolygon()),
			"z":self.z,
			"x":self.x,
			"y":self.y
		} 
		
		return document