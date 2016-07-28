import numpy
from numpy import floor
from geojson import Polygon, Feature, Point, FeatureCollection
from netCDF4 import Dataset
import os
import pprint

class DileFactory(object):

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


class DileGeometry(object):
    MAX_Z=10
    XSIZE=361
    YSIZE=181

    def __init__(self,z=0,x=0,y=0):
        self.z=z
        self.x=x
        self.y=y
        self.xSize=Dile.XSIZE
        self.ySize=Dile.YSIZE

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
        return Polygon([[(bb['lon_min'], bb['lat_min']), (bb['lon_min'], bb['lat_max']), (bb['lon_max'], bb['lat_max']), (bb['lon_max'], bb['lat_min']),(bb['lon_min'], bb['lat_min'])]])

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

    def asDocument(self):
        document= {
            "loc":Feature(geometry=self.asPolygon()),
            "z":self.z,
            "x":self.x,
            "y":self.y
        } 
        return document

class Dile(DileGeometry):
    def __init__(self):
       self.uri=None   
       self.dimensions=None
       self.variable=None
       self.attributes=None

    def asDocument(self):
       document=super(Dile, self).asDocument()
       if self.uri is not None:
           document['uri']=self.uri
       return document

    # create an empty netcdf4 matching the dile
    def createNetCDF4(self):
       dirname="/tmp/"+str(self.z)+"/"+str(self.x)+"/"+str(self.y)+"/"
       try:
           os.makedirs(dirname)
       except:
           pass
       filename=dirname+str(self.z)+"_"+str(self.x)+"_"+str(self.y)+".nc"
       rootgrp = Dataset(filename, "w", format="NETCDF4")
       # add dimensions
       lat = rootgrp.createDimension("lat", DileGeometry.YSIZE)
       lon = rootgrp.createDimension("lon", DileGeometry.XSIZE)
       # add variables
       latitudes = rootgrp.createVariable("latitude","f4",("lat",))
       longitudes = rootgrp.createVariable("longitude","f4",("lon",))
       data = rootgrp.createVariable("data","f4",("lat","lon",))
       sigma = 2**self.z
       delta_lat = 180/float(sigma)
       delta_lon = 360/float(sigma)
       bb=self.asBoundingBox()
       lats =  numpy.arange(bb['lat_min'],bb['lat_max']-delta_lat,delta_lat)
       lons =  numpy.arange(bb['lon_min'],bb['lon_max']-delta_lon,delta_lon)
       latitudes[:] = lats
       longitudes[:] = lons
       # add attributes
       return filename

if __name__ == "__main__":
    dile=Dile()
    dile.byZoomLonLat(8,14.28,40.85)
    print dile.z
    print dile.x
    print dile.y
    bb=dile.asBoundingBox()
    print str(bb)
    feature=Feature(geometry=dile.asPolygon())
    feature_collection=FeatureCollection([feature])
    print str(feature_collection)
    print dile.createNetCDF4();
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(dile.asDocument())
