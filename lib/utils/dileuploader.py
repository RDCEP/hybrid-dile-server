import boto
import boto.s3

import os
import sys

from lukepathwalker import LukePathWalker
from misc 	    	import pathLeaf, printProgress
from chrono 	    import Chrono

class DileUploader(object):

	MAX_SIZE  = 20 * 1000 * 1000
	PART_SIZE = 5  * 1000 * 1000
	
	"""used to upload the files contained in a folder, and its subfolders"""
	def __init__(self, idkeypath, secretkeypath):

		self.idkp   = idkeypath
		self.skp    = secretkeypath

		self.conn   = None
		self.bucket = None
		self.bname  = None


	def onConnect(self):

		with open(self.idkp) as myfile:
			id_access_key = myfile.read().replace('\n', '')

		with open(self.skp) as myfile:
			secret_access_key = myfile.read().replace('\n', '')

		print "connecting to s3"
		try:
			self.conn =  boto.connect_s3(id_access_key,secret_access_key)
		except:
			print "failed to connect!"
			return -1
		else:
			print "connected succesfully"


	def keyExists(self,path):
		
		# create a key to use as destination
                k = boto.s3.key.Key(self.bucket)
                # it will be set as the destination path
                k.key = path
		
		return k.exists()


	def selectBucket(self, bname):

		try:
			self.bucket = self.conn.get_bucket(bname)
			self.bname  = bname
		except:
			print 'bucket not found'
		else:
			print 'bucket fetched'


	def showFolders(self, prefix = ''):

		return list(self.bucket.list(prefix,'/'))



	#ext is the list of extentions of the file to select 
	#src is the source folder to traverse
	#dst select or create a path tree in the bucket of choice
	def onUpload(self, ext, src='',folder='', dst=''):

		lpw = LukePathWalker()

		files = []
		for file in lpw.getDirectoryContent(src+folder):
			if lpw.checkExtention(ext, file):
				files.append(file)

		n = 0 #for printing pourposes
		for fname in files:

			srcpath = fname
			# allows for custom path in the destination folder to be placed before the path
			dstpath = os.path.join(dst,fname[len(src):])
			# compute the size of the file
			fsize = os.path.getsize(srcpath)
			# create a key to use as destination
                        k = boto.s3.key.Key(self.bucket)
                        # it will be set as the destination path
                        k.key = dstpath

			if not self.KeyExists():

				# selection between single-part upload and multipart (in case is too big)
				if fsize > self.MAX_SIZE:
					mp = self.bucket.initiate_multipart_upload(dstpath)
					fp = open(srcpath,'rb')
					fpnum = 0

					while (fp.tell() < fsize):
						fpnum += 1
						# function to upload a file in chunks
						mp.upload_part_from_file(fp, fpnum, size=self.PART_SIZE)

					mp.complete_upload() # function to notify the completion of the multipart upload 

				else:	
					# uploads a file in its entirety
					k.set_contents_from_filename(srcpath)
			else:
				print "document already ingested"

			printProgress(n, len(files),"uploading on: "+self.bname, pathLeaf(fname))
			n += 1
		
		return len(files)


if __name__ == '__main__':

	idkeypath 		= '/home/ubuntu/.s3/AWS_ACCESS_KEY_ID'
	secretkeypath 	= '/home/ubuntu/.s3/AWS_SECRET_ACCESS_KEY'
	bucketname 		= 'edu-uchicago-rdcep-diles'
	
	src			= '/sdiles/ubuntu/diles'
	extensions 	= ['nc','nc4']
	
	timer 		= Chrono()	
	lpw 		= LukePathWalker()

	
	paths = []
	for file in lpw.getDirectoryContent(src):
		if lpw.checkExtention(extensions, file):
			paths.append(file)
			break
	
	print paths

	'''
	
	dup = DileUploader(idkeypath, secretkeypath)

	dup.onConnect()

	dup.selectBucket(bucketname)

	res  = dup.showFolders()

	timer.start()
	ndocs = dup.onUpload(extensions,src,'','')
	timer.stop()
	
	print ndocs, "documents ingested. task completed in: ", timer.formatted()
	'''