from numpy import floor


class Dile(object):

    def __init__(self,z=0,x=0,y=0):
        self.z=z
        self.x=x
        self.y=y
        self.xSize=361
        self.ySize=181

    def asBoundigBox(self):
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
                x = [ floor( (i + 180)/float(dlon)  ) for i in lon ]
                y = [ floor( (j - 90 )/float(-dlat) ) for j in lat ]

                self.x=int(x)
		self.y=int(y)

        except TypeError:
		
		try:
                        x = floor( (lon + 180)/float(dlon)  )
                        y = floor( (lat - 90 )/float(-dlat) )
			
		except:
			print "wrong format provided for either x and/or y"
	                        
        self.z=zoom
        self.x=int(x)
        self.y=int(y)

if __name__ == "__main__":
    dile=Dile()
    dile.byZoomLonLat(8,14.28,40.85)
    print dile.z
    print dile.x
    print dile.y
    bb=dile.asBoundigBox()
    print str(bb)
