# -*- coding: utf-8 -*-

from xml.etree import ElementTree as ET
from chordsheet.parsers import parseFingering, parseName
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4

defaultTimeSignature = 4

class Style:
    def __init__(self, **kwargs):
        # set up the style using sane defaults
        self.unit = kwargs.get('unit', mm)
        
        self.pageSize = kwargs.get('pageSize', A4)
        self.leftMargin = kwargs.get('leftMargin', 10)
        self.topMargin = kwargs.get('topMargin', 10)
        self.font = kwargs.get('font', 'FreeSans')
        self.lineSpacing = kwargs.get('lineSpacing', 1.15)
        self.separatorSize = kwargs.get('separatorSize', 5)
        self.unitWidth = kwargs.get('unitWidth', 10)
        
        self.useIncludedFont = True
        
        self.stringHzSp = 20*self.unit
        self.stringHzGap = 2*self.unit
        self.stringHeight = 5*self.unit

        self.unitHeight = 20*self.unit
        self.beatsHeight = 5*self.unit
        
        self.titleFontSize = 24
        self.subtitleFontSize = 18
        self.creditsFontSize = 12
        self.tempoFontSize = 12
        self.notesFontSize = 12
        self.chordNameFontSize = 18
        self.beatsFontSize = 12
        
class Chord:
    def __init__(self, name, **kwargs):
        self.name = name
        self.voicings = {}
        for inst, fing in kwargs.items():
            self.voicings[inst] = fing

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.voicings == other.voicings
        return NotImplemented


class Block:
    def __init__(self, length, **kwargs):
        self.length = length
        self.chord = kwargs.get('chord', None)
        self.notes = kwargs.get('notes', None)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.length == other.length and self.chord == other.chord and self.notes == other.notes
        return NotImplemented 

class Document:
    def __init__(self, chordList=None, blockList=None, title=None, subtitle=None, composer=None, arranger=None, timeSignature=defaultTimeSignature, tempo=None):
        self.chordList = chordList or []
        self.blockList = blockList or []
        self.title = title or '' # Do not initialise title empty
        self.subtitle = subtitle
        self.composer = composer
        self.arranger = arranger
        self.timeSignature = timeSignature
        self.tempo = tempo

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            textEqual = self.title == other.title and self.subtitle == other.subtitle and self.composer == other.composer and self.arranger == other.arranger and self.timeSignature == other.timeSignature and self.tempo == other.tempo # check all the text values for equality
            return textEqual and self.chordList == other.chordList and self.blockList == other.blockList
        return NotImplemented
        
    def loadXML(self, filepath):
        """
        Read an XML file and import its contents.
        """
        xmlDoc = ET.parse(filepath)
        root = xmlDoc.getroot()
        
        self.chordList = []
        if root.find('chords') is not None:
            for c in root.findall('chords/chord'):
                self.chordList.append(Chord(parseName(c.find('name').text)))
                for v in c.findall('voicing'):
                    self.chordList[-1].voicings[v.attrib['instrument']] = parseFingering(v.text, v.attrib['instrument'])
        
        self.blockList = []
        if root.find('progression') is not None:
            for b in root.findall('progression/block'):
                blockChordName = parseName(b.find('chord').text) if b.find('chord') is not None else None
                if blockChordName:
                    blockChord = None
                    for c in self.chordList:
                        if c.name == blockChordName:
                            blockChord = c
                            break
                    if blockChord is None:
                        exit("Chord {c} does not match any chord in {l}.".format(c=blockChordName, l=self.chordList))
                else:
                    blockChord = None
                blockNotes = (b.find('notes').text if b.find('notes') is not None else None)
                self.blockList.append(Block(int(b.find('length').text), chord=blockChord, notes=blockNotes))
        
        self.title = (root.find('title').text if root.find('title') is not None else '') # Do not initialise title empty
        self.subtitle = (root.find('subtitle').text if root.find('subtitle') is not None else None)
        self.composer = (root.find('composer').text if root.find('composer') is not None else None)
        self.arranger = (root.find('arranger').text if root.find('arranger') is not None else None)
        self.timeSignature = (int(root.find('timesignature').text) if root.find('timesignature') is not None else defaultTimeSignature)
        self.tempo = (root.find('tempo').text if root.find('tempo') is not None else None)
        
    def newFromXML(self, filepath):
        """
        Create a new Document object directly from an XML file.
        """
        doc = Document()
        doc.loadXML(filepath)
        return doc
    
    def saveXML(self, filepath):
        """
        Write the contents of the Document object to an XML file.
        """
        root = ET.Element("chordsheet")
        
        ET.SubElement(root, "title").text = self.title
        
        if self.subtitle is not None:
            ET.SubElement(root, "subtitle").text = self.subtitle

        if self.arranger is not None:
            ET.SubElement(root, "arranger").text = self.arranger
            
        if self.composer is not None:
            ET.SubElement(root, "composer").text = self.composer
            
        ET.SubElement(root, "timesignature").text = str(self.timeSignature)

        if self.tempo is not None:
            ET.SubElement(root, "tempo").text = self.tempo
        
        chordsElement = ET.SubElement(root, "chords")
        
        for c in self.chordList:
            chordElement = ET.SubElement(chordsElement, "chord")
            ET.SubElement(chordElement, "name").text = c.name
            for inst in c.voicings.keys():
                if inst == 'guitar':
                    ET.SubElement(chordElement, "voicing", attrib={'instrument':'guitar'}).text = ','.join(c.voicings['guitar'])
                if inst == 'piano':
                    ET.SubElement(chordElement, "voicing", attrib={'instrument':'piano'}).text = c.voicings['piano'][0] # return first element of list as feature has not been implemented
        
        progressionElement = ET.SubElement(root, "progression")
        
        for b in self.blockList:
            blockElement = ET.SubElement(progressionElement, "block")
            ET.SubElement(blockElement, "length").text = str(b.length)
            if b.chord is not None:
                ET.SubElement(blockElement, "chord").text = b.chord.name
            if b.notes is not None:
                ET.SubElement(blockElement, "notes").text = b.notes
            
        tree = ET.ElementTree(root)
        tree.write(filepath)