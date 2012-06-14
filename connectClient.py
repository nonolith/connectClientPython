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
		atexit.register(self._onClose)

		self.connection.request("GET", "/rest/v1/devices/")
		if json.loads(self.connection.getresponse().read()) == {}:
			raise Exception('No devices found.')

		if devID == "com.nonolithlabs.cee*":
			self.devID = devID
		else:
			self.connection.request("GET", "/rest/v1/devices/")
			response = json.loads(self.connection.getresponse().read())
			if response.keys()[0] == devID:
				self.devID = devID
			else:
				raise Exception('Invalid devID.')

		headers = {"Content-Type": "application/x-www-form-urlencoded"}
		options = {"sampleTime":0.000025, "current":200, "samples":48000}
		options = urllib.urlencode(options)
		self.connection.request("POST", "/rest/v1/devices/%s/configuration" % self.devID, options, headers)
		self.connection.getresponse()
		options = {"capture":"on"}
		options = urllib.urlencode(options)
		self.connection.request("POST", "/rest/v1/devices/%s" % self.devID, options, headers)
		self.connection.getresponse()
		self.connection.request("GET", "/rest/v1/devices/%s" % self.devID)
		self.devInfo = json.loads(self.connection.getresponse().read())

	def _onClose(self):
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

	def setOutputConstant(self, channel = "a", mode = "d", value = 0):
		""" Set the output state for a given channel.
			'mode' can be 'v' to set voltage, 'i' to set current, or 'd' for high impedance mode.
			'value' is a number either in volts or milliamps specifying the target value."""
		options = {"mode": mode, "value": value}
		options = urllib.urlencode(options)
		headers = {"Content-Type": "application/x-www-form-urlencoded"}
		self.connection.request("POST", "/rest/v1/devices/%s/%s/output" % (self.devID, channel),  options, headers)
		return json.loads(self.connection.getresponse().read())

	def setOutputRepeating(self, channel = "a", mode = "d", value = 0, wave="square", amplitude = 0, frequency = 0, relPhase = 1, phase = 0):
		""" Set the output state for a given channel.
			'mode' can be 'v' to set voltage, 'i' to set current, or 'd' for high impedance mode.
			'value' is a number either in volts or milliamps specifying the center value in AC mode.
			'wave' can be either triangle,' 'square,' or 'sine'.
			'amplitude' determines the maximum offset from center.
			'frequency' is the cycles per second.
			'relPhase' determines whether the starting value is based off of the previous output setting to provide seamless change in frequency.
			'phase' is the phase offset in seconds from the beginning of the stream (relPhase=0) or from the previous source (relPhase=1)."""
		if wave in ["square", "triangle", "sine"]:
			options = {"mode": mode, "value": value, "wave": wave, "amplitude": amplitude, "frequency": frequency, "relPhase": relPhase, "phase": phase}
		else:
			raise Exception('Invalid option for "wave"')
		options = urllib.urlencode(options)
		headers = {"Content-Type": "application/x-www-form-urlencoded"}
		self.connection.request("POST", "/rest/v1/devices/%s/%s/output" % (self.devID, channel),  options, headers)
		return json.loads(self.connection.getresponse().read())

	def setOutputArbitrary(self, channel = "a", mode = "d", values = [{"t":0, "v":0}]):
		""" Set the output state for a given channel.
			'mode' can be 'v' to set voltage, 'i' to set current, or 'd' for high impedance mode.
			'values' takes a list of time/value pairs like: [{"t":0, "v":0},{"t":10000, "v":5},{"t":20000, "v":3}]"""
		options = {"mode": 1, "values": values, "offset":-1, "source": "arb"}
		print options
		options = json.dumps(options)
		headers = {"Content-Type": "text/json"}
		self.connection.request("POST", "/rest/v1/devices/%s/%s/output" % (self.devID, channel),  options, headers)
		return json.loads(self.connection.getresponse().read())

	def setInput(self, channel = "a", vGain = 1, iGain = 1):
		""" Set the input gain for both streams of a given channel."""
		Gains = [0.5,1,2,4,8,16,32,64]
		if iGain == "0.5":
			iGain = float(iGain)
		elif iGain == 0.5:
			pass
		else:
			iGain = int(iGain)
		vGain = int(vGain)
		if vGain not in Gains[1::]:
			raise Exception("Invalid voltage gain.")
		if iGain not in Gains[0:-1]:
			raise Exception("Invalid current gain.")
		options = {"gain_v":vGain, "gain_i":iGain}
		options = urllib.urlencode(options)
		headers = {"Content-Type": "application/x-www-form-urlencoded"}
		self.connection.request("POST", "/rest/v1/devices/%s/%s/input" % (self.devID, channel),  options, headers)
		return json.loads(self.connection.getresponse().read())

	def getInput(self, channel = "a", resample = .01, count = 1, start = None):
		""" Returns a pair of list indicating the measured state of the specified channel.
			The first list is measured voltage, the second list is measured current.
			Each list contains 'count' samples, averaged over 'resample' seconds, separated by 'resample' seconds.
			'start' is the sample index from which to start measuring."""
		options = {"resample":resample, "count":count, "header":0}
		if start != None:
			options['start'] = start
		options = "?" + urllib.urlencode(options)
		self.connection.request("GET", "/rest/v1/devices/%s/%s/input" % (self.devID, channel) + options)
		values = [[float(item) for item in item.split(',')] 
			for item in self.connection.getresponse().read().split('\n') 
			if item != '']
		values = map(list, zip(*values))
		if count == 1:
			return [value[0] for value in values]
		else:
			return values
