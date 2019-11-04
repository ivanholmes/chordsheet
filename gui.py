#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 29 00:02:24 2019

@author: ivan
"""

import sys, fitz, io, subprocess, os
from copy import copy

from PyQt5.QtWidgets import QApplication, QAction, QLabel, QDialogButtonBox, QDialog, QFileDialog, QMessageBox, QPushButton, QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox, QTableWidgetItem, QTabWidget, QComboBox, QWidget, QScrollArea, QMainWindow, QShortcut
from PyQt5.QtCore import QFile, QObject, Qt, pyqtSlot, QSettings
from PyQt5.QtGui import QPixmap, QImage, QKeySequence
from PyQt5 import uic
from chordsheet.tableView import ChordTableView, BlockTableView , MItemModel, MProxyStyle
 
from reportlab.lib.units import mm, cm, inch, pica
from reportlab.lib.pagesizes import A4, A5, LETTER, LEGAL
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from chordsheet.document import Document, Style, Chord, Block
from chordsheet.render import savePDF
from chordsheet.parsers import parseFingering, parseName

# set the directory where our files are depending on whether we're running a pyinstaller binary or not
if getattr(sys, 'frozen', False):
    scriptDir = sys._MEIPASS
else:
    scriptDir = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True) # enable automatic high DPI scaling on Windows
QApplication.setOrganizationName("Ivan Holmes")
QApplication.setOrganizationDomain("ivanholmes.co.uk")
QApplication.setApplicationName("Chordsheet")
settings = QSettings()

pdfmetrics.registerFont(TTFont('FreeSans', os.path.join(scriptDir, 'fonts', 'FreeSans.ttf')))
if sys.platform == "darwin":
    pdfmetrics.registerFont(TTFont('HelveticaNeue', 'HelveticaNeue.ttc', subfontIndex=0))

# dictionaries for combo boxes
pageSizeDict = {'A4':A4, 'A5':A5, 'Letter':LETTER, 'Legal':LEGAL}
unitDict = {'mm':mm, 'cm':cm, 'inch':inch, 'point':1, 'pica':pica}  # point is 1 because reportlab's native unit is points.

class DocumentWindow(QMainWindow):
    """
    Class for the main window of the application.
    """
    def __init__(self, doc, style, filename=None):
        """
        Initialisation function for the main window of the application.

        Arguments:
        doc -- the Document object for the window to use
        style -- the Style object for the window to use
        """
        super().__init__()
        
        self.doc = doc
        self.style = style
        
        self.lastDoc = copy(self.doc)
        self.currentFilePath = filename

        self.UIFileLoader(str(os.path.join(scriptDir, 'ui','mainwindow.ui')))
        self.UIInitStyle()

        self.setCentralWidget(self.window.centralWidget)
        self.setMenuBar(self.window.menuBar)
        self.setWindowTitle("Chordsheet")

        if filename:
            try:
                self.doc.loadXML(filename)
            except:
                UnreadableMessageBox().exec()

    def closeEvent(self, event):
        """
        Reimplement the built in closeEvent to allow asking the user to save.
        """
        self.saveWarning()
        
    def UIFileLoader(self, ui_file):
        """
        Loads the .ui file for this window and connects the UI elements to their actions.
        """
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
 
        self.window = uic.loadUi(ui_file)
        ui_file.close()
        
        # link all the UI elements
        self.window.actionAbout.triggered.connect(self.menuFileAboutAction)

        self.window.actionNew.triggered.connect(self.menuFileNewAction)
        self.window.actionOpen.triggered.connect(self.menuFileOpenAction)
        self.window.actionSave.triggered.connect(self.menuFileSaveAction)
        self.window.actionSave_as.triggered.connect(self.menuFileSaveAsAction)
        self.window.actionSave_PDF.triggered.connect(self.menuFileSavePDFAction)
        self.window.actionPrint.triggered.connect(self.menuFilePrintAction)
        self.window.actionClose.triggered.connect(self.menuFileCloseAction)

        self.window.actionNew.setShortcut(QKeySequence.New)
        self.window.actionOpen.setShortcut(QKeySequence.Open)
        self.window.actionSave.setShortcut(QKeySequence.Save)
        self.window.actionSave_as.setShortcut(QKeySequence.SaveAs)
        self.window.actionSave_PDF.setShortcut(QKeySequence("Ctrl+E"))
        self.window.actionPrint.setShortcut(QKeySequence.Print)
        self.window.actionClose.setShortcut(QKeySequence.Close)
        self.window.actionUndo.setShortcut(QKeySequence.Undo)
        self.window.actionRedo.setShortcut(QKeySequence.Redo)
        self.window.actionCut.setShortcut(QKeySequence.Cut)
        self.window.actionCopy.setShortcut(QKeySequence.Copy)
        self.window.actionPaste.setShortcut(QKeySequence.Paste)

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
        """
        Fills the window's fields with the values from its document.
        """
        self.updateTitleBar()

        # set all fields to appropriate values from document
        self.window.titleLineEdit.setText(self.doc.title)
        self.window.composerLineEdit.setText(self.doc.composer)
        self.window.arrangerLineEdit.setText(self.doc.arranger)
        self.window.timeSignatureSpinBox.setValue(self.doc.timeSignature)
        
        self.window.chordTableView.populate(self.doc.chordList)
        self.window.blockTableView.populate(self.doc.blockList)
        self.updateChordDict()
        
    def UIInitStyle(self):
        """
        Fills the window's fields with the values from its style.
        """
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

    def getPath(self, value): 
        """
        Wrapper for Qt settings to return home directory if no setting exists.
        """
        return str((settings.value(value) if settings.value(value) else os.path.expanduser("~")))

    def setPath(self, value, fullpath):
        """
        Wrapper for Qt settings to set path to open/save from next time from current file location.
        """
        return settings.setValue(value, os.path.dirname(fullpath))

    def menuFileNewAction(self):
        self.doc = Document()
        self.lastDoc = copy(self.doc)
        self.currentFilePath = None
        self.UIInitDocument()
        self.updatePreview()
    
    def menuFileOpenAction(self):
        filePath = QFileDialog.getOpenFileName(self.window.tabWidget, 'Open file', self.getPath("workingPath"), "Chordsheet ML files (*.xml *.cml)")
        if filePath[0]:
            self.currentFilePath = filePath[0]
            self.doc.loadXML(filePath[0])
            self.lastDoc = copy(self.doc)
            self.setPath("workingPath", self.currentFilePath)
            self.UIInitDocument()
            self.updatePreview()
    
    def menuFileSaveAction(self):
        self.updateDocument()
        if not (hasattr(self, 'currentFilePath') and self.currentFilePath):
            filePath = QFileDialog.getSaveFileName(self.window.tabWidget, 'Save file', self.getPath("workingPath"), "Chordsheet ML files (*.xml *.cml)")
            self.currentFilePath = filePath[0]
        self.doc.saveXML(self.currentFilePath)
        self.lastDoc = copy(self.doc)
        self.setPath("workingPath", self.currentFilePath)
    
    def menuFileSaveAsAction(self):
        self.updateDocument()
        filePath = QFileDialog.getSaveFileName(self.window.tabWidget, 'Save file', self.getPath("workingPath"), "Chordsheet ML files (*.xml *.cml)")
        if filePath[0]:
            self.currentFilePath = filePath[0]
            self.doc.saveXML(self.currentFilePath)
            self.lastDoc = copy(self.doc)
            self.setPath("workingPath", self.currentFilePath)
            self.updateTitleBar() # as we now have a new filename
    
    def menuFileSavePDFAction(self):
        self.updateDocument()
        self.updatePreview()
        filePath = QFileDialog.getSaveFileName(self.window.tabWidget, 'Save file', self.getPath("lastExportPath"), "PDF files (*.pdf)")
        if filePath[0]:
            savePDF(d, s, filePath[0])
            self.setPath("lastExportPath", filePath[0])
    
    def menuFilePrintAction(self):
        if sys.platform == "darwin":
            pass
        #    subprocess.call()
        else:
            pass

    @pyqtSlot()
    def menuFileCloseAction(self):
        self.saveWarning()

    def menuFileAboutAction(self):
        aboutDialog = QMessageBox.information(self, "About", "Chordsheet © Ivan Holmes, 2019", buttons = QMessageBox.Ok, defaultButton = QMessageBox.Ok)

    def saveWarning(self):
        """
        Function to check if the document has unsaved data in it and offer to save it.
        """
        self.updateDocument() # update the document to catch all changes

        if (self.lastDoc == self.doc):
            self.close()
        else:
            wantToSave = UnsavedMessageBox().exec()
                
            if wantToSave == QMessageBox.Save:
                if not (hasattr(self, 'currentFilePath') and self.currentFilePath):
                    filePath = QFileDialog.getSaveFileName(self.window.tabWidget, 'Save file', str(os.path.expanduser("~")), "Chordsheet ML files (*.xml *.cml)")
                    self.currentFilePath = filePath[0]
                self.doc.saveXML(self.currentFilePath)
                self.close()
                
            elif wantToSave == QMessageBox.Discard:
                self.close()
            # if cancel or anything else do nothing at all
    
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
            self.doc.chordList[-1].voicings['guitar'] = parseFingering(self.window.guitarVoicingLineEdit.text(), 'guitar')

        self.window.chordTableView.populate(self.doc.chordList)
        self.clearChordLineEdits()
        self.updateChordDict()

    def updateChordAction(self):
        if self.window.chordTableView.selectionModel().hasSelection():
            self.updateChords()
            row = self.window.chordTableView.selectionModel().currentIndex().row()
            self.doc.chordList[row] = Chord(parseName(self.window.chordNameLineEdit.text()))
            if self.window.guitarVoicingLineEdit.text():
                self.doc.chordList[-1].voicings['guitar'] = parseFingering(self.window.guitarVoicingLineEdit.text(), 'guitar')

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
    
    def updateTitleBar(self):
        appName = "Chordsheet"
        if self.currentFilePath:
            self.setWindowTitle(appName + " – " + os.path.basename(self.currentFilePath))
        else:
            self.setWindowTitle(appName)

    def updateChords(self):
        chordTableList = []
        for i in range(self.window.chordTableView.model.rowCount()):
            chordTableList.append(Chord(parseName(self.window.chordTableView.model.item(i, 0).text()))),
            if self.window.chordTableView.model.item(i, 1).text():
                chordTableList[-1].voicings['guitar'] = parseFingering(self.window.chordTableView.model.item(i, 1).text(), 'guitar')
            
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
    """
    Dialogue to allow the user to enter a guitar chord voicing. Not particularly advanced at present!
    May be extended in future.
    """
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

class UnsavedMessageBox(QMessageBox):
    """
    Message box to alert the user of unsaved changes and allow them to choose how to act.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Unsaved changes")
        self.setText("The document has been modified.")
        self.setInformativeText("Do you want to save your changes?")
        self.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Save)

class UnreadableMessageBox(QMessageBox):
    """
    Message box to inform the user that the chosen file cannot be opened.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File cannot be opened")
        self.setText("The file you have selected cannot be opened.")
        self.setInformativeText("Please make sure it is in the right format.")
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    d = Document()
    s = Style()
    
    w = DocumentWindow(d, s, filename=(sys.argv[1] if len(sys.argv) > 1 else None)) # pass first argument as filename 
    w.show()

    sys.exit(app.exec_())
