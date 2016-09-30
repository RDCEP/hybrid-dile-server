from time import time

class Chrono(object):
	
	"""Chronometer class for testing pourpouses"""
	
	def __init__(self):
		self.t0 = 0
		self.t1 = 0
		self.times = []


	def start(self):
		self.t0 = time()


	def stop(self):
		self.t1 = time()

	def reset(self, string=''):
		if string != '':
			self.times.append({'time': self.t1 - self.t0, 'action': string})
		self.t0 = self.t1 = 0

	def secs(self):
		return self.t1 - self.t0

	def report(self):
		return self.times

	def formatted(self):

		 	hours, rem = divmod(self.t1 - self.t0, 3600)
			minutes, seconds = divmod(rem, 60)
			return "{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds)


	
