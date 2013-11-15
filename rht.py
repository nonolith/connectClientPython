import connectClient
import time
import itertools as its
import numpy as np
from bitstring import BitArray


def poll(cee):
	""" polling function for AM2302 """
	cee.setOutputConstant('a', 'v', 5)
	time.sleep(2)
	start = cee.setOutputConstant('a', 'v', 0)['startSample']
	time.sleep(0.005)
	cee.setOutputConstant('a', 'd')
	return cee.getInput('a', 0, 2000, start)

_chunk = lambda l, x: [l[i:i+x] for i in xrange(0, len(l), x)]

# runlength defs
ilen = lambda it: sum(1 for _ in it)
rle = lambda xs: list(((ilen(gp), x) for x, gp in its.groupby(xs)))

def parseData(data):
	# runlength
	rled = rle(map(lambda x: x>3, data[0]))
	# find high values, parse 1 as longer than 4 samples
	b = map(lambda x: x[0] > 4, filter(lambda x: (x[1] == True) and (x[0] < 20), rled))[3::]

	# convert to words
	d = map(lambda x: BitArray(x).uint, _chunk(b, 16))

	# verify checksum
	assert(sum(d[0:2])%256 == d[-1])

	# decode
	return d[0]/10.0, d[1]/10.0

if __name__ == "__main__":
	cee = connectClient.CEE(start=True)
	cee.setSampleRate(80e3)
	while True:
		try:
			print parseData(poll(cee))
		except:
			quit()
