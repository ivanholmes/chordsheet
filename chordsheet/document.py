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
        self.rightMargin = kwargs.get('rightMargin', 10)
        self.bottomMargin = kwargs.get('bottomMargin', 10)
        self.font = kwargs.get('font', 'FreeSans')
        self.lineSpacing = kwargs.get('lineSpacing', 1.15)
        self.unitWidth = kwargs.get('unitWidth', 10)

        self.useIncludedFont = True
        self.numberPages = True

        self.separatorSize = 5*self.unit

        self.titleFontSize = 24
        self.subtitleFontSize = 18
        self.creditsFontSize = 12
        self.tempoFontSize = 12
        self.headingFontSize = 18
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
    def __init__(self, length, chord=None, notes=None):
        self.length = length
        self.chord = chord
        self.notes = notes

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.length == other.length and self.chord == other.chord and self.notes == other.notes
        return NotImplemented


class Section:
    def __init__(self, blockList=None, name=None):
        self.blockList = blockList or []
        self.name = name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.blockList == other.blockList and self.name == other.name
        return NotImplemented


class Document:
    def __init__(self, chordList=None, sectionList=None, title=None, subtitle=None, composer=None, arranger=None, timeSignature=defaultTimeSignature, tempo=None):
        self.chordList = chordList or []
        self.sectionList = sectionList or []
        self.title = title or ''  # Do not initialise title empty
        self.subtitle = subtitle
        self.composer = composer
        self.arranger = arranger
        self.timeSignature = timeSignature
        self.tempo = tempo

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            textEqual = self.title == other.title and self.subtitle == other.subtitle and self.composer == other.composer and self.arranger == other.arranger and self.timeSignature == other.timeSignature and self.tempo == other.tempo  # check all the text values for equality
            return textEqual and self.chordList == other.chordList and self.sectionList == other.sectionList
        return NotImplemented

    def loadXML(self, filepath):
        """
        Read an XML file and import its contents.
        """
        xmlDoc = ET.parse(filepath)
        root = xmlDoc.getroot()

        self.chordList = []
        if root.find('chords'):
            for c in root.findall('chords/chord'):
                self.chordList.append(Chord(parseName(c.find('name').text)))
                for v in c.findall('voicing'):
                    self.chordList[-1].voicings[v.attrib['instrument']
                                                ] = parseFingering(v.text, v.attrib['instrument'])

        self.sectionList = []
        if root.find('section'):
            for n, s in enumerate(root.findall('section')):
                blockList = []

                for b in s.findall('block'):
                    blockChordName = parseName(b.find('chord').text) if b.find(
                        'chord') is not None else None
                    if blockChordName:
                        blockChord = None
                        for c in self.chordList:
                            if c.name == blockChordName:
                                blockChord = c
                                break
                        if blockChord is None:
                            raise ValueError("Chord {c} does not match any chord in {l}.".format(
                                c=blockChordName, l=self.chordList))
                    else:
                        blockChord = None
                    blockNotes = (b.find('notes').text if b.find(
                        'notes') is not None else None)
                    blockList.append(
                        Block(float(b.find('length').text), chord=blockChord, notes=blockNotes))
                # automatically name the section by its index if a name isn't given. The +1 is because indexing starts from 0.
                self.sectionList.append(Section(blockList=blockList, name=(
                    s.attrib['name'] if 'name' in s.attrib else "Section {}".format(n + 1))))

        self.title = (root.find('title').text if root.find(
            'title') is not None else '')  # Do not initialise title empty
        self.subtitle = (root.find('subtitle').text if root.find(
            'subtitle') is not None else None)
        self.composer = (root.find('composer').text if root.find(
            'composer') is not None else None)
        self.arranger = (root.find('arranger').text if root.find(
            'arranger') is not None else None)
        self.timeSignature = (int(root.find('timesignature').text) if root.find(
            'timesignature') is not None else defaultTimeSignature)
        self.tempo = (root.find('tempo').text if root.find(
            'tempo') is not None else None)

    @classmethod
    def newFromXML(cls, filepath):
        """
        Create a new Document object directly from an XML file.
        """
        doc = cls()
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
                    ET.SubElement(chordElement, "voicing", attrib={
                                  'instrument': 'guitar'}).text = ','.join(c.voicings['guitar'])
                if inst == 'piano':
                    ET.SubElement(chordElement, "voicing", attrib={
                                  'instrument': 'piano'}).text = ','.join(c.voicings['piano'])

        for n, s in enumerate(self.sectionList):
            sectionElement = ET.SubElement(root, "section", attrib={
                                           'name': s.name if s.name else "Section {}".format(n + 1)})
            for b in s.blockList:
                blockElement = ET.SubElement(sectionElement, "block")
                ET.SubElement(blockElement, "length").text = str(b.length)
                if b.chord is not None:
                    ET.SubElement(blockElement, "chord").text = b.chord.name
                if b.notes is not None:
                    ET.SubElement(blockElement, "notes").text = b.notes

        tree = ET.ElementTree(root)
        tree.write(filepath)
        
    def loadCSMacro(self, filepath):
        """
        Read a Chordsheet Macro file and import its contents.
        """
        self.chordList = []
        self.sectionList = []

        aliasTable = {}
        
        def chord(args):
            argList = args.split(" ")
            chordName = argList.pop(0)
            
            self.chordList.append(Chord(parseName(chordName)))
            
            argIter = iter(argList)
            subCmdsArgs = list(zip(argIter, argIter))
            
            for subCmd, arg in subCmdsArgs:
                if subCmd == "alias":
                    aliasTable[arg] = chordName
                else:
                    self.chordList[-1].voicings[subCmd] = parseFingering(arg, subCmd)         
            
        def section(args):
            blockList = []
            
            sectionName, blocks = [arg.strip() for arg in args.split("\n", 1)]
            
            self.sectionList.append(Section(name=sectionName))
            
            for b in blocks.split():
                blockParams = b.split(",")
                blockLength = float(blockParams[1])                
                
                if blockParams[0] in aliasTable:
                    blockChordName = aliasTable[blockParams[0]]
                else:
                    blockChordName = blockParams[0]
                
                blockChordName = parseName(blockChordName) if blockChordName not in ["NC", "X"] else None
                
                blockChord = None
                
                if blockChordName:
                    for c in self.chordList:
                        if c.name == blockChordName:
                            blockChord = c
                            break
                    if blockChord is None:
                        raise ValueError("Chord {c} does not match any chord in {l}.".format(
                            c=blockChordName, l=self.chordList))
                
                blockList.append(Block(blockLength, chord=blockChord))
                
            self.sectionList[-1].blockList = blockList
            
        with open(filepath, 'r') as f:
            cmatext = f.read()
            
        cmaCmdsArgs = [statement.split(" ", 1) for statement in \
            (rawStatement.strip() for rawStatement in cmatext.split("\\")[1:])]

        for cmd, args in cmaCmdsArgs:
            if cmd == "chordsheet":
                # There's only one version so no need to do anything with this
                pass
            elif cmd == "title":
                self.title = args
            elif cmd == "subtitle":
                self.subtitle = args
            elif cmd == "arranger":
                self.arranger = args
            elif cmd == "composer":
                self.composer = args
            elif cmd == "timesig":
                self.timeSignature = int(args)
            elif cmd == "tempo":
                self.tempo = args
            elif cmd == "chord":
                chord(args)
            elif cmd == "section":
                section(args)
            elif cmd in ["!", "rem"]:
                # Simply ignore comments
                pass
            else:
                raise ValueError(f"Command {cmd} not understood.")