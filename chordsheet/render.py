# -*- coding: utf-8 -*-

from math import trunc

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import BaseDocTemplate, Spacer, Paragraph, Flowable, Frame, PageTemplate

from chordsheet.document import Block


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


def splitBlocks(blockList, maxWidth):
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
                    lengthList.append(blockList[i].length - sum(lengthList))

            for l in lengthList:
                # create a block with the given length
                splitBlockList.append(Block(l, chord=c_orig, notes=n_orig))

            h_loc = lengthList[-1]
        else:
            splitBlockList.append(blockList[i])
            h_loc += blockList[i].length
    return splitBlockList


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

        self.spaceAfter = self.style.separatorSize * mm

    def wrap(self, availWidth, availHeight):
        self.width = self.chartMargin + self.style.stringHzGap + self.style.stringHzSp * \
            (len(self.guitarChordList))  # calculate the width of the flowable
        self.height = self.style.stringHeight * \
            (self.nStrings+1) + self.headingSize * \
            self.style.lineSpacing + 2*mm    # and its height
        return (self.width, self.height)

    def draw(self):
        canvas = self.canv
        title_height = writeText(canvas, self.style, "Guitar chord voicings",
                                 self.headingSize, self.height, self.width, align="left")

        chartmargin = self.chartMargin
        v_origin = self.height - title_height - 2*mm
        h_origin = chartmargin
        self.nStrings = 6
        fontsize = 12

        stringList = [
            [c.voicings['guitar'][-(r+1)] for c in self.guitarChordList] for r in range(self.nStrings)]
        stringList.append([c.name for c in self.guitarChordList])

        for i in range(self.nStrings+1):  # i is the string line currently being drawn
            writeText(canvas, self.style, ['e', 'B', 'G', 'D', 'A', 'E', 'Name'][i], fontsize, v_origin-(
                i*self.style.stringHeight), self.width, hpos=h_origin, align='right')

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

    def __init__(self, style, blockList, timeSignature):
        self.style = style
        self.blockList = blockList
        self.timeSignature = timeSignature
        self.headingSize = 18

        self.spaceAfter = self.style.separatorSize * mm

    def wrap(self, availWidth, availHeight):
        self.widthInBeats = 2 * self.timeSignature * \
            trunc((availWidth/(self.style.unitWidth*self.style.unit)) /
                  (2*self.timeSignature))  # width of each line, in beats
        self.width = self.widthInBeats * self.style.unitWidth * self.style.unit
        self.height = self.headingSize * self.style.lineSpacing + 2 * mm + self.style.beatsHeight + \
            self.style.unitHeight * \
            sum([b.length for b in self.blockList]) / self.widthInBeats
        return(self.width, self.height)

    def draw(self):
        canvas = self.canv
        unitWidth = self.style.unitWidth*self.style.unit

        title_height = writeText(canvas, self.style, "Chord progression",
                                 self.headingSize, self.height, self.width, align="left")

        v_origin = self.height - self.style.beatsHeight - title_height - 2*mm
        h_origin = 0

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

        parsedBlockList = splitBlocks(self.blockList, maxWidth)

        for b in parsedBlockList:
            if h_loc == maxWidth:
                v_loc += 1
                h_loc = 0
            canvas.rect(h_loc*unitWidth, v_origin-((v_loc+1)*self.style.unitHeight),
                        b.length*unitWidth, self.style.unitHeight)
            if b.notes is not None:
                writeText(canvas, self.style, b.notes, self.style.notesFontSize, v_origin-((v_loc+1)*self.style.unitHeight)+(
                    1.3*self.style.notesFontSize), self.width, hpos=h_origin+((h_loc+b.length/2)*unitWidth))
            v_offset = ((v_loc*self.style.unitHeight) +
                        self.style.unitHeight/2)-self.style.chordNameFontSize/2
            if b.chord is not None:
                writeText(canvas, self.style, b.chord.name, self.style.chordNameFontSize,
                          v_origin-v_offset, self.width, hpos=h_origin+((h_loc+b.length/2)*unitWidth))
            h_loc += b.length


def guitarChartCheck(cL):
    chordsPresent = False
    for c in cL:
        if 'guitar' in c.voicings.keys():
            chordsPresent = True
            break
    return chordsPresent


class TitleBlock(Flowable):
    """
    Flowable that draws the title and other text at the top of the document.
    """

    def __init__(self, style, document):
        self.style = style
        self.lS = style.lineSpacing

        self.title = document.title
        self.subtitle = document.subtitle
        self.composer = document.composer
        self.arranger = document.arranger
        self.tempo = document.tempo

        self.spaceAfter = self.style.separatorSize * mm

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.height = sum([self.style.titleFontSize * self.lS if self.title else 0,
                           self.style.subtitleFontSize * self.lS if self.subtitle else 0,
                           self.style.creditsFontSize * self.lS if self.composer else 0,
                           self.style.titleFontSize * self.lS if self.arranger else 0,
                           self.style.tempoFontSize * self.lS if self.tempo else 0])
        return(self.width, self.height)

    def draw(self):
        canvas = self.canv
        curPos = self.height

        if self.title:
            curPos -= writeText(canvas, self.style,
                                self.title, 24, curPos, self.width)

        if self.subtitle:
            curPos -= writeText(canvas, self.style,
                                self.subtitle, 18, curPos, self.width)

        if self.composer:
            curPos -= writeText(canvas, self.style,
                                "Composer: {c}".format(c=self.composer), 12, curPos, self.width)

        if self.arranger:
            curPos -= writeText(canvas, self.style,
                                "Arranger: {a}".format(a=self.arranger), 12, curPos, self.width)

        if self.tempo:
            curPos -= writeText(canvas, self.style, "♩ = {t} bpm".format(
                t=self.tempo), 12, curPos, self.width, align="left")


def savePDF(document, style, pathToPDF):
    template = PageTemplate(id='AllPages', frames=[Frame(style.leftMargin*mm, style.topMargin*mm, style.pageSize[0] - style.leftMargin*mm*2, style.pageSize[1] - style.topMargin*mm*2,
                                                         leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)])

    rlDocList = []
    rlDoc = BaseDocTemplate(
        pathToPDF, pagesize=style.pageSize, pageTemplates=[template])

    if document.title:
        rlDocList.append(TitleBlock(style, document))

    if guitarChartCheck(document.chordList):
        rlDocList.append(GuitarChart(style, document.chordList))

    if document.blockList:
        rlDocList.append(ChordProgression(
            style, document.blockList, document.timeSignature))

    rlDoc.build(rlDocList)
