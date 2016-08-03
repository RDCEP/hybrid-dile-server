from dile   import Dile
from pprint import pprint
from numpy  import array, floor


'''
	could be useful
		| | |
		V V V
'''

# Returns the sub-tree of a given dile up to "sublevels" level
# as a vector of dile objects
def fromSubTree(d, sublevels, vec):
	
	'''
	dile splitted in 4 regions:
		
		*--------*
 		|no | ne |
 		*--------*
 		|so | se |
 		*--------*

 	property of the quadtree:
 	the North-Ovest child x,y are
 	the double of the x,y of the father

	'''

	# if the current level is lower than the wanted one
	if d.z < sublevels:

		# with the said property, calculating the 4
		# children becomes a trivial task
		no = Dile(d.z+1, d.x*2, d.y*2) 
		ne = Dile(d.z+1, no.x, no.y+1)
		so = Dile(d.z+1, no.x+1, no.y)
		se = Dile(d.z+1, no.x+1, no.y+1)

		children = [no,ne,so,se]
		vec.extend(children)

		# at last we repeat the process for each children
		# since the function is recursive 
		#the final vector will be ordered
		# in a depth-first traversing fashion
		for child in children:
			fromSubTree(child, sublevels, vec)


	
class DileFactory(object):

	MAX_ZOOM = 24 # Currently (2016) google maps has a maximum zoom-level of 23
				  # precision at max zoom: 1/(16'777'216) degrees

	subTree = staticmethod(fromSubTree)
	
	# Returns one or more diles as a list given a bounding box
	# If zoom is not specified all diles of all zoomlevels are returned
	# If zoom is a range, returns all the zoomlevels in the range
	# If zoom is just one, returns one or more diles at the required zoomlevel
	@staticmethod
	def fromBoundingBox(lon_min, lat_min, lon_max, lat_max,zoom=None):

		try:
			zoom = sorted(zoom)

		except TypeError, te:

			if zoom is None:
				zoom = range(0,DileFactory.MAX_ZOOM)
			else:
				zoom = [zoom]

		vec = []

		# in order to avoid the boundary values a downscale
		# of the tiles' coords is required
		lat_min += 1e-12
		lat_max -= 1e-12
		lon_min += 1e-12
		lon_max -= 1e-12

		min_dile = Dile()
		max_dile = Dile()

		for z in zoom:

			#converting bb into tiles delimiters
			y_max,x_min = min_dile.byZoomLonLat(z,lon_min,lat_min)
			y_min,x_max = max_dile.byZoomLonLat(z,lon_max,lat_max)

			#the inversion of y_min <-> y_max is due to the
			#shifting of the center from the upper-left corner
			#in regard of the lat/lon tile model
			for i in range(int(x_min),int(x_max+1)):
					for j in range(int(y_min),int(y_max+1)):
						vec.append(Dile(z,i,j))

		return vec	


	# Returns one or more diles as a list given a point
	# If zoom is not specified all diles of all zoomlevels are returned
	# If zoom is a range, returns all the zoomlevels in the range
	# If zoom is just one, returns one dile at the required zoomlevel
	@staticmethod
	def fromPoint(lon,lat,zoom=None):
		
		try:
			zoom = sorted(zoom)

		except TypeError, te:
			
			if zoom is None:
				zoom = range(0,DileFactory.MAX_ZOOM)
			else:
				zoom = [zoom]

		vec = []

		for z in zoom:

			d = Dile()
			d.byZoomLonLat(z, lon, lat)
			vec.append(d)

		return vec

	# Returns one or more diles as the z,x,y of a tile (http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/)
	# It is used to know a dile list for a tile rendering
	@staticmethod
	def fromTile(z,x,y):
		
		'''
		further explainations needed
		'''
		pass

	


if __name__ == "__main__":

	fac = DileFactory()

	d = Dile(0,0,0)

	v1 = fac.fromBoundingBox(-180,-90,180,90,1)

	v2 = fac.fromPoint(40.85, 14.17)

	v3 = []
	fromSubTree(d, 2, v3)

	print "\nFrom boundingBox:\n"
	
	for item in v1:
		print "dile %d/%d/%d" %(item.z,item.x,item.y)

	print "\nFrom Point:\n"
	for item in v2:
		print "dile %d/%d/%d" %(item.z,item.x,item.y)

	print "\nFrom subTree:\n"
	for item in v3:
		print "dile %d/%d/%d" %(item.z,item.x,item.y)
