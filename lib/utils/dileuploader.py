import boto
import boto.s3

import os.path
import sys

from lukepathwalker import LukePathWalker
from misc 		  	import pathLeaf

class DileUploader(object):

	MAX_SIZE  = 20 * 1000 * 1000
	PART_SIZE = 5  * 1000 * 1000
	
	"""docstring for DileUploader"""
	def __init__(self, idkeypath, secretkeypath):

		self.idkp   = idkeypath
		self.skp    = secretkeypath

		self.conn   = None
		self.bucket = None
		self.bname 	= None



	def percentCB(self, complete, total):
		sys.stdout.write('.')
		sys.stdout.flush() 


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


	def selectBucket(self, bname):

		try:
			self.bucket = self.conn.get_bucket(bname)
			self.bname  = bname
		except:
			print 'bucket not found'
		else:
			print 'bucket fetched'

	#ext is the list of extentions of the file to select 
	#src is the source folder to traverse
	#dst select or create a path tree in the bucket of choice
	def onUpload(self, ext, src='',folder='', dst=''):

		lpw = LukePathWalker()

		print "building the folder-tree"
		files = []
		for file in lpw.getDirectoryContent(src+folder):
			if lpw.checkExtention(ext, file):
				files.append(file)
		print "folder tree completed"


		for fname in files:

			srcpath = fname
			dstpath = os.path.join(dst,fname[len(src):])

			print 'Uploading %s to Amazon S3 bucket %s' %\
					(pathLeaf(fname), self.bname)

			fsize = os.path.getsize(srcpath)

			if fsize > self.MAX_SIZE:
				print "multipart upload"
				mp = self.bucket.initiate_multipart_upload(dstpath)
				fp = open(srcpath,'rb')
				fpnum = 0

				while (fp.tell() < fsize):
					fpnum += 1
					print 'uploading part %i' %fpnum
					mp.upload_part_from_file(fp, fpnum, cb=percentCB, num_cb=10, size=self.PART_SIZE)

				mp.complete_upload()

			else:
				print "singlepart upload"
				k = boto.s3.key.Key(self.bucket)
				k.key = dstpath
				k.set_contents_from_filename(srcpath, cb=self.percentCB, num_cb = 10)


if __name__ == '__main__':

	idkeypath 	= '/home/ubuntu/.s3/AWS_ACCESS_KEY_ID'
	secretkeypath 	= '/home/ubuntu/.s3/AWS_SECRET_ACCESS_KEY'
	bucketname 	= 'edu-uchicago-rdcep-diles'
	src		= '/sdiles/ubuntu/diles'
	folder 		= '/cd8f4999ec88a2cc002e10fef858a2f3'
	extensions 	= ['nc','nc4']

	dup = DileUploader(idkeypath, secretkeypath)

	dup.onConnect()

	dup.selectBucket(bucketname)

	dup.onUpload(extensions,src,folder,'')
