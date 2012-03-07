import numpy
from connectClient import CEE
import pylab

CEE = CEE()
pylab.ion()

channel = 'a'
periodCount = 10 

sampleTime = CEE.devInfo['sampleTime']
maxFreq = (1/sampleTime)/20
# maximum frequency = sampling rate / 20
frequencies = numpy.logspace(numpy.log10(10), numpy.log10(maxFreq), 50)

amplitudes = []
phases = []

def findPhases(zeroesA, zeroesB):
	if len(zeroesA) != len(zeroesB):
		zeroesA = zeroesA[0:len(zeroesB)]
		zeroesB =  zeroesB[0:len(zeroesA)]
	phases = []
	for i in range(1, len(zeroesA)):
		phase = ( zeroesA[i] - zeroesB[i] ) / zeroesA[1]
		phase = (phase*180)
		phases.append(phase)
	return phases

def findLocalMaxes(values):
	chunkwidth = len(values)/periodCount
	# determine samples per period
	split = [values[i:i+chunkwidth] for i in range(0, len(values), chunkwidth)]
	# split into period
	localMaxes = map(max, split)
#	oneSigma = lambda value: abs(value-numpy.mean(localMaxes)) < numpy.std(localMaxes)
	# sketchy function to determine if value is less than one stddev away from mean
#	cleaned = [[localMax, chunk] for localMax, chunk in zip(localMaxes, split) if oneSigma(localMax)]
#	localMaxes, split = map(list, zip(*cleaned))
	localMaxTimes = [(chunk.index(localMax) + split.index(chunk)*chunkwidth)*sampleTime for localMax, chunk in zip(localMaxes, split)]
	return localMaxTimes[1:-2], localMaxes[1:-2]

for frequency in frequencies:
	period = 1/frequency
	setResponse = CEE.setOutput(channel, 'v', 2.5, 'sine', 2.5, frequency, 1, 0)
	# source sine wave with full-scale voltage range at target frequency
	sampleCount = int(( period * periodCount ) / sampleTime)
	# do math to get the equivalent of 'periodCount' in samples
	v, i = CEE.getInput(channel, 0, sampleCount, setResponse['startSample'])
	vMaxTimes, vMaxes = findLocalMaxes(v)
	iMaxTimes, iMaxes = findLocalMaxes(i)
	amplitudes.append(numpy.mean(iMaxes))
	foundPhases = findPhases(vMaxTimes, iMaxTimes)
	phases.append(numpy.mean(foundPhases))

pylab.subplot(2,1,1)
pylab.semilogx(frequencies, amplitudes, '.')
pylab.ylim(0,200)
pylab.ylabel("mean peak current")
pylab.subplot(2,1,2)
pylab.semilogx(frequencies, phases, '.')
pylab.ylim(-90,90)
pylab.ylabel("phase shift in degrees")
pylab.xlabel("frequency")
