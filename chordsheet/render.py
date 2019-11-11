# -*- coding: utf-8 -*-

from math import trunc, ceil
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
        self.chartMargin = 15*mm
        self.nStrings = 6
        self.headingSize = 18

        self.spaceAfter = self.style.separatorSize

    def splitChordList(self, l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def wrap(self, availWidth, availHeight):
        self.nChords = trunc((availWidth - self.chartMargin -
                         self.style.stringHzGap) / self.style.stringHzSp)
        # the height of one layer of chart
        self.oneHeight = self.style.stringHeight * (self.nStrings+1)
        # only one line needed
        if len(self.guitarChordList) <= self.nChords:
            self.width = self.chartMargin + self.style.stringHzGap + self.style.stringHzSp * \
                len(self.guitarChordList)  # calculate the width
            self.height = self.oneHeight  # and its height
        # multiple lines needed
        else:
            self.width = self.chartMargin + self.style.stringHzGap + \
                self.style.stringHzSp * self.nChords
            self.height = self.oneHeight * ceil(len(self.guitarChordList) / self.nChords) + \
                (self.style.stringHeight *
                 trunc(len(self.guitarChordList) / self.nChords)) 
        return (self.width, self.height)

    def draw(self):
        canvas = self.canv
        chartmargin = self.chartMargin

        for count, gcl in enumerate(self.splitChordList(self.guitarChordList, self.nChords)):
            v_origin = self.height - count * (self.oneHeight + self.style.stringHeight)

            self.nStrings = 6
            fontsize = 12

            stringList = [
                [c.voicings['guitar'][-(r+1)] for c in gcl] for r in range(self.nStrings)]
            stringList.append([c.name for c in gcl])

            for i in range(self.nStrings+1):  # i is the string line currently being drawn
                writeText(canvas, self.style, ['e', 'B', 'G', 'D', 'A', 'E', 'Name'][i], fontsize, v_origin-(
                    i*self.style.stringHeight), self.width, hpos=chartmargin, align='right')

                # j is which chord (0 is first chord, 1 is 2nd etc)
                for j in range(len(stringList[-1])):
                    currentWidth = canvas.stringWidth(stringList[i][j])
                    if j == 0:
                        x = self.style.stringHzGap + chartmargin
                        l = self.style.stringHzSp/2 - self.style.stringHzGap - \
                            ((currentWidth/2)) - self.style.stringHzGap
                        y = v_origin-(self.style.stringHeight*i) - \
                            self.style.stringHeight/2
                        canvas.line(x, y, x+l, y)
                    else:
                        x = chartmargin + self.style.stringHzSp * \
                            (j-0.5)+(lastWidth/2+self.style.stringHzGap)
                        l = self.style.stringHzSp - currentWidth / \
                            2 - lastWidth/2 - self.style.stringHzGap*2
                        y = v_origin-(self.style.stringHeight*i) - \
                            self.style.stringHeight/2
                        canvas.line(x, y, x+l, y)

                    if j == len(stringList[-1])-1:
                        x = chartmargin + self.style.stringHzSp * \
                            (j+0.5) + currentWidth/2 + self.style.stringHzGap
                        l = self.style.stringHzSp/2 - currentWidth/2 - self.style.stringHzGap
                        y = v_origin-(self.style.stringHeight*i) - \
                            self.style.stringHeight/2
                        canvas.line(x, y, x+l, y)

                    writeText(canvas, self.style, stringList[i][j], fontsize, v_origin-(
                        i*self.style.stringHeight), self.width, hpos=chartmargin+self.style.stringHzSp*(j+0.5))

                    lastWidth = currentWidth


class ChordProgression(Flowable):
    """
    Flowable that draws a chord progression made up of blocks.
    """

    def __init__(self, style, heading, blockList, timeSignature):
        self.style = style
        self.heading = heading  # the title of the section
        self.blockList = blockList
        self.timeSignature = timeSignature
        self.headingSize = 18

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
                        # print(lengthList)
                    else:
                        lengthList.append(
                            blockList[i].length - sum(lengthList))
                        # print(lengthList)

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
        self.height = self.style.beatsHeight + self.style.unitHeight * \
            sum([b.length for b in self.blockList]) / self.widthInBeats
        return(self.width, self.height)

    def split(self, availWidth, availHeight):
        if availHeight >= self.height:
            return [self]
        else:
            vUnits = trunc(
                (availHeight - self.style.beatsHeight) / self.style.unitHeight)
            firstPart, secondPart = self.splitBlockList(
                self.blockList, vUnits * self.widthInBeats)

            return [ChordProgression(self.style, self.heading, firstPart, self.timeSignature),
                    PageBreak(),
                    ChordProgression(self.style, self.heading, secondPart, self.timeSignature)]

    def draw(self):
        canvas = self.canv
        unitWidth = self.style.unitWidth*self.style.unit

        v_origin = self.height - self.style.beatsHeight

        h_loc = 0
        v_loc = 0

        maxWidth = self.widthInBeats

        for u in range(maxWidth+1):
            y = v_origin
            x = u*unitWidth
            if u % self.timeSignature == 0:
                l = self.style.beatsHeight
            else:
                l = self.style.beatsHeight/2
            canvas.line(x, y, x, y+l)
            if u == maxWidth:  # Avoid writing beat number after the final line
                break
            writeText(canvas, self.style, str((u % self.timeSignature)+1), self.style.beatsFontSize,
                      v_origin+self.style.beatsHeight, self.width, hpos=x+unitWidth/2)

        parsedBlockList = self.wrapBlocks(self.blockList, maxWidth)

        for b in parsedBlockList:
            if h_loc == maxWidth:
                v_loc += 1
                h_loc = 0
            canvas.rect(h_loc*unitWidth, v_origin-((v_loc+1)*self.style.unitHeight),
                        b.length*unitWidth, self.style.unitHeight)
            if b.notes is not None:
                writeText(canvas, self.style, b.notes, self.style.notesFontSize, v_origin-((v_loc+1)*self.style.unitHeight)+(
                    1.3*self.style.notesFontSize), self.width, hpos=((h_loc+b.length/2)*unitWidth))
            v_offset = ((v_loc*self.style.unitHeight) +
                        self.style.unitHeight/2)-self.style.chordNameFontSize/2
            if b.chord is not None:
                writeText(canvas, self.style, b.chord.name, self.style.chordNameFontSize,
                          v_origin-v_offset, self.width, hpos=((h_loc+b.length/2)*unitWidth))
            h_loc += b.length


def guitarChartCheck(cL):
    chordsPresent = False
    for c in cL:
        if 'guitar' in c.voicings.keys():
            chordsPresent = True
            break
    return chordsPresent


class Renderer:
    def __init__(self, document, style):
        self.document = document
        self.style = style

    def savePDF(self, pathToPDF):
        template = PageTemplate(id='AllPages', frames=[Frame(self.style.leftMargin*mm, self.style.bottomMargin*mm,
                                                             self.style.pageSize[0] - self.style.leftMargin*mm - self.style.rightMargin*mm,
                                                             self.style.pageSize[1] - self.style.topMargin*mm - self.style.bottomMargin*mm,
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

        if guitarChartCheck(self.document.chordList):
            rlDocList.extend([
                Paragraph('Guitar chord voicings', styles['Heading']),
                GuitarChart(self.style, self.document.chordList)])

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
