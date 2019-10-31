# -*- coding: utf-8 -*-

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.shapes import *

def writeText(currentCanvas, style, string, size, vpos, **kwargs):
	margin = style.leftMargin*style.unit
	
	align = kwargs.get('align', 'centre')
	if align == 'centre' or align == 'center':
		hpos = kwargs.get('hpos', style.pageSize[0]/2)
	elif align == 'left':
		hpos = kwargs.get('hpos', margin)
	elif align == 'right':
		hpos = kwargs.get('hpos', style.pageSize[0]-margin)
	spacing = kwargs.get('spacing', style.lineSpacing)
	
	currentCanvas.setFont(style.font, size)
	
	if align == 'centre' or align == 'center':
		currentCanvas.drawCentredString(hpos, vpos+(0.75*size*spacing),string)
	elif align == 'left':
		currentCanvas.drawString(hpos, vpos+(0.75*size*spacing),string)
	elif align == 'right':
		currentCanvas.drawString(hpos-currentCanvas.stringWidth(string), vpos+(0.75*size*spacing),string)

	return size*style.lineSpacing

def drawHorizLine(currentCanvas, startpoint, endpoint, v_pos, h_origin, v_origin):
	x1 = h_origin+startpoint
	x2 = h_origin+endpoint
	currentCanvas.line(x1, v_pos, x2, v_pos)
	
def drawVertLine(currentCanvas, startpoint, endpoint, h_pos, h_origin, v_origin):
	y1 = v_origin+startpoint
	y2 = v_origin+endpoint
	currentCanvas.line(h_pos, y1, h_pos, y2)
	