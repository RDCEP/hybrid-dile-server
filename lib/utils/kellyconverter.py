

class KellyConverter(object):
	
	tdelta = 120

	# latidx to lat
	def min_lat(self, latidx):
		return 90 - ((self.tdelta * latidx) / 60)

	
	# lonidx to lon
	def min_lon(self, lonidx):
		return -180 + (self.tdelta * lonidx / 60)

	
	# lat to latidx
	def min_latidx(self, lat):
		return (90-lat)*60/self.tdelta

	
	# lon to lonidx
	def min_lonidx(self, lon):
		return (60*(lon+180)/self.tdelta)

	
	def bbox_to_indices(self, bbox):
		
		minlonidx=self.min_lonidx(bbox['lon_min'])
		maxlonidx=self.min_lonidx(bbox['lon_max'])
		
		
		if minlonidx > maxlonidx:
			#print "switching lonidx!"
			temp=minlonidx
			minlonidx=maxlonidx
			maxlonidx=temp
	
		minlatidx=self.min_latidx(bbox['lat_min'])
		maxlatidx=self.min_latidx(bbox['lat_max'])
		
		
		if minlatidx > maxlatidx:
			#print "switching latidx!"
			temp=minlatidx
			minlatidx=maxlatidx
			maxlatidx=temp    
		
		return 	{ 
					"latidx_min": int(minlatidx),
					"latidx_max": int(maxlatidx),
					"lonidx_min": int(minlonidx),
					"lonidx_max": int(maxlonidx)
				}

	
	def indices_to_bbox(self, latidx, lonidx):
		
		minlon=self.min_lon(lonidx)
		maxlon=minlon-2
		

		
		if minlon > maxlon:
			#print "switching lon!"
			temp=minlon
			minlon=maxlon
			maxlon=temp
		

		minlat=self.min_lat(latidx)
		maxlat=minlat+2
		
		
		if minlat > maxlat:
			#print "switching lat!"
			temp=minlat
			minlat=maxlat
			maxlat=temp
		

		return 	{
					"lat_min":minlat,
					"lat_max":maxlat,
					"lon_min":minlon,
					"lon_max":maxlon
				}


if __name__ == '__main__':
	
	kc = KellyConverter()

	lon = -42.18
	lat = 76.99

	print "lat_id: ", kc.min_latidx(lat)
	print "lon_id: ", kc.min_lonidx(lon)
