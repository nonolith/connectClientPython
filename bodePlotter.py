from numpy import logspace, log10, mean, linspace, ceil
from connectClient import CEE
import pylab
import time

CEE = CEE()
pylab.ion()

periodCount = 10 

sampleTime = CEE.devInfo['sampleTime']
maxFreq = (1/sampleTime)/20
# maximum frequency = sampling rate / 20

frequencies = list(logspace(log10(10), log10(maxFreq), 40))
#log-spaced array of frequencies
amplitudes = []
phases = []

def findPhases(maxesA, maxesB):
	phases = []
	maxesA = maxesA[1::]
	maxesB = maxesB[1::]
	for i in range(len(maxesA)):
		phase = ( maxesA[i] - maxesB[i] ) * frequency * 360.0
		if phase > 180:
			phase = 180 - phase
		if phase < -180:
			phase = 360 + phase
		phases.append(phase)
	print max(phases), phases
	return phases 

def findLocalMaxes(values, a):
	lenFreqs = len(frequencies)
	index = frequencies.index(frequency)
	pylab.subplot(lenFreqs/2, 2, index+1)
	chunkwidth = len(values)/periodCount
	# determine samples per period
	split = [values[i:i+chunkwidth] for i in range(0, len(values), chunkwidth)]
	# split into periods
	localMaxes = map(max, split)
	# find local maximums
	pylab.plot(values)
	localMaxTimes = [ (chunk.index(localMax) + split.index(chunk)*chunkwidth) for localMax, chunk in zip(localMaxes, split) ]
	[pylab.axvline(x=point, color='r') for point in [i+chunkwidth for i in range(1, len(values), chunkwidth)]]
	pylab.plot(localMaxTimes, localMaxes, 'ro')
	localMaxTimes = [ (chunk.index(localMax) + split.index(chunk)*chunkwidth) * sampleTime
		for localMax, chunk in zip(localMaxes, split) ]
	# find indexes of local maximums
	return localMaxes, localMaxTimes
	# trim the garbage datapoints and return the information

for frequency in frequencies:
	period = 1/frequency
	setResponse = CEE.setOutput('a', 'v', 2.5, 'sine', 2.5, frequency, 0, 0)
	# source sine wave with full-scale voltage range at target frequency
	sampleCount = ( period * periodCount ) / sampleTime
	# do math to get the equivalent of 'periodCount' in samples
	startSample = ceil(setResponse['startSample']/period)*period
#	print setResponse['startSample'], startSample
	v = CEE.getInput('a', 0, int(sampleCount), int(startSample))[0]
	i = CEE.getInput('b', 0, int(sampleCount), int(startSample))[0]
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
