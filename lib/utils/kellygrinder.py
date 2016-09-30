from netCDF4 				import *
from diles.dile 			import Dile
from utils.misc 			import ncOpen, serialize, retrive, exists, pathLeaf
from utils.gridfile 		import GridFile
from utils.cdoregridder		import CdoRegridder
from utils.serializer 		import Serializer
from utils.kellyconverter 	import KellyConverter
from utils.chrono 			import Chrono
from numpy 					import linspace
from urllib2 				import urlopen 
from os 					import path, makedirs, remove




class KellyGrinder(object):
	

	# check for a bbox what are the tiles available in agmerra
	def getUriList(self, bboxidxs, src):

		uri = []


		for latidx in range(bbidxs['latidx_min'],bbidxs['latidx_max']+1):
			for lonidx in range(bbidxs['lonidx_min'],bbidxs['lonidx_max']+1):
				try:
					url = "%s/%04d/clim_%04d_%04d.tile.nc4" %(src,latidx,latidx,lonidx) 
					urlopen(url)
				
				except:
					pass
				
				else:
					uri.append({'name': pathLeaf(url), 'uri':url, 'latidx':latidx, 'lonidx':lonidx})

		return uri

	
	# finds the closest match of a value in a vector, returing the correspondent index
	# where lambda is an anonymous function that impose the key of the min function
	def match(self, vector, element):
		return min(range(len(vector)), key=lambda i: abs(vector[i]-element))

	

	# function to download a file
	def downloadFile(self,url,dst):

		try:
			response = urlopen(url)
		except:
			print "couldn't reach ", url
			return False
		else:
			try:
				if not path.exists(dst): 
					makedirs(dst)
			except:
				print "couldn't create the destination folder for the file!"
				raise
				exit()
			else:
				CHUNK = 16 * 1024
				fname = pathLeaf(url)
				with open(dst+fname, 'wb') as f:
 					while True:
						chunk = response.read(CHUNK)
						if not chunk:
							break
						f.write(chunk)
					
					print url + "-->" + " Downloded!"
					return str(dst+fname)



	# function to create a grid file, used in case of cdo interpolation
	def createTileGrid(self, src, dst, latidx, lonidx, z):

		srcfile = ncOpen(src,"r")
		fname 	= pathLeaf(src,False)
		bbox 	= self.indices_to_bbox(latidx, lonidx)
		inc 	= 1/float(2**z)		
		xsize	= len(srcfile.variables['lon'][:])
		ysize	= len(srcfile.variables['lon'][:])
		xfirst	= bbox["lon_min"]
		yfirst	= bbox["lat_min"]
		xinc   	= inc
		yinc	= inc
		
		gf  = GridFile("latlon", xsize, ysize, xfirst, xinc, yfirst, yinc)

		fgrid = gf.createGrid(dst+fname+".grid")

		return str(dst+fname+".grid")



	# regridding via cdo 
	def regridTile(self, src, dst, fgrid, remap):

		fname 	= pathLeaf(src)
		cdo 	= CdoRegridder(src, dst+fname, fgrid)
		cdo.regridLocal(remap)
		return str(dst+fname)		


    
    # inizialization of a sdile
	def initSdile(self,dile,variable,dimensions,path,fname):


		nc = Dataset(path+fname,'w')

		bbox = dile.asBoundingBox()


		nc.createDimension("lat", dile.YSIZE)
		nc.createDimension("lon", dile.XSIZE)

		# add variables
		latitudes = nc.createVariable("lat","f4",("lat",))
		longitudes = nc.createVariable("lon","f4",("lon",))

		latitudes[:]  = linspace(bbox['lat_min'],bbox['lat_max'],dile.YSIZE, endpoint=True)
		longitudes[:] = linspace(bbox['lon_min'],bbox['lon_max'],dile.XSIZE, endpoint=True)

		latitudes.units  = 'degrees_north'
		latitudes.axis   = 'Y'
		longitudes.units = 'degrees_east'
		longitudes.axis  = 'X'

		for d in dimensions:
			nc.createDimension(d.name,d.shape[0])
			newdim = nc.createVariable(d.name,d.dtype,d.dimensions)
			newdim[:] = d[:]

			for attr in d.ncattrs():
				
				if attr != '_FillValue':
					newdim.setncattr(attr,d.getncattr(attr))

		if '_FillValue' in variable.ncattrs():				
			newvar = nc.createVariable(variable.name,variable.dtype,variable.dimensions, fill_value = variable.getncattr('_FillValue'))
		else:
			newvar = nc.createVariable(variable.name,variable.dtype,variable.dimensions, fill_value = 1e+20)

		for attr in variable.ncattrs():
				
			if attr != '_FillValue':
				newvar.setncattr(attr,variable.getncattr(attr))	

		return nc



	def createSdilesDict(self, basenc, dile, sdilesfolder):

		variables = [v for v in basenc.variables.values() if v.name not in [d.name for d in basenc.dimensions.values()]]
		sdiles = {}

		for v in variables:

			filename = 	("sdile_"+
						v.name+"_"+
						str(dile.z)+"_"+
						str(dile.y)+"_"+
						str(dile.x)+".nc")

			print filename

			if exists(sdilesfolder, filename):
				sdiles.update({v.name: Dataset(sdilesfolder+filename, mode='a',clobber = False)})
			else:
				d =  [d for d in basenc.variables.values() if d.name in v.dimensions and d.name not in ['lat','lon']]
				sdiles.update({v.name:self.initSdile(dile, v, d, sdilesfolder, filename)})

		return sdiles




if __name__ == '__main__':

	kg  = KellyGrinder()
	kc 	= KellyConverter()
	timer = Chrono()

	baselink 		= "http://users.rcc.uchicago.edu/~davidkelly999/agmerra.origgrid.2deg.tile"
	basefilelink 	= baselink + "/0004/clim_0004_0047.tile.nc4"
	sdilesfolder 	= "results/sdiles/"
	
	# basefile setup
	
	print "downloading base file..."
	timer.start()

	basefile 	= kg.downloadFile(basefilelink, "results/base/")
	basenc 		= ncOpen(basefile)
	basefolder 	= "results/"
	
	timer.stop()
	print "basefile downloaded in ", timer.formatted()

	timer.reset('basefile downloaded')

    # ---- loping part starts ---- #

    #inizialization
	dile = Dile(2,0,2)

	bbox = dile.asBoundingBox()		
	lats = linspace(bbox['lat_min'],bbox['lat_max'],dile.YSIZE, endpoint=True)
	lons = linspace(bbox['lon_min'],bbox['lon_max'],dile.XSIZE, endpoint=True)
	bboxidxs = kc.bbox_to_indices(bbox)


	# superdiles creation		
	print "creating super diles..."	
	timer.start()
	
	sdiles = kg.createSdilesDict(basenc, dile, sdilesfolder)

	timer.stop()
	print "super diles created in ", timer.formatted()

	timer.reset('sdiles created')


	# uris extraction	
	print "extracting uri list..."
	timer.start()
	
	urifolder 	= basefolder+"uris/"
	name 		= "dile_"+str(dile.z)+"_"+str(dile.y)+"_"+str(dile.x)+"_"+"urilist.json"
	
	if exists(urifolder,name):
		urls = retrive(urifolder,name)
	else:		
		urls = kg.getUriList(bboxidxs, baselink)
		serialize(urls,urifolder,name)

	timer.stop()
	print len(urls)," extracted in ", timer.formatted()

	timer.reset('uris extraction')


	# index initialization
	indexfolder = basefolder+"index/"
	name 		= "dile_"+str(dile.x)+"_"+str(dile.y)+"_"+str(dile.z)+"_"+"index.json"

	if exists(indexfolder, name):
		index = retrive(indexfolder, name)
	else:
		index = 0
		serialize(index, indexfolder, name)



	# sdiles armonization
	for i in range(index,len(urls)):

		src = kg.downloadFile(urls[i]['uri'], basefolder+"temp/raw/")
		if src:

			'''
			This parts use cdo to regrid the downloaded file into the dile grid

			zoom    = 2
			grid 	= kg.createTileGrid(src, basefolder+"grid/", urls[i]['latidx'], urls[i]['lonidx'], zoom)
			tile 	= kg.regridTile(src, basefolder+"regrid/", grid, "remapbic")
			nctile  = nco.ncOpen(tile)
			'''

			timer.start()
			
			nctile = ncOpen(src)
			
			latind = []
			for lat in nctile.variables['lat'][:]:
				latind.append(kg.match(lats,lat))

			lonind = []
			for lon in nctile.variables['lon'][:]:
				lonind.append(kg.match(lons,lon))



			dimensions = nctile.dimensions.values()
			variables  = [v for v in nctile.variables.values() if v.name not in [d.name for d in dimensions ]]

			for v in variables: 
				if len(v.shape) > 2:
					sdiles[v.name][v.name][...,latind,lonind] = nctile[v.name][...,:,:]
				else:
					sdiles[v.name][v.name][latind,lonind] = nctile[v.name][:,:]

			serialize(i, indexfolder, name)
			nctile.close()
			remove(src)

			timer.stop()

			print urls[i]['name']," elaboration completed. ", timer.formatted, " [",i+1,"/",len(urls),"]"

			timer.reset()



	# closing the super diles
	for key, value in sdiles.iteritems():
		value.close()
