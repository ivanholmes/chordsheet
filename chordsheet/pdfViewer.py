from PyQt5.QtWidgets import QScrollArea, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

import fitz

class PDFViewer(QScrollArea):
    def __init__(self, parent):
        super().__init__(parent)
        self.scrollAreaContents = QWidget()
        self.scrollAreaLayout = QVBoxLayout()

        self.setWidget(self.scrollAreaContents)
        self.setWidgetResizable(True)

        self.scrollAreaContents.setLayout(self.scrollAreaLayout)
        self.pixmapList = []

    def resizeEvent(self, event):
        pass
        # do something about this later
    
    def update(self, pdf):
        self.render(pdf)
        self.clear()
        self.show()

    def render(self, pdf):
        """
        Update the preview shown by rendering a new PDF and drawing it to the scroll area.
        """

        self.pixmapList = []
        pdfView = fitz.Document(stream=pdf, filetype='pdf')
        # render at 4x resolution and scale
        for page in pdfView:
            self.pixmapList.append(page.getPixmap(matrix=fitz.Matrix(4, 4), alpha=False))
                    
    def clear(self):
        while self.scrollAreaLayout.count():
            item = self.scrollAreaLayout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
    
    def show(self):
        for p in self.pixmapList:
            label = QLabel(parent=self.scrollAreaContents)
            label.setAlignment(Qt.AlignHCenter)
            qtimg = QImage(p.samples, p.width, p.height, p.stride, QImage.Format_RGB888)
            # -45 because of various margins... value obtained by trial and error.
            label.setPixmap(QPixmap.fromImage(qtimg).scaled(self.width()-45, self.height()*2, Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation))
            self.scrollAreaLayout.addWidget(label)
        
        # necessary on Mojave with PyInstaller (or previous contents will be shown)
        self.repaint()