#"!/usr/bin/python
# Pythonic abstraction layer for Nonolith Connect's RESTful API.
# Released under the terms of the GNU GPLv3+
# (C) 2012 Nonolith Labs, LLC
# Authors:
#   Ian Daniher 

import httplib, atexit, urllib, json

class CEE:

	def __init__(self, devID = "com.nonolithlabs.cee*"):
		""" Starts an HTTP connection, determines the target device ID, and starts capture."""
		self.connection = httplib.HTTPConnection("localhost:9003")
		atexit.register(self.onClose)

		if devID == "com.nonolithlabs.cee*":
			self.devID = devID

		elif devID:
			self.connection.request("GET", "/rest/v1/devices/")
			response = json.loads(self.connection.getresponse().read())
			if response.keys()[0] == devID:
				self.devID = devID
			elif response.keys()[0] == '':
				raise Exception('No devices found.')
			elif type(devID) == int:
				try:
					self.devID = response.keys()[devID]
				except:
					raise Exception('Device index invalid.')

		options = {"capture":"on"}
		options = urllib.urlencode(options)
		headers = {"Content-Type": "application/x-www-form-urlencoded"}
		self.connection.request("POST", "/rest/v1/devices/%s" % self.devID, options, headers)
		self.connection.getresponse()

	def onClose(self):
		""" Stop capturing and close the HTTP connection."""
		options = {"capture":"off"}
		options = urllib.urlencode(options)
		headers = {"Content-Type": "application/x-www-form-urlencoded"}
		self.connection.request("POST", "/rest/v1/devices/%s" % self.devID, options, headers)
		self.connection.getresponse()
		self.connection.close()

	def getOutput(self, channel = "a"):
		""" Return a dictionary containing the output state of a given channel."""
		self.connection.request("GET", "/rest/v1/devices/%s/%s/output" % (self.devID, channel))
		return dict(json.loads(self.connection.getresponse().read()))

	def setOutput(self, channel = "a", stream = "d", value = 0, wave="constant", amplitude = None, frequency = 0, relPhase = 1, phase = 0):
		""" Set the output state for a given channel.
			'stream' can be 'v' to set voltage, 'i' to set current, or 'd' for high impedance mode.
			'value' is an number either in volts or milliamps determining the target value in DC mode or the center value in AC mode.
			'wave' can be either 'constant,' 'triangle,' 'square,' or 'sine.'
			The following parameters only have meaning when 'wave' is not constant:
				'amplitude' determines the maximum offset from center.
				'frequency' is the cycles per second.
				'relPhase' determines whether the starting value is based off of the previous output setting to provide seamless change in frequency.
				'phase' is the phase offset in seconds from the beginning of the stream (relPhase=0) or from the previous source (relPhase=1)."""
		if wave == "constant":
			options = {"mode": stream, "value": value}
		elif wave in ["square", "triangle", "sine"]:
			options = {"mode": stream, "value": value, "wave": wave, "amplitude": amplitude, "frequency": frequency, "relPhase": relPhase, "phase": phase}
		else:
			raise Exception('Invalid option for "wave"')
		options = urllib.urlencode(options)
		headers = {"Content-Type": "application/x-www-form-urlencoded"}
		self.connection.request("POST", "/rest/v1/devices/%s/%s/output" % (self.devID, channel),  options, headers)
		return json.loads(self.connection.getresponse().read())

	def getInput(self, channel = "a", resample = .01, count = 1):
		""" Returns a pair of list indicating the measured state of the specified channel.
			The first list is measured voltage, the second list is measured current.
			Each list contains 'count' samples, averaged over 'resample' seconds, separated by 'resample' seconds."""
		options = {"resample":resample, "count":count, "header":0}
		options = "?" + urllib.urlencode(options)
		self.connection.request("GET", "/rest/v1/devices/%s/%s/input" % (self.devID, channel) + options)
		values = [[float(item) for item in item.split(',')] 
			for item in self.connection.getresponse().read().split('\n') 
			if item != '']
		return map(list, zip(*values))

if __name__ == "__main__":
	from numpy import arange
	CEE = CEE()
	print(CEE.setOutput(stream = "v", wave = "sine", amplitude = 1, value = 1, frequency = 100))
	print(CEE.getInput(resample = 0, count = 100))
