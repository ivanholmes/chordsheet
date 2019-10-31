# -*- coding: utf-8 -*-

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import *

from graphics.primitives import *

class ChordProgression:
	def __init__(self, currentCanvas, blockList, **kwargs):
		self.currentCanvas = currentCanvas
		
		self.beatsHeight = kwargs.get('beatsHeight', 5*mm)
		self.timeFontSize = kwargs.get('timeFontSize', 12)
		self.chordNameFontSize = kwargs.get('chordNameFontSize', 18)
		self.notesFontSize = kwargs.get('notesFontSize', 12)
		self.unitWidth = kwargs.get('unitWidth', 10*mm)
		self.unitHeight = kwargs.get('unitHeight', 20*mm)
		
		self.timeSignature = kwargs.get('timeSignature', 4)
	def draw(self):
		global cur_pos, margin, pagesize
		writeText(self.currentCanvas, "Chord progression", size=18, align="left")
		
		v_origin = cur_pos + 2*mm + self.beatsHeight
		h_origin = margin
		
		h_loc = 0
		v_loc = 0
		
		maxWidth = int((((pagesize[0]-(2*margin))/self.unitWidth)//(self.timeSignature*2))*(self.timeSignature*2)) # use integer division to round maxWidth to nearest multiple of time signature
		
		for u in range(maxWidth+1):
			s = 0
			x = u*self.unitWidth+margin
			if u % self.timeSignature == 0:
				e = -self.beatsHeight
			else: 
				e = -self.beatsHeight/2
			drawVertLine(self.currentCanvas, s, e, x, h_origin, v_origin)
			if u == maxWidth: # Avoid writing beat number after the final line
				break
			writeText(str((u % self.timeSignature)+1),size=self.timeFontSize, hpos=x+self.unitWidth/2, vpos=v_origin-self.beatsHeight)
			
		blockList = parseBlockList(self.blockList, maxWidth)
		
		for b in blockList:
			if h_loc == maxWidth:
				v_loc += 1
				h_loc = 0
			currentCanvas.rect(h_origin+(h_loc*self.unitWidth), v_origin+(v_loc*self.unitHeight), b[0]*self.unitWidth, self.unitHeight)
			if b[2]:
				writeText(currentCanvas, b[2], size=self.notesFontSize, hpos=h_origin+((h_loc+b[0]/2)*self.unitWidth), vpos=v_origin+((v_loc+1)*self.unitHeight)-(1.3*self.notesFontSize))
			v_offset = (v_loc*self.unitHeight+self.unitHeight/2)-self.chordNameFontSize/2
			writeText(currentCanvas, parseName(b[1]), size=self.chordNameFontSize, hpos=h_origin+((h_loc+b[0]/2)*self.unitWidth), vpos=v_origin+v_offset)
			h_loc += b[0]
		
		cur_pos = v_origin+(v_loc+1)*self.unitHeight+self.beatsHeight