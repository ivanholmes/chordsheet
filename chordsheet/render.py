# -*- coding: utf-8 -*-

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.shapes import *
from chordsheet.primitives import writeText, drawVertLine, drawHorizLine
from chordsheet.document import Block

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
				splitBlockList.append(Block(l, chord=c_orig, notes=n_orig)) # create a block with the given length

			h_loc = lengthList[-1]
		else:
			splitBlockList.append(blockList[i])
			h_loc += blockList[i].length
	return splitBlockList

def guitarChart(currentCanvas, style, chordList, cur_pos):
	title_height = writeText(currentCanvas, style, "Guitar chord voicings", 18, cur_pos, align="left")
	cur_pos += title_height
	
	string_hz_sp = style.stringHzSp
	string_hz_gap = style.stringHzGap
	string_height = style.stringHeight
	
	margin = style.leftMargin*style.unit
	pagesize = style.pageSize
	
	chartmargin = 15*mm
	v_origin = cur_pos + 2*mm
	h_origin = margin + chartmargin
	nstrings = 6
	fontsize = 12
	
	guitarChordList = [[chordList[q].guitar[-(r+1)] for q in range(len(chordList)) if hasattr(chordList[q], 'guitar')] for r in range(6)]
	guitarChordList.append([chordList[q].name for q in range(len(chordList)) if hasattr(chordList[q], 'guitar')])
	
	for i in range(nstrings+1): # i is the string currently being drawn
		writeText(currentCanvas, style, ['e','B','G','D','A','E','Name'][i], fontsize, v_origin+(i*string_height), hpos=h_origin, align='right')

		for j in range(len(guitarChordList[-1])): # j is which chord (0 is first chord, 1 is 2nd etc)
			if j == 0:
				charpos = string_hz_sp/2
				s = string_hz_gap
				e = charpos-((currentCanvas.stringWidth(guitarChordList[i][j])/2)+string_hz_gap)
				y = v_origin+(string_height*i)+string_height/2
				drawHorizLine(currentCanvas, s, e, y, h_origin, v_origin)
			else:
				charpos = string_hz_sp*(j+0.5)
				s = charpos-string_hz_sp+(lastWidth/2+string_hz_gap)
				e = charpos-((currentCanvas.stringWidth(guitarChordList[i][j])/2)+string_hz_gap)
				y = v_origin+(string_height*i)+string_height/2
				drawHorizLine(currentCanvas, s, e, y, h_origin, v_origin)
			
			if j == len(guitarChordList[-1])-1:
				s = charpos+(currentCanvas.stringWidth(guitarChordList[i][j])/2+string_hz_gap)
				e = charpos+string_hz_sp/2
				y = v_origin+(string_height*i)+string_height/2
				drawHorizLine(currentCanvas, s, e, y, h_origin, v_origin)

			writeText(currentCanvas, style, guitarChordList[i][j], fontsize, v_origin+(i*string_height), hpos=h_origin+charpos)
			
			lastWidth = currentCanvas.stringWidth(guitarChordList[i][j])
			
	return (string_height*(nstrings+1)) + title_height # calculate the height of the block

def chordProgression(currentCanvas, style, document, cur_pos):
		margin = style.leftMargin*style.unit
		pagesize = style.pageSize
		
		title_height = writeText(currentCanvas, style, "Chord progression", 18, cur_pos, align="left")
		cur_pos += title_height
		
		v_origin = cur_pos + 2*mm + style.beatsHeight
		h_origin = margin
		
		h_loc = 0
		v_loc = 0
		
		maxWidth = int((((pagesize[0]-(2*margin))/style.unitWidth)//(document.timeSignature*2))*(document.timeSignature*2)) # use integer division to round maxWidth to nearest two bars
		
		for u in range(maxWidth+1):
			s = 0
			x = u*style.unitWidth+margin
			if u % document.timeSignature == 0:
				e = -style.beatsHeight
			else: 
				e = -style.beatsHeight/2
			drawVertLine(currentCanvas, s, e, x, h_origin, v_origin)
			if u == maxWidth: # Avoid writing beat number after the final line
				break
			writeText(currentCanvas, style, str((u % document.timeSignature)+1), style.beatsFontSize, v_origin-style.beatsHeight, hpos=x+style.unitWidth/2)
			
		parsedBlockList = splitBlocks(document.blockList, maxWidth)
		
		for b in parsedBlockList:
			if h_loc == maxWidth:
				v_loc += 1
				h_loc = 0
			currentCanvas.rect(h_origin+(h_loc*style.unitWidth), v_origin+(v_loc*style.unitHeight), b.length*style.unitWidth, style.unitHeight)
			if b.notes is not None:
				writeText(currentCanvas, style, b.notes, style.notesFontSize, v_origin+((v_loc+1)*style.unitHeight)-(1.3*style.notesFontSize), hpos=h_origin+((h_loc+b.length/2)*style.unitWidth))
			v_offset = ((v_loc*style.unitHeight)+style.unitHeight/2)-style.chordNameFontSize/2
			if b.chord is not None:
				writeText(currentCanvas, style, b.chord.name, style.chordNameFontSize, v_origin+v_offset, hpos=h_origin+((h_loc+b.length/2)*style.unitWidth))
			h_loc += b.length
		
		return v_origin + (v_loc+1)*style.unitHeight + style.beatsHeight + title_height # calculate the height of the generated chart

def guitarChartCheck(cL):
	chordsPresent = False
	for c in cL:
		if hasattr(c, 'guitar'):
			chordsPresent = True
			break
	return chordsPresent

def savePDF(document, style, pathToPDF):
	
		c = canvas.Canvas(pathToPDF, pagesize=style.pageSize, bottomup=0)
		
		curPos = style.topMargin*style.unit
		
		if document.title is not None:
			curPos += writeText(c, style, document.title, 24, curPos)
		
		if document.composer is not None:
			curPos += writeText(c, style, "Composer: {c}".format(c = document.composer), 12, curPos)
		
		if document.arranger is not None:
			curPos += writeText(c, style, "Arranger: {a}".format(a = document.arranger), 12, curPos)
		
		curPos += style.separatorSize*style.unit
			
		if guitarChartCheck(document.chordList):
			curPos += guitarChart(c, style, document.chordList, curPos)
		
		curPos += style.separatorSize*style.unit
			
		if document.blockList:
			curPos += chordProgression(c, style, document, curPos)
		
		curPos += style.separatorSize*style.unit
		
		c.save()