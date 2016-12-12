import boto
import boto.s3
from   misc import printProgress, pathLeaf

idkeypath 		= '/home/ubuntu/.s3/AWS_ACCESS_KEY_ID'
secretkeypath 	= '/home/ubuntu/.s3/AWS_SECRET_ACCESS_KEY'
bucketname 		= 'edu-uchicago-rdcep-diles'
folder          = ''

with open(idkeypath) as myfile:
	id_access_key = myfile.read().replace('\n', '')

with open(secretkeypath) as myfile:
	secret_access_key = myfile.read().replace('\n', '')

print "connecting to s3"
try:
	conn =  boto.connect_s3(id_access_key,secret_access_key)
except:
	print "failed to connect!"
	exit()
else:
	print "connected succesfully"

bucket = conn.get_bucket(bucketname)


keys = bucket.list(prefix = folder)


for key in keys:
	key.delete()