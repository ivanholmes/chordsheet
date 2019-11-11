# -*- coding: utf-8 -*-


def parseFingering(fingering, instrument):
    """
    Converts fingerings into the list format that Chord objects understand.
    """
    if instrument == 'guitar':
        numStrings = 6
        if len(fingering) == numStrings:  # if the fingering is entered in concise format e.g. xx4455
            output = list(fingering)
        else:  # if entered in long format e.g. x,x,10,10,11,11
            output = fingering.split(",")
        if len(output) == numStrings:
            return output
        else:
            raise Exception("Voicing <{}> is malformed.".format(fingering))
    elif instrument == 'piano':
        return [parseName(note).upper() for note in fingering.split(",")]
    else:
        return [fingering]


# dictionary holding text to be replaced in chord names
nameReplacements = {"b": "♭", "#": "♯"}

def parseName(chordName):
    """
    Replaces symbols in chord names.
    """
    parsedName = chordName
    for i, j in nameReplacements.items():
        parsedName = parsedName.replace(i, j)
    return parsedName