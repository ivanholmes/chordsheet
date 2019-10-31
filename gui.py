#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 29 00:02:24 2019

@author: ivan
"""

import sys, fitz, io, subprocess, os

from PyQt5.QtWidgets import QApplication, QAction, QLabel, QDialogButtonBox, QDialog, QFileDialog, QMessageBox, QPushButton, QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QComboBox, QWidget, QScrollArea
from PyQt5.QtCore import QFile, QObject
from PyQt5.QtGui import QPixmap, QImage
from PyQt5 import uic
from chordsheet.tableView import ChordTableView, BlockTableView , MItemModel, MProxyStyle
 
from reportlab.lib.units import mm, cm, inch, pica
from reportlab.lib.pagesizes import A4, A5, LETTER, LEGAL
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from chordsheet.document import Document, Style, Chord, Block
from chordsheet.render import savePDF
from chordsheet.parsers import parseFingering, parseName

if getattr(sys, 'frozen', False):
    scriptDir = sys._MEIPASS
else:
    scriptDir = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

pdfmetrics.registerFont(TTFont('FreeSans', os.path.join(scriptDir, 'fonts', 'FreeSans.ttf')))
if sys.platform == "darwin":
    pdfmetrics.registerFont(TTFont('HelveticaNeue', 'HelveticaNeue.ttc', subfontIndex=0))

pageSizeDict = {'A4':A4, 'A5':A5, 'Letter':LETTER, 'Legal':LEGAL}
unitDict = {'mm':mm, 'cm':cm, 'inch':inch, 'point':1, 'pica':pica}  # point is 1 because reportlab's native unit is points.

class DocumentWindow(QWidget):
    def __init__(self, doc, style, parent=None):
        super().__init__(parent)
        
        self.doc = doc
        self.style = style
                
        self.UIFileLoader(str(os.path.join(scriptDir, 'ui','mainwindow.ui')))
        self.UIInitStyle()
        # self.UIInitDocument()
        
    def UIFileLoader(self, ui_file):
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
 
        self.window = uic.loadUi(ui_file)
        ui_file.close()
        
        self.window.actionNew.triggered.connect(self.menuFileNewAction)
        self.window.actionOpen.triggered.connect(self.menuFileOpenAction)
        self.window.actionSave.triggered.connect(self.menuFileSaveAction)
        self.window.actionSave_as.triggered.connect(self.menuFileSaveAsAction)
        self.window.actionSave_PDF.triggered.connect(self.menuFileSavePDFAction)
        self.window.actionPrint.triggered.connect(self.menuFilePrintAction)
        self.window.actionClose.triggered.connect(self.menuFileCloseAction)
        
        self.window.pageSizeComboBox.currentIndexChanged.connect(self.pageSizeAction)
        self.window.documentUnitsComboBox.currentIndexChanged.connect(self.unitAction)

        self.window.includedFontCheckBox.stateChanged.connect(self.includedFontAction)
        
        self.window.generateButton.clicked.connect(self.generateAction)

        self.window.guitarVoicingButton.clicked.connect(self.guitarVoicingAction)
        self.window.addChordButton.clicked.connect(self.addChordAction)
        self.window.removeChordButton.clicked.connect(self.removeChordAction)
        self.window.updateChordButton.clicked.connect(self.updateChordAction)
        
        self.window.addBlockButton.clicked.connect(self.addBlockAction)
        self.window.removeBlockButton.clicked.connect(self.removeBlockAction)
        self.window.updateBlockButton.clicked.connect(self.updateBlockAction)

        self.window.chordTableView.clicked.connect(self.chordClickedAction)
        self.window.blockTableView.clicked.connect(self.blockClickedAction)
        
    def UIInitDocument(self):

        self.window.titleLineEdit.setText(self.doc.title)
        self.window.composerLineEdit.setText(self.doc.composer)
        self.window.arrangerLineEdit.setText(self.doc.arranger)
        self.window.timeSignatureSpinBox.setValue(self.doc.timeSignature)
        
        # chord and block table lists here
        self.window.chordTableView.populate(self.doc.chordList)
        self.window.blockTableView.populate(self.doc.blockList)
        self.updateChordDict()

        self.window.tabWidget.setCurrentWidget(self.window.tabWidget.findChild(QWidget, 'Overview'))
        # self.updatePreview()
        
    def UIInitStyle(self):
        self.window.pageSizeComboBox.addItems(list(pageSizeDict.keys()))
        self.window.pageSizeComboBox.setCurrentText(list(pageSizeDict.keys())[0])
        
        self.window.documentUnitsComboBox.addItems(list(unitDict.keys()))
        self.window.documentUnitsComboBox.setCurrentText(list(unitDict.keys())[0])
        
        self.window.lineSpacingDoubleSpinBox.setValue(self.style.lineSpacing)
        
        self.window.leftMarginLineEdit.setText(str(self.style.leftMargin))
        self.window.topMarginLineEdit.setText(str(self.style.topMargin))
        
        self.window.fontComboBox.setDisabled(True)
        self.window.includedFontCheckBox.setChecked(True)
        
    def pageSizeAction(self, index):
        self.pageSizeSelected = self.window.pageSizeComboBox.itemText(index)
        
    def unitAction(self, index):
        self.unitSelected = self.window.documentUnitsComboBox.itemText(index)
        
    def includedFontAction(self):
        if self.window.includedFontCheckBox.isChecked():
            self.style.useIncludedFont = True
        else:
            self.style.useIncludedFont = False
            
    def chordClickedAction(self, index):
        self.window.chordNameLineEdit.setText(self.window.chordTableView.model.item(index.row(), 0).text())
        self.window.guitarVoicingLineEdit.setText(self.window.chordTableView.model.item(index.row(), 1).text())

    def blockClickedAction(self, index):
        self.window.blockChordComboBox.setCurrentText(self.window.blockTableView.model.item(index.row(), 0).text())
        self.window.blockLengthLineEdit.setText(self.window.blockTableView.model.item(index.row(), 1).text())
        self.window.blockNotesLineEdit.setText(self.window.blockTableView.model.item(index.row(), 2).text())

    def menuFileNewAction(self):
        self.doc = Document()
    
    def menuFileOpenAction(self):
        filePath = QFileDialog.getOpenFileName(self.window.tabWidget, 'Open file', str(os.path.expanduser("~")), "Chordsheet ML files (*.xml *.cml)")
        if filePath[0]:
            self.currentFilePath = filePath[0]
            self.doc.loadXML(filePath[0])
            self.UIInitDocument()
            self.updatePreview()
    
    def menuFileSaveAction(self):
        self.updateDocument()
        if not (hasattr(self, 'currentFilePath') and self.currentFilePath):
            filePath = QFileDialog.getSaveFileName(self.window.tabWidget, 'Save file', str(os.path.expanduser("~")), "Chordsheet ML files (*.xml *.cml)")
            self.currentFilePath = filePath[0]
        self.doc.saveXML(self.currentFilePath)
    
    def menuFileSaveAsAction(self):
        self.updateDocument()
        filePath = QFileDialog.getSaveFileName(self.window.tabWidget, 'Save file', str(os.path.expanduser("~")), "Chordsheet ML files (*.xml *.cml)")
        if filePath[0]:
            self.currentFilePath = filePath[0]
            self.doc.saveXML(self.currentFilePath)
    
    def menuFileSavePDFAction(self):
        self.updateDocument()
        self.updatePreview()
        filePath = QFileDialog.getSaveFileName(self.window.tabWidget, 'Save file', str(os.path.expanduser("~")), "PDF files (*.pdf)")
        if filePath[0]:
            savePDF(d, s, filePath[0])
    
    def menuFilePrintAction(self):
        if sys.platform == "darwin":
            pass
        #    subprocess.call()
        else:
            pass
            
    def menuFileCloseAction(self):
        pass
    
    def guitarVoicingAction(self):
        gdialog = GuitarDialog()
        
        voicing = gdialog.getVoicing()
        if voicing:
            self.window.guitarVoicingLineEdit.setText(voicing)

    def clearChordLineEdits(self):
        self.window.chordNameLineEdit.clear()
        self.window.guitarVoicingLineEdit.clear()
        self.window.chordNameLineEdit.repaint() # necessary on Mojave with PyInstaller (or previous contents will be shown)
        self.window.guitarVoicingLineEdit.clear()

    def updateChordDict(self):
        self.chordDict = {c.name:c for c in self.doc.chordList}
        self.window.blockChordComboBox.clear()
        self.window.blockChordComboBox.addItems(list(self.chordDict.keys()))

    def removeChordAction(self):
        self.updateChords()
        
        row = self.window.chordTableView.selectionModel().currentIndex().row()
        self.doc.chordList.pop(row)

        self.window.chordTableView.populate(self.doc.chordList)
        self.clearChordLineEdits()
        self.updateChordDict()
    
    def addChordAction(self):
        self.updateChords()

        self.doc.chordList.append(Chord(parseName(self.window.chordNameLineEdit.text())))
        if self.window.guitarVoicingLineEdit.text():
            setattr(self.doc.chordList[-1], 'guitar', parseFingering(self.window.guitarVoicingLineEdit.text(), 'guitar'))

        self.window.chordTableView.populate(self.doc.chordList)
        self.clearChordLineEdits()
        self.updateChordDict()

    def updateChordAction(self):
        if self.window.chordTableView.selectionModel().hasSelection():
            self.updateChords()
            row = self.window.chordTableView.selectionModel().currentIndex().row()
            self.doc.chordList[row] = Chord(parseName(self.window.chordNameLineEdit.text()))
            if self.window.guitarVoicingLineEdit.text():
                setattr(self.doc.chordList[row], 'guitar', parseFingering(self.window.guitarVoicingLineEdit.text(), 'guitar'))

            self.window.chordTableView.populate(self.doc.chordList)
            self.clearChordLineEdits()
            self.updateChordDict()
    
    def clearBlockLineEdits(self):
        self.window.blockLengthLineEdit.clear()
        self.window.blockNotesLineEdit.clear()
        self.window.blockLengthLineEdit.repaint() # necessary on Mojave with PyInstaller (or previous contents will be shown)
        self.window.blockNotesLineEdit.repaint()

    def removeBlockAction(self):
        self.updateBlocks()

        row = self.window.blockTableView.selectionModel().currentIndex().row()
        self.doc.blockList.pop(row)

        self.window.blockTableView.populate(self.doc.blockList)
    
    def addBlockAction(self):
        self.updateBlocks()

        self.doc.blockList.append(Block(self.window.blockLengthLineEdit.text(),
                                        chord = self.chordDict[self.window.blockChordComboBox.currentText()],
                                        notes = (self.window.blockNotesLineEdit.text() if not "" else None)))

        self.window.blockTableView.populate(self.doc.blockList)
        self.clearBlockLineEdits()

    def updateBlockAction(self):
        if self.window.blockTableView.selectionModel().hasSelection():
            self.updateBlocks()
            row = self.window.blockTableView.selectionModel().currentIndex().row()
            self.doc.blockList[row] = (Block(self.window.blockLengthLineEdit.text(),
                                         chord = self.chordDict[self.window.blockChordComboBox.currentText()],
                                         notes = (self.window.blockNotesLineEdit.text() if not "" else None)))

            self.window.blockTableView.populate(self.doc.blockList)
            self.clearBlockLineEdits()
    
    def generateAction(self):
        self.updateDocument()
        self.updatePreview()

    def updatePreview(self):
        self.currentPreview = io.BytesIO()
        savePDF(self.doc, self.style, self.currentPreview)
        
        pdfView = fitz.Document(stream=self.currentPreview, filetype='pdf')
        pix = pdfView[0].getPixmap(alpha = False)

        fmt = QImage.Format_RGB888
        qtimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)

        self.window.imageLabel.setPixmap(QPixmap.fromImage(qtimg))
        self.window.imageLabel.repaint() # necessary on Mojave with PyInstaller (or previous contents will be shown)

    def updateChords(self):
        chordTableList = []
        for i in range(self.window.chordTableView.model.rowCount()):
            chordTableList.append(Chord(parseName(self.window.chordTableView.model.item(i, 0).text()))),
            if self.window.chordTableView.model.item(i, 1).text():
                chordTableList[-1].guitar = parseFingering(self.window.chordTableView.model.item(i, 1).text(), 'guitar')
            
        self.doc.chordList = chordTableList
    
    def updateBlocks(self):
        blockTableList = []
        for i in range(self.window.blockTableView.model.rowCount()):
            blockLength = int(self.window.blockTableView.model.item(i, 1).text())
            blockChordName = parseName(self.window.blockTableView.model.item(i, 0).text())
            if blockChordName:
                blockChord = None
                for c in self.doc.chordList:
                    if c.name == blockChordName:
                        blockChord = c
                        break
                if blockChord is None:
                    exit("Chord {c} does not match any chord in {l}.".format(c=blockChordName, l=self.doc.chordList))
            else:
                blockChord = None
            blockNotes = self.window.blockTableView.model.item(i, 2).text() if self.window.blockTableView.model.item(i, 2).text() else None
            blockTableList.append(Block(blockLength, chord=blockChord, notes=blockNotes))
        
        self.doc.blockList = blockTableList

    def updateDocument(self):
        self.doc.title = self.window.titleLineEdit.text() # Title can be empty string but not None
        self.doc.composer = (self.window.composerLineEdit.text() if self.window.composerLineEdit.text() else None)
        self.doc.arranger = (self.window.arrangerLineEdit.text() if self.window.arrangerLineEdit.text() else None)
        
        self.doc.timeSignature = int(self.window.timeSignatureSpinBox.value())
        self.style.pageSize = pageSizeDict[self.pageSizeSelected]
        self.style.unit = unitDict[self.unitSelected]
        self.style.leftMargin = int(self.window.leftMarginLineEdit.text())
        self.style.topMargin = int(self.window.topMarginLineEdit.text())
        self.style.lineSpacing = float(self.window.lineSpacingDoubleSpinBox.value())

        self.updateChords()
        self.updateBlocks()
        
        self.style.font = ('FreeSans' if self.style.useIncludedFont else 'HelveticaNeue')
        # something for the font box here
        
class GuitarDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.UIFileLoader(str(os.path.join(scriptDir, 'ui','guitardialog.ui')))
        
    def UIFileLoader(self, ui_file):
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
 
        self.dialog = uic.loadUi(ui_file)
        ui_file.close()

    def getVoicing(self):
        if self.dialog.exec_() == QDialog.Accepted:
            result = [self.dialog.ELineEdit.text(),
                      self.dialog.ALineEdit.text(),
                      self.dialog.DLineEdit.text(),
                      self.dialog.GLineEdit.text(),
                      self.dialog.BLineEdit.text(),
                      self.dialog.eLineEdit.text()]
            resultJoined = ",".join(result)
            return resultJoined
        else:
            return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    d = Document()
    s = Style()
    
    w = DocumentWindow(d, s)
    w.window.show()

    sys.exit(app.exec_())
