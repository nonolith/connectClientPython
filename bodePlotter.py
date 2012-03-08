# -*- coding: utf-8 -*-
from numpy import logspace, log10, mean
from connectClient import CEE
import pylab

CEE = CEE()

periodCount = 10 

sampleTime = CEE.devInfo['sampleTime']
minFreq = 10
maxFreq = (1/sampleTime)/20
# maximum frequency = sampling rate / 20

frequencies = logspace(log10(minFreq), log10(maxFreq), 100)
# log-spaced array of frequencies
amplitudes = []
phases = []

def findPhases(maxesA, maxesB):
	phases = []
	for i in range(len(maxesA)):
		phase = ( maxesA[i] - maxesB[i] ) * sampleTime * frequency * 360.0
		# calculate phase
		if phase > 180:
			phase = 180 - phase
		if phase < -180:
			phase = 360 + phase
		# normalize phase
		phases.append(phase)
	return phases 

def findLocalMaxes(values):
	chunkwidth = len(values)/periodCount
	# determine samples per period
	split = [values[i:i+chunkwidth] for i in range(0, len(values), chunkwidth)]
	# split into periods
	localMaxes = map(max, split)
	# find local maximums
	localMaxTimes = [ (chunk.index(localMax) + split.index(chunk)*chunkwidth)
		for localMax, chunk in zip(localMaxes, split) ]
	# find indexes of local maximums
	return localMaxes[1::], localMaxTimes[1::]
	# trim the garbage datapoints and return the information

for frequency in frequencies:
	period = 1/frequency
	setResponse = CEE.setOutput('a', 'v', 2.5, 'sine', 2.5, frequency, 0, 0)
	# source sine wave with full-scale voltage range at target frequency
	sampleCount = ( period * periodCount ) / sampleTime
	# do math to get the equivalent of 'periodCount' in samples
	v = CEE.getInput('a', 0, int(sampleCount), setResponse['startSample'])[0]
	i = CEE.getInput('b', 0, int(sampleCount), setResponse['startSample'])[0]
	# get samples from CEE
	vMaxes, vMaxTimes = findLocalMaxes(v)
	iMaxes, iMaxTimes = findLocalMaxes(i)
	# get timestamps and maximum values for voltage and current
	amplitudes.append(mean(iMaxes))
	# calculate and record amplitude from array of local maximum currents
	phases.append(mean(findPhases(vMaxTimes, iMaxTimes)))
	# calculate and record phases from v/i maximums' timestamps 

pylab.figure()
pylab.subplot(2,1,1)
pylab.loglog(frequencies, amplitudes, '.')
pylab.xlim(minFreq,maxFreq)
pylab.ylim(0,5)
pylab.ylabel("Amplitude(V)")
pylab.subplot(2,1,2)
pylab.semilogx(frequencies, phases, '.')
pylab.xlim(minFreq,maxFreq)
pylab.ylabel("Phase Shift(deg)")
pylab.xlabel("frequency")
pylab.show()
