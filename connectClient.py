#"!/usr/bin/python
# Pythonic abstraction layer for Nonolith Connect's RESTful API.
# Released under the terms of the GNU GPLv3+
# (C) 2012 Nonolith Labs, LLC
# Authors:
#   Ian Daniher 

import httplib, atexit, urllib, json

class CEE:
	def __init__(self, devID = "com.nonolithlabs.cee*", start=True, server="localhost:9003"):
		""" Starts an HTTP connection, determines the target device ID, and optionally starts capture."""
		self.connection = httplib.HTTPConnection(server)

		deviceList = self.request("/rest/v1/devices/")

		for deviceEntry in deviceList.itervalues():
			if deviceEntry['model'] == 'com.nonolithlabs.cee':
				if deviceEntry['id'] == devID or devID == "com.nonolithlabs.cee*":
					break
		else:
			raise Exception('Device not found.')

		self.devID = deviceEntry['id']
		self.deviceResource = "/rest/v1/devices/{0}/".format(self.devID)

		self.getInfo()

		self.stopOnClose = False
		atexit.register(self._onClose)

		if start:
			self.start(True)

	def request(self, path, method='GET', encoding='url', jsonReply=True, **kwds):
		"""Send a request to the server.
			`path` is relative to the device resource if it does not begin with '/'.
			Keyword arguments are passed as POST parameters.
		"""
		if not path.startswith('/'): path = self.deviceResource + path

		#print method, path, kwds

		if method == 'GET':
			self.connection.request(method, path)
		elif method == 'POST' and encoding == 'url':
			headers = {"Content-Type": "application/x-www-form-urlencoded"}
			body = urllib.urlencode(kwds)
			self.connection.request(method, path, body, headers)

		r = self.connection.getresponse().read()
		if jsonReply:
			r = json.loads(r)
		return r

	def getInfo(self):
		"""Refresh the device metadata"""
		self.devInfo = self.request('')

	def start(self, stopOnClose=False):
		"""Start sampling. If stopOnClose is true, the CEE will stop automatically when python exits."""
		self.request('', 'POST', capture='on')
		self.stopOnClose = stopOnClose

	def pause(self):
		"""Stop sampling."""
		self.request('', 'POST', capture='off')

	def setSampleRate(self, sampleRate):
		"""Set the sample rate of the device"""
		if sampleRate < 1000:
			sampleRate *= 1000

		if sampleRate not in [1000, 5000, 10000, 20000, 40000, 80000, 100000]:
			raise ValueError("Invalid sample rate")

		sampleTime = 1.0 / sampleRate
		if sampleTime == self.devInfo['sampleTime']:
			return True

		if sampleTime < self.devInfo.get('minSampleTime', 1.0/40e3):
			raise ValueError("The device does not support this sample rate.")

		nsamples = int(self.devInfo['samples'] * self.devInfo['sampleTime'] / sampleTime)

		self.request('configuration', 'POST', sampleTime=sampleTime, samples=nsamples)
		self.getInfo()

		if self.stopOnClose:
			self.start(True)


	def _onClose(self):
		if self.stopOnClose:
			self.pause()
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

	def setOutputArbitrary(self, channel = "a", mode = "d", times = [0], values = [0]): 
		""" Set the output state for a given channel.
			'mode' can be 'v' to set voltage, 'i' to set current, or 'd' for high impedance mode.
			'times' is a list of times in seconds.
			'values' is a list of values in SI units, either volts or amps."""
		values = [value * 1000.0 if mode == "i" else value for value in values]
		output = [{"t":times[i]/self.devInfo['sampleTime'], "v":values[i]} for i in range(len(times))]
		options = {"mode": {"d":0,"v":1,"i":2}[mode], "values": output, "offset":-1, "source": "arb"}
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
		""" Returns a pair of lists indicating the measured state of the specified channel.
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
