from datetime 	import datetime
from geolocation import GeoLocation

class QueryBuilderMongo(object):
	
	"""class that builds queries for a mongodb database"""
	def __init__(self):
		
		self.query = {}
		self.projection = {}
		self.pipeline = {}


	def formatTime(self,time):

		if isinstance(time,datetime):
			return time
		elif isinstance(time,str):
			try:
				return datetime.strptime(time,"%Y-%m-%d-%H:%M:%S")
			except:
				raise Exception('Illegal argument')



	# can't be used with addTime
	def queryTimeRange(self, field, start, finish):
		
		try:
			query = { 
					field: {
						"$gte": self.formatTime(start),
						"$lt":  self.formatTime(finish)    			
					}
				}
		except:
			raise
		else:
			return query


	def queryRange(self,field, start, finish):

		query = {
					field: {
						"$gte": start,
						"$lt":  finish    			
					}		
			}

		return query


	def circToBB(self,lon,lat,radius,unit="kilometers"):

		loc = GeoLocation.from_degrees(lat,lon)
		sw, ne = loc.bounding_locations(radius,unit)
		bb = {
				'lon_min': sw.deg_lon,
				'lon_max': ne.deg_lon,
				'lat_min': sw.deg_lat,
				'lat_max': ne.deg_lat
			 }

		return bb


	def queryIntersectPoint(self, field, lon, lat):

		query = {
				field: { 
					"$geoIntersects" : { 
						"$geometry" : { "type": "Point", "coordinates": [float(lon),float(lat)]} 
					}
				}
			}

		return query


	def intersectFeature(self,field,feature):

		try:
			query = {
						field: {
								"$geoIntersects": {
									"geometry": feature["geometry"]			
								}
						}
			}
		except:
			return None
		else:
			return query
	
	def queryIntersectBbox(self, field, bb):

		query = {
				field: {
					"$geoIntersects": {
						"$geometry": {
							"type": "Polygon",
							"coordinates": [[
								[ float(bb['lon_min']), float(bb['lat_min']) ],
								[ float(bb['lon_min']), float(bb['lat_max']) ],
								[ float(bb['lon_max']), float(bb['lat_max']) ],
								[ float(bb['lon_max']), float(bb['lat_min']) ],
								[ float(bb['lon_min']), float(bb['lat_min']) ]
							]]
						}
					}
				}
			}

		return query


	def queryIntersectRadius(self,field, lon,lat,radius,unit="kilometers"):
		
		bb = self.circToBB(lon, lat, radius, unit)
		query = self.queryIntersectBbox(field, bb)
		return query


	def queryLogical(self,operator,vec):

		if operator.lower() in ['and', '&&', '&']:
			if len(vec) > 1:
				query = {"$and":vec}
			else:
				raise Exception("Invalid size ( expected at least 2 items got "+str(len(vec))+" )")

		elif operator.lower() in ['or', '||', '|']:
			if len(vec) > 1:
				query = {"$or":vec}
			else:
				raise Exception("Invalid size ( expected at least 2 items got "+str(len(vec))+" )")

		elif operator.lower() in ['not', '!', '!!']:
			if len(vec) == 1:
				query = {"$not":vec}
			else:
				raise Exception("Invalid size (expected 1 item got "+str(len(vec))+" )")

		elif operator.lower() in ['nor', '!|']:
			if len(vec) > 1:
				query = {"$nor":vec}
			else:
				raise Exception("Invalid size ( expected at least 2 items got "+str(len(vec))+" )")
		else:
			raise Exception("Invalid Operator")

		return query

# ------------- AGGREGATION (future development) ---------------- #

		def aggregateByField(self,fields):

			pass

# --------------------------------------------------------------- #


# -------------- OPERATIONAL ------------- #

	def addField(self,field):
		for key, value in field.iteritems():
			if key not in self.query:
				self.query[key] = value
			else:
				raise Exception('The key already exist')

	def addFields(self, fields):
		for field in fields:
			self.addField(field)


	def addProjection(self, proj):
		for key, value in proj.iteritems():
			if key not in self.projection:
				self.projection[key] = value
			else:
				raise Exception('The key already exist, use queryLogical()')

	def getQuery(self):
		return [self.query,self.projection]

# --------------------------------------- #

if __name__ == '__main__':
	
	qbm = QueryBuilderMongo()

	rng = qbm.queryTimeRange("time","2016-10-01-00:00:00","2016-10-03-00:00:00")
	pt  = qbm.queryIntersectPoint("loc.geometry", -135.0, 67.5)
	cir = qbm.queryIntersectRadius("loc.geometry", -135.0, 67.5, 20) 



	qbm.addField(rng)
	qbm.addField(cir)
	qbm.addProjection({"_id": 0, "url" : 1})
	print qbm.getQuery()