# -*- coding: utf-8 -*-

from math import trunc, ceil
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, white
from reportlab.platypus import BaseDocTemplate, Spacer, Paragraph, Flowable, Frame, PageTemplate, PageBreak

from chordsheet.document import Block
from chordsheet.rlStylesheet import getStyleSheet


def writeText(canvas, style, string, size, vpos, width, **kwargs):
    """
    Wrapper function to conveniently write text and return how much vertical space it took up.
    """

    align = kwargs.get('align', 'centre')
    if align == 'centre' or align == 'center':
        hpos = kwargs.get('hpos', width/2)
    elif align == 'left':
        hpos = kwargs.get('hpos', 0)
    elif align == 'right':
        hpos = kwargs.get('hpos', width)
    spacing = kwargs.get('spacing', style.lineSpacing)

    canvas.setFont(style.font, size)

    if align == 'centre' or align == 'center':
        canvas.drawCentredString(hpos, vpos-(0.75*size*spacing), string)
    elif align == 'left':
        canvas.drawString(hpos, vpos-(0.75*size*spacing), string)
    elif align == 'right':
        canvas.drawString(hpos-canvas.stringWidth(string),
                          vpos-(0.75*size*spacing), string)

    return size*style.lineSpacing


class Tempo(Flowable):
    """
    Flowable that draws the tempo. Necessary because Paragraph does not support the crotchet character.
    """

    def __init__(self, tempo, paraStyle):
        self.tempo = tempo
        self.text = "♩ = {t} bpm".format(t=self.tempo)
        self.fontSize = paraStyle.fontSize
        self.fontname = paraStyle.fontname
        self.leading = paraStyle.leading

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.height = self.leading
        return (self.width, self.height)

    def draw(self):
        canvas = self.canv
        canvas.setFont(self.fontname, self.fontSize)
        canvas.drawString(0, self.leading * 0.25, self.text)


class GuitarChart(Flowable):
    """
    Flowable that draws a guitar chord voicing chart.
    """

    def __init__(self, style, chordList):
        self.style = style
        self.guitarChordList = [
            c for c in chordList if 'guitar' in c.voicings.keys()]
        self.chartMargin = 13*mm
        self.nStrings = 6

        self.stringHzSp = 20*mm
        self.stringHzGap = 2*mm
        self.stringHeight = 5*mm

        self.spaceAfter = self.style.separatorSize

    def splitChordList(self, l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def wrap(self, availWidth, availHeight):
        self.nChords = trunc((availWidth - self.chartMargin -
                              self.stringHzGap) / self.stringHzSp)
        # the height of one layer of chart
        self.oneHeight = self.stringHeight * (self.nStrings+1)
        # only one line needed
        if len(self.guitarChordList) <= self.nChords:
            self.width = self.chartMargin + self.stringHzGap + self.stringHzSp * \
                len(self.guitarChordList)  # calculate the width
            self.height = self.oneHeight  # and its height
        # multiple lines needed
        else:
            self.width = self.chartMargin + self.stringHzGap + \
                self.stringHzSp * self.nChords
            self.height = self.oneHeight * ceil(len(self.guitarChordList) / self.nChords) + \
                (self.stringHeight *
                 trunc(len(self.guitarChordList) / self.nChords))
        return (self.width, self.height)

    def draw(self):
        canvas = self.canv
        chartmargin = self.chartMargin

        for count, gcl in enumerate(self.splitChordList(self.guitarChordList, self.nChords)):
            v_origin = self.height - count * \
                (self.oneHeight + self.stringHeight)

            self.nStrings = 6
            fontsize = 12

            stringList = [
                [c.voicings['guitar'][-(r+1)] for c in gcl] for r in range(self.nStrings)]
            stringList.append([c.name for c in gcl])

            for i in range(self.nStrings+1):  # i is the string line currently being drawn
                writeText(canvas, self.style, ['e', 'B', 'G', 'D', 'A', 'E', 'Name'][i], fontsize, v_origin-(
                    i*self.stringHeight), self.width, hpos=chartmargin, align='right')

                # j is which chord (0 is first chord, 1 is 2nd etc)
                for j in range(len(stringList[-1])):
                    currentWidth = canvas.stringWidth(stringList[i][j])
                    if j == 0:
                        x = self.stringHzGap + chartmargin
                        l = self.stringHzSp/2 - self.stringHzGap - \
                            ((currentWidth/2)) - self.stringHzGap
                        y = v_origin-(self.stringHeight*i) - \
                            self.stringHeight/2
                        canvas.line(x, y, x+l, y)
                    else:
                        x = chartmargin + self.stringHzSp * \
                            (j-0.5)+(lastWidth/2+self.stringHzGap)
                        l = self.stringHzSp - currentWidth / \
                            2 - lastWidth/2 - self.stringHzGap*2
                        y = v_origin-(self.stringHeight*i) - \
                            self.stringHeight/2
                        canvas.line(x, y, x+l, y)

                    if j == len(stringList[-1])-1:
                        x = chartmargin + self.stringHzSp * \
                            (j+0.5) + currentWidth/2 + self.stringHzGap
                        l = self.stringHzSp/2 - currentWidth/2 - self.stringHzGap
                        y = v_origin-(self.stringHeight*i) - \
                            self.stringHeight/2
                        canvas.line(x, y, x+l, y)

                    writeText(canvas, self.style, stringList[i][j], fontsize, v_origin-(
                        i*self.stringHeight), self.width, hpos=chartmargin+self.stringHzSp*(j+0.5))

                    lastWidth = currentWidth


class PianoChart(Flowable):
    """
    Flowable that draws a series of piano chord charts.
    """

    def __init__(self, style, chordList):
        self.style = style
        self.pianoChordList = [
            c for c in chordList if 'piano' in c.voicings.keys()]

        self.whiteKeyWidth = 2.5 * mm
        self.blackKeyWidth = 1.5 * mm
        self.whiteKeyHeight = 10 * mm
        self.blackKeyHeight = 5.5 * mm
        self.dotRadius = 0.5 * mm

        self.chartMargin = 0.7 * mm
        self.iconHzSpacing = 5 * mm
        self.vSpacing = 2*mm

        self.indicatorFontSize = 8
        self.chordNameFontSize = 12
        self.lineSpacing = 1.15

        self.keyDict = {'A': 'white', 'A♯': 'black', 'B': 'white', 'C': 'white', 'C♯': 'black', 'D': 'white',
                        'D♯': 'black', 'E': 'white', 'F': 'white', 'F♯': 'black', 'G': 'white', 'G♯': 'black'}
        self.keyList = list(self.keyDict.keys())

        self.spaceAfter = self.style.separatorSize

    def wrap(self, availWidth, availHeight):
        self.availWidth = availWidth
        vUnits = 1
        currentWidth = self.chartMargin
        widest = 0
        for index, c in enumerate(self.pianoChordList):
            cKL, vL, fKN, iconWidth = self.calculate(c)
            if currentWidth + iconWidth >= availWidth:
                vUnits += 1
                currentWidth = self.chartMargin
            else:
                currentWidth += self.iconHzSpacing
            currentWidth += iconWidth

            if currentWidth > widest:
                widest = currentWidth
                if vUnits == 1:
                    widest -= self.iconHzSpacing  #  chop off the trailing space
        self.oneHeight = self.chordNameFontSize * self.lineSpacing + \
            self.whiteKeyHeight + self.indicatorFontSize * self.lineSpacing

        self.width = widest
        self.height = self.oneHeight * vUnits + self.vSpacing * (vUnits - 1)
        return (self.width, self.height)

    def replaceFlats(self, fingering):
        # note name replacements
        noteReplacements = {"B♭": "A♯", "D♭": "C♯",
                            "E♭": "D♯", "G♭": "F♯", "A♭": "G♯"}

        parsedFingering = []
        for key in fingering:
            parsedFingering.append(noteReplacements.get(key, key))

        return parsedFingering

    def splitChordList(self, chordList, width):
        bigList = []
        currentList = []
        currentWidth = self.chartMargin
        for c in self.pianoChordList:
            cKL, vL, fKN, iconWidth = self.calculate(c)

            if currentWidth + iconWidth >= width + self.iconHzSpacing:
                bigList.append(currentList)
                currentList = [c]
                currentWidth = self.chartMargin
            else:
                currentList.append(c)
                currentWidth += self.iconHzSpacing
            currentWidth += iconWidth

        bigList.append(currentList)
        return bigList

    def calculate(self, c):
        voicingList = self.replaceFlats(c.voicings['piano'])
        # save this as we convert all the flats to sharps, but the user would probably like to see the name they entered...
        firstKeyName = c.voicings['piano'][0]
        chartKeyList = []

        # get the list of keys to be drawn for each chord
        for count, note in enumerate(voicingList):
            if count == 0:
                curIndex = self.keyList.index(note)
                if self.keyDict[self.keyList[curIndex-1]] == 'black':
                    chartKeyList.append(
                        self.keyList[curIndex-2])  # don't start on a black key
                chartKeyList.append(self.keyList[curIndex-1])  # the key before

                chartKeyList.append(note)
            else:
                lastIndex = self.keyList.index(lastNote)
                curIndex = self.keyList.index(note)

                if curIndex > lastIndex:
                    chartKeyList.extend(
                        self.keyList[lastIndex+1:((curIndex+1) % len(self.keyList))])
                elif curIndex < lastIndex:
                    chartKeyList.extend(self.keyList[lastIndex+1:])
                    chartKeyList.extend(
                        self.keyList[0:((curIndex+1) % len(self.keyList))])
                else:
                    chartKeyList.append(note)

            if count == len(voicingList) - 1:
                curIndex = self.keyList.index(note)
                chartKeyList.append(
                    self.keyList[((curIndex+1) % len(self.keyList))])
                # don't finish on a black key
                if self.keyDict[self.keyList[((curIndex+1) % len(self.keyList))]] == 'black':
                    chartKeyList.append(
                        self.keyList[((curIndex+2) % len(self.keyList))])

            lastNote = note

        iconWidth = sum([self.whiteKeyWidth if self.keyDict[k]
                         == 'white' else 0 for k in chartKeyList])

        return chartKeyList, voicingList, firstKeyName, iconWidth

    def draw(self):
        canvas = self.canv

        for index, cL in enumerate(self.splitChordList(self.pianoChordList, self.width)):
            h_offset = self.chartMargin
            v_offset = self.height - self.oneHeight * index - self.vSpacing * \
                index - self.chordNameFontSize * self.lineSpacing

            for c in cL:
                chartKeyList, voicingList, firstKeyName, iconWidth = self.calculate(
                    c)
                # draw chord names
                canvas.setFont(self.style.font, self.chordNameFontSize)
                canvas.drawCentredString(h_offset + iconWidth/2, v_offset+(
                    0.3*self.chordNameFontSize*self.lineSpacing), c.name)

                # draw the keys
                count = 0
                for key in chartKeyList:
                    if self.keyDict[key] == 'white':
                        canvas.rect(h_offset + (count*self.whiteKeyWidth), v_offset -
                                    self.whiteKeyHeight, self.whiteKeyWidth, self.whiteKeyHeight)
                        count += 1
                    elif self.keyDict[key] == 'black':
                        canvas.rect(h_offset + (count*self.whiteKeyWidth) - (self.blackKeyWidth/2),
                                    v_offset-self.blackKeyHeight, self.blackKeyWidth, self.blackKeyHeight, fill=1)

                # draw the indicator dots
                count = 0
                dotCount = 0
                for key in chartKeyList:
                    if self.keyDict[key] == 'white':
                        count += 1
                        if len(voicingList) > dotCount and key == voicingList[dotCount]:
                            hpos = h_offset + \
                                (count*self.whiteKeyWidth) - \
                                (self.whiteKeyWidth/2)
                            if dotCount == 0:
                                canvas.setFont(self.style.font,
                                               self.indicatorFontSize)
                                canvas.drawCentredString(
                                    hpos, v_offset - self.whiteKeyHeight*1.3, firstKeyName)
                            dotCount += 1
                            canvas.circle(hpos, v_offset - self.whiteKeyHeight + (self.whiteKeyWidth/2),
                                          self.dotRadius, stroke=0, fill=1)
                    elif self.keyDict[key] == 'black':
                        if len(voicingList) > dotCount and key == voicingList[dotCount]:
                            hpos = h_offset + \
                                (count*self.whiteKeyWidth)
                            if dotCount == 0:
                                canvas.setFont(self.style.font,
                                               self.indicatorFontSize)
                                canvas.drawCentredString(
                                    hpos, v_offset - self.whiteKeyHeight*1.3, firstKeyName)
                            dotCount += 1
                            canvas.setFillColor(white)
                            canvas.circle(hpos, v_offset - self.blackKeyHeight + (self.blackKeyWidth/2),
                                          self.dotRadius, stroke=0, fill=1)
                            canvas.setFillColor(black)

                h_offset += iconWidth + self.iconHzSpacing


class ChordProgression(Flowable):
    """
    Flowable that draws a chord progression made up of blocks.
    """

    def __init__(self, style, heading, blockList, timeSignature):
        self.style = style
        self.heading = heading  # the title of the section
        self.blockList = blockList
        self.timeSignature = timeSignature
        self.chartMargin = 0.7*mm  # kludge factor to account for line width

        self.unitHeight = 20*mm
        self.beatsHeight = 5*mm

        self.spaceAfter = self.style.separatorSize

    def wrapBlocks(self, blockList, maxWidth):
        """
        Splits any blocks that won't fit in the remaining space on the line.
        """
        h_loc = 0
        splitBlockList = []
        for i in range(len(blockList)):
            c_orig = blockList[i].chord
            n_orig = blockList[i].notes
            if h_loc == maxWidth:
                h_loc = 0
            if h_loc+blockList[i].length > maxWidth:
                lengthList = [maxWidth - h_loc]
                while sum(lengthList) < blockList[i].length:
                    if blockList[i].length - sum(lengthList) >= maxWidth:
                        lengthList.append(maxWidth)
                    else:
                        lengthList.append(
                            blockList[i].length - sum(lengthList))

                for l in lengthList:
                    # create a block with the given length
                    splitBlockList.append(Block(l, chord=c_orig, notes=n_orig))

                h_loc = lengthList[-1]
            else:
                splitBlockList.append(blockList[i])
                h_loc += blockList[i].length
        return splitBlockList

    def splitBlockList(self, blockList, length):
        """
        Splits a blockList into two lists, one of the given length (in beats) and one for the rest. Also wraps the blocks to
        given length in case the split would fall in the middle of one.
        """
        secondPart = self.wrapBlocks(blockList, length)
        firstPart = []
        currentBeat = 0
        while currentBeat != length:
            block = secondPart.pop(0)
            firstPart.append(block)
            currentBeat += block.length

        return firstPart, secondPart

    def wrap(self, availWidth, availHeight):
        self.widthInBeats = 2 * self.timeSignature * \
            trunc((availWidth/(self.style.unitWidth*self.style.unit)) /
                  (2*self.timeSignature))  # width of each line, in beats
        self.width = self.widthInBeats * self.style.unitWidth * self.style.unit
        self.height = self.beatsHeight + self.unitHeight * \
            sum([b.length for b in self.blockList]) / self.widthInBeats
        return(self.width, self.height)

    def split(self, availWidth, availHeight):
        if availHeight >= self.height:
            return [self]
        else:
            vUnits = trunc(
                (availHeight - self.beatsHeight) / self.unitHeight)
            firstPart, secondPart = self.splitBlockList(
                self.blockList, vUnits * self.widthInBeats)

            return [ChordProgression(self.style, self.heading, firstPart, self.timeSignature),
                    PageBreak(),
                    ChordProgression(self.style, self.heading, secondPart, self.timeSignature)]

    def draw(self):
        canvas = self.canv
        unitWidth = self.style.unitWidth*self.style.unit

        v_origin = self.height - self.beatsHeight
        h_offset = self.chartMargin

        h_loc = 0
        v_loc = 0

        maxWidth = self.widthInBeats

        for u in range(maxWidth+1):
            y = v_origin
            x = u*unitWidth + h_offset
            if u % self.timeSignature == 0:
                l = self.beatsHeight
            else:
                l = self.beatsHeight/2
            canvas.line(x, y, x, y+l)
            if u == maxWidth:  # Avoid writing beat number after the final line
                break
            writeText(canvas, self.style, str((u % self.timeSignature)+1), self.style.beatsFontSize,
                      v_origin+self.beatsHeight, self.width, hpos=x+unitWidth/2)

        parsedBlockList = self.wrapBlocks(self.blockList, maxWidth)

        for b in parsedBlockList:
            if h_loc == maxWidth:
                v_loc += 1
                h_loc = 0
            canvas.rect(h_offset+h_loc*unitWidth, v_origin-((v_loc+1)*self.unitHeight),
                        b.length*unitWidth, self.unitHeight)
            if b.notes is not None:
                writeText(canvas, self.style, b.notes, self.style.notesFontSize, v_origin-((v_loc+1)*self.unitHeight)+(
                    1.3*self.style.notesFontSize), self.width, hpos=h_offset+((h_loc+b.length/2)*unitWidth))
            v_offset = ((v_loc*self.unitHeight) +
                        self.unitHeight/2)-self.style.chordNameFontSize/2
            if b.chord is not None:
                writeText(canvas, self.style, b.chord.name, self.style.chordNameFontSize,
                          v_origin-v_offset, self.width, hpos=h_offset+((h_loc+b.length/2)*unitWidth))
            h_loc += b.length


def instChartCheck(cL, inst):
    """
    Check if a file contains a chord chart for a certain instrument.
    """
    chordsPresent = False
    for c in cL:
        if inst in c.voicings.keys():
            chordsPresent = True
            break
    return chordsPresent


class Renderer:
    def __init__(self, document, style):
        self.document = document
        self.style = style

    def savePDF(self, pathToPDF):
        template = PageTemplate(id='AllPages', frames=[Frame(self.style.leftMargin*mm, self.style.bottomMargin*mm,
                                                             self.style.pageSize[0] - self.style.leftMargin *
                                                             mm - self.style.rightMargin*mm,
                                                             self.style.pageSize[1] - self.style.topMargin *
                                                             mm - self.style.bottomMargin*mm,
                                                             leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)])

        rlDocList = []
        rlDoc = BaseDocTemplate(
            pathToPDF, pagesize=self.style.pageSize, pageTemplates=[template])

        styles = getStyleSheet(self.style)

        if self.document.title:
            rlDocList.append(Paragraph(self.document.title, styles['Title']))

        if self.document.subtitle:
            rlDocList.append(
                Paragraph(self.document.subtitle, styles['Subtitle']))

        if self.document.composer or self.document.arranger:
            rlDocList.append(Spacer(0, 2*mm))

        if self.document.composer:
            rlDocList.append(Paragraph("Composer: {c}".format(
                c=self.document.composer), styles['Credits']))

        if self.document.arranger:
            rlDocList.append(Paragraph("Arranger: {a}".format(
                a=self.document.arranger), styles['Credits']))

        if self.document.tempo:
            rlDocList.append(Tempo(self.document.tempo, styles['Tempo']))

        if self.document.title or self.document.subtitle or self.document.composer or self.document.arranger or self.document.tempo:
            rlDocList.append(Spacer(0, self.style.separatorSize))

        if instChartCheck(self.document.chordList, 'guitar'):
            rlDocList.extend([
                Paragraph('Guitar chord voicings', styles['Heading']),
                GuitarChart(self.style, self.document.chordList)])

        if instChartCheck(self.document.chordList, 'piano'):
            rlDocList.extend([
                Paragraph('Piano chord voicings', styles['Heading']),
                PianoChart(self.style, self.document.chordList)])

        for s in self.document.sectionList:
            rlDocList.append(Paragraph(s.name, styles['Heading']))
            # only draw the chord progression if there are blocks
            if s.blockList:
                rlDocList.append(ChordProgression(
                    self.style, s.name, s.blockList, self.document.timeSignature))

        rlDoc.build(rlDocList)

    def stream(self):
        virtualFile = BytesIO()
        self.savePDF(virtualFile)
        return virtualFile
