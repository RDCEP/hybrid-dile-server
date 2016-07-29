from numpy import arange

class dilefactory(object):

	# Returns one or more diles as a list given a bounding box
	# If zoom is not specified all diles of all zoomlevels are returned
	# If zoom is a range, returns all the zoomlevels in the range
	# If zoom is just one, returns one dile at the required zoomlevel
	@staticmethod
	def fromBoundingBox(lon_min, lat_min, lon_max, lat_max,zoom=None):
		pass

	# Returns one or more diles as a list given a point
	# If zoom is not specified all diles of all zoomlevels are returned
	# If zoom is a range, returns all the zoomlevels in the range
	# If zoom is just one, returns one dile at the required zoomlevel
	@staticmethod
	def fromPoint(lon,lat,zoom=None):
		pass

        # Returns one or more diles as the z,x,y of a tile (http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/)
        # It is used to know a dile list for a tile rendering
        @staticmethod
        def fromTile(z,x,y):
                pass
