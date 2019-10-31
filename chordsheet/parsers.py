# -*- coding: utf-8 -*-

from sys import exit

def parseFingering(fingering, instrument):
	if instrument == 'guitar':
		numStrings = 6
		if len(fingering) == numStrings:
			output = list(fingering)
		else:
			output = [x for x in fingering.split(',')]
		if len(output) == numStrings:
			return output
		else:
			exit("Voicing <{v}> is malformed.".format(v=fingering))
	else:
		return [fingering]

nameReplacements = { "b":"♭", "#":"♯" }

def parseName(chordName):
	parsedName = chordName
	for i, j in nameReplacements.items():
		parsedName = parsedName.replace(i, j)
	return parsedName