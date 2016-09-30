import os
import ntpath

class LukePathWalker(object):
	

	def getDirectoryContent(self,mydir):
		for root, dirs, files in os.walk(mydir):
			for file in files:
				yield os.path.join(root, file)

	
	def checkExtention(self, ext, filename):

		if type(ext) == str:
			
			if filename[-len(ext):] == ext:
				return True
			else:
				return False
		
		elif type(ext) == list:
			
			for e in ext:
				if filename[-len(e):] == e:
					return True
		
			return False

		else:
			print "type must be str or list!"




if __name__ == '__main__':
	
	lpw = LukePathWalker()

	mydir = "../../files/agm_files/"
	myext = ["nc","nc4"]

	result = []
	for file in lpw.getDirectoryContent(mydir):
		if lpw.checkExtention(myext, file):
			result.append(file)

	resultlat = sorted(result)
	resultlon = sorted(result,key = lambda i: int(i[-13:-9]))
	print resultlat[0]
	print resultlat[-1]
	print resultlon[0]
	print resultlon[-1]
