from numpy import logspace, log10, mean
from connectClient import CEE
import pylab

CEE = CEE()
pylab.ion()

channel = 'a'
periodCount = 10 

sampleTime = CEE.devInfo['sampleTime']
maxFreq = (1/sampleTime)/20
# maximum frequency = sampling rate / 20

frequencies = logspace(log10(10), log10(maxFreq), 50)
#log-spaced array of frequencies
amplitudes = []
phases = []

def findPhases(zeroesA, zeroesB):
	phases = []
	for i in range(1, len(zeroesA)):
		phase = ( zeroesA[i] - zeroesB[i] ) / zeroesA[1]
		# calculate percent difference between spacing of two events
		phase = phase * 180
		# normalize to degrees
		phases.append(phase)
	return phases

def findLocalMaxes(values):
	chunkwidth = len(values)/periodCount
	# determine samples per period
	split = [values[i:i+chunkwidth] for i in range(0, len(values), chunkwidth)]
	# split into periods
	localMaxes = map(max, split)
	# find local maximums
	localMaxTimes = [ (chunk.index(localMax) + split.index(chunk)*chunkwidth) * sampleTime 
		for localMax, chunk in zip(localMaxes, split) ]
	# find indexes of local maximums
	localMaxTimes = [ time - localMaxTimes[0] for time in localMaxTimes]
	# zero indexes of local maximums against the first
	return localMaxes[1:-2], localMaxTimes[1:-2]
	# trim the garbage datapoints and return the information

for frequency in frequencies:
	setResponse = CEE.setOutput(channel, 'v', 2.5, 'sine', 2.5, frequency, 1, 0)
	# source sine wave with full-scale voltage range at target frequency
	sampleCount = int( ( (1/frequency) * periodCount ) / sampleTime)
	# do math to get the equivalent of 'periodCount' in samples
	v, i = CEE.getInput(channel, 0, sampleCount, setResponse['startSample'])
	# get samples from CEE
	vMaxes, vMaxTimes = findLocalMaxes(v)
	iMaxes, iMaxTimes = findLocalMaxes(i)
	# get timestamps and maximum values for voltage and current
	amplitudes.append(mean(iMaxes))
	# calculate and record amplitude from array of local maximum currents
	phases.append(mean(findPhases(vMaxTimes, iMaxTimes)))
	# calculate and record phases from v/i maximums' timestamps 

pylab.subplot(2,1,1)
pylab.semilogx(frequencies, amplitudes, '.')
pylab.ylim(0,200)
pylab.ylabel("mean peak current")
pylab.subplot(2,1,2)
pylab.semilogx(frequencies, phases, '.')
pylab.ylim(-90,90)
pylab.ylabel("phase shift in degrees")
pylab.xlabel("frequency")
