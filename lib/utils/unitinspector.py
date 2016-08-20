from cfunits import Units

"""
Class used to verify that the dimensions are cf-compliant
the attributes may be passed both as ncvariables or dictionaries.
In the latter case units value must be inside a dictionary filed named
attributes.

Ex:
	var = {
			...
			... 
			attributes : { units: ... }
			...
			...
	}

"""

class UnitInspector(object):

	def __init__(self, lat = None, lon = None, time = None, level = None):
		
		self.lat    = lat
		self.lon    = lon
		self.time   = time
		self.level  = level
		self.islat  = False
		self.islon  = False
		self.istime = False 
		self.islev  = False



	# naive way to understand if latitude was found in the file 
	def verifyLat(self,var):

			try:	u = Units(var.units).islatitude
			
			except:

				try: 
					u = Units(var["attributes"]["units"]).islatitude
				except:
					return False
				else:
					return u
			
			else:	return u

	# compliant way to understand if longitude was found in the file 
	def verifyLon(self,var):

			try: u = Units(var.units).islongitude
			
			except:

				try: 
					u = Units(var["attributes"]["units"]).islongitude
				except:
					return False
				else:
					return u
			
			else:	return u


	# compliant way to understand if time was found in the file 
	def verifyTime(self,var):

			try: 	u = Units(var.units).isreftime
			except:

				try: 
					u = Units(var["attributes"]["units"]).isreftime
				except:
					return False
				else:
					return u
			
			else:	return u

	# naive way to understand if time was found in the file
	def verifyLevel(self, var):
		
		# a more rigorous way should be implemented
		flag = False

		try:
			if   var.name == 'level':    flag = True
			elif var.name == 'lev':      flag = True
			elif var.name == 'altitude': flag = True
			elif var.name == 'alt':      flag = True
			elif var.name == 'Level':    flag = True
			elif var.name == 'Lev':      flag = True
			elif var.name == 'Alt':      flag = True
			elif var.name == 'altitude': flag = True
			elif var.name == 'z':        flag = True
			elif var.name == 'Z':        flag = True
			elif var.name == 'height':   flag = True
			elif var.name == 'Height':   flag = True
		
		except:
				try: 
					if   var["name"] == 'level':    flag = True
					elif var["name"] == 'lev':      flag = True
					elif var["name"] == 'altitude': flag = True
					elif var["name"] == 'alt':      flag = True
					elif var["name"] == 'Level':    flag = True
					elif var["name"] == 'Lev':      flag = True
					elif var["name"] == 'Alt':      flag = True
					elif var["name"] == 'altitude': flag = True
					elif var["name"] == 'z':        flag = True
					elif var["name"] == 'Z':        flag = True
					elif var["name"] == 'height':   flag = True
					elif var["name"] == 'Height':   flag = True
				
				except:
					return False
				
				else:
					return flag
			
		else:
			return flag

	#check if the given dimensions are cf-compliant and if requested, return a dictionary with the evaluation
	def dimensionsCheck(self, lat = None, lon  = None, time = None, level = None, report = False):

		if not lat:   lat   = self.lat
		if not lon:   lon   = self.lon
		if not time:  time  = self.time 
		if not level: level = self.level


		self.islat  = self.verifyLat(lat)
		self.islon  = self.verifyLon(lon)
		self.istime = self.verifyTime(time)
		self.islev  = self.verifyLevel(level)

		if report:
			
			status = {}
			if lat:   status["latitude"]  = self.islat
			if lon:   status["longitude"] = self.islon
			if time:  status["time"]	  = self.istime
			if level: status["level"]	  =	self.islev
			
			return status


if __name__ == '__main__':

	print "this is unit inspector!"

	# dimensions' variables metadata examples

	time = 	{
				'ndim': 1, 
				'name': 'time', 
				'dtype': 'float32', 
				'shape': [365], 
				'attributes': {'units': 'days since 1980-01-01 12:00:00'}, 
				'dimensions': ['time']
			}

	lat = 	{
				'ndim': 1, 
				'name': 'lat', 
				'dtype': 'float32', 
				'shape': [720], 
				'attributes': {'units': 'degrees_north'}, 
				'dimensions': ['lat']
			}

	lon =	{
				'ndim': 1, 
				'name': 'lon', 
				'dtype': 'float32', 
				'shape': [1440], 
				'attributes': {'units': 'degrees_east'}, 
				'dimensions': ['lon']
			}

	ui = unitinspector()

	print ui.dimensionsCheck(lat=lat,lon=lon,time=time,report=True)