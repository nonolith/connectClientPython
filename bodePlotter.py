from numpy import logspace, log10, mean, linspace
from connectClient import CEE
import pylab
import time

CEE = CEE()
pylab.ion()

periodCount = 10 

sampleTime = CEE.devInfo['sampleTime']
maxFreq = (1/sampleTime)/20
# maximum frequency = sampling rate / 20

frequencies = logspace(log10(10), log10(maxFreq), 10)
#log-spaced array of frequencies
amplitudes = []
phases = []

def findPhases(maxesA, maxesB):
	phases = []

	maxesA = [ maxA - maxesA[0] for maxA in maxesA ]
	maxesB = [ maxB - maxesA[0] for maxB in maxesB ]
	# normalize times against the start time of array A

	print period 
	print maxesA
	print maxesB

	if (maxesA[1]-maxesB[1]) < (maxesB[2] - maxesA[2]):
		maxesA = maxesA[1:-1]
		maxesB = maxesB[0:-2]
	elif (maxesA[1]-maxesB[1]) > (maxesB[2] - maxesA[2]):
		maxesB = maxesB[1:-1]
		maxesA = maxesA[0:-2]
	# shift arrays to match eachother

	print '\n'

	for i in range(len(maxesA)):
		phase = ( maxesB[i] - maxesA[i] ) / maxesA[1] * 360.0
		# calculate percent difference between spacing of two events
		# normalize to degrees
		phases.append(phase)
	return phases

def findLocalMaxes(values, a):
	chunkwidth = len(values)/periodCount
	# determine samples per period
	split = [values[i:i+chunkwidth] for i in range(0, len(values), chunkwidth)]
	# split into periods
	localMaxes = map(max, split)
	# find local maximums
	localMaxTimes = [ (chunk.index(localMax) + split.index(chunk)*chunkwidth) * sampleTime
		for localMax, chunk in zip(localMaxes, split) ]
	# find indexes of local maximums
	return localMaxes, localMaxTimes
	# trim the garbage datapoints and return the information

for frequency in frequencies:
	period = 1/frequency
	setResponse = CEE.setOutput('a', 'v', 2.5, 'sine', 2.5, frequency, 1, 0)
	# source sine wave with full-scale voltage range at target frequency
	sampleCount = int( ( period * periodCount ) / sampleTime)
	# do math to get the equivalent of 'periodCount' in samples
	v = CEE.getInput('a', 0, sampleCount, setResponse['startSample'])[0]
	i = CEE.getInput('b', 0, sampleCount, setResponse['startSample'])[0]
	# get samples from CEE
	vMaxes, vMaxTimes = findLocalMaxes(v, True)
	iMaxes, iMaxTimes = findLocalMaxes(i, False)
	# get timestamps and maximum values for voltage and current
	amplitudes.append(mean(iMaxes))
	# calculate and record amplitude from array of local maximum currents
	phases.append(mean(findPhases(vMaxTimes, iMaxTimes)))
	# calculate and record phases from v/i maximums' timestamps 

pylab.figure()
pylab.subplot(2,1,1)
pylab.semilogx(frequencies, amplitudes, '.')
#pylab.ylim(0,5)
pylab.ylabel("mean peak current")
pylab.subplot(2,1,2)
pylab.semilogx(frequencies, phases, '.')
pylab.ylabel("phase shift in degrees")
pylab.xlabel("frequency")
