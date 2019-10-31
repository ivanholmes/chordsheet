# -*- coding: utf-8 -*-

from xml.etree import ElementTree as ET
from chordsheet.parsers import parseFingering, parseName
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4

defaultTimeSignature = 4

class Style:
    def __init__(self, **kwargs):
        self.unit = kwargs.get('unit', mm)
        
        self.pageSize = kwargs.get('pageSize', A4)
        self.leftMargin = kwargs.get('leftMargin', 10)
        self.topMargin = kwargs.get('topMargin', 10)
        self.font = kwargs.get('font', 'FreeSans')
        self.lineSpacing = kwargs.get('lineSpacing', 1.15)
        self.separatorSize = kwargs.get('separatorSize', 5)
        
        self.useIncludedFont = False
        
        self.stringHzSp = 20*self.unit
        self.stringHzGap = 2*self.unit
        self.stringHeight = 5*self.unit
        
        self.unitWidth = 10*self.unit
        self.unitHeight = 20*self.unit
        self.beatsHeight = 5*self.unit
        
        self.notesFontSize = 12
        self.chordNameFontSize = 18
        self.beatsFontSize = 12
        
class Chord:
    def __init__(self, name, **kwargs):
        self.name = name
        for inst, fing in kwargs.items():
            setattr(self, inst, fing)

class Block:
    def __init__(self, length, **kwargs):
        self.length = length
        self.chord = kwargs.get('chord', None)
        self.notes = kwargs.get('notes', None)

class Document:
    def __init__(self, chordList=None, blockList=None, title=None, composer=None, arranger=None, timeSignature=defaultTimeSignature):
        self.chordList = chordList or []
        self.blockList = blockList or []
        self.title = title or '' # Do not initialise title empty
        self.composer = composer
        self.arranger = arranger
        self.timeSignature = timeSignature
        
    def loadXML(self, filepath):
        xmlDoc = ET.parse(filepath)
        root = xmlDoc.getroot()
        
        self.chordList = []
        if root.find('chords') is not None:
            for c in root.findall('chords/chord'):
                self.chordList.append(Chord(parseName(c.find('name').text)))
                for v in c.findall('voicing'):
                    setattr(self.chordList[-1], v.attrib['instrument'],
                        parseFingering(v.text, v.attrib['instrument']))
        
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
        self.composer = (root.find('composer').text if root.find('composer') is not None else None)
        self.arranger = (root.find('arranger').text if root.find('arranger') is not None else None)
        self.timeSignature = (int(root.find('timesignature').text) if root.find('timesignature') is not None else defaultTimeSignature)
        
    def newFromXML(filepath):
        doc = Document()
        doc.loadXML(filepath)
        return doc
    
    def saveXML(self, filepath):
        root = ET.Element("chordsheet")
        
        ET.SubElement(root, "title").text = self.title
        
        if self.arranger is not None:
            ET.SubElement(root, "arranger").text = self.arranger
            
        if self.composer is not None:
            ET.SubElement(root, "composer").text = self.composer
            
        ET.SubElement(root, "timesignature").text = str(self.timeSignature)
        
        chordsElement = ET.SubElement(root, "chords")
        
        for c in self.chordList:
            chordElement = ET.SubElement(chordsElement, "chord")
            ET.SubElement(chordElement, "name").text = c.name
            if hasattr(c, 'guitar'):
                ET.SubElement(chordElement, "voicing", attrib={'instrument':'guitar'}).text = ','.join(c.guitar)
            if hasattr(c, 'piano'):
                ET.SubElement(chordElement, "voicing", attrib={'instrument':'piano'}).text = c.piano[0] # return first element of list as feature has not been implemented
        
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
            
        
        