import hashlib
import os
import json

from netCDF4 import *
from ntpath  import split, basename
from sys 	 import stdout


def printProgress (iteration, total, prefix = '', suffix = '',ratio = True, last = True, decimals = 2, barLength = 30):
	
	"""
	Call in a loop to create terminal progress bar
	@params:
		iteration   - Required  : current iteration (Int)
		total       - Required  : total iterations (Int)
		prefix      - Optional  : prefix string (Str)
		suffix      - Optional  : suffix string (Str)
	"""
	filledLength 	= int(round(barLength * iteration / float(total)))
	percents		= round(100.00 * (iteration / float(total)), decimals)
	bar 			= '#' * filledLength + '-' * (barLength - filledLength)

	if last:  mode = "\r"
	else:     mode = " "
	if ratio: rat  = '['+str(iteration)+'/'+str(total)+']'
	else:	  rat  = ''

	stdout.write('%s [%s] %.2f%s %s %s %s' % (prefix, bar, percents, '%', suffix, rat, mode ))
	stdout.flush()

def flush():
	stdout.flush()

def serialize(data, path, file):

	doc = {}
	doc['data'] = data

	with open(str(path)+str(file),'w') as f:
		json.dump(doc, f)


def retrive(path, file):

	with open(str(path)+str(file),'r') as f:
		doc = json.load(f)

		return doc['data']


def exists(path,file):

	if os.path.isfile(str(path)+str(file)):
		return True
	else:
		return False
	

def ncOpen(nc, mode = 'r'):
		
	try:
		net = Dataset(str(nc),mode)
	except:
		print "NetcdfOpener: couldn't open the netcdf file"
		return False


	return net


def ncStreamOpen(srcitem, dstitem):

		
	try:
		src = Dataset(str(srcitem),"r")
	except:
		print "couldn't open the source file"
		return False
	
	try:
		dst = Dataset(str(dstitem),"w")
	except:
		print "couldn't open the destination file"
		return False


	return src, dst


# create md5 for the file 
def getMD5(path):
	hash_md5 = hashlib.md5()
	with open(path, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)
	return hash_md5.hexdigest()


#finds the name of the file in a path string
def pathLeaf(path, ext=True):

	head, tail = split(path)
	
	if ext:
		return tail or basename(head)
	else:
		return tail[:tail.rfind('.')] or basename(head)[:basename(head).rfind('.')]