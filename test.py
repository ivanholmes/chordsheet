import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from chordsheet.document import Document, Style
from chordsheet.render import Renderer

pdfmetrics.registerFont(TTFont('FreeSans', os.path.join('fonts', 'FreeSans.ttf')))

doc = Document.newFromXML('examples/angela.xml')
style = Style(unitWidth=20)
ren = Renderer(doc, style)

ren.savePDF('test.pdf') 