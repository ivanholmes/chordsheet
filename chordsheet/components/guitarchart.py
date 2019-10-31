# -*- coding: utf-8 -*-

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import *

from graphics.primitives import *

string_hz_sp = 20*mm
string_hz_gap = 2*mm
string_height = 5*mm

def guitarChart(currentCanvas, string_hz_sp, string_hz_gap, string_height):
	global cur_pos, margin, pagesize
	
	writeText("Guitar chord voicings", size=18, align="left")
	
	chartmargin = 15*mm
	v_origin = cur_pos + 2*mm
	h_origin = margin + chartmargin
	nstrings = 6
	fontsize = 12
	
	guitarChordList = [[chordList[q].guitar[r] for q in range(len(chordList)) if hasattr(chordList[q], 'guitar')] for r in range(6)]
	guitarChordList.append([chordList[q].name for q in range(len(chordList))])
	
	for i in range(nstrings+1): # i is the string currently being drawn
		writeText(['e','B','G','D','A','E','Name'][i], size=fontsize, hpos=(h_origin), vpos=v_origin+(i*string_height), align='right')

		for j in range(len(ls.chords)): # j is which chord (0 is first chord, 1 is 2nd etc)
			if j == 0:
				charpos = string_hz_sp/2
				s = string_hz_gap
				e = charpos-((c.stringWidth(chordList[i][j])/2)+string_hz_gap)
				y = v_origin+(string_height*i)+string_height/2
				drawHorizLine(currentCanvas, s, e, y, h_origin, v_origin)
			else:
				charpos = string_hz_sp*(j+0.5)
				s = charpos-string_hz_sp+(lastWidth/2+string_hz_gap)
				e = charpos-((currentCanvas.stringWidth(chordList[i][j])/2)+string_hz_gap)
				y = v_origin+(string_height*i)+string_height/2
				drawHorizLine(currentCanvas, s, e, y, h_origin, v_origin)
				if j == len(ls.chords)-1:
					s = charpos+(currentCanvas.stringWidth(chordList[i][j])/2+string_hz_gap)
					e = charpos+string_hz_sp/2
					y = v_origin+(string_height*i)+string_height/2
					drawHorizLine(currentCanvas, s, e, y, h_origin, v_origin)

			writeText(chordList[i][j], size=fontsize, hpos=h_origin+charpos, vpos=v_origin+(i*string_height))
			
			lastWidth = currentCanvas.stringWidth(chordList[i][j])
			
	cur_pos += (string_height*(nstrings+2))