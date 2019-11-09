from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from chordsheet.document import Document, Style
from chordsheet.render import savePDF

pdfmetrics.registerFont(TTFont('FreeSans', os.path.join('fonts', 'FreeSans.ttf')))

doc = Document.newFromXML('examples/example.xml')
style = Style()

savePDF(doc, style, 'test.pdf')  